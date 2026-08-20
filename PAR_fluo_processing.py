"""
author: Sasha Coles
date: August 19th, 2026
about: This script is for processing Concerto RBR sensor data (specifically fluorescence and PAR)
This script is designed to process one profile at a time, and follows the processing
guidelines outlined in Halverson et al. (2017).

This code is based on the RBR CTD processing script found here: https://github.com/IOS-OSD-DPG/RBR-CTD-Processing/tree/main
"""
import sys
import pyrsktools
import pandas as pd
from tkinter import Tk, filedialog

from openpyxl.styles import Alignment

# GLOBAL VARIABLES -- DONT CHANGE
processing_record = {}
original_raw_downcast_data = []


# USER-DEFINED VARIABLES -- FILL THESE IN BEFORE RUNNING!
dest_dir = "C:\\Users\\COLESS\\Documents\\Python_CTDscript\\PAR_fluo_script-main\\station1"
rsk_file_name = "Eureka2024_PAR_Fluo_St1.rsk"

def read_rsk():
    print("Reading RSK file...")
    file_name = str(dest_dir + "\\" + rsk_file_name)
    print(file_name)
    rsk = pyrsktools.RSK(file_name, readHiddenChannels=False)
    rsk.open()
    rsk.readdata()

    profiles = rsk.getprofilesindices()
    if len(profiles) != 1:
        sys.exit("RSK file has either: "
                 "- more than one profile. Make sure profiles are separated into their "
                 "own .rsk files before processing"
                 "- no profiles in the file")

    return rsk

def create_metadata_file(rsk):
    metadata_dict = {}
    metadata_file_name = dest_dir + "\\metadata.xlsx"

    # gather metadata information
    metadata_dict["Instrument Information"] = rsk.instrument
    metadata_dict["RSK File Name"] = rsk_file_name
    metadata_dict["Channels"] = rsk.channels
    metadata_dict["Number of Channels"] = len(rsk.channels)
    metadata_dict["Deployment"] = rsk.deployment

    metadata_df = pd.DataFrame(list(metadata_dict.items()),columns=["Key", "Value"])
    with pd.ExcelWriter(metadata_file_name, engine="openpyxl") as writer:
        metadata_df.to_excel(writer, index=False, sheet_name="Metadata")

        worksheet = writer.sheets["Metadata"]

        # Wrap text in all cells
        for row in worksheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(
                    wrap_text=True,
                    vertical="top"
                )

        worksheet.column_dimensions["A"].width = 20
        worksheet.column_dimensions["B"].width = 100
    print("Creating metadata file...")

def derive_values(rsk):
    #derive salinity (?), sea pressure, depth, and velocity (?)
    return rsk
    print("Deriving values...")

def get_downcast_and_upcast(rsk):

    ## or use this: upcast = rsk.casts(pyrsktools.Region.CAST_UP)
    # determine which records are upcast, which are downcast
    try:
        downcast_indices = rsk.getprofilesindices(direction="down")
        upcast_indices = rsk.getprofilesindices(direction="up")
    except AttributeError:
        rsk.computeprofiles()  # This should fix the problem
        downcast_indices = rsk.getprofilesindices(direction="down")
        upcast_indices = rsk.getprofilesindices(direction="up")

    print("Getting downcast and upcast...")

def pre_processing_plots():
    print("Pre-processing plots...")

def check_for_zoh():
    # this function calls each individual step in the processing pipeline, serves as main controller
    print("Checking for zoh...")

def prompt_user_for_spk_zoh():
    #ask the user if they want to despike the data, and ask if they want to correct for
    #zero order holds
    print("Prompting user for despiking and zoh correction...")

def correct_spikes_and_zoh():
    print("Correcting spikes and zoh...")


def process_rsk():
    original_rsk = read_rsk()
    create_metadata_file(original_rsk)
    pre_processing_plots()
    derived_rsk = derive_values(original_rsk)
    check_for_zoh()
    prompt_user_for_spk_zoh()
    correct_spikes_and_zoh()



process_rsk()