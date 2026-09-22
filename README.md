## PAR_fluo_script-main
A python script for processing raw RBR Concerto/Brevio Fluo-PAR duo sensor data.


https://github.com/guanlu129/RBR_CTD_Processing/tree/master

https://github.com/IOS-OSD-DPG/RBR-CTD-Processing/blob/main/ios_rbr_processing/RBR_CTD_IOS.py

processes a single .rsk file containing a single profile.

### Running Instructions
prior to running, check the 'user-defined variables' section
at the top of the script. This can be found on line 31:

```
# USER-DEFINED VARIABLES -- FILL THESE IN BEFORE RUNNING
dest_dir = "C:\\Users\\COLESS\\Documents\\Python_CTDscript\\PAR_fluo_script-main\\station5"
rsk_file_name = "Eureka2024_PAR_Fluo_St5.rsk"
fill_action = 'interp' 
## despiking variables:
spk_std = 3
spk_window = 11
## clipping variables:
limit_pressure_change_down = 0.02
limit_pressure_change_up = -0.03
## low-pass filter variables:
filter_type = 'FIR' # can be one of two values: 'FIR' or 'moving average'
filter_window_width = 6
## bin average variables:
bin_interval_fluo = 1
bin_interval_par = 0.5
```
Make sure you check over all of these values to ensure the data is processed
correctly for your purposes.
Most importantly, **make sure dest_dir and rsk_file_name contain the correct values**
for your data/files.

References: Halverson, M., Jackson, J., Richards, C., Melling, H., Brunsting, R., Dempsey, M., Ga- tien, G., Hamilton, A., Hunt, B., Jacob, W., and Zimmerman, S. 2017. Guidelines for processing RBR CTD profiles. Can. Tech. Rep. Hydrogr. Ocean Sci. 314: iv + 38 p.
