#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard library
import logging
from pathlib import Path
import sys, importlib
import os, platform

# Third party
from stemcellorganellesizescaling.analyses.data_prep import outlier_removal, initial_parsing
importlib.reload(sys.modules["stemcellorganellesizescaling.analyses.data_prep"])

# Relative

print("Libraries loaded succesfully")
###############################################################################

log = logging.getLogger(__name__)

###############################################################################

#%% Directories
if platform.system() == "Windows":
    data_root = Path("E:/DA/Data/scoss/Data/")
    pic_root = Path("E:/DA/Data/scoss/Pics/")
elif platform.system() == "Linux":
    data_root = Path("/allen/aics/modeling/theok/Projects/Data/scoss/Data/")
    pic_root = Path("/allen/aics/modeling/theok/Projects/Data/scoss/Pics/")
dirs = []
dirs.append(data_root)
dirs.append(pic_root)

#%% Data preparation - Initial Parsing
print('##################### Data preparation - Initial Parsing #####################')
tableIN = "/allen/aics/assay-dev/MicroscopyOtherData/Viana/projects/cell_shape_variation/local_staging/expand/manifest.csv"
tableSNIP = "Manifest_snippet_202010106.csv"
tableOUT = "SizeScaling_20201006.csv"
initial_parsing(dirs, tableIN, tableSNIP, tableOUT)

#%% Data preparation - Outlier Removal
print('##################### Data preparation - Outlier Removal #####################')
# tableIN = "SizeScaling_20200828.csv"
# tableOUT = "SizeScaling_20200828_clean.csv"
# outlier_removal(dirs, tableIN, tableOUT)