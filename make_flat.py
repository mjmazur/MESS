#!/usr/bin/env python3
import numpy as np
from PIL import Image
import glob
import os
import argparse
import sys

def load_and_swap(path):
    """Load a 16-bit PNG and byteswap it."""
    try:
        img = Image.open(path)
        data = np.asarray(img)
        if data.dtype == np.uint16:
            return data.byteswap()
        else:
            print(f"Warning: {path} is not uint16 ({data.dtype}). Swapping anyway.")
            return data.byteswap()
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Generate a master flat field from a directory of PNG images.")
    parser.add_argument("input_patterns", nargs='+', help="Directory or wildcard pattern(s) for input PNG images.")
    parser.add_argument("-o", "--output", default="flat.png", help="Output filename (default: flat.png)")
    parser.add_argument("--scale", type=int, default=32768, 
                        help="Value that represents 1.0 in the output 16-bit PNG (default: 32768)")
    parser.add_argument("--norm-mode", choices=['median', 'mean', 'max'], default='median',
                        help="Value to normalize the master flat to 1.0 (default: median)")
    
    args = parser.parse_args()

    all_files = []
    for pattern in args.input_patterns:
        if os.path.isdir(pattern):
            current_pattern = os.path.join(pattern, "*.png")
        else:
            current_pattern = pattern
            
        all_files.extend(glob.glob(current_pattern, recursive=True))

    files = sorted(list(set(all_files))) # Sort and remove duplicates
    if not files:
        print(f"No PNG files found matching the provided patterns.")
        sys.exit(1)

    print(f"Found {len(files)} images. Loading and byteswapping...")
    
    stack = []
    for f in files:
        data = load_and_swap(f)
        if data is not None:
            stack.append(data)
    
    if not stack:
        print("No valid images loaded.")
        sys.exit(1)

    stack = np.array(stack, dtype=np.float32)
    
    if len(stack) > 300:
        n_discard = 200
    elif len(stack) > 200:
        n_discard = 100
    elif len(stack) > 100:
        n_discard = 50
    elif len(stack) > 10:
        n_discard = 5
    else:
        n_discard = 0

    if n_discard > 0:
        print(f"Discarding {n_discard} highest values from {len(stack)} images at each pixel...")
        # Sort along axis 0 (the stack axis)
        stack = np.sort(stack, axis=0)
        # Discard the highest values
        stack = stack[:-n_discard, :, :]
    
    print(f"Combining remaining {len(stack)} images using median...")
    master_flat = np.median(stack, axis=0)
    
    print(f"Normalizing to 1.0 using {args.norm_mode}...")
    if args.norm_mode == 'median':
        norm_val = np.median(master_flat)
    elif args.norm_mode == 'mean':
        norm_val = np.mean(master_flat)
    elif args.norm_mode == 'max':
        norm_val = np.max(master_flat)
    
    if norm_val == 0:
        print("Error: Normalization value is 0. Cannot normalize.")
        sys.exit(1)
        
    master_flat /= norm_val
    
    print(f"Scaling for output (1.0 -> {args.scale})...")
    # Clip to avoid overflow before converting to uint16
    final_image = np.clip(master_flat * args.scale, 0, 65535).astype(np.uint16)
    
    print(f"Saving to {args.output}...")
    out_img = Image.fromarray(final_image)
    out_img.save(args.output)
    
    print("\nSuccess!")
    print(f"Master flat: {args.output}")
    print(f"Normalization value ({args.norm_mode}): {norm_val:.2f}")
    print(f"Scaling factor: 1.0 = {args.scale}")

if __name__ == "__main__":
    main()
