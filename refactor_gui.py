import re
import sys

with open("responsivity_calculator.py", "r") as f:
    content = f.read()

# 1. Imports
content = content.replace("import argparse", "import argparse\nfrom PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter, QWidget, QVBoxLayout, QInputDialog, QMessageBox, QAction, QFileDialog, QToolBar\nfrom PyQt5.QtCore import Qt\nfrom matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas\nfrom matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar\nfrom matplotlib.figure import Figure\n")

# 2. SpectralScaler init
old_scaler_init = """    def __init__(self, image_data, filename, aoi_width=10):
        self.image_data = image_data
        self.filename = filename
        self.aoi_width = aoi_width
        self.points = [] # list of (pixel_x, pixel_y, wavelength)
        self.aoi_artist = []
        
        # Set up plot
        self.fig, self.ax = plt.subplots(figsize=(12, 8))"""
new_scaler_init = """    def __init__(self, image_data, filename, aoi_width=10, canvas=None, fig=None, ax=None, on_extracted=None):
        self.image_data = image_data
        self.filename = filename
        self.aoi_width = aoi_width
        self.points = [] # list of (pixel_x, pixel_y, wavelength)
        self.aoi_artist = []
        self.canvas = canvas
        self.fig = fig
        self.ax = ax
        self.on_extracted = on_extracted"""
content = content.replace(old_scaler_init, new_scaler_init)

content = content.replace("self.fig.colorbar(self.img_plot, label='Intensity')", "self.fig.colorbar(self.img_plot, label='Intensity', ax=self.ax)")

old_scaler_show = """        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        plt.tight_layout()
        plt.show()"""
new_scaler_show = """        self.cid = self.canvas.mpl_connect('button_press_event', self.onclick)
        self.fig.tight_layout()
        self.canvas.draw()"""
content = content.replace(old_scaler_show, new_scaler_show)

# 3. SpectralScaler onclick
old_onclick = """        print(f"\\nClicked at pixel coordinate: x={px:.2f}, y={py:.2f}")
        try:
            wl_input = input("Enter wavelength in nm (or 'c' to cancel): ").strip()
            if wl_input.lower() == 'c' or wl_input == '':
                temp_mark.remove()
                self.fig.canvas.draw()
                print("Point cancelled.")
                return
            
            wl = float(wl_input)"""
new_onclick = """        print(f"\\nClicked at pixel coordinate: x={px:.2f}, y={py:.2f}")
        try:
            wl, ok = QInputDialog.getDouble(None, "Wavelength Input", f"Enter wavelength in nm for pixel x={px:.2f}:", decimals=2, min=0, max=10000)
            if not ok:
                temp_mark.remove()
                self.canvas.draw()
                print("Point cancelled.")
                return"""
content = content.replace(old_onclick, new_onclick)

content = content.replace("self.fig.canvas.draw()", "self.canvas.draw()")

old_onclick_end = """            if len(self.points) >= 2:
                self.update_aoi()
                
            self.canvas.draw()
            print(f"Added: Pixel {px:.2f} -> {wl} nm")
            
        except ValueError:"""
new_onclick_end = """            if len(self.points) >= 2:
                self.update_aoi()
                
            self.canvas.draw()
            print(f"Added: Pixel {px:.2f} -> {wl} nm")
            
            if len(self.points) >= 2:
                if self.report():
                    strip, profile, angle = self.extract_spectrum(aoi_width=self.aoi_width)
                    if strip is not None and self.on_extracted:
                        self.on_extracted(strip, profile, angle, self)
            
        except ValueError:"""
content = content.replace(old_onclick_end, new_onclick_end)


# 4. InteractiveProfile init
old_prof_init = """    def __init__(self, strip, profile, filename, scaler=None, ref_spec=None, star_info=None):
        self.strip = strip
        self.profile = profile
        self.filename = filename
        self.scaler = scaler
        self.ref_spec = ref_spec
        self.star_info = star_info
        self.resp_line = None
        
        has_star = (self.ref_spec is not None and hasattr(self.scaler, 'm') and hasattr(self.scaler, 'c'))
        
        if has_star:
            self.fig, (self.ax_resp, self.ax_star, self.ax_prof, self.ax_strip) = plt.subplots(4, 1, figsize=(12, 12), 
                                                                   gridspec_kw={'height_ratios': [2, 2, 3, 1], 'hspace': 0.3},
                                                                   sharex=True)"""
new_prof_init = """    def __init__(self, strip, profile, filename, scaler=None, ref_spec=None, star_info=None, canvas=None, fig=None, ax_resp=None, ax_star=None, ax_prof=None, ax_strip=None):
        self.strip = strip
        self.profile = profile
        self.filename = filename
        self.scaler = scaler
        self.ref_spec = ref_spec
        self.star_info = star_info
        self.resp_line = None
        
        self.canvas = canvas
        self.fig = fig
        self.ax_resp = ax_resp
        self.ax_star = ax_star
        self.ax_prof = ax_prof
        self.ax_strip = ax_strip
        
        has_star = (self.ref_spec is not None and hasattr(self.scaler, 'm') and hasattr(self.scaler, 'c'))
        
        if has_star:
            pass # Axes are passed in from MainWindow"""
content = content.replace(old_prof_init, new_prof_init)

old_prof_else = """        else:
            self.fig, (self.ax_prof, self.ax_strip) = plt.subplots(2, 1, figsize=(12, 8), 
                                                                   gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.3},
                                                                   sharex=True)"""
new_prof_else = """        else:
            pass # Axes are passed in from MainWindow"""
content = content.replace(old_prof_else, new_prof_else)

old_prof_show = """        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        plt.tight_layout()
        plt.show()"""
new_prof_show = """        self.cid = self.canvas.mpl_connect('button_press_event', self.onclick)
        self.fig.tight_layout()
        self.canvas.draw()"""
content = content.replace(old_prof_show, new_prof_show)


# 5. MainWindow class definition
main_window_code = """
class MainWindow(QMainWindow):
    def __init__(self, data, filename, image_path, args, ref_spec=None, star_info=None):
        super().__init__()
        self.setWindowTitle("Unified Responsivity Calculator")
        self.resize(1600, 900)
        
        self.data = data
        self.filename = filename
        self.image_path = image_path
        self.args = args
        self.ref_spec = ref_spec
        self.star_info = star_info
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)
        
        # Left Panel (Image)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.img_fig = Figure(figsize=(8, 8))
        self.img_canvas = FigureCanvas(self.img_fig)
        self.img_ax = self.img_fig.add_subplot(111)
        left_layout.addWidget(NavigationToolbar(self.img_canvas, self))
        left_layout.addWidget(self.img_canvas)
        self.splitter.addWidget(left_widget)
        
        # Right Panel (Profiles)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self.prof_fig = Figure(figsize=(8, 8))
        self.prof_canvas = FigureCanvas(self.prof_fig)
        right_layout.addWidget(NavigationToolbar(self.prof_canvas, self))
        right_layout.addWidget(self.prof_canvas)
        self.splitter.addWidget(right_widget)
        
        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        export_action = QAction("Export CSV", self)
        export_action.triggered.connect(self.export_csv)
        toolbar.addAction(export_action)
        
        self.init_left()
        
    def init_left(self):
        self.scaler = SpectralScaler(self.data, self.filename, aoi_width=self.args.aoi_width,
                                     canvas=self.img_canvas, fig=self.img_fig, ax=self.img_ax,
                                     on_extracted=self.on_extracted)
                                     
    def on_extracted(self, strip, profile, angle, scaler):
        self.prof_fig.clear()
        has_star = (self.ref_spec is not None)
        
        if has_star:
            ax_resp, ax_star, ax_prof, ax_strip = self.prof_fig.subplots(4, 1, gridspec_kw={'height_ratios': [2, 2, 3, 1], 'hspace': 0.3}, sharex=True)
            self.profile_app = InteractiveProfile(strip, profile, self.filename, scaler=scaler, ref_spec=self.ref_spec, star_info=self.star_info, canvas=self.prof_canvas, fig=self.prof_fig, ax_resp=ax_resp, ax_star=ax_star, ax_prof=ax_prof, ax_strip=ax_strip)
        else:
            ax_prof, ax_strip = self.prof_fig.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.3}, sharex=True)
            self.profile_app = InteractiveProfile(strip, profile, self.filename, scaler=scaler, canvas=self.prof_canvas, fig=self.prof_fig, ax_prof=ax_prof, ax_strip=ax_strip)

    def export_csv(self):
        if hasattr(self, 'profile_app') and hasattr(self.profile_app, 'resp_data') and self.star_info:
            wls, resp = self.profile_app.resp_data
            xlims = self.profile_app.ax_resp.get_xlim()
            valid_mask = (wls >= min(xlims)) & (wls <= max(xlims))
            vis_wls = wls[valid_mask]
            vis_resp = resp[valid_mask]
            
            if len(vis_wls) > 0:
                import re, os
                date_match = re.search(r'(\d{8})', os.path.basename(self.image_path))
                date_str = date_match.group(1) if date_match else "YYYYMMDD"
                
                sao_match = re.search(r'sao0*(\d+)', os.path.basename(self.image_path), re.IGNORECASE)
                sao_num = sao_match.group(1) if sao_match else "Unknown"
                
                common_name = self.star_info.get('name', 'Unknown').replace(" ", "")
                csv_filename = f"response_{common_name}_{sao_num}_{date_str}.csv"
                out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_filename)
                
                out_wls = np.arange(300, 1101, 1.0)
                out_resp = np.interp(out_wls, vis_wls, vis_resp)
                
                try:
                    with open(out_path, 'w') as f:
                        f.write("Wavelength_nm,Responsivity\\n")
                        for w, r in zip(out_wls, out_resp):
                            f.write(f"{w:.1f},{r:.8f}\\n")
                    QMessageBox.information(self, "Export Successful", f"Saved to:\\n{out_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Export Error", f"Error saving CSV:\\n{e}")
            else:
                QMessageBox.warning(self, "Export Error", "No visible responsivity data to export.")
        else:
            QMessageBox.warning(self, "Export Error", "Calibration incomplete or no reference star.")
"""

# Insert MainWindow before def main():
content = content.replace("def main():", main_window_code + "\ndef main():")

# 6. main function refactor
old_main_extract = """    scaler = SpectralScaler(data, os.path.basename(image_path), aoi_width=args.aoi_width)
    if scaler.report():
        strip, profile, angle = scaler.extract_spectrum(aoi_width=args.aoi_width, mode=args.mode)
        if strip is not None:
            # Load star library if requested
            ref_spec = None
            lib_path = args.lib or os.path.join(os.path.dirname(__file__), "spectral_library/DriverInputFiles/StarSpectra_V5.0_RA_0_360_DEC_56_90.txt")
            
            # Try to auto-detect star from filename if not provided
            star_hip = args.star
            if star_hip is None:
                import re
                match = re.search(r'sao0*(\d+)', os.path.basename(image_path), re.IGNORECASE)
                if match:
                    sao_num = int(match.group(1))
                    print(f"Detected SAO {sao_num} from filename.")
                    lib = StarSpectraLibrary(lib_path)
                    star_hip = lib.get_hip_from_sao(sao_num)
                    if star_hip:
                        print(f"Mapped SAO {sao_num} to HIP {star_hip}")
                    else:
                        print(f"Warning: SAO {sao_num} not in star_index.csv")

            if star_hip or args.lib:
                if 'lib' not in locals(): # Might already be loaded by auto-detect
                    lib = StarSpectraLibrary(lib_path)
                
                if star_hip:
                    star_info = lib.get_star(star_hip)
                    if star_info:
                        print(f"Reference star selected: {star_info.get('name', 'Unknown')} ({star_info['sptype']})")
                        ref_spec = (lib.wavelengths, star_info['intensities'])
                    else:
                        print(f"Error: Star HIP {star_hip} not found in library.")
                        lib.list_stars()

            profile_app = InteractiveProfile(strip, profile, os.path.basename(image_path), scaler=scaler, ref_spec=ref_spec, star_info=star_info if 'star_info' in locals() else None)
            plt.show()
            
            # Export responsivity when window is closed
            if hasattr(profile_app, 'resp_data') and profile_app.star_info:
                print("\\nProcessing final responsivity curve for export...")
                wls, resp = profile_app.resp_data
                xlims = profile_app.ax_resp.get_xlim()
                
                # Get visible region
                valid_mask = (wls >= min(xlims)) & (wls <= max(xlims))
                vis_wls = wls[valid_mask]
                vis_resp = resp[valid_mask]
                
                if len(vis_wls) > 0:
                    import re
                    # Parse filename metadata
                    date_match = re.search(r'(\d{8})', os.path.basename(image_path))
                    date_str = date_match.group(1) if date_match else "YYYYMMDD"
                    
                    sao_match = re.search(r'sao0*(\d+)', os.path.basename(image_path), re.IGNORECASE)
                    sao_num = sao_match.group(1) if sao_match else "Unknown"
                    
                    common_name = profile_app.star_info.get('name', 'Unknown').replace(" ", "")
                    
                    csv_filename = f"response_{common_name}_{sao_num}_{date_str}.csv"
                    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_filename)
                    
                    # 1 nm interpolation grid from 300 to 1100
                    out_wls = np.arange(300, 1101, 1.0)
                    
                    # np.interp handles the flat extrapolation by default at boundaries
                    out_resp = np.interp(out_wls, vis_wls, vis_resp)
                    
                    try:
                        with open(out_path, 'w') as f:
                            f.write("Wavelength_nm,Responsivity\\n")
                            for w, r in zip(out_wls, out_resp):
                                f.write(f"{w:.1f},{r:.8f}\\n")
                        print(f"Success: Saved extrapolated responsivity curve to {out_path}")
                    except Exception as e:
                        print(f"Error saving CSV: {e}")
                else:
                    print("Error: No visible responsivity data to export.")"""

new_main_extract = """    app = QApplication(sys.argv)
    
    # Load star library if requested
    ref_spec = None
    star_info = None
    lib_path = args.lib or os.path.join(os.path.dirname(__file__), "spectral_library/DriverInputFiles/StarSpectra_V5.0_RA_0_360_DEC_56_90.txt")
    
    star_hip = args.star
    if star_hip is None:
        import re
        match = re.search(r'sao0*(\d+)', os.path.basename(image_path), re.IGNORECASE)
        if match:
            sao_num = int(match.group(1))
            lib = StarSpectraLibrary(lib_path)
            star_hip = lib.get_hip_from_sao(sao_num)
            if not star_hip:
                print(f"Warning: SAO {sao_num} not in star_index.csv")

    if star_hip or args.lib:
        if 'lib' not in locals():
            lib = StarSpectraLibrary(lib_path)
        
        if star_hip:
            star_info = lib.get_star(star_hip)
            if star_info:
                ref_spec = (lib.wavelengths, star_info['intensities'])

    window = MainWindow(data, os.path.basename(image_path), image_path, args, ref_spec=ref_spec, star_info=star_info)
    window.show()
    sys.exit(app.exec_())"""
content = content.replace(old_main_extract, new_main_extract)

with open("responsivity_calculator.py", "w") as f:
    f.write(content)
