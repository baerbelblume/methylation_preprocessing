## load dependencies
import pandas as pd
import numpy as np
import sys
import os
import pyreadr
from DNAm.python.illuminaio import list_idat
from DNAm.python.preprocess import load_data, read_manifests

##load data for testing
data_file = 'Python_package/DNAm/python/dnam/R05C01_beads.csv'
data = load_data(data_file)
# shape (622399, 7)
data = data[1:10000]


#read manifests
#probes_file = 'DNAm/python/illumina_manifests/hm450_probes.rds'
#controls_file = 'DNAm/python/illumina_manifests/hm450_controls.rds'

#quick fix -csv file
probes_file = 'DNAm/python/testing/probes.csv'
controls_file = 'DNAm/python/testing/control_beads.csv'

probes, controls = read_manifests(probes_file, controls_file)

##Preprocessing
samples, cpgs, snps, intensities_A, intensities_B, controls_red, controls_grn = preprocessing(data, probes, controls,
    idat_files_folder, arg_beads=3, arg_detection=0.05, return_intensities=True)