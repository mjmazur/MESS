import re

with open("responsivity_calculator.py", "r") as f:
    content = f.read()

# 1. StarSpectraLibrary load_index and get_star
content = content.replace('''    def load_index(self, index_path):
        import csv
        try:
            with open(index_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        sao = int(row['SAO'])
                        hip = int(row['HIP'])
                        self.sao_map[sao] = hip
                    except: continue
            print(f"Loaded {len(self.sao_map)} SAO-HIP mappings from {index_path}")
        except Exception as e:
            print(f"Error loading star index: {e}")

    def get_hip_from_sao(self, sao):
        return self.sao_map.get(sao)''',
'''    def load_index(self, index_path):
        import csv
        self.hip_names = {}
        try:
            with open(index_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        sao = int(row['SAO'])
                        hip = int(row['HIP'])
                        self.sao_map[sao] = hip
                        if 'Name' in row and row['Name'].strip():
                            self.hip_names[hip] = row['Name'].strip()
                    except: continue
            print(f"Loaded {len(self.sao_map)} SAO-HIP mappings from {index_path}")
        except Exception as e:
            print(f"Error loading star index: {e}")

    def get_hip_from_sao(self, sao):
        return self.sao_map.get(sao)''')

content = content.replace('''    def get_star(self, hip):
        return self.stars.get(hip)''',
'''    def get_star(self, hip):
        star = self.stars.get(hip)
        if star:
            star['name'] = getattr(self, 'hip_names', {}).get(hip, f"HIP {hip}")
        return star''')

# 2. SpectralScaler zoom logic
content = content.replace('''        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        plt.tight_layout()
        plt.show()''',
'''        self.zoom_xlim = self.ax.get_xlim()
        self.zoom_ylim = self.ax.get_ylim()
        
        def on_lims_change(axes):
            self.zoom_xlim = axes.get_xlim()
            self.zoom_ylim = axes.get_ylim()
            self.update_aoi()
            
        self.ax.callbacks.connect('xlim_changed', on_lims_change)
        self.ax.callbacks.connect('ylim_changed', on_lims_change)
        
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        plt.tight_layout()
        plt.show()''')

content = content.replace('''        # Remove old AOI if it exists
        for artist in self.aoi_artist:
            artist.remove()
        self.aoi_artist = []
        
        if len(self.points) < 2:
            return''',
'''        if len(self.points) < 2:
            return''')

content = content.replace('''        width = self.image_data.shape[1]
        height = self.image_data.shape[0]
        
        if dx != 0:
            x0, x1 = 0, width
            y0, y1 = b, m * width + b
        else:
            x0, x1 = b, b
            y0, y1 = 0, height
            
        # AOI corners
        c1 = (x0 + ox, y0 + oy)
        c2 = (x1 + ox, y1 + oy)
        c3 = (x1 - ox, y1 - oy)
        c4 = (x0 - ox, y0 - oy)
        
        poly = plt.Polygon([c1, c2, c3, c4], color='yellow', alpha=0.15, fill=True, zorder=1)
        l1, = self.ax.plot([c1[0], c2[0]], [c1[1], c2[1]], 'y--', alpha=0.4, linewidth=1, zorder=2)
        l2, = self.ax.plot([c4[0], c3[0]], [c4[1], c3[1]], 'y--', alpha=0.4, linewidth=1, zorder=2)
        
        self.aoi_artist = [poly, l1, l2]
        self.ax.add_patch(poly)''',
'''        width = self.image_data.shape[1]
        height = self.image_data.shape[0]
        
        x_min, x_max = min(self.zoom_xlim), max(self.zoom_xlim)
        y_min, y_max = min(self.zoom_ylim), max(self.zoom_ylim)
        
        x0, x1 = max(0, x_min), min(width, x_max)
        
        if dx != 0:
            y0, y1 = m * x0 + b, m * x1 + b
        else:
            x0, x1 = b, b
            y0, y1 = max(0, y_min), min(height, y_max)
            
        # AOI corners
        c1 = (x0 + ox, y0 + oy)
        c2 = (x1 + ox, y1 + oy)
        c3 = (x1 - ox, y1 - oy)
        c4 = (x0 - ox, y0 - oy)
        
        if not self.aoi_artist:
            poly = plt.Polygon([c1, c2, c3, c4], color='yellow', alpha=0.15, fill=True, zorder=1)
            l1, = self.ax.plot([c1[0], c2[0]], [c1[1], c2[1]], 'y--', alpha=0.4, linewidth=1, zorder=2)
            l2, = self.ax.plot([c4[0], c3[0]], [c4[1], c3[1]], 'y--', alpha=0.4, linewidth=1, zorder=2)
            
            self.aoi_artist = [poly, l1, l2]
            self.ax.add_patch(poly)
        else:
            self.aoi_artist[0].set_xy([c1, c2, c3, c4])
            self.aoi_artist[1].set_data([c1[0], c2[0]], [c1[1], c2[1]])
            self.aoi_artist[2].set_data([c4[0], c3[0]], [c4[1], c3[1]])''')

content = content.replace('''        # Create a mask to identify the original image boundaries after rotation
        mask = np.ones_like(self.image_data, dtype=float)
        rotated_mask = nd.rotate(mask, angle_deg, reshape=True, order=0)''',
'''        # Create a mask to identify the zoomed-in image boundaries after rotation
        mask = np.zeros_like(self.image_data, dtype=float)
        
        x_min, x_max = int(max(0, min(self.zoom_xlim))), int(min(w, max(self.zoom_xlim)))
        y_min, y_max = int(max(0, min(self.zoom_ylim))), int(min(h, max(self.zoom_ylim)))
        
        mask[y_min:y_max, x_min:x_max] = 1.0
        
        rotated_mask = nd.rotate(mask, angle_deg, reshape=True, order=0)''')

# 3. InteractiveProfile
content = content.replace('''class InteractiveProfile:
    def __init__(self, strip, profile, filename, scaler=None, ref_spec=None):
        self.strip = strip
        self.profile = profile
        self.filename = filename
        self.scaler = scaler
        self.ref_spec = ref_spec
        
        has_star = (self.ref_spec is not None and hasattr(self.scaler, 'm') and hasattr(self.scaler, 'c'))
        
        if has_star:
            self.fig, (self.ax_star, self.ax_prof, self.ax_strip) = plt.subplots(3, 1, figsize=(12, 10), 
                                                                   gridspec_kw={'height_ratios': [2, 3, 1], 'hspace': 0.05},
                                                                   sharex=True)''',
'''class InteractiveProfile:
    def __init__(self, strip, profile, filename, scaler=None, ref_spec=None, star_info=None):
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
                                                                   sharex=True)''')

content = content.replace('''        else:
            self.fig, (self.ax_prof, self.ax_strip) = plt.subplots(2, 1, figsize=(12, 8), 
                                                                   gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.05},
                                                                   sharex=True)''',
'''        else:
            self.fig, (self.ax_prof, self.ax_strip) = plt.subplots(2, 1, figsize=(12, 8), 
                                                                   gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.3},
                                                                   sharex=True)''')

content = content.replace('''        self.ax_prof.set_ylabel("Intensity")
        self.ax_prof.set_title(f"Extracted Spectrum Profile: {filename}")
        self.ax_prof.grid(True, alpha=0.3)
        
        # Display strip''',
'''        self.ax_prof.set_ylabel("Intensity")
        self.ax_prof.set_title(f"Extracted Spectrum Profile: {filename}")
        self.ax_prof.grid(True, alpha=0.3)
        
        if hasattr(self.scaler, 'm') and hasattr(self.scaler, 'c'):
            info_text = f"Scale: {self.scaler.m:.4f} nm/px\\nIntercept: {self.scaler.c:.2f} nm"
            if self.star_info:
                info_text += f"\\nStar: {self.star_info.get('name', 'Unknown')} ({self.star_info.get('sptype', 'Unknown')})"
                
            self.info_box = self.ax_prof.text(0.02, 0.95, info_text, 
                                              transform=self.ax_prof.transAxes, verticalalignment='top', 
                                              bbox=dict(facecolor='white', alpha=0.8, edgecolor='black'))
        
        if has_star:
            self.update_responsivity(wls)
        
        # Display strip''')

content = content.replace('''        self.ax_star.set_xlim(min(new_wls), max(new_wls))
        self.fig.canvas.draw()
        print("Plots updated with new calibration!")''',
'''        self.ax_star.set_xlim(min(new_wls), max(new_wls))
        
        if hasattr(self, 'info_box'):
            info_text = f"Scale: {m:.4f} nm/px\\nIntercept: {c:.2f} nm"
            if self.star_info:
                info_text += f"\\nStar: {self.star_info.get('name', 'Unknown')} ({self.star_info.get('sptype', 'Unknown')})"
            self.info_box.set_text(info_text)
            
        if hasattr(self, 'ax_resp'):
            self.update_responsivity(new_wls)
            
        self.fig.canvas.draw()
        print("Plots updated with new calibration!")

    def update_responsivity(self, wls):
        smoothed_prof = nd.gaussian_filter1d(self.profile, sigma=5)
        smoothed_star = nd.gaussian_filter1d(self.ref_spec[1], sigma=5)
        
        interp_star = np.interp(wls, self.ref_spec[0], smoothed_star)
        
        # Avoid division by zero
        interp_star[interp_star < 1e-6] = 1e-6
        resp = smoothed_prof / interp_star
        
        if self.resp_line is None:
            self.resp_line, = self.ax_resp.plot(wls, resp, 'g-')
            self.ax_resp.set_ylabel("Responsivity")
            self.ax_resp.set_title("System Responsivity (Smoothed Extracted / Smoothed Star)")
            self.ax_resp.grid(True, alpha=0.3)
        else:
            self.resp_line.set_xdata(wls)
            self.resp_line.set_ydata(resp)
            self.ax_resp.relim()
            self.ax_resp.autoscale_view(scalex=False, scaley=True)
            
        self.resp_data = (wls, resp)''')

content = content.replace('''                        print(f"Reference star selected: HIP {star_hip} ({star_info['sptype']})")
                        ref_spec = (lib.wavelengths, star_info['intensities'])
                    else:
                        print(f"Error: Star HIP {star_hip} not found in library.")
                        lib.list_stars()

            InteractiveProfile(strip, profile, os.path.basename(image_path), scaler=scaler, ref_spec=ref_spec)
            plt.show()''',
'''                        print(f"Reference star selected: {star_info.get('name', 'Unknown')} ({star_info['sptype']})")
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
                    print("Error: No visible responsivity data to export.")''')

with open("responsivity_calculator.py", "w") as f:
    f.write(content)
