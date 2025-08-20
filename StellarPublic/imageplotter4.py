import numpy as np
import argparse
import os, glob
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib.widgets import RectangleSelector

' Trying with inerpolation, rotation, and optional ROI selection '

from scipy.ndimage import rotate, zoom
import cv2  # For ROI selection (optional)

# =========================
# Image Processing Functions
# =========================

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
    ax.imshow(image_array, cmap='gray' if image_array.ndim == 2 else None)
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

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="View and process PNG spectra with ROI")
    arg_parser.add_argument('image_path', nargs='+', metavar='DIR_PATH', type=str,
                            help='Path to the image file directory.')
    arg_parser.add_argument('--rotate', type=float, default=0.0,
                            help='Angle in degrees to rotate the image (counterclockwise).')
    arg_parser.add_argument('--interpolate', type=float, default=1.0,
                            help='Scale factor for interpolation (e.g., 2 = 2x bigger).')
    arg_parser.add_argument('--roi', action='store_true',
                            help='Enable ROI selection for each image.')

    cml_args = arg_parser.parse_args()
    image_path = cml_args.image_path
    images = glob.glob(os.path.join(image_path[0], "*.png"), recursive=False)

    for img_path in images:
        # print(f"\nProcessing: {os.path.basename(img_path)}")
        image = Image.open(img_path)
        image_array = np.asarray(image)
        image_array = byteswap_and_normalize(image_array)
        image_array = image_array.byteswap()

        # Optional interpolation
        if cml_args.interpolate != 1.0:
            image_array = interpolate_image(image_array, scale_factor=cml_args.interpolate)

        # Optional rotation
        if cml_args.rotate != 0.0:
            image_array = rotate_image(image_array, angle_deg=cml_args.rotate)

        # Optional ROI selection
        if cml_args.roi:
            image_array = select_roi(image_array)

        # # Step 2: Let user pick two points
        # angle = extract_angle_from_points(image_array)

        # View processed image
        # plt.figure(figsize=(10, 8))
        # plt.imshow(image_array, colorizer="crimson", aspect='auto')
        # plt.title(os.path.basename(img_path))
        # plt.colorbar(label="Intensity")
        # plt.tight_layout()
        # plt.show()

        plt.figure(figsize=(10, 2))
        plt.imshow(image_array, cmap='inferno' if image_array.ndim == 2 else None, aspect='auto')
        plt.title(os.path.basename(img_path))
        plt.colorbar(label="Intensity")
        plt.tight_layout()
        plt.show()

        # Extracting 1D spectrum
        spectrum = extract_1d_spectrum(image_array) 

        # =========================
        # Wavelength Calibration
        # =========================
        wavelength_start = 400  # Example starting wavelength
        wavelength_end = 800    # Example ending wavelength
        wavelength = np.linspace(wavelength_start, wavelength_end, len(spectrum))

        # Plotting the 1D spectrum
        plt.figure(figsize=(15, 8))
        plt.plot(wavelength, spectrum, color='blue')
        plt.title(f"1D Spectrum of {os.path.basename(img_path)}")
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Intensity")
        plt.grid(True)
        plt.tight_layout()
        plt.show()
