import numpy as np
import argparse
import os, glob
import matplotlib.pyplot as plt
from PIL import Image

''' Same as imageplotter2.py but with flat field correction '''


def load_flat_field(flat_path):
    flat_img = Image.open(flat_path).convert('L')
    flat_array = np.array(flat_img).astype(np.float32)
    flat_mean = np.mean(flat_array)
    flat_array[flat_array == 0] = 1  # avoid division by 0
    return flat_array, flat_mean

# def apply_flat_field(image_array, flat_array, flat_mean):
#     # Resize flat field to match input image shape
#     if flat_array.shape != image_array.shape:
#         from PIL import Image
#         flat_resized = Image.fromarray(flat_array).resize(image_array.shape[::-1], resample=Image.BICUBIC)
#         flat_array = np.array(flat_resized).astype(np.float32)

#     corrected = (image_array.astype(np.float32) / flat_array) * flat_mean
#     corrected = np.clip(corrected, 0, 255)  # stay in valid image range
#     return corrected.astype(np.uint8)

# Cleaner method for flat field correction
# def apply_flat_field(image_array, flat_array, flat_mean):
#     # Normalize flat field
#     flat_norm = flat_array / np.mean(flat_array)
    
#     # Ensure flat and image are same shape
#     if flat_norm.shape != image_array.shape:
#         flat_norm_resized = Image.fromarray(flat_norm).resize(image_array.shape[::-1], resample=Image.BICUBIC)
#         flat_norm = np.array(flat_norm_resized)

#     # Apply correction (image divided by normalized flat)
#     corrected = image_array.astype(np.float32) / flat_norm
#     corrected = np.clip(corrected, 0, 255)
#     return corrected.astype(np.uint8)

# Trying this now
def apply_flat_field(image_array, flat_array, flat_mean):
    # Ensure float format for division
    image_array = image_array.astype(np.float32)
    flat_array = flat_array.astype(np.float32)

    # Normalize the flat to have mean = 1.0
    flat_mean = np.mean(flat_array)
    flat_array[flat_array == 0] = flat_mean  # Prevent division by 0
    flat_normalized = flat_array / flat_mean

    # Resize flat if needed
    if flat_array.shape != image_array.shape:
        flat_normalized = np.array(
            Image.fromarray(flat_normalized).resize(
                (image_array.shape[1], image_array.shape[0]),
                resample=Image.BICUBIC
            )
        )

    # Apply correction
    corrected = image_array / flat_normalized

    # Rescale to 0–255 for display
    corrected = corrected - corrected.min()
    corrected = (corrected / corrected.max()) * 255.0
    corrected = np.clip(corrected, 0, 255)

    return corrected.astype(np.uint8)



def extract_angle_from_points(img_array):
    plt.imshow(img_array, cmap='gray', origin='upper')
    plt.title("Click two points along the spectrum")
    pts = plt.ginput(2, timeout=0)
    plt.close()
    if len(pts) != 2:
        raise ValueError("Two points must be selected!")
    (x1, y1), (x2, y2) = pts
    dx, dy = x2 - x1, y2 - y1
    return np.degrees(np.arctan2(dy, dx))

def rotate_image(img_array, angle_deg):
    return np.array(
        Image.fromarray(img_array).rotate(-angle_deg, resample=Image.BICUBIC, expand=True, fillcolor=0)
    )

def extract_1d_spectrum(rotated_array):
    return np.sum(rotated_array, axis=0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spectral PNG extraction with flat-field correction")
    parser.add_argument("image_path", metavar="IMG_DIR", type=str, help="Directory with PNG images")
    parser.add_argument("--flat", metavar="FLAT_PATH", type=str, default="flatfield2.png", help="Path to flat field PNG image")
    args = parser.parse_args()

    # Troubleshoot existence of flat field image
    if not os.path.exists(args.flat):
        raise FileNotFoundError(f"Flat field image not found: {args.flat}")


    # Load flat-field image
    flat_array, flat_mean = load_flat_field(args.flat)

    # Load all spectrum images
    image_files = glob.glob(os.path.join(args.image_path, "*.png"))

    for img_path in image_files:
        print(f"\nProcessing: {os.path.basename(img_path)}")

        # Load image and convert to grayscale
        image = Image.open(img_path).convert('L')
        image_array = np.array(image)

        # Apply flat-field correction
        corrected_array = apply_flat_field(image_array, flat_array, flat_mean)

        # Ask user to click 2 points
        angle = extract_angle_from_points(corrected_array)

        # Rotate image
        rotated = rotate_image(corrected_array, angle)

        # Extract 1D spectrum
        spectrum = extract_1d_spectrum(rotated)

        # Plot spectrum
        plt.figure(figsize=(10, 4))
        plt.plot(spectrum, color='blue')
        plt.title(f"Spectrum from: {os.path.basename(img_path)}")
        plt.xlabel("Pixel Position (proxy for Wavelength)")
        plt.ylabel("Intensity")
        plt.grid(True)
        plt.tight_layout()
        plt.show()
