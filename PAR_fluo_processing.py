"""
author: Sasha Coles
date: August 19th, 2026
about: This script is for processing Concerto RBR sensor data (specifically fluorescence and PAR)
This script is designed to process one profile at a time, and follows the processing
guidelines outlined in Halverson et al. (2017).

This code is based on the RBR CTD processing script found here: https://github.com/IOS-OSD-DPG/RBR-CTD-Processing/tree/main
"""

import pyrsktools

# GLOBAL VARIABLES -- DONT CHANGE
processing_record = {}
original_raw_downcast_data = []


# USER-DEFINED VARIABLES -- FILL THESE IN BEFORE RUNNING!
dest_dir = "C:\\Users\\COLESS\\Documents\\Python_CTDscript\\PAR_fluo_script-main\\station1"

def read_rsk():
    #read in the .rsk file thats located in dest_dir
    #save raw data in original_raw_downcast_data
def create_metadata_file():
    # create metadata csv file with information from rsk object
def derive_values():
    #derive salinity (?), sea pressure, depth, and velocity (?)
def format_profile_data():
    # determine which records are upcast, which are downcast
def pre_processing_plots():

def check_for_zoh():
    # this function calls each individual step in the processing pipeline, serves as main controller
def prompt_user_for_spk_zoh():
    #ask the user if they want to despike the data, and ask if they want to correct for
    #zero order holds
def correct_spikes_and_zoh():


def process_rsk():
    read_rsk()
    create_metadata_file()
    derive_values()
    format_profile_data()
    pre_processing_plots()
    check_for_zoh()
    prompt_user_for_spk_zoh()
    correct_spikes_and_zoh()
