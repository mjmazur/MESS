# MESS (Meteor Elemental Spectral Software)

**MESS** is an advanced, PyQt-based scientific analysis package designed to extract, reduce, and model meteor spectra from static camera observations and video workflows. Initially based on the CAMO-S code, MESS provides a rich Graphical User Interface to process high-speed `.vid.bz2` streams, calibrate wavelengths, model elemental abundance against various thermal profiles, and fit spectral emissions against deep meteor composition libraries.

---

## Features & Capabilities

- **Native `.bz2` Event Ingestion:** Seamlessly parses `ev_...txt` metadata and unpacks heavily compressed `02I` and `02J` video archives using direct stream extraction without memory-bottlenecking.
- **Automated Flattening & Bounding Regions:** Cycle through video frames to perform auto-flat transformations, background bias rejection, and auto-picking of zeroth-order optical images and ROIs (Regions of Interest).
- **Stellar & Synthetic Calibrations:** Calibrate instruments against cataloged stellar spectrum references, scaling pixel intensity against absolute nm wavelengths.
- **Warm & Hot Plasma Modeling:** Integrate the Gural Spectral Library natively via Cython (`SpectralTest.so`) to model thermodynamic spectra (e.g., matching column densities, electron distribution, and hot-to-warm plasma ratios). 
- **Multi-Element Decomposition Unpacking:** Overlay and curve-fit precise transitions for elements spanning the periodic table (Fe, Mg, Na, Ni, etc.) concurrently.

---

## Requirements & Dependencies

To successfully compile and run the software, Python 3.8+ and PyQt5 are required alongside the following critical domain libraries:

- **Core Computation & UI:** `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `pyqtgraph`, `imageio`
- **Bindings:** `Cython` (required to compile the native spectral math core)
- **External Astronomical Frameworks:**
  - **WMPL** (Western Meteor PyLib)
  - **RMS** (Global Meteor Network / CroatianMeteorNetwork)

> **Note:** If you experience import path issues resolving RMS binaries (like `BinImageCy`), you may need to explicitly soft-link the compiled `.pyx`/`.so` paths natively into the MESS working directory.

---

## Quick Installation Guide

Installation in an isolated `virtualenv` or `Conda` environment is highly recommended to protect dependency graphs.

**1. Create and Activate the Environment**
```bash
conda create -n mess python=3.8
conda activate mess
```

**2. Install Core GUI & Math Modules**
```bash
conda install -y -c conda-forge pyqtgraph imageio scikit-learn
```

**3. Install Meteor Research Tooling**
Follow the installation manuals natively to hook into your environment for:
- [WMPL (Western Meteor PyLib)](https://github.com/wmpg/WesternMeteorPyLib)
- [RMS (Croatian Meteor Network)](https://github.com/CroatianMeteorNetwork/RMS)

**4. Build the C/Cython Spectral Core**
```bash
cd spectral_library
make
make install
```

---

## Workflow & Usage Guide

Launch the main UI interface via:
```bash
python MESS.py
```

### The `Setup` Tab
1. **Load Event Stream:** Click **Load Event/Spectral Vid** to select a standard `ev...txt` configuration or a direct `VID/BZ2` media stream. 
2. **Scan Frames:** The preview should render a bounded spectrum. Use the left/right arrow timeline keys above the render window to scan for peak emission frames.
3. **Geometry & Transformations:** Apply **Auto Flat** to flatten intensity, adjust bias limits via rollboxes, and automatically hunt bounds using **Autopick 0th Order** / **Autopick ROI**. 
4. **Wavelength Calibration:** Anchor a known elemental transition in the viewer by picking a bright spectral node (Often Mg @ 518 nm or Na @ 589 nm) and aligning it using the local $\lambda_0$ transform inputs.
5. **View Target:** Click **Show Spectrum** to convert the localized frame bounds into a 1D pixel/intensity curve map.

### The `Fitting` Tab
*Proceed to the fitting layer to begin isolating column densities, overlaying thermal variants, fitting Fe/Mg/Na peaks, determining baseline continuum noise boundaries, and generating statistical output graphs.*

---

**Input data types:** `*.vid`, `*.bz2`, `ev*.txt`, `*.png`  
**Output data types:** `*.csv`, `*.txt`, `*.png`
