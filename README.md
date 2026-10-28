## PAR_fluo_script-main
A python script for processing raw RBR Concerto/Brevio Fluo-PAR duo sensor data.

Based on code in the following repos:

https://github.com/guanlu129/RBR_CTD_Processing

https://github.com/IOS-OSD-DPG/RBR-CTD-Processing

processes a single .rsk file containing a single profile.

### Dependencies & Versions
Python version: 3.13

### Data Processing Steps
- derive sea pressure, depth, and velocity
- remove soak period and trim cast
- correct zero order holds
- despike PAR and chlorophyll a channels
- remove par and chlorophyll a values below detection limits
- low pass filter (butterworth or moving average)
- descent rate filter/delete pressure reversals
- bin data by depth

### Running Instructions
*if running in terminal:*
```py PAR_fluo_processing.py```or ```python3 PAR_fluo_processing.py```

Recommended: Run the program in PyCharm IDE (available on the DFO network)

#### User-defined Variables
Before running the program, you must read through and change the user-defined variables in the code based on your data and processing requirements.

Navigate to line 31, where you will see the following comment:

```# USER-DEFINED VARIABLES -- FILL THESE IN BEFORE RUNNING```

This marks the start of the user-defined variables, and you should read through and change values as needed up until you see the following line:

```#END OF USER-DEFINED VARIABLES```

Below you will find brief explanations for some of the variables.

**dest_dir**: File path to your working folder. This value indicates where to find the input files and where to put output files. This
must be the same folder that contains your .rsk file. It should look something like the following:
```
dest_dir = "C:\\Users\\COLESS\\Documents\\Python_CTDscript\\PAR_fluo_script-main\\station1"
```
**rsk_file**: the name of your rsk file.
```
rsk_file = "St1.rsk"
```
**spk_window**: total size of the filter window for despiking. Must be odd.

**spk_std**: amount of standard deviations to use for the spike criterion.

**filter_type**: must be a value of either 'butterworth' or 'fir'. indicates what type
of filter should be used for low pass filtering.

**fluo_detection_threshold**: detection threshold value for the chlorophyll a channel.
chlorophyll a values below this threshold are set to 0.

**par_detection_threshold**: detection threshold value for the par channel.
par values below this value are set to 0.

**bin_interval**: depth intervals by which the data should be binned. Can be ignored if you
entered 'False' for bin_data. Value is in meters.

**plotting_depth_limit**: depth limit in meters for pre vs. post processing plots. 
Figures will be created that plot the data before and after processing, but only up to this user-defined
depth. Plot will then be titled with this depth limit, e.g. Pre_VS_Post_Processing_C_to_15m.png.

Most importantly, **make sure dest_dir and rsk_file_name contain the correct values**
for your data/files.

While running, view the output in the terminal to see what's currently happening. 

#### User Input
At certain points you will be prompted to answer questions. The program will halt 
until you enter a valid answer.

You will be prompted for the following information:
- if you want to choose your own custom trim depth for the beginning of the downcast data
  - enter either 'yes' or 'no'
  - if you answer 'yes', you will then be prompted for the depth to trim to
    - if you answered 'yes', the beginning of your downcast data will be trimmed up to your
    custom depth, and then the regular soak removal and trim functions will still
    be applied
  - if you answer 'no', the regular soak removal and trim functions will be applied
- if you would like to correct zero order holds (enter either true or false)
- if you would like to despike PAR (enter either true or false)
- if you would like to despike chlorophyll a (enter either true or false)


# Output
- **[rsk file name]_raw_data.csv**: contains the raw data from your provided .rsk file in csv format
- **metadata.xlsx**: contains metadata derived from your provided .rsk file
- **downcast_processed_binned.csv**: contains fully processed downcast data, binned to your specific interval
- **upcast_processed_binned.csv**: contains fully processed upcast data, binned to your specified interval
- **downcast_processed_unbinned.csv**: contains fully processed downcast data that has not been binned
- **upcast_processed_unbinned.csv**: contains fully processed upcast data that has not been binned

References: Halverson, M., Jackson, J., Richards, C., Melling, H., Brunsting, R., Dempsey, M., Ga- tien, G., Hamilton, A., Hunt, B., Jacob, W., and Zimmerman, S. 2017. Guidelines for processing RBR CTD profiles. Can. Tech. Rep. Hydrogr. Ocean Sci. 314: iv + 38 p.
