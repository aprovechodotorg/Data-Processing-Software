
import os.path
from datetime import datetime as dt
from datetime import timedelta
import easygui
import matplotlib.pyplot as plt
import LEMS_DataProcessing_IO as io
import matplotlib
from uncertainties import ufloat

inputpath = "Z:\\Jaden\\3.25.25\\3.25.25_TimeSeriesMetrics"
pemsinputpath = "Z:\\Jaden\\3.25.25\\3.25.25_TimeSeries_test.csv"
scaleinputpath = "Z:\\Jaden\\3.25.25\\3.25.25_FormattedScaleData.csv"
intscaleinputpath = "Z:\\Jaden\\3.25.25\\3.25.25_FormattedIntScaleData.csv"
energyinputpath = "Z:\\Jaden\\3.25.25\\3.25.25_EnergyOutputs.csv"
cuttimepath = "Z:\\Jaden\\3.25.25\\3.25.25_ThermalEfficiencyCutTimes"
fuelcutpic = "Z:\\Jaden\\3.25.25\\3.25.25_ThermalEfficiencyCut"
outputtimepath = "Z:\\Jaden\\3.25.25\\3.25.25_TimeSeriesCanThermalEfficiency"
outputpath = "Z:\\Jaden\\3.25.25\\3.25.25_CanThermalEfficiency.csv"
logpath = "Z:\\Jaden\\3.25.25\\3.25.25_log.txt"

def LEMS_CANThermalEfficiency(inputpath, pemsinputpath, scaleinputpath, intscaleinputpath, energyinputpath,
                              cuttimepath, fuelcutpic, outputtimepath, outputpath, logpath):

    ver = '0.0'
    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'PEMS_CANThermalEfficiency v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    Tstd = float(293)  # define standard temperature in Kelvin
    Pstd = float(101325)  # define standard pressure in Pascals
    Cp = ufloat(1,
                0.1)  # J/g/K  heat capacity of flue gas. good enough for now. update as a function of flue gas composition and temperature
    R = float(8.314)  # universal gas constant (m^3Pa/mol/K)

    MW = {}
    MW['C'] = float(12.01)  # molecular weight of carbon (g/mol)
    MW['CO'] = float(28.01)  # molecular weight of carbon monoxide (g/mol)
    MW['COhi'] = float(28.01)  # molecular weight of carbon monoxide (g/mol)
    MW['CO2'] = float(44.01)  # molecular weight of carbon dioxide (g/mol)
    MW['CO2hi'] = float(44.01)  # molecular weight of carbon dioxide (g/mol)
    MW['SO2'] = float(64.07)  # molecular weight of sulfur dioxide (g/mol)
    MW['NO'] = float(30.01)  # molecular weight of nitrogen monoxide (g/mol)
    MW['NO2'] = float(46.01)  # molecular weight of nitrogen dioxide (g/mol)
    MW['H2S'] = float(34.1)  # molecular weight of hydrogen sulfide (g/mol)
    MW['HxCy'] = float(56.11)  # molecular weight of isobutylene (g/mol)
    MW['HC'] = float(56.11)  # molecular weight of isobutylene (g/mol)
    MW['VOC'] = float(56.11)  # molecular weight of isobutylene (g/mol)
    MW['CH4'] = float(16.04)  # molecular weight of methane (g/mol)
    MW['air'] = float(29)  # molecular weight of air (g/mol)
    MW['O2'] = float(32)  # molecular weight of oxygen (g/mol)
    MW['N2'] = float(28.01)  # molecular weight of nitrogen (g/mol)
    MW['H2O'] = float(18.02)  # molecular weight of water (g/mol)

    # Default Fuel Values
    # Dug Fir (To use, comment out oak values and uncomment doug fir values)
    HHV = 19810  # kJ/kg
    C = 48.73  # % Carbon
    H = 6.87  # % Hydrogen
    O = 43.9  # % Oxygen
    ash = 0.5  # % ash

    # Oak (To use, comment out dug fir values and uncomment oak values)
    # HHV = 19887  # kJ/kg
    # C = 50  # % Carbon
    # H = 6.6  # % Hydrogen
    # O = 42.9  # % Oxygen
    # ash = 0.5  # % ash

    # list of phases
    #phases = ['L1', 'hp', 'mp', 'lp', 'L5']
    phases = ['hp']

    ####################################################################
    # 13.7.2.1 WOOD-FUEL-BASED TESTS

    # read in energy metrics
    [enames, eunits, eval, eunc, edata] = io.load_constant_inputs(energyinputpath)
    line = 'Loaded energy output file:' + energyinputpath
    print(line)
    logs.append(line)

    for phase in phases:
        inputpath = f'{inputpath}_{phase}.csv'
        if os.path.isfile(inputpath):  # If the phase data exists
            names = []
            data = {}
            units = {}

            # load time series data from LEMS
            [lnames, lunits, ldata] = io.load_timeseries(inputpath)
            line = f'Loaded time series data from LEMS emission calculations: {inputpath}'
            print(line)
            logs.append(line)

            # load time series data from PEMS
            [pnames, punits, pdata] = io.load_timeseries(pemsinputpath)
            line = f'Loaded time series data from PEMS emission calculations: {inputpath}'
            print(line)
            logs.append(line)

            # load time series data file of scale (try both scale types)
            try:
                [snames, sunits, sdata] = io.load_timeseries(scaleinputpath)

                line = 'Loaded time series data from scale:' + scaleinputpath
                print(line)
                logs.append(line)
            except:
                [snames, sunits, sdata] = io.load_timeseries(intscaleinputpath)

                line = 'Loaded time series data from intelligent scale:' + intscaleinputpath
                print(line)
                logs.append(line)

            # time channel: convert date strings to date numbers
            ldata, lunits, lnames = Convert_Time(ldata, lunits, lnames)

            # record the phase start and end times
            start = ldata['datenumbers'][0]
            end = ldata['datenumbers'][-1]

            # scale time channel: convert date strings to date numbers
            sdata, sunits, snames = Convert_Time(sdata, sunits, snames)
            # cut to phase time
            full_sdata = Cut_Data(sdata, snames, start, end)

            # pems time channel: convert date strings to date numbers
            pdata, punits, pnames = Convert_Time(pdata, punits, pnames)
            # cut to phase time
            full_pdata = Cut_Data(pdata, pnames, start, end)

            date, time = ldata['time'][0].split(" ")

            # Check if cut times have already been assigned
            cuttimepath = f'{cuttimepath}_{phase}.csv'
            if os.path.isfile(cuttimepath):
                line = f'Cut times for thermal efficiency already exists at: {cuttimepath}. \n' \
                       f'Cut times loaded from current file.'
                print(line)
                logs.append(line)
                [tnames, tunits, tval, tunc, tdata] = io.load_constant_inputs(cuttimepath)

            else:  # Create a new file with cut times
                tnames = []
                tunits = {}
                tval = {}
                tunc = {}
                tdata = {}

                name = 'start_time'
                tnames.append(name)
                tunits[name] = eunits[f'{name}_{phase}']
                tdata[name] = eval[f'{name}_{phase}']
                start = tdata[name]

                name = 'end_time'
                tnames.append(name)
                tunits[name] = eunits[f'{name}_{phase}']
                tdata[name] = eval[f'{name}_{phase}']
                end = tdata[name]

                # Write file
                io.write_constant_outputs(cuttimepath, tnames, tunits, tval, tunc, tdata)
                line = f'Created cut times file for thermal efficiency: {cuttimepath}'
                print(line)
                logs.append(line)

            try:
                start_split = tdata['start_time'].split(" ")
                tdata['start_time'] = f"{date} {start_split[-1]}"
            except:
                tdata['start_time'] = f"{date} {tdata['start_time']}"
            try:
                end_split = tdata['end_time'].split(" ")
                tdata['end_time'] = f"{date} {end_split[-1]}"
            except:
                tdata['end_time'] = f"{date} {tdata['end_time']}"

            # convert times to datenumbers
            tdata, tunits, tnames = Convert_Time(tdata, tunits, tnames)

            start = tdata['datenumbers'][0]
            end = tdata['datenumbers'][1]

            # cut data to cut time
            cut_ldata = Cut_Data(ldata, lnames, start, end)
            cut_sdata = Cut_Data(sdata, snames, start, end)
            cut_pdata = Cut_Data(pdata, pnames, start, end)

            #################################################
            # plot with cut times and ask for update on times
            plt.ion()

            lw = float(5)  # define the linewidth for the data series
            plw = float(2)  # define the linewidth for the bkg and sample period marker
            msize = 30  # marker size for start and end pints of each period

            fig, ax = plt.subplots()

            # Plot CO2
            scale_CO2 = []
            for val in ldata['CO2']:
                scale_CO2.append(val * 0.01)

            cut_scale_CO2 = []
            for val in cut_ldata['CO2']:
                cut_scale_CO2.append(val * 0.01)

            ax.plot(ldata['datenumbers'], scale_CO2, color='turquoise', label='Full Phase CO2')
            ax.plot(cut_ldata['datenumbers'], cut_scale_CO2, color='blue', label='Cut CO2')

            # Plot scale weight
            ax.plot(full_sdata['datenumbers'], full_sdata['weight'], color='pink', label='Full Phase Weight')
            ax.plot(cut_sdata['datenumbers'], cut_sdata['weight'], color='red', label='Cut Weight')

            ax.legend()
            ax.set(ylabel='ppm, lbs', title='Please Confirm that the cut time period is correct, the scale weight'
                                            'should decrease over time. Anomolies may need to be fixed in the raw'
                                            'data.')

            # Format x axis to readable times
            xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')  # pull and format time data
            ax.xaxis.set_major_formatter(xfmt)
            for tick in ax.get_xticklabels():
                tick.set_rotation(30)

            ################################################################
            # Replot for new inputs
            running = 'fun'
            while running == 'fun':
                # GUI box to edit input times
                zeroline = 'Edit period for best weight\n'
                firstline = 'Click OK to update plot\n'
                secondline = 'Click Cancel to exit\n'
                msg = zeroline + firstline + secondline
                title = "Edit Phase Time"

                tnames = ['start_time', 'end_time']
                fieldnames = tnames
                currentvals = []

                for name in fieldnames:
                    currentvals.append(tdata[name])

                newvals = easygui.multenterbox(msg, title, fieldnames, currentvals)  # ask for and save new vals

                if newvals:
                    if newvals != currentvals:  # reassign user input to current vals
                        currentvals = newvals
                        tdata['start_time'] = currentvals[0]
                        tdata['end_time'] = currentvals[1]

                        # Record new values in the cut times files
                        io.write_constant_outputs(cuttimepath, tnames, tunits, tdata, tunc, tdata)
                        line = f'Updated the cut times: {cuttimepath}'
                        print(line)
                        logs.append(line)
                else:
                    running = 'not fun'
                    savefigpath = f'{fuelcutpic}_{phase}.png'
                    plt.savefig(savefigpath)
                    plt.close()
                    plt.ioff()

                #######################################################
                # Re-run cuts

                # convert times to datenumbers
                tdata, tunits, tnames = Convert_Time(tdata, tunits, tnames)

                start = tdata['datenumbers'][0]
                end = tdata['datenumbers'][1]

                # cut data to cut time
                cut_ldata = Cut_Data(ldata, lnames, start, end)
                cut_sdata = Cut_Data(sdata, snames, start, end)
                cut_pdata = Cut_Data(pdata, pnames, start, end)

                ax.cla()

                # Plot CO2
                cut_scale_CO2 = []
                for val in cut_ldata['CO2']:
                    cut_scale_CO2.append(val * 0.01)

                ax.plot(ldata['datenumbers'], scale_CO2, color='turquoise', label='Full Phase CO2')
                ax.plot(cut_ldata['datenumbers'], cut_scale_CO2, color='blue', label='Cut CO2')

                # Plot scale weight
                ax.plot(full_sdata['datenumbers'], full_sdata['weight'], color='pink', label='Full Phase Weight')
                ax.plot(cut_sdata['datenumbers'], cut_sdata['weight'], color='red', label='Cut Weight')

                ax.legend()
                ax.set(ylabel='ppm, lbs', title='Please Confirm that the cut time period is correct, the scale weight'
                                                'should decrease over time. Anomolies may need to be fixed in the raw'
                                                'data.')

                # Format x axis to readable times
                xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')  # pull and format time data
                ax.xaxis.set_major_formatter(xfmt)
                for tick in ax.get_xticklabels():
                    tick.set_rotation(30)

            #################################################################
            # Set up data for calculations
            name = 'time'
            names.append(name)
            units[name] = tunits['start_time']
            data[name] = []
            name = 'seconds'
            names.append(name)
            units[name] = 's'
            data[name] = []
            for n, val in enumerate(cut_ldata['time']):
                data['time'].append(val)
                data['seconds'].append(cut_ldata['seconds'][n])

            # Cut scale data to the same 1 second sample period as the LEMS
            filtered_sdata = {'time': []}
            for key in cut_sdata:
                if key != 'time':
                    filtered_sdata[key] = []

            # determine scale sample rate
            start_idx = cut_sdata['dateobjects'][0]
            end_idx = start_idx + timedelta(seconds=1)

            samples_in_sec = sum(1 for t in sdata['dateobjects'] if start_idx <= t < end_idx)
            sample_rate = max(samples_in_sec-1, 1)  # must be at least 1

            filtered_sdata = {'time': []}
            for key in cut_sdata:
                if key != 'time':
                    filtered_sdata[key] = []

            # Select every nth sample based on detected sample rate
            for i in range(0, len(cut_sdata['dateobjects']), sample_rate):
                filtered_sdata['time'].append(cut_sdata['time'][i])  # Keep original string format
                for key in cut_sdata:
                    if key != 'time':
                        filtered_sdata[key].append(cut_sdata[key][i])

            # ensure same length of data
            target_length = min(len(filtered_sdata['time']), len(cut_ldata['time']))

            for key in filtered_sdata:
                filtered_sdata[key] = filtered_sdata[key][:target_length]

            for key in cut_ldata:
                cut_ldata[key] = cut_ldata[key][:target_length]

            '''
            # Start from first ldata timestamp and increment by 1 second
            start_time = cut_ldata['dateobjects'][0]
            current_time = start_time

            for _ in range(len(cut_ldata['dateobjects'])):  # Loop for the number of seconds in ldata
                # Find the closest matching timestamp in data (exact second match)
                for i, t in enumerate(cut_sdata['dateobjects']):
                    if t.replace(microsecond=0) == current_time:  # Check if matches second
                        filtered_sdata['time'].append(sdata['time'][i])  # Keep original string format
                        for key in sdata:
                            if key != 'time':
                                filtered_sdata[key].append(sdata[key][i])
                        break  # Stop after finding the first match for that second

                current_time += timedelta(seconds=1)  # Move to next second
            '''

            cut_sdata = filtered_sdata

            name = 'remaining_weight'
            names.append(name)
            units[name] = 'kg'
            data[name] = []
            for val in cut_sdata['weight']:
                data[name].append(val / 2.205)  # Convert lbs to kg

            name = 'CO'
            names.append(name)
            units[name] = 'ppm'
            data[name] = []
            for val in cut_pdata['COhi']:
                data[name].append(val)

            name = 'CO2'
            names.append(name)
            units[name] = 'ppm'
            data[name] = []
            for val in cut_pdata['CO2hi']:
                data[name].append(val)

            name = 'per_CO'
            names.append(name)
            units[name] = '%'
            data[name] = []
            for val in cut_pdata['COhi']:
                data[name].append((val / 1000000) * 100)  # Convert ppm to %

            name = 'per_CO2'
            names.append(name)
            units[name] = '%'
            data[name] = []
            for val in cut_pdata['CO2hi']:
                data[name].append((val / 1000000) * 100)  # Convert ppm to %

            name = 'flue_gas'
            names.append(name)
            units[name] = 'K'
            data[name] = []
            for val in cut_ldata['TC2']:
                data[name].append(val + 273.15)  # convert C to K

            name = 'amb_temp'
            names.append(name)
            units[name] = 'K'
            data[name] = []
            for val in cut_ldata['H2Otemp']:
                data[name].append(val + 273.15)  # convert C to K

            #######################################################################
            # Begin Calculations
            # 13.7.2.1
            # a
            # initial dry weight = initial weight * [1 - (0.01 * initial moisture content)]
            initial_dry_weight = data['remaining_weight'][0] * (1 - (0.01 * float(eval['fuel_mc_1'])))

            # b
            # current dry weight = current weight * [1 - (0.01 * initial moisture content)]
            name = 'dry_weight'
            names.append(name)
            units[name] = 'kg'
            data[name] = []
            for val in data['remaining_weight']:
                data[name].append(val * (1 - (0.01 * float(eval['fuel_mc_1']))))

            # c
            # current mc (wet basis) = initial moisture content * R
            # in the spreadsheet R is 0.55556 but there is no explanation as to why
            name = 'current_mc_wb'
            names.append(name)
            units[name] = '%'
            data[name] = []
            for val in data['remaining_weight']:
                data[name].append(float(eval['fuel_mc_1']) * 0.55556)

            # d
            # current mc (dry basis) = 100 * [current mc (wet basis) / (100 - current mc (wet basis)
            name = 'current_mc_db'
            names.append(name)
            units[name] = '%'
            data[name] = []
            for val in data['current_mc_wb']:
                data[name].append(100 * (val / (100 - val)))

            # 13.7.3.2
            # a
            # ultimate CO2 = (fraction C atoms/
            # (fraction C atoms+3.77 * ((2*fraction C atoms+fraction H atoms/2-fraction O atoms)/2)))*100

            # 13.7.4 (
            frac_C = C / 12
            frac_H = H / 1
            frac_O = O / 16
            ult_CO2 = (frac_C / (frac_C + 3.77 * ((2 * frac_C + frac_H / 2 - frac_O) / 2))) * 100
            # )

            # b
            # Excess Air = ultimate CO2 / (CO2 concentration + CO concentration)
            name = 'EA'
            names.append(name)
            units[name] = '%'
            data[name] = []
            for n, val in enumerate(data['per_CO']):
                data[name].append((ult_CO2 / (val + data['per_CO2'][n]))-1)

            # c
            # Total oxygen = [ultimate CO2 + (excess air - 1) * 20.94] / excess air
            name = 'total_O2'
            names.append(name)
            units[name] = ''
            data[name] = []
            for val in data['EA']:
                data[name].append((ult_CO2 + (val) * 20.94) / (val + 1))

            # d
            # Oxygen concentration = total oxygen - moles CO2 per 100 moles dry flue gas +
            # moles CO per 100 moles dry flue gas / 2)
            # Or (total O - percent CO - percent CO2) / 2 in the spreadsheet

            name = 'mols_CO2'
            names.append(name)
            units[name] = 'moles'
            data[name] = []
            for val in data['per_CO2']:
                data[name].append((val / 100) * 100)  # will be the same as concentration

            name = 'mols_CO'
            names.append(name)
            units[name] = 'moles'
            data[name] = []
            for val in data['per_CO']:
                data[name].append((val / 100) * 100)  # will be the same as concentration

            name = 'O_conc'
            names.append(name)
            units[name] = 'g'
            data[name] = []
            for n, val in enumerate(data['total_O2']):
                data[name].append(val - (data['mols_CO2'][n] + (data['mols_CO'][n] / 2)))

            # 13.7.5
            # moles of N2 per 100 moles of dry flue gas =
            # 100 - moles CO2 per 100 moles gas - moles CO per 100 moles gas - moles O2 per 100 moles gas
            name = 'mols_N2'
            names.append(name)
            units[name] = 'moles'
            data[name] = []
            for n, val in enumerate(data['mols_CO']):
                data[name].append(100 - val - data['mols_CO2'][n] - data['O_conc'][n])

            # moles of oxygen entering per 100 moles of dry flue gas =
            # moles of N2 per 100 moles gas / 3.77
            name = 'mols_O2_enter'
            names.append(name)
            units[name] = 'moles'
            data[name] = []
            for val in data['mols_N2']:
                data[name].append(val / 3.77)

            # moles of dry fuel per 100 moles of dry flue gas =
            # (8 * moles of CO2 per 100 moles gas + 4 * moles of O2 per 100 moles gas +
            # 6 * moles of CO per 100 moles gas - 4 * moles of O2 entering per 100 moles gas) /
            # (4 * fraction of C in fuel - fraction of H in fuel + 2 * fraction of O in fuel)
            name = 'mols_dry_fuel'
            names.append(name)
            units[name] = 'moles'
            data[name] = []
            for n, val in enumerate(data['mols_CO2']):
                data[name].append((8 * val + 4 * data['O_conc'][n] + 6 * data['mols_CO'][n] - 4 * data['mols_O2_enter'][n]) /
                                  (4 * frac_C - frac_H + 2 * frac_O))

            # moles of CH4 per 100 moles of dry flue gas = moles of dry fuel per 100 moles gas * fraction of C in fuel
            # - moles of CO2 per 100 moles gas - moles of CO per 100 moles gas
            name = 'mols_CH4'
            names.append(name)
            units[name] = 'moles'
            data[name] = []
            for n, val in enumerate(data['mols_dry_fuel']):
                data[name].append(val * frac_C - data['mols_CO2'][n] - data['mols_CO'][n])

            # moles of H2O per 100 moles of dry flue gas = (fraction of H in fuel * moles of dry flue per 100 moles gas
            # - 4 * moles of CH4 per 100 moles gas) / 2
            name = 'mols_H2O'
            names.append(name)
            units[name] = 'moles'
            data[name] = []
            for n, val in enumerate(data['mols_dry_fuel']):
                data[name].append((frac_H * val - 4 * data['mols_CH4'][n]) / 2)

            # 13.7.7
            # a
            # chemical loss rate = molar flow rate of CO * 282993 + molar flow rate of CH4 * 890156
            name = 'kg_fuel'
            names.append(name)
            units[name] = 'kg'
            data[name] = []
            for val in data['mols_dry_fuel']:
                data[name].append(0.001 * val * (12 * frac_C * frac_H * 16 * frac_O))

            name = 'CH4_flow'
            names.append(name)
            units[name] = 'moles/kg'
            data[name] = []
            for n, val in enumerate(data['mols_CH4']):
                data[name].append(val / data['kg_fuel'][n])

            name = 'CO_flow'
            names.append(name)
            units[name] = 'moles/kg'
            data[name] = []
            for n, val in enumerate(data['mols_CO']):
                data[name].append(val / (0.001 * data['mols_dry_fuel'][n] * (12 * frac_C + frac_H + 16 * frac_O)))

            '''
            name = 'chem_loss'
            names.append(name)
            units[name] = 'joules/mole'
            data[name] = []
            for n, val in enumerate(data['CO_flow']):
                data[name].append(val * 282993 + data['CH4_flow'][n] * 890156)
            '''
            # sensible and latent loss rate = sum of all species (molar flow rate *
            # (((specific heat at vent temperature + specific heat at room temperature) / 2) * (vent temperature -
            # ambient temperature)) + molar flow rate of water vapor * 43969)
            name = 'CO2_flow'
            names.append(name)
            units[name] = 'moles/kg'
            data[name] = []
            for n, val in enumerate(data['mols_CO2']):
                data[name].append(val / (0.001 * data['mols_dry_fuel'][n] * (12 * frac_C + frac_H + 16 * frac_O)))

            name = 'O2_flow'
            names.append(name)
            units[name] = 'moles/kg'
            data[name] = []
            for n, val in enumerate(data['O_conc']):
                data[name].append(val / (0.001 * data['mols_dry_fuel'][n] * (12 * frac_C + frac_H + 16 * frac_O)))

            name = 'N2_flow'
            names.append(name)
            units[name] = 'moles/kg'
            data[name] = []
            for n, val in enumerate(data['mols_N2']):
                data[name].append(val / data['kg_fuel'][n])

            name = 'H2O_flow'
            names.append(name)
            units[name] = 'moles/kg'
            data[name] = []
            for n, val in enumerate(data['mols_H2O']):
                data[name].append(val / data['kg_fuel'][n])

            '''
            name = 'SH_CO_ambient'
            names.append(name)
            units[name] = 'joules/mole * K'
            for val in data['amb_temp']:
                data[name].append(0.0056 * val + 27.162)

            name = 'SH_CO2_ambient'
            names.append(name)
            units[name] = 'joules/mole * K'
            for val in data['amb_temp']:
                data[name].append(0.029 * val + 29.54)

            name = 'SH_H2O_ambient'
            names.append(name)
            units[name] = 'joules/mole * K'
            for val in data['amb_temp']:
                data[name].append(0.0057 * val + 32.859)

            name = 'SH_O2_ambient'
            names.append(name)
            units[name] = 'joules/mole * K'
            for val in data['amb_temp']:
                data[name].append(0.009 * val + 26.782)

            name = 'SH_N2_ambient'
            names.append(name)
            units[name] = 'joules/mole * K'
            for val in data['amb_temp']:
                data[name].append(0.0062 * val + 26.626)

            name = 'SH_CH4_ambient'
            names.append(name)
            units[name] = 'joules/mole * K'
            for val in data['amb_temp']:
                data[name].append(0.056 * val + 18.471)

            name = 'SH_CO_vent'
            names.append(name)
            units[name] = 'joules/mole * K'
            for val in data['flue_gas']:
                data[name].append(0.0056 * val + 27.162)

            name = 'SH_CO2_vent'
            names.append(name)
            units[name] = 'joules/mole * K'
            for val in data['flue_gas']:
                data[name].append(0.029 * val + 29.54)

            name = 'SH_H2O_vent'
            names.append(name)
            units[name] = 'joules/mole * K'
            for val in data['flue_gas']:
                data[name].append(0.0057 * val + 32.859)

            name = 'SH_O2_vent'
            names.append(name)
            units[name] = 'joules/mole * K'
            for val in data['flue_gas']:
                data[name].append(0.009 * val + 26.782)

            name = 'SH_N2_vent'
            names.append(name)
            units[name] = 'joules/mole * K'
            for val in data['flue_gas']:
                data[name].append(0.0062 * val + 26.626)

            name = 'SH_CH4_vent'
            names.append(name)
            units[name] = 'joules/mole * K'
            for val in data['flue_gas']:
                data[name].append(0.056 * val + 18.471)

            species = ['CO', 'CO2', 'H2O', 'O2', 'N2', 'CH4']

            name = 'sensible_latent_loss'
            names.append(name)
            units[name] = 'joules/moles'
            data[name] = ''
            for n, val in enumerate(data['H2O_flow']):
                loss = 0
                for em in species:
                    loss = loss + data[f'{em}_flow'][n] * (((data[f'SH_{em}_vent'][n] - data[f'SH_{em}_ambient'][n])/2)
                                                         * (data['flue_gas'][n] - data['amb_temp'][n])) + val * 43969
                data[name].append(loss)
            '''

            name = 'amb_stack_heat_content_change_CO2'
            names.append(name)
            units[name] = '?'
            data[name] = []
            for n, val in enumerate(data['flue_gas']):
                data[name].append((val - data['amb_temp'][n]) * (0.029 * ((val + data['amb_temp'][n]) / 2) + 29.54))

            name = 'amb_stack_heat_content_change_CO'
            names.append(name)
            units[name] = '?'
            data[name] = []
            for n, val in enumerate(data['flue_gas']):
                data[name].append((val - data['amb_temp'][n]) * (0.0056 * ((val + data['amb_temp'][n]) / 2) + 27.162))

            name = 'amb_stack_heat_content_change_H2O'
            names.append(name)
            units[name] = '?'
            data[name] = []
            for n, val in enumerate(data['flue_gas']):
                data[name].append((val - data['amb_temp'][n]) * (0.0057 * ((val + data['amb_temp'][n]) / 2) + 32.859))

            name = 'amb_stack_heat_content_change_O2'
            names.append(name)
            units[name] = '?'
            data[name] = []
            for n, val in enumerate(data['flue_gas']):
                data[name].append((val - data['amb_temp'][n]) * (0.009 * ((val + data['amb_temp'][n]) / 2) + 26.782))

            name = 'amb_stack_heat_content_change_N2'
            names.append(name)
            units[name] = '?'
            data[name] = []
            for n, val in enumerate(data['flue_gas']):
                data[name].append((val - data['amb_temp'][n]) * (0.0062 * ((val + data['amb_temp'][n]) / 2) + 26.626))

            name = 'amb_stack_heat_content_change_CH4'
            names.append(name)
            units[name] = '?'
            data[name] = []
            for n, val in enumerate(data['flue_gas']):
                data[name].append((val - data['amb_temp'][n]) * (0.056 * ((val + data['amb_temp'][n]) / 2) + 18.471))

            name = 'energy_loss_CO2'
            names.append(name)
            units[name] = 'kJ/kg'
            data[name] = []
            for n, val in enumerate(data['amb_stack_heat_content_change_CO2']):
                data[name].append(0.001 * val * data['CO2_flow'][n])

            name = 'energy_loss_O2'
            names.append(name)
            units[name] = 'kJ/kg'
            data[name] = []
            for n, val in enumerate(data['amb_stack_heat_content_change_O2']):
                data[name].append(0.001 * val * data['O2_flow'][n])

            name = 'energy_loss_CO'
            names.append(name)
            units[name] = 'kJ/kg'
            data[name] = []
            for n, val in enumerate(data['amb_stack_heat_content_change_CO']):
                data[name].append(0.001 * val * data['CO_flow'][n])

            name = 'energy_loss_N2'
            names.append(name)
            units[name] = 'kJ/kg'
            data[name] = []
            for n, val in enumerate(data['amb_stack_heat_content_change_N2']):
                data[name].append(0.001 * val * data['N2_flow'][n])

            name = 'energy_loss_CH4'
            names.append(name)
            units[name] = 'kJ/kg'
            data[name] = []
            for n, val in enumerate(data['amb_stack_heat_content_change_CH4']):
                data[name].append(0.001 * (val + 890156) * data['CH4_flow'][n])

            name = 'energy_loss_H2O'
            names.append(name)
            units[name] = 'kJ/kg'
            data[name] = []
            for n, val in enumerate(data['amb_stack_heat_content_change_H2O']):
                data[name].append(0.001 * (val + 43969) * data['H2O_flow'][n])

            name = 'energy_loss_H2O_vapor'
            names.append(name)
            units[name] = 'kJ/kg'
            data[name] = []
            for n, val in enumerate(data['amb_stack_heat_content_change_H2O']):
                data[name].append(0.001 * (val + 43969) * data['current_mc_db'][n])

            species = ['CO2', 'CO', 'O2', 'N2', 'CH4', 'H2O', 'H2O_vapor']  # list of species to loop through

            name = 'total_loss_rate'
            names.append(name)
            units[name] = 'kJ/kg'
            data[name] = []
            for n, val in enumerate(data['energy_loss_CO2']):
                loss = 0
                for em in species:
                    loss = loss + data[f'energy_loss_{em}'][n]
                data[name].append(loss)

            name = 'total_loss'
            names.append(name)
            units[name] = 'kJ'
            data[name] = []
            for n, val in enumerate(data['total_loss_rate']):
                data[name].append((initial_dry_weight - data['dry_weight'][n]) * val)

            name = 'grams_produced_CO'
            names.append(name)
            units[name] = 'g'
            data[name] = []
            for n, val in enumerate(data['CO_flow']):
                data[name].append((initial_dry_weight - data['dry_weight'][n]) * 28 * val)

            name = 'grams_produced_CH4'
            names.append(name)
            units[name] = 'g'
            data[name] = []
            for n, val in enumerate(data['CH4_flow']):
                data[name].append((initial_dry_weight - data['dry_weight'][n]) * 16 * val)

            name = 'chemical_loss_1'
            names.append(name)
            units[name] = 'kJ'
            data[name] = []
            for n, val in enumerate(data['grams_produced_CH4']):
                data[name].append(val * 55.6344 + data['grams_produced_CO'][n] * 10.1069)

            name = 'sensible and latent loss'
            names.append(name)
            units[name] = 'kJ'
            data[name] = []
            for n, val in enumerate(data['total_loss']):
                data[name].append(val - data['chemical_loss_1'][n])

            name = 'total_input'
            names.append(name)
            units[name] = 'kg * kJ'
            data[name] = []
            for n, val in enumerate(data['dry_weight']):
                data[name].append((initial_dry_weight - val) * HHV)

            name = 'total_output'
            names.append(name)
            units[name] = 'kg * kJ'
            data[name] = []
            for n, val in enumerate(data['total_input']):
                data[name].append(val - data['total_loss'][n])

            name = 'chemical_loss_2'
            names.append(name)
            units[name] = 'kJ'
            data[name] = []
            for n, val in enumerate(data['dry_weight']):
                data[name].append((initial_dry_weight - val) * (0.001 * data['CO_flow'][n] * 282993 + 0.001 *
                                                                data['CH4_flow'][n] * 890156))

            name = 'combustion_eff'
            names.append(name)
            units[name] = '%'
            data[name] = []
            for n, val in enumerate(data['CO_flow']):
                data[name].append((HHV - (data['CO_flow'][n] * 282.993 + data['CH4_flow'][n] * 890.156)) / HHV)

            name = 'heat_transfer'
            names.append(name)
            units[name] = '%'
            data[name] = []
            for n, val in enumerate(data['total_loss_rate']):
                data[name].append(((HHV - val ) / HHV) / data['combustion_eff'][n])

            name = 'net_eff'
            names.append(name)
            units[name] = '%'
            data[name] = []
            for n, val in enumerate(data['combustion_eff']):
                data[name].append(val * data['heat_transfer'][n])

            outputtimepath = f'{outputtimepath}_{phase}.csv'
            io.write_timeseries(outputtimepath, names, units, data)
            line = f'Created: {outputtimepath}'
            print(line)
            logs.append(line)

        inputpath = inputpath[:-7]
        cuttimepath = cuttimepath[:-7]
        fuelcutpic = fuelcutpic[:-7]
        outputtimepath = outputtimepath[:-7]
    # print to log file
    io.write_logfile(logpath, logs)

def Convert_Time(data, units, names):
    # time channel: convert date strings to date numbers
    name = 'dateobjects'
    names.append(name)
    units[name] = 'date'
    data[name] = []
    try:
        for n, val in enumerate(data['time']):
            dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')  # Convert time to readable datetime object
            data[name].append(dateobject)
    except:
        try:
            for n, val in enumerate(data['time']):
                dateobject = dt.strptime(val, '%Y-%m-%d %H:%M:%S')  # Convert time to readable datetime object
                data[name].append(dateobject)
        except:
            for key in data:
                if 'time' in key:
                    dateobject = dt.strptime(data[key], '%Y%m%d %H:%M:%S')  # Convert time to readable datetime object
                    data[name].append(dateobject)

    name = 'datenumbers'
    names.append(name)
    units[name] = 'date'
    datenums = matplotlib.dates.date2num(data['dateobjects'])
    datenums = list(datenums)  # convert ndarray to a list in order to use index function
    data[name] = datenums

    return data, units, names

def Cut_Data(data, names, start, end):
    cutdata = {}
    # cut scale data to phase time
    for name in names:
        cutdata[name] = []
        for x, date in enumerate(data['datenumbers']):
            if start <= date <= end:
                cutdata[name].append(data[name][x])

    return cutdata

#######################################################################
#run function as executable if not called by another function
if __name__ == "__main__":
    LEMS_CANThermalEfficiency(inputpath, pemsinputpath, scaleinputpath, intscaleinputpath, energyinputpath,
                              cuttimepath, fuelcutpic, outputtimepath, outputpath, logpath)
