# import numpy as np
# import matplotlib.pyplot as plt
# from PIL import Image
# # import cv2

# # === Step 1: Load PNG Image ===
# img_path = "spectrum.png"  # <-- update with your actual file path
# image = Image.open(img_path).convert('L')  # grayscale
# img_array = np.array(image)

# # === Step 2: Interactively Pick Two Points on Spectrum ===
# print("Click two points along the star's spectrum (e.g. start and end)...")

# plt.imshow(img_array, cmap='gray', origin='upper')
# pts = plt.ginput(2, timeout=0)
# plt.close()

# # Get angle of rotation needed
# (x1, y1), (x2, y2) = pts
# dx, dy = x2 - x1, y2 - y1
# angle_deg = np.degrees(np.arctan2(dy, dx))

# # === Step 3: Rotate the Image to Flatten Spectrum ===
# def rotate_image(image, angle):
#     (h, w) = image.shape
#     center = (w // 2, h // 2)
#     matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
#     rotated = cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_LINEAR)
#     return rotated

# flattened = rotate_image(img_array, -angle_deg)

# # === Step 4: Extract 1D Spectrum (Sum along vertical) ===
# spectrum = np.sum(flattened, axis=0)  # sum rows for each column (x-axis)

# # === Step 5: Plot Spectrum ===
# plt.figure(figsize=(10, 4))
# plt.plot(spectrum, color='blue')
# plt.title("Extracted 1D Spectrum")
# plt.xlabel("Pixel Position (proxy for Wavelength)")
# plt.ylabel("Intensity (arbitrary units)")
# plt.grid(True)
# plt.tight_layout()
# plt.show()

# Without OpenCV, we can use PIL for rotation and numpy for image manipulation.
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

# === Step 1: Load PNG Image ===
img_path = "/Users/aubz/Desktop/Spectra/Elginfield_20250630_024724_spectral_sao007593_5kapDra.png"  # <-- update with your actual file path
image = Image.open(img_path) # using grayscale changes the image to just dots on a screen
img_array = np.array(image)

# === Step 2: Interactively Pick Two Points on Spectrum ===
print("Click two points along the star's spectrum (e.g. start and end)...")
plt.imshow(img_array, cmap='gray', origin='upper')
pts = plt.ginput(2, timeout=0)
plt.close()

# Get angle of rotation needed
# (x1, y1), (x2, y2) = pts
# dx, dy = x2 - x1, y2 - y1
# angle_deg = np.degrees(np.arctan2(dy, dx))  # positive = counterclockwise

# === Step 3: Rotate the Image to Flatten Spectrum ===
# PIL rotates counterclockwise, so we negate the angle
angle_deg = 37.5
image_rotated = Image.fromarray(img_array).rotate(angle_deg, resample=Image.BICUBIC, expand=True, fillcolor=0)
flattened = np.array(image_rotated)

# === Step 4: Extract 1D Spectrum (Sum along vertical) ===
spectrum = np.sum(flattened, axis=0)
plt.imshow(flattened, cmap='gray', origin='upper')

# === Step 5: Plot Spectrum ===
plt.figure(figsize=(10, 4))
plt.plot(spectrum, color='blue')
plt.title("Extracted 1D Spectrum")
plt.xlabel("Pixel Position (proxy for Wavelength)")
plt.ylabel("Intensity (arbitrary units)")
plt.grid(True)
plt.tight_layout()
plt.show()
