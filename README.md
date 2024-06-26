# MESS
 The **M**eteor **E**lemental **S**pectra **S**oftware is a package based on the CAMO-S code for reducing meteor spectra from a static camera.
 
 # Installation
 To successfully run the software, Python and QT are required along with the following Python modules...
 - Cython
 - Numpy
 - Matplotlib
 - pyqtgraph
 - scipy
 - imageio
 - sklearn

It is also necessary to have the WMPL and RMS installed. If you find that you have trouble importing some of the modules from RMS (BinImageCy, for example), you can create soft links from the MESS.py directory to the appropriate files (BinImageCy.py and BinImageCy.pyx, in my case). 

 Installation in a virtualenv or a Conda environment is recommended.
 
 Build and install SpectralTest.so
 cd into spectral_library and type 'make' and then 'make install'
 
 **Input data types:** VID files, ev* txt files, PNG images<br>
 **Output data types:** CSV and PNG images

 # Quick Install
 - Install virtualenv or Anaconda3 (ex. conda create -n mess python=3.8)
 - Create an environment with Python=3.8 and activate it (ex. conda activate mess)
 - Go to https://github.com/wmpg/WesternMeteorPyLib and follow the instructions to install it to the environment that you're currently working in
 - Install some more packages...
  - conda install -y -c conda-forge pyqtgraph
  - conda install -y -c conda-forge imageio
  - conda install -y -c conda-forge scikit-learn
 - Go to https://github.com/CroatianMeteorNetwork/RMS and follow the instructions to install it to the environment that you're currently working in
 
 
# Using MESS
Under the 'Setup' tab...<br>
Step 1: Click on 'Load Spectral Vid' button to select a VID file for viewing.<br>
Step 2: The display should show a frame with a spectrum in it. If not, cycle through the frames with the left/right arrow buttons above the image display.<br>
Step 3: Click on 'Auto Flat' to automatically flatten the image.<br>
Step 4: If you see a zeroth-order image, you can try to auto-pick it with the 'Autopick 0th Order' button. If not, no problem.<br>
Step 5: Click on the 'Autopick ROI' button. If you're not happy with the area of interest, click it again.<br>
Step 6: Create a transform by clicking on a bright spectral feature and setting the lambda_0 to the correct value. Hint: Mg (518 nm) and Na (589 nm) are commonly visible.<br>
Step 7: Click 'Show Spectrum' button. You should see a spectrum appear within a few seconds.<br>
Under the 'Fitting' tab...<br>
