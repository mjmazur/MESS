import numpy as np
import argparse
import os, glob
import matplotlib.pyplot as plt
from PIL import Image

from scipy.ndimage import rotate, zoom
from scipy.signal import savgol_filter

def extract_angle_from_points(img_array):
    plt.imshow(img_array, cmap='gray', origin='upper')
    plt.title("Click two points along the spectrum")
    pts = plt.ginput(2, timeout=0)
    plt.close()

    if len(pts) != 2:
        raise ValueError("Two points must be selected!")

    (x1, y1), (x2, y2) = pts
    dx, dy = x2 - x1, y2 - y1
    angle_deg = np.degrees(np.arctan2(dy, dx))
    return angle_deg

def rotate_image(img_array, angle_deg):
    return np.array(
        Image.fromarray(img_array).rotate(-angle_deg, resample=Image.BICUBIC, expand=True, fillcolor=0)
    )

def extract_1d_spectrum(rotated_array):
    return np.sum(rotated_array, axis=0)

# # avg spectrum over a band
# def extract_1d_spectrum(rotated_array):
#     h = rotated_array.shape[0]
#     band_half = 10  # adjust as needed
#     center = h // 2
#     roi = rotated_array[center - band_half:center + band_half, :]
#     return np.mean(roi, axis=0)


def load_flat_field(flat_path): # Load flat field image and calculate mean
    flat_img = Image.open(flat_path).convert('L')
    flat_array = np.array(flat_img).astype(np.float32)
    flat_mean = np.mean(flat_array)
    flat_array[flat_array == 0] = 1  # avoid division by 0
    return flat_array, flat_mean

def apply_flat_field(image_array, flat_array, flat_mean):
    corrected = (image_array.astype(np.float32) / flat_array) * flat_mean
    corrected = np.clip(corrected, 0, 255)  # stay in valid image range
    return corrected.astype(np.uint64)

if __name__ == "__main__":
    # Argument parser to get directory from command line
    arg_parser = argparse.ArgumentParser(description="Extract and plot 1D spectra from PNGs")
    arg_parser.add_argument('image_path', nargs='+', metavar='DIR_PATH', type=str,
                            help='Path to the image file directory.')
    # arg_parser.add_argument('--flat', metavar='FLAT_PATH', type=str,
                        # help='Path to flat field PNG image.')

    cml_args = arg_parser.parse_args()
   

    # # Load flat field correction image
    # flat_array, flat_mean = load_flat_field(cml_args)

    # parser = argparse.ArgumentParser(description="Spectral PNG extraction with flat-field correction")
    # parser.add_argument("image_path", metavar="IMG_DIR", type=str, help="Directory with PNG images")
    # parser.add_argument("--flat", metavar="FLAT_PATH", type=str, help="Path to flat field PNG image")
    # args = parser.parse_args()

    # if args.flat:
    #     flat_array, flat_mean = load_flat_field(args.flat)
    #     # apply correction
    # else:
    #     print("Warning: No flat field supplied. Skipping correction.")


    # Load flat-field image
    #flat_array, flat_mean = load_flat_field(args.flat)

    # Load all spectrum images
    image_path = cml_args.image_path  # Wrap in list to match original code structure

    # Get all PNG images in the specified directory
    images = glob.glob(os.path.join(image_path[0], "*.png"), recursive=False)


    for i in range(len(images)):
        # print(f"\nProcessing: {os.path.basename(img_path)}")

        # Load and convert to grayscale
        image = Image.open(images[i])
        img_array = np.asarray(image)

        # image_bs = image.byteswap()
        # print(f"Max value: {np.max(img_array)}, Byteswapped Max: {np.max(image_bs)}")
        # print(f"Min value: {np.min(img_array)}, Byteswapped Min: {np.min(image_bs)}")

        # Step 1: Apply flat field correction
        #corrected_array = apply_flat_field(img_array, flat_array, flat_mean)

        # Step 2: Let user pick two points
        angle = extract_angle_from_points(img_array)

        # Step 3: Rotate the image
        rotated = rotate_image(img_array, angle)

        # Step 4: Extract 1D spectrum
        spectrum = extract_1d_spectrum(rotated)


        # Step 5: Plot spectrum
        plt.figure(figsize=(10, 4))
        plt.plot(spectrum, color='blue')
        plt.title(f"Spectrum from: {os.path.basename(images[i])}")
        plt.xlabel("Pixel Position (proxy for Wavelength)")
        plt.ylabel("Intensity")
        plt.grid(True)
        plt.tight_layout()
        plt.show()
