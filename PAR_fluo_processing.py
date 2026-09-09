"""
author: Sasha Coles
date: August 19th, 2026
about: This script is for processing Concerto RBR sensor data (specifically fluorescence and PAR)
This script is designed to process one profile at a time, and follows the processing
guidelines outlined in Halverson et al. (2017).

This code is based on the RBR CTD processing script found here: https://github.com/IOS-OSD-DPG/RBR-CTD-Processing/tree/main
"""
import copy
import shutil
import sys
import os
import re

import numpy as np
import pyrsktools
import pandas as pd

from matplotlib import pyplot as plt
from openpyxl.styles import Alignment
from pyrsktools._rsk.export import RSK2CSV
from scipy import signal

# GLOBAL VARIABLES
CHANNELS = ["chlorophyll_a", "par"]
CHANNEL_UNTIS = {"chlorophyll_a" : "µg/l", "par":"µMol/m²/s"}
processing_record = {}
original_raw_downcast_data = []
sampling_period = np.nan



# USER-DEFINED VARIABLES -- FILL THESE IN BEFORE RUNNING!
dest_dir = "C:\\Users\\COLESS\\Documents\\Python_CTDscript\\PAR_fluo_script-main\\station2"
rsk_file_name = "Eureka2024_PAR_Fluo_St2.rsk"
fill_action = 'interp' ## how we want to correct for zero order holds and despike--can either be 'interp' or na
## despiking variables:
spk_std = 3
spk_window = 11
## clipping variables:
limit_pressure_change_down = 0.02
limit_pressure_change_up = -0.03
## low-pass filter variables:
filter_type = 'FIR' # can be one of two values: 'FIR' or 'moving average'
filter_window_width = 6

def read_rsk():
    print("Reading RSK file...")
    file_name = str(dest_dir + "\\" + rsk_file_name)
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
    metadata_dict["Sampling Interval"] = str(rsk.scheduleInfo.samplingperiod()) + " seconds"
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

def get_sampling_period(rsk):
    interval = rsk.scheduleInfo.samplingperiod()
    global sampling_period

    if interval <= 0 and sampling_period is np.nan:
        sys.exit("Sampling period not detected correctly in metadata. Fill out sampling period manually on line 25.")
    else:
        sampling_period = interval

def derive_values(rsk):
    print("Deriving sea pressure, depth, and velocity...")
    rsk.deriveseapressure()
    rsk.derivedepth()
    rsk.derivevelocity()
    return rsk

def get_downcast_and_upcast(rsk):
    # determine which records are upcast, which are downcast, return indices
    try:
        downcast_indices = rsk.gsetprofilesindices(direction="down")
        upcast_indices = rsk.getprofilesindices(direction="up")
    except AttributeError:
        rsk.computeprofiles()  # This should fix the problem
        downcast_indices = rsk.getprofilesindices(direction="down")
        upcast_indices = rsk.getprofilesindices(direction="up")

    if len(downcast_indices) == 0:
        raise ValueError("No downcast found.")

    if len(upcast_indices) == 0:
        raise ValueError("No upcast found.")

    return downcast_indices[0], upcast_indices[0]

def plot_channels(rsk_df, stage, figure_dir):
    ## plot each channel vs pressure
    print("Plotting channels...")
    if stage == "pre" or stage == "1_pre":
        figure_name = "1_pre_processing_"
        title = "Pre-Processing "
    elif stage == "post":
        figure_name = "post_processing_"
        title = "Post-Processing "
    else:
        figure_name = stage + "_"
        title = re.sub(r'\d+', '', (stage.replace("_", " ") + " "))

    for channel in CHANNELS:
        figure, ax = plt.subplots()
        ax.plot(rsk_df[channel], rsk_df["pressure"])
        ax.invert_yaxis()
        ax.xaxis.set_label_position("top")
        ax.xaxis.set_ticks_position("top")
        ax.tick_params(bottom=True, top=True, left=True, right=True, labelbottom=True, labeltop=True, labelleft=True, labelright=True)
        plt.ylabel("Pressure (decibar)")
        plt.xlabel(channel.capitalize() + " (" + CHANNEL_UNTIS[channel] + ")")
        plt.title(title.title() + channel.replace("_", " ").capitalize() + " vs. Pressure")
        plt.tight_layout()
        plt.savefig(figure_dir + "\\"+ figure_name + channel)

def plot_pressure_diff(rsk_df, stage, figure_dir):
    ##plot pressure for all scans in rsk data
    print("Plotting pressure...")

    if stage == "pre":
        figure_name = "pressure_differences.png"
        title = "Pressure Difference Between Consecutive Scans"
    elif stage == "post":
        figure_name = "pressure_differences_with_corrections.png"
        title = "Pressure Difference Between Consecutive Scans (with ZOH corrections made)"

    pressure_diff = rsk_df["pressure"].diff()

    figure = plt.figure(figsize = (14, 6), dpi = 600)

    plt.plot(pressure_diff, color = "blue", linewidth = 0.5, label = "Pressure Diff")
    plt.ylabel("Pressure (decibar)")
    plt.xlabel("Scans")
    plt.grid()
    plt.legend()
    plt.title(title)
    plt.tight_layout()
    plt.savefig(os.path.join(figure_dir + "\\" + figure_name))

def trim_profile(rsk):
    rsk = remove_soak(rsk)
    downcast_indices, upcast_indices = get_downcast_and_upcast(rsk)
    down_start, down_end = clip_cast(rsk, 'down', downcast_indices, limit_pressure_change_down)
    up_start, up_end = clip_cast(rsk, 'up', upcast_indices, limit_pressure_change_up)
    downcast_indices = downcast_indices[down_start:down_end]
    upcast_indices = upcast_indices[up_start:up_end]
    keep_indices = np.sort(np.concatenate([downcast_indices, upcast_indices]))
    rsk.data = rsk.data[keep_indices].copy()
    return rsk

def remove_soak(rsk):
    print("- Removing soak from beginning of downcast")
    window = 100
    run = 100  ## instrument must be actively dropping/rising for at least 100 samples in a row

    pressure = pd.Series(rsk.data["pressure"])

    # soak detection
    rolling_std = pressure.rolling(window).std()
    threshold = rolling_std.quantile(0.10)
    moving = rolling_std > threshold  # moving = true means the instrument is actively dropping/rising, false means its soaking

    start = None

    for i in range(len(moving) - run):  # check samples 1-49, 1-50, 2-51, etc
        if moving.iloc[i:i + run].all():  ## do all samples within the window have the value moving = true?
            start = i
            break
    if start is None:
        print("No samples trimmed from downcast--no soak period detected.\n")
        start = 0

    rsk.data = rsk.data[start:]

    return rsk

def clip_cast(rsk, cast_direction, indices, limit_pressure_change):
    pressure = pd.Series(rsk.data["pressure"][indices])
    diff = pressure.diff()

    index_start = pressure.index[0]
    if cast_direction == "down":
        limit_drop = limit_pressure_change
        diff_mask = diff > limit_drop
    elif cast_direction == "up":
        limit_rise = limit_pressure_change
        diff_mask = diff < limit_rise
    else:
        sys.exit(f"cast_direction {cast_direction} is invalid. Ending program")
    diff_rise = diff.loc[diff_mask]
    for j in range(len(diff.loc[diff_mask])):
        index_1 = diff_rise.index[j]
        if (
                (diff_rise.index[j + 1] == index_1 + 1)
                and (diff_rise.index[j + 2] == index_1 + 2)
                and (diff_rise.index[j + 3] == index_1 + 3)
                and (diff_rise.index[j + 4] == index_1 + 4)
                and (diff_rise.index[j + 5] == index_1 + 5)
                and (diff_rise.index[j + 6] == index_1 + 6)
                and (diff_rise.index[j + 7] == index_1 + 7)
                and (diff_rise.index[j + 8] == index_1 + 8)
        ):
            index_end_1 = index_1 - 1
            break
    cut_start = index_end_1 - index_start

    for j in range(-1, -len(diff.loc[diff_mask]), -1):
        index_2 = diff_rise.index[j]
        if (
                (diff_rise.index[j - 1] == index_2 - 1)
                and (diff_rise.index[j - 2] == index_2 - 2)
                and (diff_rise.index[j - 3] == index_2 - 3)
                and (diff_rise.index[j - 4] == index_2 - 4)
                and (diff_rise.index[j - 5] == index_2 - 5)
        ):
            index_end_2 = index_2 + 1
            break
    cut_end = index_end_2 - index_start

    return cut_start, cut_end

## this might be misleading since it only talks about pressure
## but other channels have holds that should be fixed/interpolated, not just pressure
def check_for_zoh(rsk):
    print("Checking for zoh...")
    rsk_df = pd.DataFrame(rsk.data)
    pressure = pd.to_numeric(rsk_df["pressure"], errors="coerce").dropna()
    pressure_diffs = np.diff(pressure)

    print("\n--------------------------------------------------------------")
    print("checking for zero order holds. Use the following values to help decide if corrections are needed or not:")
    print("Total number of pressure records:", len(pressure))
    print(
        "Sum of zero pressure differences "
        "(number of neighboring samples with identical pressure values):",
        sum(pressure_diffs == 0)
    )
    print("\n")
    sec2min = 1 / 60

    if sum(pressure_diffs == 0) >= np.floor(
            len(pressure) * sampling_period * sec2min
    ):
        zoh_correction_needed = True
        print("based on these values, it is likely ZOH corrections are needed.")
    else:
        zoh_correction_needed = False
        print("based on these values, it is unlikely ZOH corrections are needed.")

    print("--------------------------------------------------------------")

def prompt_user_for_despiking(channel):
    #ask the user if they want to despike chlorophyll a and/or par
    valid_input = False
    while not valid_input:
        user_input = input(f'Is despiking needed for {channel}? Enter either true or false:').lower().strip()
        if user_input == 'true':
            user_input = True
            valid_input = True
            print(f"{channel} will be despiked.")
        elif user_input == 'false':
            user_input = False
            valid_input = True
        else:
            print('Invalid input. You must enter either true or false.')
    return user_input

    ## i think separate prompts for spk and zoh this time, maybe depending on if we want to despike BOTH par and fluo!!

def prompt_user_for_zoh():
    valid_input = False
    while not valid_input:
        user_input = input('Is zero order hold correction needed? Enter either true or false:').lower().strip()
        if user_input =='true':
            user_input = True
            valid_input = True
            print("zero order holds will be corrected.")
        elif user_input == 'false':
            user_input = False
            valid_input = True
            print("zero order holds will not be corrected.")
        else:
            print('Invalid input. You must enter either true or false.')
    return user_input

def correct_spikes_and_zoh(rsk):
    print("Correcting spikes and zoh...")
    check_for_zoh(rsk)

    if prompt_user_for_zoh():
        rsk.correcthold(action = fill_action)
    if prompt_user_for_despiking('chlorophyll a'):
        rsk.despike(channels='chlorophyll_a', threshold=spk_std, windowLength=spk_window, action=fill_action)
    if prompt_user_for_despiking('par'):
        rsk.despike(channels='par', threshold=spk_std, windowLength=spk_window, action=fill_action)
    return rsk

def rsk_to_csv(rsk, file_name):
    RSK2CSV(rsk, outputDir=dest_dir)
    default_csv = os.path.join(dest_dir, rsk_file_name.replace(".rsk", ".csv"))  # same base name as your .rsk file
    new_csv = os.path.join(dest_dir,file_name)
    shutil.move(default_csv, new_csv)

def separate_casts(rsk):
    downcast_indices, upcast_indices = get_downcast_and_upcast(rsk)
    rsk_df = pd.DataFrame(rsk.data)
    rsk_df["Date"] = rsk_df["timestamp"].dt.strftime("%d/%m/%Y")
    rsk_df["TIME"] = rsk_df["timestamp"].dt.strftime("%H:%M:%S")

    downcast = rsk_df.iloc[downcast_indices].copy()
    upcast = rsk_df.iloc[upcast_indices].copy()

    return downcast, upcast

def low_pass_filter(downcast, upcast):
    print('applying low pass filter...')
    sample_rate = int(np.round(1 / float(sampling_period)))

    if filter_type.lower() == 'fir':
        Wn = (1.0 / sampling_period) / (sample_rate * 2)
        # Numerator (b) and denominator (a) polynomials of the IIR filter
        b, a = signal.butter(2, Wn, "low")
    elif filter_type.lower() == 'moving average':
        b = (np.ones(filter_window_width)) / filter_window_width  # numerator co-effs of filter transfer function
        a = np.ones(1)  # denominator co-effs of filter transfer function
    else:
        sys.exit("invalid filter type. \nNavigate to line ~44 and change filter type to either 'FIR' or 'moving average'.")

    downcast["pressure"] = signal.filtfilt(b, a, downcast["pressure"])
    downcast["chlorophyll_a"] = signal.filtfilt(b, a, downcast["chlorophyll_a"])
    downcast["par"] = signal.filtfilt(b, a, downcast["par"])
    upcast["pressure"] = signal.filtfilt(b, a, upcast["pressure"])
    upcast["chlorophyll_a"] = signal.filtfilt(b, a, upcast["chlorophyll_a"])
    upcast["par"] = signal.filtfilt(b, a, upcast["par"])

    return downcast, upcast

def descent_rate_filter(cast, direction):
    print("applying descent rate filter and correcting wake effect...")
    n_before = len(cast)

    press = cast['pressure'].values
    # go to 10db off the bottom
    press_max = np.nanmax(press) - 10
    cast['p_range'] = np.repeat('p_range', len(cast))
    # get a subset of between 10m and 10 off the bottom
    cast['p_range'] = np.where(
        cast['pressure'].between(10, press_max), 'in_range', 'out_range'
    )
    subsetter = np.where(
        (cast['p_range'] == 'in_range') & (cast['velocity'] < 0.3)
    )
    ref = press[0]

    if direction == "down":
        inversions = np.diff(np.r_[press, press[-1]]) < 0 # a mask
    elif direction == 'up':
        inversions = np.diff(np.r_[press, press[-1]]) > 0 # a mask
    else:
        sys.exit('invalid direction given to descent_rate_filter function. '
                 'correct this value (line 444-445) and try again.')

    mask = np.zeros_like(inversions)
    for k, p in enumerate(inversions):
        if p:
            ref = press[k]
            if direction == 'down':
                cut = press[k + 1:] < ref
            elif direction == 'up':
                cut = press[k + 1:] > ref
            else:
                sys.exit('invalid direction given to descent_rate_filter function. ')
            mask[k + 1:][cut] = True
    # Now also mask the low descent rate between 10db and the 10 off the bottom
    mask[subsetter] = True

    # Diagnostics
    n_inversions = np.sum(inversions)
    n_masked = np.sum(mask)
    n_low_velocity = len(subsetter[0])

    print(f"  Original rows:       {n_before}")
    print(f"  Pressure inversions: {n_inversions}")
    print(f"  Low velocity points: {n_low_velocity}")
    print(f"  Total rows removed:  {n_masked}")

    cast[mask] = np.nan
    cast = cast.drop(columns=['p_range', 'velocity'])
    cast = cast.dropna(how='any')

    n_after = len(cast)

    print(f"  Rows remaining:      {n_after}")

    return cast

def process_rsk():
    raw_rsk = read_rsk() # copy of the untouched raw data
    raw_rsk_df = pd.DataFrame(raw_rsk.data) # convert it into dataframe format

    rsk = read_rsk() # copy of the rsk object that will be processed

    get_sampling_period(rsk)
    create_metadata_file(rsk)
    rsk_to_csv(rsk, rsk_file_name.replace(".rsk", "_raw_data.csv"))
    figure_dir = os.path.join(dest_dir, "figures")
    if not os.path.exists(figure_dir): os.makedirs(figure_dir)
    plot_channels(raw_rsk_df, "1_pre", figure_dir)
    plot_pressure_diff(raw_rsk_df, "pre", figure_dir)

    rsk = derive_values(rsk)
    rsk = trim_profile(rsk)
    plot_channels(pd.DataFrame(rsk.data), "2_post_trim", figure_dir)

    rsk = correct_spikes_and_zoh(rsk)
    plot_channels(pd.DataFrame(rsk.data), "3_post_despiking", figure_dir)

    rsk_to_csv(rsk, rsk_file_name.replace(".rsk", "_processed.csv"))

    downcast, upcast = separate_casts(rsk) ## can also return the whole profile as df from this function if needed :p
    downcast.to_csv(os.path.join(dest_dir,'downcast.csv'), index=False)
    upcast.to_csv(os.path.join(dest_dir, 'upcast.csv'), index=False)

    downcast, upcast = low_pass_filter(downcast, upcast)
    plot_channels(downcast, '4_post_filter_downcast', figure_dir) ## can get rid of this after

    downcast = descent_rate_filter(downcast, 'down')
    upcast = descent_rate_filter(upcast, 'up')
    plot_channels(downcast, '5_post_delete_downcast', figure_dir)

    # correct for atmospheric pressure
    # low-pass filtering (which channel?)
    # descent rate filtering
    # derive depth again?
    # plots
    # binning
    # binned plots
    # output




process_rsk()