import numpy as np
import matplotlib

# test_imageplotter4.py

matplotlib.use('Agg')  # Avoid GUI for tests

from imageplotter4 import (
    byteswap_and_normalize,
    interpolate_image,
    rotate_image,
    extract_1d_spectrum
)

def test_byteswap_and_normalize():
    arr = np.array([[1, 2], [3, 4]], dtype=np.uint16)
    norm = byteswap_and_normalize(arr)
    assert norm.shape == arr.shape
    assert norm.dtype == np.uint8
    assert norm.min() == 0
    assert norm.max() == 255

def test_interpolate_image():
    arr = np.ones((4, 4), dtype=np.uint8)
    out = interpolate_image(arr, scale_factor=2)
    assert out.shape == (8, 8)
    assert np.allclose(out, 1)

def test_rotate_image():
    arr = np.array([[1, 2], [3, 4]], dtype=np.uint8)
    out = rotate_image(arr, 90)
    # Rotating 2x2 by 90 degrees should still be 2x2, but values move
    assert out.shape == (2, 2)
    # The rotated array should have the original's first column as its last row
    assert np.allclose(np.rot90(arr), out, atol=1)

def test_extract_1d_spectrum_2d():
    arr = np.arange(12).reshape(3, 4)
    spectrum = extract_1d_spectrum(arr)
    expected = np.sum(arr, axis=0)
    assert np.allclose(spectrum, expected)

def test_extract_1d_spectrum_3d():
    arr = np.ones((2, 3, 3), dtype=np.uint8) * np.array([[[10, 20, 30]]])
    # Each pixel is [10, 20, 30], mean is 20, sum over rows: 2*20=40 per column
    spectrum = extract_1d_spectrum(arr)
    assert np.allclose(spectrum, [40, 40, 40])

# Demonstration: summing columns of ROI gives 1D spectrum
def test_sum_columns_matches_extract_1d_spectrum():
    arr = np.random.randint(0, 255, (10, 20), dtype=np.uint8)
    roi = arr[2:8, 5:15]
    spectrum1 = extract_1d_spectrum(roi)
    spectrum2 = np.sum(roi, axis=0)
    assert np.allclose(spectrum1, spectrum2)