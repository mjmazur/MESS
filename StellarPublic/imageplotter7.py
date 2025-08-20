import numpy as np
import argparse
import os, glob
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib.widgets import RectangleSelector

' Trying with inerpolation, rotation, and optional ROI selection '

from scipy.ndimage import rotate, zoom
import cv2  # For ROI selection (optional)

''' Structure containing flat field data and methods for correction '''

class FlatStruct(object):

    def __init__(self, flat_array, dark=None):
        self.flat_array = flat_array.astype(np.float64) # converts flat to float64
        
        self.flat_img_raw = np.copy(self.flat_img)

        self.applyDark(dark)  # Initialize without dark field correction

        self.computeAverage()

        self.fixValues()

    def applyDark(self, dark):
        """ Apply dark field correction to flat field. """

        if dark is not None:
            self.flat_img = self.applyDark(self.flat_img_raw, dark)
            self.dark_applied = True

        else:
            self.flat_img = np.copy(self.flat_img_raw)
            self.dark_applied = False

        # Compute flat median
        self.computeAverage()

        # Fix values close to 0
        self.fixValues()


    def computeAverage(self):
        """ Compute the reference level. """


        # # Bin the flat by a factor of 4 using the average method
        # flat_binned = binImage(self.flat_img, 4, method='avg')

        # # Take the maximum average level of pixels that are in a square of 1/4*height from the centre
        # radius = flat_binned.shape[0]//4
        # img_h_half = flat_binned.shape[0]//2
        # img_w_half = flat_binned.shape[1]//2
        # self.flat_avg = np.max(flat_binned[img_h_half-radius:img_h_half+radius, \
        #     img_w_half-radius:img_w_half+radius])

        self.flat_avg = np.median(self.flat_img)

        # Make sure the self.flat_avg value is relatively high
        if self.flat_avg < 1:
            self.flat_avg = 1

    def fixValues(self):
        """ Handle values close to 0 on flats. """

        # Make sure there are no values close to 0, as images are divided by flats
        self.flat_img[(self.flat_img < self.flat_avg/10) | (self.flat_img < 10)] = self.flat_avg


    # def binFlat(self, binning_factor, binning_method):
    #     """ Bin the flat. """

    #     # Bin the processed flat
    #     self.flat_img = binImage(self.flat_img, binning_factor, binning_method)

    #     # Bin the raw flat image
    #     self.flat_img_raw = binImage(self.flat_img_raw, binning_factor, binning_method)

# =========================
# Image Processing Functions
# =========================

def applyFlat(img, flat_struct):
    """ Apply a flat field to the image.
    Arguments:
        img: [ndarray] Image to flat field.
        flat_struct: [Flat struct] Structure containing the flat field.
        
    Return:
        [ndarray] Flat corrected image.
    """

    # Check that the input image and the flat have the same dimensions, otherwise do not apply it
    if img.shape != flat_struct.flat_img.shape:
        return img

    input_type = img.dtype

    # Apply the flat
    img = flat_struct.flat_avg*img.astype(np.float64)/flat_struct.flat_img

    # Limit the image values to image type range
    dtype_info = np.iinfo(input_type)
    img = np.clip(img, dtype_info.min, dtype_info.max)

    # Make sure the output array is the same as the input type
    img = img.astype(input_type)

    return img

def interpolate_image(image_array, scale_factor=2):
    return zoom(image_array, zoom=scale_factor, order=3)  # cubic interpolation

def rotate_image(image_array, angle_deg):
    return rotate(image_array, angle=angle_deg, reshape=True, order=3)

def byteswap_and_normalize(image_array):
    """Byte swap to fix endian order and normalize to 0-255."""
    swapped = image_array.byteswap().view(image_array.dtype.newbyteorder())
    norm = (swapped - swapped.min()) / (swapped.max() - swapped.min())
    return (norm * 255).astype(np.uint8)

# def select_roi(image_array):
#     plt.imshow(image_array, cmap='gray')
#     plt.title("Select ROI: Click and drag to draw a rectangle")

#     roi_coords = []
    
#     # If using RectangleSelector, define a callback to capture the rectangle coordinates
#     roi = None

#     def on_select(eclick, erelease):
#         global roi
#         try:
#             x1, y1 = int(eclick.xdata), int(eclick.ydata)
#             x2, y2 = int(erelease.xdata), int(erelease.ydata)
#             xmin, xmax = sorted([x1, x2])
#             ymin, ymax = sorted([y1, y2])

#             # Check shape to determine grayscale or RGB
#             if image_array.ndim == 2:
#                 roi = image_array[ymin:ymax, xmin:xmax]        # Grayscale
#             elif image_array.ndim == 3:
#                 roi = image_array[ymin:ymax, xmin:xmax, :]      # RGB
#             else:
#                 raise ValueError("Unsupported image format.")

#             plt.close()
#         except Exception as e:
#             print(f"Error selecting ROI: {e}")
#             None



#     rs = rs = RectangleSelector(
#     plt.gca(), on_select,
#     useblit=True,
#     button=[1],
#     minspanx=5, minspany=5,
#     spancoords='pixels',
#     interactive=True
# )
#     plt.show()

#     if roi_coords:
#         x1, y1, x2, y2 = roi_coords
#         x1, x2 = sorted([x1, x2])
#         y1, y2 = sorted([y1, y2])
#         return image_array[y1:y2, x1:x2]
#     else:
#         raise ValueError("ROI selection failed.")

def extract_1d_spectrum(roi_array):
    """Sum vertically to collapse to 1D spectrum."""
    if roi_array.ndim == 3:  # If RGB, convert to grayscale before summing
        roi_array = np.mean(roi_array, axis=2)
    return np.sum(roi_array, axis=0)  # sum over rows → intensity vs column
    
# def select_roi(image_array):
#     fig, ax = plt.subplots()
#     ax.imshow(image_array, cmap='gray' if image_array.ndim == 2 else None)
#     plt.title("Draw ROI and close the window")

#     roi_box = {}

#     def on_select(eclick, erelease):
#         x1, y1 = int(eclick.xdata), int(eclick.ydata)
#         x2, y2 = int(erelease.xdata), int(erelease.ydata)
#         xmin, xmax = sorted([x1, x2])
#         ymin, ymax = sorted([y1, y2])
#         roi_box['roi'] = (
#             image_array[ymin:ymax, xmin:xmax] if image_array.ndim == 2
#             else image_array[ymin:ymax, xmin:xmax, :]
#         )

#     selector = RectangleSelector(ax, on_select, useblit=True, interactive=True)
#     plt.show()

#     if 'roi' not in roi_box:
#         raise ValueError("ROI selection failed. You must draw a rectangle before closing.")
#     return roi_box['roi']

def select_roi(image_array):
    fig, ax = plt.subplots()
    image_bs = image_array.byteswap()  # Ensure byte order is correct
    ax.imshow(image_bs, cmap='inferno' if image_array.ndim == 2 else None)
    plt.title("Draw ROI and close the window")

    roi_box = {}

    def on_select(eclick, erelease):
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        xmin, xmax = sorted([x1, x2])
        ymin, ymax = sorted([y1, y2])
        roi_box['roi'] = (
            image_array[ymin:ymax, xmin:xmax] if image_array.ndim == 2
            else image_array[ymin:ymax, xmin:xmax, :]
        )

    selector = RectangleSelector(ax, on_select, useblit=True, interactive=True)
    plt.show()

    if 'roi' not in roi_box:
        raise ValueError("ROI selection failed. You must draw a rectangle before closing.")
    return roi_box['roi']

# =========================
# Main
# =========================

# ...existing imports...

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="View and process PNG spectra with ROI and flat field correction")
    arg_parser.add_argument('image_path', nargs='+', metavar='DIR_PATH', type=str,
                            help='Path to the image file directory.')
    # arg_parser.add_argument('--flat', type=str, required=True,
    #                         help='Path to the flat field PNG image.')
    # arg_parser.add_argument('--dark', type=str, default=None,
    #                         help='Path to the dark field PNG image (optional).')
    arg_parser.add_argument('--rotate', type=float, default=0.0,
                            help='Angle in degrees to rotate the image (counterclockwise).')
    arg_parser.add_argument('--interpolate', type=float, default=1.0,
                            help='Scale factor for interpolation (e.g., 2 = 2x bigger).')
    arg_parser.add_argument('--roi', action='store_true',
                            help='Enable ROI selection for each image.')

    cml_args = arg_parser.parse_args()
    image_path = cml_args.image_path
    images = glob.glob(os.path.join(image_path[0], "*.png"), recursive=False)

    # --- Load flat and dark field images ---
    flat_img = np.asarray(Image.open(cml_args.flat))
    dark_img = np.asarray(Image.open(cml_args.dark)) if cml_args.dark else None

    # --- Create FlatStruct instance ---
    flat_struct = FlatStruct(flat_img, dark=dark_img)

    for img_path in images:
        image = Image.open(img_path)
        image = np.asarray(image)

        # Apply byte swap (like ByteSwapViewer.py)
        image_bs = image.byteswap()

        # --- Apply flat field correction ---
        image_bs = applyFlat(image_bs, flat_struct)

        # Optional interpolation
        if cml_args.interpolate != 1.0:
            image_bs = interpolate_image(image_bs, scale_factor=cml_args.interpolate)

        # Optional rotation
        if cml_args.rotate != 0.0:
            image_bs = rotate_image(image_bs, angle_deg=cml_args.rotate)

        # Optional ROI selection
        if cml_args.roi:
            image_bs = select_roi(image_bs)

        print(np.max(image), np.max(image_bs))
        print(np.min(image), np.min(image_bs))
        plt.figure(figsize=(10,10))
        plt.imshow(image_bs, vmin=2400, vmax= 3000)
        plt.title(os.path.basename(img_path))
        plt.colorbar()
        plt.tight_layout()
        plt.show()

        # Normalize for display (do not overwrite image_bs)
        image_disp = image_bs.astype(float)
        image_disp = (image_disp - image_disp.min()) / (image_disp.max() - image_disp.min()) * 255

        plt.figure(figsize=(10, 4))
        plt.imshow(image_bs, cmap='inferno', aspect='auto')
        plt.title(f"Processed {os.path.basename(img_path)}")
        plt.colorbar(label="Intensity")
        plt.tight_layout()
        plt.show()

        # 1D spectrum extraction (sum columns)
        spectrum = extract_1d_spectrum(image_bs)

        # Wavelength calibration
        wavelength_start = 400
        wavelength_end = 800
        wavelength = np.linspace(wavelength_start, wavelength_end, len(spectrum))

        # Plot 1D spectrum
        plt.figure(figsize=(15, 8))
        plt.plot(wavelength, spectrum, color='blue')
        plt.title(f"1D Spectrum of {os.path.basename(img_path)}")
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Intensity")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

# if __name__ == "__main__":
#     arg_parser = argparse.ArgumentParser(description="View and process PNG spectra with ROI")
#     arg_parser.add_argument('image_path', nargs='+', metavar='DIR_PATH', type=str,
#                             help='Path to the image file directory.')
#     arg_parser.add_argument('--rotate', type=float, default=0.0,
#                             help='Angle in degrees to rotate the image (counterclockwise).')
#     arg_parser.add_argument('--interpolate', type=float, default=1.0,
#                             help='Scale factor for interpolation (e.g., 2 = 2x bigger).')
#     arg_parser.add_argument('--roi', action='store_true',
#                             help='Enable ROI selection for each image.')

#     cml_args = arg_parser.parse_args()
#     image_path = cml_args.image_path
#     images = glob.glob(os.path.join(image_path[0], "*.png"), recursive=False)

#     for img_path in images:
#         image = Image.open(img_path)
#         image = np.asarray(image)

#         # Apply byte swap (like ByteSwapViewer.py)
#         image_bs = image.byteswap() # Keep this to reduce noise of spectra

#         # Optionally normalize if needed:
#         # image_array = byteswap_and_normalize(image_array)

#         # Optional interpolation
#         if cml_args.interpolate != 1.0:
#             image_bs = interpolate_image(image_bs, scale_factor=cml_args.interpolate)

#         # Optional rotation
#         if cml_args.rotate != 0.0:
#             image_bs = rotate_image(image_bs, angle_deg=cml_args.rotate)

#         # Optional ROI selection
#         if cml_args.roi:
#             image_bs = select_roi(image_bs)

#         print(np.max(image), np.max(image_bs))
#         print(np.min(image), np.min(image_bs))
#         plt.figure(figsize=(10,10))
#         plt.imshow(image_bs, vmin=2400, vmax= 3000)
#         plt.title(os.path.basename(img_path))
#         plt.colorbar()
#         plt.tight_layout()
#         plt.show()


#         # Normalize for display (do not overwrite image_bs)
#         image_disp = image_bs.astype(float)
#         image_disp = (image_disp - image_disp.min()) / (image_disp.max() - image_disp.min()) * 255


#         # Show processed image with a colormap (follows roi picking)
#         plt.figure(figsize=(10, 4))
#         plt.imshow(image_bs, cmap='inferno', aspect='auto')
#         plt.title(f"Processed {os.path.basename(img_path)}")
#         plt.colorbar(label="Intensity")
#         plt.tight_layout()
#         plt.show()

#         # 1D spectrum extraction (sum columns)
#         spectrum = extract_1d_spectrum(image_bs)

#         # =========================
#         # Wavelength calibration
#         # =========================
#         wavelength_start = 400
#         wavelength_end = 800
#         wavelength = np.linspace(wavelength_start, wavelength_end, len(spectrum))

#         # Plot 1D spectrum
#         plt.figure(figsize=(15, 8))
#         plt.plot(wavelength, spectrum, color='blue')
#         plt.title(f"1D Spectrum of {os.path.basename(img_path)}")
#         plt.xlabel("Wavelength (nm)")
#         plt.ylabel("Intensity")
#         plt.grid(True)
#         plt.tight_layout()
#         plt.show()

        # # Extracting 1D spectrum
        # spectrum = extract_1d_spectrum(image_array) 

        # # =========================
        # # Wavelength Calibration
        # # =========================
        # wavelength_start = 400  # Example starting wavelength
        # wavelength_end = 800    # Example ending wavelength
        # wavelength = np.linspace(wavelength_start, wavelength_end, len(spectrum))

        # # Plotting the 1D spectrum
        # plt.figure(figsize=(15, 8))
        # plt.plot(wavelength, spectrum, color='blue')
        # plt.title(f"1D Spectrum of {os.path.basename(img_path)}")
        # plt.xlabel("Wavelength (nm)")
        # plt.ylabel("Intensity")
        # plt.grid(True)
        # plt.tight_layout()
        # plt.show()
