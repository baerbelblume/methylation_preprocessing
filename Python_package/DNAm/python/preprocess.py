# -*- coding: utf-8 -*-
# For license information, see LICENSE.TXT
import sys
import os
import pyreadr
import pandas as pd
import numpy as np
from scipy.stats import norm
from DNAm.python.illuminaio import list_idat


def load_data(csv_file):
    data = pd.read_csv(csv_file, low_memory=False)
    data.columns = ['sample_id', 'grn_n', 'grn_mean', 'grn_sd', 'red_n', 'red_mean', 'red_sd']
    return data

def read_manifests(probes_file, controls_file):
    #result_p = pyreadr.read_r(probes_file)
    #probes = pd.DataFrame((result_p[None])) #columns=['chr', 'pos', 'type', 'address_a', 'address_b'])

    #result_c = pyreadr.read_r(controls_file)
    #controls = pd.DataFrame((result_c[None])) #columns=['type', 'color', 'description', 'comment'])
    
    ## temporary solution (pyreader does not recognise the index labels)
    controls = pd.read_csv(controls_file, low_memory=True)
    controls.set_index(['Unnamed: 0'], inplace=True)
    controls.index.names = ['sample_id']

    probes = pd.read_csv(probes_file, low_memory=True)
    #probes.set_index(['Unnamed: 0'], inplace=True)
    #probes.index.names = ['sample_id']
    return probes, controls


def preprocess(data, probes, controls, idat_files_folder, min_beads=3, detection=0.05, return_intensities=False, return_snps_r=False):
""" 
Preprocesses Illumina Infinium DNA methylation bead chips

Parses .idat files and performs probe censoring, background subtraction and dye-bias correction. 
SNPs and summary statistics including information from control beads are also provided.

Parameters
-----------
    data (): 
    probes():
    idat_files_folder (path): path to folder containing .idat files (2 per sample)
    min_beads (int, optional): probes with less beads will be censored (default 3)
    detection (float, optional): p-value for probe-detection, probes that aren't significantly different from negative control beads are censored (default 0.05)
    return_intensities (bool): returns four (large) matrices containing preprocessed intensities: intensities_A, intensities_B and controls_red, controls_grn
    return_snps_r (bool): returns matrix containing SNP r-coordinate in polar coordinate system
    verbose (bool): prints timestamp per sample and overall time taken

Returns
--------
    Returns list with at least three elements
    
    dataframe: containing sample metadata and summary statistics
    matrix: containing CpG beta-values (= methylation proportions)
    matrix: containing theta-values of SNPs in polar coordinate system
    matrix: containing r-values of SNPs in polar coordinate system (optional))
    matrix: containing unmethylated-intensities (A-beads for Illumina I, red channel for Illumina II, optional))
    matrix: containing methylated-intensities (B-beads for Illumina I, green channel for Illumina II, optional))
    matrix: containing control-bead-intensities on red channel (optional))
    matrix: containing control-bead-intensities on green channel (optional))


    {
        'idat_files_folder': idat_files_folder
        'min_beads': min_beads
        'detection': detection
        'return_intensities': return_intensities
        'return_snps_r': return_snps_r
        'verbose': verbose

    }

Raises:


"""

    ## check argument values
    assert detection > 0 
    assert detection <= 1
    assert min_beads > 0

    ## preparation of outputs
    inf1grn = probes[probes['type'] == "I-Grn"]
    inf1red = probes[probes['type'] == "I-Red"]
    inf2 = probes[probes['type'] == "II"]
    idat_files = list_idat(idat_files_folder)

    ## create intensities
    ## create empty dataframes to append to
    intensities_A = pd.DataFrame(np.nan, index=probes.index, columns=pd.unique(idat_files['sample.id']))
    intensities_B = pd.DataFrame(np.nan, index=probes.index, columns=pd.unique(idat_files['sample.id']))

    controls_grn = pd.DataFrame(np.nan, index=controls.index, columns=pd.unique(idat_files['sample.id']))
    controls_red = pd.DataFrame(np.nan, index=controls.index, columns=pd.unique(idat_files['sample.id']))


    ##Separation of unmethylated and methylated intensities
    # Separate Grn/Red intensities into A (unmethylated) and B (methylated) intensities
    # depending on their type

    ad_a_grn = (probes['address.a'].loc[probes['type'] == 'I-Grn']).index
    ad_b_grn = (probes['address.b'].loc[probes['type'] == 'I-Grn']).index
    ad_a_red = (probes['address.b'].loc[probes['type'] == 'I-Red']).index
    ad_b_red = (probes['address.b'].loc[probes['type'] == 'I-Red']).index
    ad_a_inf = (probes['address.a'].loc[probes['type'] == 'II']).index

    inf1grn = probes[probes['type'] == "I-Grn"].index
    inf1red = probes[probes['type'] == "I-Red"].index
    inf2 = probes[probes['type'] == "II"].index

    con_ind = controls.index
    sample_ids = pd.unique(idat_files['sample.id'])


    #loop over sample id index and fill out rows based on if value is in data
    
    for column in intensities_A:
        print (np.where(data.loc[ad_a_grn]))
        
        intensities_A[column].loc[inf1grn] = np.where(data.loc[ad_a_grn, 'grn_n'] >= min_beads, data.loc[ad_a_grn, 'grn_mean'], np.nan)
        intensities_A[column].loc[inf1red] = np.where(data.loc[ad_a_red, 'red_n'] >= min_beads, data.loc[ad_a_red, 'red_mean'], np.nan)
        intensities_A[column].loc[inf2] = np.where(data.loc[ad_a_inf, 'grn_n'] >= min_beads, data.loc[ad_a_inf, 'grn_mean'], np.nan)


    for column in intensities_B:
        intensities_B[column].loc[inf1grn] = np.where(data.loc[ad_b_grn, 'grn_n'] >= min_beads, data.loc[ad_b_grn, 'grn_mean'], np.nan)
        intensities_B[column].loc[inf1red] = np.where(data.loc[ad_b_red, 'red_n'] >= min_beads, data.loc[ad_b_red, 'red_mean'], np.nan)
        intensities_B[column].loc[inf2] = np.where(data.loc[ad_a_inf, 'red_n'] >= min_beads, data.loc[ad_a_inf, 'grn_mean'], np.nan)

    for column in controls_grn:
        dataa = data.set_index('sample_id')
        controls_grn[column].loc[con_ind] = np.where(dataa.loc[con_ind, 'grn_n'] > 0,
                                                      dataa.loc[con_ind, 'grn_mean'],
                                                      np.nan)

        neg_beads_grn = controls[controls['type'] == "NEGATIVE"].index
        neg_means_grn = (controls_grn[column].loc[neg_beads_grn]).mean()
        neg_sds_grn = (controls_grn[column].loc[neg_beads_grn]).std(axis=0)

    for column in controls_red:
        controls_red[column].loc[con_ind] = np.where(dataa.loc[con_ind, 'red_n'] > 0,
                                                      dataa.loc[con_ind, 'red_mean'],
                                                      np.nan)

        neg_beads_red = controls[controls['type'] == "NEGATIVE"].index
        neg_means_red = (controls_red[column].loc[neg_beads_red]).mean()
        neg_sds_red = (controls_red[column].loc[neg_beads_red]).std(axis=0)


    ## Defining a threshold of detection
    neg_means_ = np.mean([neg_means_grn, neg_means_red])
    neg_sds_ = np.std([neg_sds_grn, neg_sds_red])

    z = norm.ppf(1 - detection)

    threshold_inf1grn = 2 * neg_means_grn + z * np.sqrt(2) * neg_sds_grn
    threshold_inf1red = 2 * neg_means_red + z * np.sqrt(2) * neg_sds_red
    threshold_inf2 = np.sum(neg_means_) + z * np.sqrt(np.sum(neg_sds_ ** 2))

    # Censoring of values below the detection limit and background subtraction
    # Background subtraction

    for column in intensities_A:
        I_A = (intensities_A).sum(axis=1) #sum(axis=1)

        ## slower, alternative way of censoring values
        #intensities_AA[column].loc[inf1grn] = (np.where((intensities_AA.loc[inf1grn].gt(neg_means_grn).values & (I_A.loc[inf1grn].gt(threshold_inf1grn).values)),
        #                                            (intensities_AA[column].loc[inf1grn] - neg_means_grn),
        #                                            np.nan))
        
        intensities_A_grn = intensities_A[column].loc[inf1grn]
        intensities_A_grn[column] = intensities_A_grn[(intensities_A_grn.gt(neg_means_grn).values) & (I_A.loc[inf1grn].gt(threshold_inf1grn).values)]


        intensities_A_red = intensities_A[column].loc[inf1red]
        intensities_A_red[column] = intensities_A_red[(intensities_A_red.gt(neg_means_red).values) & (I_A.loc[inf1red].gt(threshold_inf1red).values)]


        intensities_A_inf2 = intensities_A[column].loc[inf2]
        intensities_A_inf2[column] = intensities_A_inf2[(intensities_A_inf2.gt(neg_means_red).values) & (I_A.loc[inf2].gt(threshold_inf2).values)]


    for column in intensities_B:
        I_B = (intensities_B).sum(axis=1)
        intensities_B_grn = intensities_B[column].loc[inf1grn]
        intensities_B_grn[column] = intensities_B_grn[(intensities_B_grn.gt(neg_means_grn).values) & (I_B.loc[inf1grn].gt(threshold_inf1grn).values)]


        intensities_B_red = intensities_B[column].loc[inf1red]
        intensities_B_red[column] = intensities_B_red[(intensities_B_red.gt(neg_means_red).values) & (I_B.loc[inf1red].gt(threshold_inf1red).values)]


        intensities_B_inf2 = intensities_B[column].loc[inf2]
        intensities_B_inf2[column] = intensities_B_inf2[(intensities_B_inf2.gt(neg_means_red).values) & (I_B.loc[inf2].gt(threshold_inf2).values)]


    # Extract normalization probes for Grn and Red, and form the dye bias correction constant
    norm_grn_beads = controls[controls['type'].isin(['NORM_C', 'NORM_G'])].index

    match_ = controls['description'].loc[norm_grn_beads].str.translate(str.maketrans('CG', 'TA'))
    norm_red_beads = controls['description'].isin(match_).index

    for column1, column2 in zip(controls_grn, controls_red):
        grn = controls_grn[column1].loc[norm_grn_beads]
        red = controls_red[column2].loc[norm_red_beads]
        norm_data = pd.concat([grn, red], axis=1)

        corrections_grn = (np.mean(norm_data[column1], axis=1)/ grn).mean(axis=0)
        corrections_red = (np.mean(norm_data[column2], axis=1)/ red).mean(axis=0)

    ## Apply dye bias correction
        intensities_A.loc[inf2] = intensities_A.loc[inf2] * corrections_red
        intensities_B.loc[inf2] = intensities_B.loc[inf2] * corrections_grn


    ## Computing DNA methylation ratios (β values)
    #Some of the probes are SNPs (N=65), these can be identified because they start with the prefix “rs”

    # Create DNAm ratios as B (methylated) over total

    probes.set_index(['Unnamed: 0'], inplace=True)
    probes.index.names = ['sample_id']
    idx = probes[probes.index.str.contains('rs')].index
    intensities = intensities_A.add(intensities_B, fill_value=0)

    dnam = intensities_B.loc[intensities_B.index.difference(idx)]/intensities


    ## SNPS

    intensities_A.set_index(probes.index, inplace=True)
    intensities_B.set_index(probes.index, inplace=True)

    #snps = pd.DataFrame(np.nan, index=probes.loc[idx].index, columns=pd.unique(idat_files['sample.id']))
    
    idx = probes[probes.index.str.contains('rs')].index
    snps = np.arctan2(intensities_B.loc[idx], intensities_A.loc[idx]) / (np.pi/2)
    


    ### matching 
    # Extract all control probes data, and add summary statistics to samples table

    summary = pd.DataFrame(np.nan, columns=pd.unique(idat_files['sample.id']), 
        index=['bc1_red', 'bc2', 'ext_a', 'ext_c', 'ext_g', 'ext_t',
                'hyp_low', 'hyp_med', 'hyp_high', 'np_a', 'np_c',
                'np_g', 'np_t', 'spec1_red', 'spec2', 'st_grn', 'st_red',
                'tr', 'missing', 'median_chrX', 'missing_chrY'])


    # match 1
    bg = ['BS Conversion I-U4', 'BS Conversion I-U5','BS Conversion I-U6']
    idx_bg = (controls[controls['description'].str.contains('|'.join(bg))]).index

    match_ = controls['description'].loc[idx_bg].str.translate(str.maketrans('U', 'C'))
    idx_signal = controls['description'].isin(match_).index
    summary.loc['bc1_red'] = (np.nanmean(controls_red.loc[idx_signal])/np.nanmean(controls_red.loc[idx_bg]))

    idx = controls[controls['type'] == 'BISULFITE CONVERSION II'].index
    summary.loc['bc2'] = np.nanmean(controls_red.loc[idx]/np.nanmean(controls_grn.loc[idx]))

    idd = controls[controls['description'] == 'Extension (A)'].index
    summary.loc['ext_a'] = controls_red.loc[idd].values
    
    idd = controls[controls['description'] == "Extension (C)"].index
    summary.loc['ext_a'] = controls_grn.loc[idd].values 

    idd = controls[controls['description'] == 'Extension (G)'].index
    summary.loc['ext_t'] = controls_grn.loc[idd].values

    idd = controls[controls['description'] == 'Extension (T)'].index
    summary.loc['ext_t'] = controls_red.loc[idd].values
    
    idd = controls[controls['description'] == 'Hyb (Low)'].index
    summary.loc['hyp_low'] = controls_grn.loc[idd].values 

    idd = controls[controls['description'] == 'Hyb (Medium)'].index
    summary.loc['hyp_med'] = controls_grn.loc[idd].values 

    idd = controls[controls['description'] == 'Hyb (High)'].index
    summary.loc['hyp_high'] = controls_grn.loc[idd].values 

    idd = controls[controls['description'] == 'NP (A)'].index
    summary.loc['np_a'] = controls_red.loc[idd].values 

    idd = controls[controls['description'] == 'NP (C)'].index
    summary.loc['np_c'] = controls_grn.loc[idd].values 

    idd = controls[controls['description'] == 'NP (G)'].index
    summary.loc['np_g'] = controls_grn.loc[idd].values 

    idd = controls[controls['description'] == 'NP (T)'].index
    summary.loc['np_t'] = controls_red.loc[idd].values 

    # match 2
    bg = ["GT Mismatch 1 (MM)", "GT Mismatch 2 (MM)", "GT Mismatch 3 (MM)"]
    idx_bg = controls[controls.description.str.contains('|'.join(bg))].index
    match_ = controls['description'].loc[idx_bg].str.translate(str.maketrans('MM', 'PM'))
    idx_signal = controls['description'].isin(match_).index

 
    summary.loc['spec1_red'] = (np.nanmean(controls_red.loc[idx_signal])/np.nanmean(controls_red.loc[idx_bg]))

    idx = controls[controls['type'] == 'SPECIFICITY II'].index
    summary.loc['spec2'] = (np.nanmean(controls_red.loc[idx])/np.nanmean(controls_grn.loc[idx]))

    # match 3 
    idx_bg = controls[controls['description'] == ('Biotin (Bkg)')].index
    idx_signal = controls[controls['description'] == ('Biotin (High)')].index
    summary.loc['st_grn'] = controls_grn.loc[idx_signal].values / controls_grn.loc[idx_signal].values

    # match 4
    idx_bg = controls[controls['description'] == ('DNP (Bkg)')].index
    idx_signal = controls[controls['description'] == ('DNP (High)')].index
    summary.loc['st_red'] = controls_red.loc[idx_signal].values / controls_red.loc[idx_signal].values

    # match 5
    idx = controls[controls['type'] == ('TARGET REMOVAL')].index
    summary.loc['tr'] = np.nanmax(controls_grn.loc[idx], axis=0)
    summary.loc['missing'] = dnam.isnull().mean(axis=0)

    # match 6
    idx = probes[probes['chr'] == 'X'].index
    dnam.set_index(probes.index, inplace=True)
    summary.loc['median_chrX'] = np.nanmedian(dnam.loc[idx], axis=0)

    idy = probes[probes['chr'] == 'Y'].index
    summary.loc['missing_chrY'] = dnam.loc[idy].isnull().mean(axis=0)

    samples = summary
    cpgs = dnam

    ## add SNPs r values??

    if return_intensities == True:
        return samples, cpgs, snps, intensities_A, intensities_B, controls_red, controls_grn

    elif return_snps == True:
        return snps

    else:
        return samples, cpgs, snps




