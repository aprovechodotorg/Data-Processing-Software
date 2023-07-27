# LEMS-Data-Processing
Description: 
Calculates ISO 19867-1 emissions and energy performance metrics 
Energy performance metrics are calculated from the test data sheet
Emissions performance metrics are calculated from the test data sheet and LEMS time series data file

Installation instructions:
NOTE: Installation instructions only need to be run the first time the code is used on a new machine.
1. check that python3 is installed
    Windows command prompt: py --version
2. check that python3 has been added to Path Environment variable so the python command is recognized in any directory

3. Install the required python modules:
        If pip needs upgrade:
        -Windows command prompt: py -m pip install --upgrade pip

        easygui
        -Download package: https://sourceforge.net/projects/easygui/files/0.97/
        -Windows command prompt: py -m pip install easygui

        uncertainties
        -Download package: https://pypi.org/project/uncertainties/#files
        -Windows command prompt: py -m pip install uncertainties

        openpyxl
        -Download package: https://pypi.org/project/openpyxl/#files
        -Windows command prompt: py -m pip install openpyxl

        xlrd
        -Download package: https://pypi.org/project/xlrd3/#files
        -Windows command prompt: py -m pip install xlrd

        matplotlib
        -Download package: https://pypi.org/project/matplotlib/#files
        -Windows command prompt: py -m pip install matplotlib

        numpy
        -Download package: https://pypi.org/project/numpy/#files
        -Windows command prompt: py -m pip install numpy


Usage instructions:
Before use, fill out testname_test#_TE_DataEntryForm.xlsx with required information. Save file to Z drive under
Python_Data/testname folder.
1. Open command line terminal and change directory to the LEMS-Data-Processing software folder
2. Run the master script by one of the following commands (python command depends on how python is setup on your system):
        py LEMSDataCruncher_ISO.py 
        python LEMSDataCruncher_ISO.py     
        python3 LEMSDataCruncher_ISO.py 
3. A file open box will pop open. Browse to select the desired test data sheet: testname_test#_TE_DataEntryForm.xlsx
4. Data processing steps are listed. Select menu item for each desired step:
        1. load data entry form
                Reads the test data sheet selected in the previous step (yatzo_test1_TE_DataEntryForm.xlsx)
                Outputs the list of all variables as a csv file: (yatzo_test1_EnergyInputs.csv)
                
        2. calculate energy metrics
                Reads energy metrics input file (yatzo_test1_EnergyInputs.csv)
                Calculates ISO 19867-1 energy performance metrics
                Outputs a list of all variables including reporting metrics and all input variables (yatzo_test1_EnergyOutputs.csv)
                
        3. adjust sensor calibrations
                Calibration parameters for each data channel are stored in the data acquisition system and printed in the header of the raw data file. 
                This script recalculates the data channels using updated calibration parameters that are defined in the header input file. 
                The header input file is just a copy of the header from the raw data file.
                
                Checks for header file and creates header file if it does not exist (yatzo_test1_Header.csv)
                Prompts user to edit to the calibration parameters in the header file
                Reads header file
                Reads raw data file (yatzo_test1_RawData.csv)
                Prompts user for the sensor box firmware version (Listed in startup diagnostics at the beginning of the raw data file: SB4003.16)
                Recalculates the raw data series using the calibration parameters in the header file
                Prints the names of data channels that were recalculated
                Plots the raw data series that changed
                Outputs new raw data file with the new recalculated data channels (yatzo_test1_RawData_Recalibrated.csv)
        
        4. correct for response times
                This script shifts selected time series data channels forward or backward along the time axis to correct for response time delays.
                Sensor response time is a function of the sensor detection principle, sample train flow and volume, and sensor location within the sample train.
                Once the timeshifts input file is determined for the sensor box, it should be consistent for every test.
        
                Reads raw data file (time series) from previous step  (yatzo_test1_RawData_Recalibrated.csv)
                Checks for timeshifts input file and creates it if does not exist (yatzo_test1_TimeShifts.csv)
                Prompts user to edit timeshifts input file (current issue: too many data channels for easygui)
                Outputs new raw data file with selected data channels shifted forward or backward (yatzo_test1_RawData_Shifted.csv)
                
        5. subtract background
                Reads raw data file (time series) from previous step  (yatzo_test1_RawData_Shifted.csv)
                Checks for phase times input file and creates it if does not exist
                Plots CO, CO2, and PM data series, both raw data and after background subtraction, with phase markers
                Prompts user to edit the start and end times
                Applies the background subtraction using the average of the pre and post background period values
                Prints report of phase averages before and after background subtraction
                Outputs full length background-subtracted time series data file, same length as raw data file (yatzo_test1_TimeSeries.csv)
                Outputs background-subtracted time series data file for each phase      (yatzo_test1_TimeSeries_phase.csv , phase=prebkg, hp, mp, lp, postbkg)
                Outputs a list of average values for each phase of each data channel    (yatzo_test1_Averages.csv)
        
        6. calculate gravimetric PM
                Reads filter weights from gravimetric input file (yatzo_test1_GravInputs.csv)
                    Note: User must manually create this file (copy, paste, and edit from another test)
                Calculates PM mass and concentration for each grav flow train during each test phase based on the variables defined in the grav input file
                Prints gravimetric variables for each phase
                Outputs a list of gravimetric PM metrics (yatzo_test1_GravOutputs.csv)
        
        7. calculate emission metrics
                Reads phase averages data file (yatzo_test1_Averages.csv)
                Reads energy performance metrics file (yatzo_test1_EnergyOutputs.csv)
                Reads gravimetric PM metrics file (yatzo_test1_GravOutputs.csv)
                Reads background-subtracted time series data file for each phase (yatzo_test1_TimeSeries_phase.csv , phase=hp, mp, lp)
                Calculates time series data for duct flow and emission rates
                Calculates ISO 19867-1 energy performance metrics
                Outputs time series data files for each phase with processed emissions added (yatzo_test1_TimeSeriesMetrics_phase.csv , phase=hp, mp, lp)
                Outputs a list of all emission performance variables, including inputs and reporting metrics (yatzo_test1_EmissionOutputs.csv)
                Outputs a list of all variables, including inputs, intermediate variables, and reporting metrics for emissions and energy performance (yatzo_test1_AllOutputs.csv)

###############################################
Do:

Improve instructions
Make specific install instructions for each operating system/virtual environment -Jaden
Finish plotting functions - Ryan
Check and remove unused libraries
Check all variable names, variable units, and variable values -Sam (Check variable names and units for consistency. If units change calc changes)
Add data range warnings (for quality control) - Some calcs have example calc currently - Warnings for missing values too
Add error handling as errors are discovered
Create time series of 1 minute averages and calculate emission metrics (for instantaneous emission factors) and time series statistics - Lower priority
make launcher for windows, mac, linux
Improve scripts (see do list at the beginning of each script)
Decide/standardize folder system, file naming system - make compatible with old data

Level 2 Data processing
    output for clean cooking catalog (write to: upload_template from christian.csv)
    output ISO reporting templates: VPT summary
    plots

Create database sync functions
	user login (define user name and server name)
		server name within arc network is stovesimulator
				outside of arc network arcfileshare.ddns.net
	read verified server data
		rsync -a user@server:/home/sam/python_data/ /home/user/python_data
	write unverified workstation data to workstation copy on server
		rysnc -a /home/user/python_data/ user@server:/home/user/python_data
	notify sam



###############################################
Resources:

Excel modules for python: https://www.python-excel.org/



        