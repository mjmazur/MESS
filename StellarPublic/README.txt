This project was made to test the calibration of CAMO-S, by analyzing the spectra of known stars over several days to see if there are any dramatic/unexpected deviations in its spectral profile
The script giving the best results is 'imageplotter6.py' coded in python version 3.12.3, which gives plots of the spectra resembling a blackbody. The folders named spectra with corresponding dates on them contain the PNGs of the spectra.

Here are the steps on how to use the script once this project is copied to your local device:

1. Open a bash terminal and chande your directory to the folder this project is copied to.
2. Run the code (MacOS): 'python3 imageplotter6.py spectra [date] --interpolate 2.0 --rotate 55.2 --roi' (could get the three arguments to automatically run in a future script if desired)
3. The first image loaded is the image that CAMO took. Click ad drag on the image to select and roi to isolate the spectrum. The spectrum we want to aim for is usually the brightest/longest in these images.
  NOTE: When roi picking, DO NOT include the outer edges of the flat in the roi. The script currently thinks this is a part of the night sky and will greatly distort the spectrum and the plot that is made in the follownig steps.
4. Close the tab when the roi is made, and an enhanced, byteswapped image of the spectrum will be loaded in the next tab. (Could impliment here the option to remove background objects from the image, as this creates lines of 'emission' that are not a part of the star's spectrum)
5. Close this tab to load the plot of the spectrum (wavelength vs intensity). Save the spectrum (if desired) by clicking the right-most button at the bottom of the window (should look like a floppy disk / hdd)
6. Close this tab when done, and the following image in the folder will be loaded. Repeat steps 3-5 for the remaining spectra in the folder.

   Something that is worth noting is that flatfield correction has not been implimented into this version of the script yet. There are some commented out functions at the bottom that I was playing around with but could not get to work properly.
   I tried contacting Mike Mazur (WMG, mjmazur@uwo.ca) for help as he is the spectra expert in the group so he could lend a useful hand in this process.

If there are any questions or concerns about this version of the code, reach out to me by zaubry@uwo.ca and I can provide any help/guidance you need!
