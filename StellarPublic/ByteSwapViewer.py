import numpy as np
import argparse
import os, glob

import matplotlib.pyplot as plt
from PIL import Image

if __name__=="__main__":
		# Read arguments with argparser
	arg_parser = argparse.ArgumentParser(description="Create a contact sheet with observations and TLE overlays")
	arg_parser.add_argument('image_path', nargs='+', metavar='DIR_PATH', type=str, \
		help='Path to the image file directory.')

	

	# Parse command-line arguments
	cml_args = arg_parser.parse_args()

	# Get the path to the ff files from the parser
	image_path = cml_args.image_path

	images = glob.glob(os.path.join(image_path[0], "*.png"), recursive=False)

	


	for i in range(len(images)):
		image = Image.open(images[i])
		image = np.asarray(image)
		image_bs = image.byteswap()
		print(np.max(image), np.max(image_bs))
		print(np.min(image), np.min(image_bs))
		plt.figure(figsize=(10,10))
		plt.imshow(image_bs, vmin=2400, vmax= 3000)
		plt.title(os.path.basename(images[i]))
		plt.colorbar()
		plt.tight_layout()
		plt.show()
		plt.close()
	# for i in range(len(images)):
