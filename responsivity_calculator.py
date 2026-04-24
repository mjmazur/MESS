#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import argparse
from PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter, QWidget, QVBoxLayout, QInputDialog, QMessageBox, QAction, QFileDialog, QToolBar
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import os
import sys
import scipy.ndimage as nd

def load_image(path, byteswap=True):
    """Load a 16-bit PNG and optionally byteswap it."""
    try:
        img = Image.open(path)
        data = np.asarray(img)
        if byteswap:
            # Check if it's actually 16-bit before swapping? 
            # Usually these are uint16.
            if data.dtype == np.uint16:
                data = data.byteswap()
            else:
                print(f"Warning: Image is {data.dtype}, not uint16. Byteswap might not be necessary or correct.")
                data = data.byteswap() # Following ByteSwapViewer.py logic
        return data
    except Exception as e:
        print(f"Error loading image: {e}")
        sys.exit(1)

class StarSpectraLibrary:
    def __init__(self, filepath, index_path="star_index.csv"):
        self.stars = {}
        self.sao_map = {}
        self.wavelengths = []
        self.scale_factor = 1.0
        if filepath and os.path.exists(filepath):
            self.parse_file(filepath)
        elif filepath:
            print(f"Warning: Star library file {filepath} not found.")
        
        if os.path.exists(index_path):
            self.load_index(index_path)

    def load_index(self, index_path):
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
        return self.sao_map.get(sao)

    def parse_file(self, filepath):
        print(f"Parsing star library: {filepath}...")
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading star library: {e}")
            return

        for line in lines:
            if "Spectra scale factor =" in line:
                try:
                    self.scale_factor = float(line.split('=')[1].strip())
                except: pass
            
            # Header line with wavelengths
            if "HIP#" in line and ":" in line:
                parts = line.split(':')
                wl_parts = parts[1].split()
                self.wavelengths = np.array([float(x) for x in wl_parts])
                continue

            line_strip = line.strip()
            # Skip comments and metadata-only lines
            if not line_strip or line_strip.startswith('-') or "=" in line or ":" in line:
                continue
                
            parts = line_strip.split()
            # Expecting metadata + wavelengths
            if len(parts) > 10:
                try:
                    hip = int(parts[0])
                    sptype = parts[1]
                    # The intensities start at index 8
                    intensities = np.array([float(x) for x in parts[8:]]) * self.scale_factor
                    
                    self.stars[hip] = {
                        'sptype': sptype,
                        'vmag': float(parts[4]),
                        'bv': float(parts[5]),
                        'intensities': intensities
                    }
                except (ValueError, IndexError):
                    continue

    def get_star(self, hip):
        star = self.stars.get(hip)
        if star:
            star['name'] = getattr(self, 'hip_names', {}).get(hip, f"HIP {hip}")
        return star

    def list_stars(self, limit=10):
        print("\nAvailable stars in library (first 10):")
        for hip, info in list(self.stars.items())[:limit]:
            print(f"  HIP {hip:6d} | SpType: {info['sptype']:5s} | Vmag: {info['vmag']:5.2f}")

class SpectralScaler:
    def __init__(self, image_data, filename, aoi_width=10, canvas=None, fig=None, ax=None, on_extracted=None):
        self.image_data = image_data
        self.filename = filename
        self.aoi_width = aoi_width
        self.points = [] # list of (pixel_x, pixel_y, wavelength)
        self.aoi_artist = []
        self.canvas = canvas
        self.fig = fig
        self.ax = ax
        self.on_extracted = on_extracted
        
        # Auto-scale vmin/vmax for better visibility of spectral lines
        # Using percentiles to avoid being blinded by hot pixels or noise
        vmin = np.percentile(self.image_data, 1)
        vmax = np.percentile(self.image_data, 99.9)
        
        self.img_plot = self.ax.imshow(self.image_data, cmap='viridis', origin='upper', vmin=vmin, vmax=vmax)
        self.fig.colorbar(self.img_plot, label='Intensity', ax=self.ax)
        
        self.ax.set_title(f"Spectral Calibration: {filename}\nClick on features to assign wavelengths. Close window when done.")
        self.ax.set_xlabel("Pixel X")
        self.ax.set_ylabel("Pixel Y")
        
        print("\n--- Interaction Instructions ---")
        print("1. Click on a spectral feature in the image.")
        print("2. Go to this terminal and enter the wavelength (in nm).")
        print("3. Repeat for at least 2 points.")
        print("4. Close the plot window to finish and see results.")
        
        self.zoom_xlim = self.ax.get_xlim()
        self.zoom_ylim = self.ax.get_ylim()
        
        def on_lims_change(axes):
            self.zoom_xlim = axes.get_xlim()
            self.zoom_ylim = axes.get_ylim()
            self.update_aoi()
            
        self.ax.callbacks.connect('xlim_changed', on_lims_change)
        self.ax.callbacks.connect('ylim_changed', on_lims_change)
        
        self.cid = self.canvas.mpl_connect('button_press_event', self.onclick)
        self.fig.tight_layout()
        self.canvas.draw()

    def onclick(self, event):
        if event.inaxes != self.ax:
            return
        
        px = event.xdata
        py = event.ydata
        
        # Mark the spot temporarily
        temp_mark, = self.ax.plot(px, py, 'ro', markersize=10, alpha=0.5)
        self.canvas.draw()
        
        print(f"\nClicked at pixel coordinate: x={px:.2f}, y={py:.2f}")
        try:
            wl, ok = QInputDialog.getDouble(None, "Wavelength Input", f"Enter wavelength in nm for pixel x={px:.2f}:", decimals=2, min=0, max=10000)
            if not ok:
                temp_mark.remove()
                self.canvas.draw()
                print("Point cancelled.")
                return
            self.points.append((px, py, wl)) # Store py too for angle calculation
            
            # Update plot with permanent marker and label
            self.ax.plot(px, py, 'rx')
            self.ax.text(px, py + 10, f"{wl}nm", color='white', fontweight='bold', 
                         bbox=dict(facecolor='black', alpha=0.5))
            
            if len(self.points) >= 2:
                self.update_aoi()
                
            self.canvas.draw()
            print(f"Added: Pixel {px:.2f} -> {wl} nm")
            
            if len(self.points) >= 2:
                if self.report():
                    strip, profile, angle = self.extract_spectrum(aoi_width=self.aoi_width)
                    if strip is not None and self.on_extracted:
                        self.on_extracted(strip, profile, angle, self)
            
        except ValueError:
            print("Error: Invalid wavelength. Please enter a number.")
            temp_mark.remove()
            self.canvas.draw()

    def update_aoi(self):
        """Draw the Area of Interest (AOI) on the main plot."""
        if len(self.points) < 2:
            return
            
        pts = np.array([(p[0], p[1]) for p in self.points])
        x_pts = pts[:, 0]
        y_pts = pts[:, 1]
        
        # Calculate line
        if len(self.points) == 2:
            dx = pts[1, 0] - pts[0, 0]
            dy = pts[1, 1] - pts[0, 1]
            m = dy / dx if dx != 0 else np.inf
            b = pts[0, 1] - m * pts[0, 0] if dx != 0 else pts[0, 0]
        else:
            # Linear fit for more than 2 points
            m, b = np.polyfit(x_pts, y_pts, 1)
            dx = 1.0
            dy = m
            
        angle = np.arctan2(dy, dx)
        perp_angle = angle + np.pi/2
        
        half_w = self.aoi_width / 2.0
        ox = half_w * np.cos(perp_angle)
        oy = half_w * np.sin(perp_angle)
        
        width = self.image_data.shape[1]
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
            self.aoi_artist[2].set_data([c4[0], c3[0]], [c4[1], c3[1]])

    def report(self):
        if len(self.points) < 2:
            print("\nError: At least two points are required to calculate the spectral scale.")
            return False

        # Sort points by pixel position
        self.points.sort()
        pixels_x = np.array([p[0] for p in self.points])
        wls = np.array([p[2] for p in self.points])
        
        # Linear fit: wl = m * pixel_x + c
        # (Assuming dispersion is primarily horizontal)
        m, c = np.polyfit(pixels_x, wls, 1)
        self.m = m
        self.c = c
        
        print("\n" + "="*40)
        print("CALIBRATION RESULTS")
        print("="*40)
        for p in self.points:
            print(f"Pixel X: {p[0]:8.2f} | Assigned: {p[2]:8.2f} nm")
        
        print("-" * 40)
        print(f"Spectral Scale: {m:.6f} nm/pixel")
        print(f"Intercept:      {c:.4f} nm")
        print("-" * 40)
        
        # Calculate residuals
        fit_wls = m * pixels_x + c
        residuals = wls - fit_wls
        for i, res in enumerate(residuals):
            print(f"Point {i+1} residual: {res:+.4f} nm")
        
        rmse = np.sqrt(np.mean(residuals**2))
        print(f"RMSE:           {rmse:.4f} nm")
        print("="*40)
        return True

    def extract_spectrum(self, aoi_width=10, mode='mean'):
        if len(self.points) < 2:
            return

        p1 = self.points[0]
        p2 = self.points[-1]
        
        # Calculate angle (in degrees)
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        angle_rad = np.arctan2(dy, dx)
        angle_deg = np.degrees(angle_rad)
        
        print(f"\nRotating image by {angle_deg:.2f} degrees CCW to align spectrum...")
        
        # Rotate image so the line is horizontal
        # reshape=True ensures we don't crop the corners.
        # If the line is at angle_deg (measured with y-down), 
        # rotating the image by +angle_deg CCW will bring it to horizontal.
        rotated = nd.rotate(self.image_data, angle_deg, reshape=True, order=1)
        
        # Find the new position of the points
        h, w = self.image_data.shape
        rh, rw = rotated.shape
        cx, cy = w / 2.0, h / 2.0
        rcx, rcy = rw / 2.0, rh / 2.0
        
        # The coordinate transformation should match the rotation angle used in nd.rotate
        def get_rotated_coord(x, y):
            # Move to origin (center of image)
            nx = x - cx
            ny = y - cy
            # CCW rotation in y-down coordinates:
            # x' = x*cos(A) + y*sin(A)
            # y' = -x*sin(A) + y*cos(A)
            rx = nx * np.cos(angle_rad) + ny * np.sin(angle_rad)
            ry = -nx * np.sin(angle_rad) + ny * np.cos(angle_rad)
            # Move to new center
            return rx + rcx, ry + rcy

        rp1 = get_rotated_coord(p1[0], p1[1])
        rp2 = get_rotated_coord(p2[0], p2[1])
        
        # The y-coordinate should now be roughly the same for both
        avg_y = (rp1[1] + rp2[1]) / 2.0
        y_start = int(round(avg_y - aoi_width / 2.0))
        y_end = y_start + aoi_width
        
        # Clip to image bounds
        y_start = max(0, min(y_start, rh - 1))
        y_end = max(1, min(y_end, rh))
        
        # Create a mask to identify the zoomed-in image boundaries after rotation
        mask = np.zeros_like(self.image_data, dtype=float)
        
        x_min, x_max = int(max(0, min(self.zoom_xlim))), int(min(w, max(self.zoom_xlim)))
        y_min, y_max = int(max(0, min(self.zoom_ylim))), int(min(h, max(self.zoom_ylim)))
        
        mask[y_min:y_max, x_min:x_max] = 1.0
        
        rotated_mask = nd.rotate(mask, angle_deg, reshape=True, order=0)
        
        spectrum_strip = rotated[y_start:y_end, :]
        
        # Find columns that are within the original image boundaries
        # We check the middle row of the AOI for valid data
        mid_y_idx = int(round(avg_y))
        mid_y_idx = max(0, min(mid_y_idx, rotated_mask.shape[0] - 1))
        valid_cols = np.where(rotated_mask[mid_y_idx, :] > 0.5)[0]
        
        if len(valid_cols) > 0:
            x_start, x_end = valid_cols[0], valid_cols[-1] + 1
            spectrum_strip = spectrum_strip[:, x_start:x_end]
        
        # Calculate intensity profile
        if mode == 'mean':
            profile = np.mean(spectrum_strip, axis=0)
        elif mode == 'median':
            profile = np.median(spectrum_strip, axis=0)
        elif mode == 'max':
            profile = np.max(spectrum_strip, axis=0)
        else:
            profile = np.mean(spectrum_strip, axis=0)
            
        return spectrum_strip, profile, angle_deg

class InteractiveProfile:
    def __init__(self, strip, profile, filename, scaler=None, ref_spec=None, star_info=None, canvas=None, fig=None, ax_resp=None, ax_star=None, ax_prof=None, ax_strip=None):
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
            pass # Axes are passed in from MainWindow
            
            pixels = np.arange(len(self.profile))
            wls = self.scaler.m * pixels + self.scaler.c
            
            self.ax_star.plot(self.ref_spec[0], self.ref_spec[1], 'r-')
            self.ax_star.set_ylabel("Intensity")
            self.ax_star.set_title(f"Reference Star Spectrum")
            self.ax_star.grid(True, alpha=0.3)
            
            self.ax_prof.plot(wls, self.profile, 'b-')
            
            # Matplotlib's sharex can misbehave when zooming on imshow if the extent left > right
            if wls[0] > wls[-1]:
                self.extent = [wls[-1], wls[0], self.strip.shape[0], 0]
                self.strip_display = np.fliplr(self.strip)
            else:
                self.extent = [wls[0], wls[-1], self.strip.shape[0], 0]
                self.strip_display = self.strip
                
            self.ax_strip.set_xlabel("Wavelength (nm)")
        else:
            pass # Axes are passed in from MainWindow
            self.ax_prof.plot(self.profile, 'b-')
            self.extent = [0, len(self.profile), self.strip.shape[0], 0]
            self.strip_display = self.strip
            self.ax_strip.set_xlabel("Pixel (Rotated Frame)")
            
        self.ax_prof.set_ylabel("Intensity")
        self.ax_prof.set_title(f"Extracted Spectrum Profile: {filename}")
        self.ax_prof.grid(True, alpha=0.3)
        
        if hasattr(self.scaler, 'm') and hasattr(self.scaler, 'c'):
            info_text = f"Scale: {self.scaler.m:.4f} nm/px\nIntercept: {self.scaler.c:.2f} nm"
            if self.star_info:
                info_text += f"\nStar: {self.star_info.get('name', 'Unknown')} ({self.star_info.get('sptype', 'Unknown')})"
                
            self.info_box = self.ax_prof.text(0.02, 0.95, info_text, 
                                              transform=self.ax_prof.transAxes, verticalalignment='top', 
                                              bbox=dict(facecolor='white', alpha=0.8, edgecolor='black'))
        
        if has_star:
            self.update_responsivity(wls)
        
        # Display strip
        mask = self.strip_display > 0
        if np.any(mask):
            vmin = np.percentile(self.strip_display[mask], 10)
        else:
            vmin = np.percentile(self.strip_display, 10)
            
        vmax = np.percentile(self.strip_display, 99.9)
        self.ax_strip.imshow(self.strip_display, aspect='auto', cmap='viridis', vmin=vmin, vmax=vmax, extent=self.extent)
        self.ax_strip.set_yticks([])
        
        if has_star:
            # Explicitly enforce the shared x-limits after all plots have been drawn
            # to override any autoscaling done by imshow
            self.ax_star.set_xlim(min(wls), max(wls))
        
        # Interactive state
        self.pending_extract_x = None
        self.pending_extract_line = []
        self.completed_pairs = []

        print("\n--- Interactive Profile Plot ---")
        if has_star:
            print("1. Click a feature on the EXTRACTED spectrum (bottom plots).")
            print("2. Click the corresponding feature on the STAR spectrum (top plot).")
            print("3. Repeat for a second feature pair.")
            print("   (Right-click any dashed line to remove a pair)")
        else:
            print("This plot is ready for further interaction. Close it to exit.")
        

        
        self.cid = self.canvas.mpl_connect('button_press_event', self.onclick)
        self.fig.tight_layout()
        self.canvas.draw()

    def onclick(self, event):
        if not hasattr(self, 'ax_star'):
            valid_axes = [self.ax_prof, self.ax_strip]
            if event.inaxes not in valid_axes:
                return
            print(f"Profile Click: x={event.xdata:.2f}, y={event.ydata:.2f}")
            self.ax_prof.axvline(event.xdata, color='r', linestyle='--', alpha=0.5)
            self.canvas.draw()
            return
            
        if event.inaxes not in [self.ax_star, self.ax_prof, self.ax_strip]:
            return
            
        # Handle right click (remove pair)
        if event.button == 3:
            min_dist = float('inf')
            target_pair = None
            target_is_pending = False
            
            for pair in self.completed_pairs:
                for line in pair['lines']:
                    if line.axes == event.inaxes:
                        dist = abs(line.get_xdata()[0] - event.xdata)
                        if dist < min_dist:
                            min_dist = dist
                            target_pair = pair
            
            if self.pending_extract_line:
                for line in self.pending_extract_line:
                    if line.axes == event.inaxes:
                        dist = abs(line.get_xdata()[0] - event.xdata)
                        if dist < min_dist:
                            min_dist = dist
                            target_pair = None
                            target_is_pending = True
                            
            ax_range = event.inaxes.get_xlim()[1] - event.inaxes.get_xlim()[0]
            if min_dist < abs(ax_range) * 0.05:
                if target_is_pending:
                    print("Removed pending extract pick.")
                    for line in self.pending_extract_line:
                        line.remove()
                    self.pending_extract_line = []
                    self.pending_extract_x = None
                elif target_pair is not None:
                    print("Removed completed pair.")
                    for line in target_pair['lines']:
                        line.remove()
                    self.completed_pairs.remove(target_pair)
                    if len(self.completed_pairs) >= 2:
                        self.recalculate_scale()
                self.canvas.draw()
            return
            
        if event.button != 1:
            return
            
        # Left click state machine
        if self.pending_extract_x is None:
            # Expecting an extract click
            if event.inaxes not in [self.ax_prof, self.ax_strip]:
                print("Please click on the EXTRACTED spectrum (bottom plots) first.")
                return
            
            print(f"Extracted feature picked at x={event.xdata:.2f}")
            self.pending_extract_x = event.xdata
            l1 = self.ax_prof.axvline(event.xdata, color='r', linestyle='--', alpha=0.5)
            l2 = self.ax_strip.axvline(event.xdata, color='r', linestyle='--', alpha=0.5)
            self.pending_extract_line = [l1, l2]
            print("Now click the corresponding feature on the STAR spectrum (top plot).")
            self.canvas.draw()
            
        else:
            # Expecting a star click
            if event.inaxes != self.ax_star:
                print("Please click on the STAR spectrum (top plot).")
                return
                
            print(f"Star feature picked at wavelength={event.xdata:.2f}")
            l3 = self.ax_star.axvline(event.xdata, color='r', linestyle='--', alpha=0.5)
            
            pixel = (self.pending_extract_x - self.scaler.c) / self.scaler.m
            
            pair = {
                'pixel': pixel,
                'star_wl': event.xdata,
                'lines': self.pending_extract_line + [l3],
                'old_extract_wl': self.pending_extract_x
            }
            self.completed_pairs.append(pair)
            
            self.pending_extract_x = None
            self.pending_extract_line = []
            
            self.canvas.draw()
            
            if len(self.completed_pairs) >= 2:
                self.recalculate_scale()

    def recalculate_scale(self):
        print("\n--- Recalculating Spectral Scale ---")
        pxs = np.array([p['pixel'] for p in self.completed_pairs])
        wls = np.array([p['star_wl'] for p in self.completed_pairs])
        
        m, c = np.polyfit(pxs, wls, 1)
        self.scaler.m = m
        self.scaler.c = c
        
        print(f"New Spectral Scale: {m:.6f} nm/pixel")
        print(f"New Intercept:      {c:.4f} nm")
        
        pixels = np.arange(len(self.profile))
        new_wls = m * pixels + c
        
        self.ax_prof.lines[0].set_xdata(new_wls)
        
        if new_wls[0] > new_wls[-1]:
            self.extent = [new_wls[-1], new_wls[0], self.strip.shape[0], 0]
            self.strip_display = np.fliplr(self.strip)
        else:
            self.extent = [new_wls[0], new_wls[-1], self.strip.shape[0], 0]
            self.strip_display = self.strip
            
        self.ax_strip.images[0].set_extent(self.extent)
        self.ax_strip.images[0].set_data(self.strip_display)
        
        for pair in self.completed_pairs:
            new_x = pair['star_wl']
            for line in pair['lines']:
                line.set_xdata([new_x, new_x])
                
        self.ax_star.set_xlim(min(new_wls), max(new_wls))
        
        if hasattr(self, 'info_box'):
            info_text = f"Scale: {m:.4f} nm/px\nIntercept: {c:.2f} nm"
            if self.star_info:
                info_text += f"\nStar: {self.star_info.get('name', 'Unknown')} ({self.star_info.get('sptype', 'Unknown')})"
            self.info_box.set_text(info_text)
            
        if hasattr(self, 'ax_resp'):
            self.update_responsivity(new_wls)
            
        self.canvas.draw()
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
            
        self.resp_data = (wls, resp)


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
                        f.write("Wavelength_nm,Responsivity\n")
                        for w, r in zip(out_wls, out_resp):
                            f.write(f"{w:.1f},{r:.8f}\n")
                    QMessageBox.information(self, "Export Successful", f"Saved to:\n{out_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Export Error", f"Error saving CSV:\n{e}")
            else:
                QMessageBox.warning(self, "Export Error", "No visible responsivity data to export.")
        else:
            QMessageBox.warning(self, "Export Error", "Calibration incomplete or no reference star.")

def main():
    default_dir = "/srv/meteor/klingon/spectral/mirchk"
    example_file = "20260220/Elginfield_20260220_021451_spectral_sao005006_gamCam.png"
    default_path = os.path.join(default_dir, example_file) if os.path.exists(os.path.join(default_dir, example_file)) else default_dir

    parser = argparse.ArgumentParser(description="Interactive Spectral Scaling Tool")
    parser.add_argument("image_path", nargs='?', default=None, 
                        help=f"Path to the PNG image. Default search dir: {default_dir}")
    parser.add_argument("--no-swap", action="store_false", dest="byteswap", 
                        help="Disable byteswapping of the PNG image.")
    parser.add_argument("--aoi-width", type=int, default=15, 
                        help="Width of the Area of Interest (AOI) in pixels. Default: 15")
    parser.add_argument("--mode", choices=['mean', 'median', 'max'], default='mean', 
                        help="Intensity calculation mode along AOI columns. Default: mean")
    parser.add_argument("--flat", help="Path to a master flat field image (PNG).")
    parser.add_argument("--star", type=int, help="HIP number of the reference star for responsivity.")
    parser.add_argument("--lib", help="Path to the StarSpectra library file.")
    parser.set_defaults(byteswap=True)

    args = parser.parse_args()

    # If no path provided, prompt or use default
    image_path = args.image_path
    if image_path is None:
        print(f"No image path provided. Searching in {default_dir}...")
        # Check if default_dir exists
        if not os.path.exists(default_dir):
            print(f"Warning: Default directory {default_dir} not found.")
            image_path = input("Please enter the path to a PNG image: ").strip()
        else:
            # Try to find the example or latest PNG
            if os.path.exists(os.path.join(default_dir, example_file)):
                image_path = os.path.join(default_dir, example_file)
            else:
                # Just use the dir and let them choose? Or list files.
                print(f"Contents of {default_dir}:")
                pngs = []
                for root, dirs, files in os.walk(default_dir):
                    for f in files:
                        if f.endswith(".png"):
                            pngs.append(os.path.join(root, f))
                
                if pngs:
                    # Sort by modification time to get the latest
                    pngs.sort(key=os.path.getmtime, reverse=True)
                    print(f"Found {len(pngs)} PNGs. Using the most recent one:")
                    image_path = pngs[0]
                    print(f"  {image_path}")
                else:
                    image_path = input("No PNGs found in default dir. Enter path: ").strip()

    if not image_path or not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return

    print(f"Loading {image_path}...")
    data = load_image(image_path, byteswap=args.byteswap).astype(np.float32)
    
    if args.flat:
        print(f"Applying flat field: {args.flat}...")
        flat_data = load_image(args.flat, byteswap=False)
        flat_norm = flat_data.astype(np.float32) / 32768.0
        # Avoid division by zero or very small values
        flat_norm[flat_norm < 0.001] = 1.0
        data /= flat_norm

    app = QApplication(sys.argv)
    
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
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
