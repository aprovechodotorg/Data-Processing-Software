#v0.2 Python3

#    Copyright (C) 2022 Aprovecho Research Center
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Contact: sam@aprovecho.org

import easygui
import pandas as pd
from easygui import *
import os
import csv
from LEMS_FormatData_L3 import LEMS_FormatData_L3
from LEMS_boxplots import LEMS_boxplots
from LEMS_barcharts import LEMS_barcharts
from LEMS_scatterplots import LEMS_scatterplots
from LEMS_multiscatterslopt import LEMS_multiscaterplots
from LEMS_multiboxplots import LEMS_multiboxplots
from LEMS_multibarcharts import LEMS_multibarcharts
from LEMS_subplotscatterplot import LEMS_subplotscatterplot
from LEMS_CSVFormatted_L3 import LEMS_CSVFormatted_L3
from LEMS_CustomFormatted_L3 import LEMS_CustomFormatted_L3
from LEMS_CustomFormatted_L3Pairs import LEMS_CustomFormatted_L3Pairs
from LEMS_FormatData_L3Pairs import LEMS_FormatData_L3Pairs
import traceback
import datetime
from concurrent.futures import ProcessPoolExecutor
import matplotlib
# --- Imports for L2 reprocessing steps 1-15 ---
from LEMS_MakeInputFile_EnergyCalcs import LEMS_MakeInputFile_EnergyCalcs
from LEMS_EnergyCalcs import LEMS_EnergyCalcs
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from LEMS_Combined_Scale import LEMS_Combined_Scale
from LEMS_ShiftTimeSeries import LEMS_ShiftTimeSeries
from LEMS_SubtractBkg import LEMS_SubtractBkg
from LEMS_GravCalcs import LEMS_GravCalcs
from LEMS_EmissionCalcs import LEMS_EmissionCalcs
from PEMS_SubtractBkg import PEMS_SubtractBkg
from PEMS_Plotter1 import PEMS_Plotter
from LEMS_Scale import LEMS_Scale
from LEMS_Int_Scale import LEMS_Int_Scale
from LEMS_FormattedL1 import LEMS_FormattedL1
from LEMS_CSVFormatted_L1 import LEMS_CSVFormatted_L1
from LEMS_Nanoscan import LEMS_Nanoscan
from LEMS_TEOM import LEMS_TEOM
from LEMS_Sensirion import LEMS_Senserion
from PEMS_PlotTimeSeries import PEMS_PlotTimeSeries
from PEMS_PlotTimeSeries import PEMS_PlotTimeSeries_Grid
from LEMS_Realtime import LEMS_Realtime
from LEMS_TEOM_SubtractBkg import LEMS_TEOM_SubtractBkg
from LEMS_OPS import LEMS_OPS
from LEMS_Pico import LEMS_Pico
from LEMS_CANThermalEfficiency import LEMS_CANThermalEfficiency
from LEMS_Adam_Scale import LEMS_Adam_Scale
# --- Imports for L2 comparison steps 16-19 and upload step ---
from PEMS_L2 import PEMS_L2
from LEMS_EnergyCalcs_L2 import LEMS_EnergyCalcs_L2
from LEMS_BasicOp_L2 import LEMS_BasicOP_L2
from LEMS_Emissions_L2 import LEMS_Emissions_L2
from LEMS_CSVFormatted_L2 import LEMS_CSVFormatted_L2
from UploadData import UploadData

#from LEMSDataCruncher_Energy import LEMSDataCruncher_Energy



# ==============================================================================
# Multi-Process Reprocessing Workers & Dispatch (Steps 1-15)
# ==============================================================================

def updatedonelist(donelist, var):
    index = int(var) - 1
    donelist[index] = '(done)'  # mark the completed step as 'done'
    for num, item in enumerate(donelist):  # mark the remaining steps as 'not done'
        if num < index:
            if item == '':
                donelist[num] = '(pass)'
        if num > index:
            donelist[num] = ''
    return donelist


def updatedonelisterror(donelist, var):
    index = int(var) - 1
    donelist[index] = '(error)'  # mark the completed step as 'error'
    for num, item in enumerate(donelist):  # mark the remaining steps as 'not done'
        if num < index:
            if item == '':
                donelist[num] = '(pass)'
        if num > index:
            donelist[num] = ''
    return donelist


def _log_main(message, main_logpath=None):
    """Write message to main L3_log.txt with timestamp."""
    if not main_logpath:
        return
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with open(main_logpath, 'a', encoding='utf-8', errors='replace') as f:
            f.write(f'[{timestamp}] {message}\n')
    except Exception as e:
        print(f'Warning: could not write to main log {main_logpath}: {e}')


def _log_test(test_logpath, message):
    """Write message to a test-specific log file with timestamp."""
    if not test_logpath:
        return
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with open(test_logpath, 'a', encoding='utf-8', errors='replace') as f:
            f.write(f'[{timestamp}] {message}\n')
    except Exception as e:
        print(f'Warning: could not write to test log {test_logpath}: {e}')


def _log_step_error(var, step_desc, testname, test_logpath, err, tb, main_logpath=None, logs=None):
    """Print exception, log to test log and main L3 log."""
    line = f"Error: {err}"
    print(line)
    if tb:
        print(tb.strip())
    if logs is not None:
        logs.append(line)
    err_entry = f"ERROR in step {var} ({step_desc}) for [{testname}]:\n{err}\n{tb.strip() if tb else ''}"
    _log_test(test_logpath, err_entry)
    _log_main(err_entry, main_logpath)


def _finish_step(donelist, var, funs, error, main_logpath=None, logs=None):
    """Update donelist, print status to terminal, and append to L3_log.txt and logs list."""
    idx = int(var) - 1
    step_desc = funs[idx] if 0 <= idx < len(funs) else var
    if error == 1:
        updatedonelisterror(donelist, var)
        line = f"\nstep {var}: {step_desc} completed WITH ERRORS (see log files for details)"
    else:
        updatedonelist(donelist, var)
        line = f"\nstep {var}: {step_desc} done, back to main menu"
    print(line)
    if logs is not None:
        logs.append(line)
    _log_main(line.strip(), main_logpath)


def _run_parallel(worker_fn, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=None, step_info=""):
    """Submit worker_fn for every test in parallel. Returns 1 if any error, else 0."""
    args_list = [
        (t, list_directory[t], list_testname[t], list_input[t], inputmethod)
        for t in range(len(list_directory))
    ]
    dir_by_test = {list_testname[i]: list_directory[i] for i in range(len(list_testname))}
    error = 0
    if main_logpath and step_info:
        _log_main(f"--- Starting {step_info} in parallel ({len(args_list)} tests, {max_workers} worker(s)) ---", main_logpath)

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        for testname, err in pool.map(worker_fn, args_list):
            test_dir = dir_by_test.get(testname, '')
            test_log = os.path.join(test_dir, f"{testname}_log.txt") if test_dir else None
            if err:
                print(f'  ERROR [{testname}]:\n{err}')
                error = 1
                err_msg = f"ERROR in {step_info or worker_fn.__name__} for [{testname}]:\n{err.strip()}"
                _log_test(test_log, err_msg)
                _log_main(err_msg, main_logpath)
            else:
                print(f'  OK    [{testname}]')
                if test_log and step_info:
                    _log_test(test_log, f"{step_info} completed successfully.")

    if main_logpath and step_info:
        status_str = "COMPLETED WITH ERRORS" if error else "COMPLETED SUCCESSFULLY"
        _log_main(f"--- Finished {step_info}: {status_str} ---", main_logpath)

    return error


def _worker_step1(args):
    """Worker for step 1: plot raw data."""
    import matplotlib
    matplotlib.use('Agg')
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    inputpath = os.path.join(directory, testname + '_RawData.csv')
    fuelpath = os.path.join(directory, testname + '_null.csv')
    exactpath = os.path.join(directory, testname + '_null.csv')
    fuelmetricpath = os.path.join(directory, testname + '_null.csv')
    scalepath = os.path.join(directory, testname + '_null.csv')
    intscalepath = os.path.join(directory, testname + '_null.csv')
    ascalepath = os.path.join(directory, testname + '_null.csv')
    cscalepath = os.path.join(directory, testname + '_FormattedCombinedScaleData.csv')
    nanopath = os.path.join(directory, testname + '_null.csv')
    TEOMpath = os.path.join(directory, testname + '_null.csv')
    senserionpath = os.path.join(directory, testname + '_null.csv')
    OPSpath = os.path.join(directory, testname + '_null.csv')
    Picopath = os.path.join(directory, testname + '_null.csv')
    plotpath = os.path.join(directory, testname + '_rawplots.csv')
    savefig = os.path.join(directory, testname + '_rawplot.png')
    try:
        names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
            PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath, ascalepath, cscalepath, nanopath,
                         TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
        PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cscalepath, nnames, tnames, sennames, opsnames, pnames, plotpath,
                            savefig)
        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())


def _worker_step2(args):
    """Worker for step 2: load energy inputs."""
    t, directory, testname, inputpath_t, inputmethod = args
    inputpath = inputpath_t
    logpath = os.path.join(directory, testname + '_log.txt')
    outputpath = os.path.join(directory, testname + '_EnergyInputs.csv')
    try:
        LEMS_MakeInputFile_EnergyCalcs(inputpath, outputpath, logpath)
        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())


def _worker_step3(args):
    """Worker for step 3: load scale and aux raw data files."""
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    try:
        inputpath = os.path.join(directory, testname + '_ScaleRawData.csv')
        outputpath = os.path.join(directory, testname + '_FormattedScaleData.csv')
        try:
            LEMS_Scale(inputpath, outputpath, logpath)
        except Exception:
            pass

        inputpath = os.path.join(directory, testname + '_IntScaleRawData.csv')
        outputpath = os.path.join(directory, testname + '_FormattedIntScaleData.csv')
        try:
            LEMS_Int_Scale(inputpath, outputpath, logpath)
        except Exception:
            pass

        inputpath = os.path.join(directory, testname + '_AdamScaleRawData.csv')
        outputpath = os.path.join(directory, testname + '_FormattedAdamScaleData.csv')
        try:
            LEMS_Adam_Scale(inputpath, outputpath, logpath)
        except Exception:
            pass

        inputpath = os.path.join(directory, testname + '_NanoscanRawData.csv')
        outputpath = os.path.join(directory, testname + '_FormattedNanoscanData.csv')
        try:
            LEMS_Nanoscan(inputpath, outputpath, logpath)
        except Exception:
            pass

        inputpath = os.path.join(directory, testname + '_TEOMRawData.txt')
        rawoutputpath = os.path.join(directory, testname + '_TEOMRawData.csv')
        outputpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
        try:
            LEMS_TEOM(inputpath, rawoutputpath, outputpath, logpath)
        except Exception:
            pass

        inputpath = os.path.join(directory, testname + '_SenserionRawData.csv')
        outputpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
        senpath = os.path.join(directory, testname + '_SenserionInputs.csv')
        try:
            LEMS_Senserion(inputpath, outputpath, senpath, logpath, inputmethod)
        except Exception:
            pass

        inputpath = os.path.join(directory, testname + '_OPSRawData.csv')
        outputpath = os.path.join(directory, testname + '_FormattedOPSData.csv')
        try:
            LEMS_OPS(inputpath, outputpath, logpath)
        except Exception:
            pass

        inputpath = os.path.join(directory, testname + '_PicoRawData.csv')
        lemspath = os.path.join(directory, testname + '_RawData.csv')
        outputpath = os.path.join(directory, testname + '_FormattedOPSData.csv')
        try:
            LEMS_Pico(inputpath, lemspath, outputpath, logpath)
        except Exception:
            pass

        scale_path = os.path.join(directory, testname + '_FormattedScaleData.csv')
        adam_scale_path = os.path.join(directory, testname + '_FormattedAdamScaleData.csv')
        if os.path.isfile(scale_path) and os.path.isfile(adam_scale_path):
            out_path = os.path.join(directory, testname + '_FormattedCombinedScaleData.csv')
            try:
                LEMS_Combined_Scale(scale_path, adam_scale_path, out_path, logpath)
            except Exception:
                pass

        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())


def _worker_step4(args):
    """Worker for step 4: calculate energy metrics."""
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    inputpath = os.path.join(directory, testname + '_EnergyInputs.csv')
    outputpath = os.path.join(directory, testname + '_EnergyOutputs.csv')
    try:
        LEMS_EnergyCalcs(inputpath, outputpath, logpath)
        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())


def _worker_step5(args):
    """Worker for step 5: adjust sensor calibrations."""
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    inputpath = os.path.join(directory, testname + '_RawData.csv')
    outputpath = os.path.join(directory, testname + '_RawData_Recalibrated.csv')
    sensorpath = os.path.join(directory, testname + '_SensorboxVersion.csv')
    headerpath = os.path.join(directory, testname + '_Header.csv')
    try:
        LEMS_Adjust_Calibrations(inputpath, sensorpath, outputpath, headerpath, logpath, inputmethod)
        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())


def _worker_step6(args):
    """Worker for step 6: shift timeseries."""
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    inputpath = os.path.join(directory, testname + '_RawData_Recalibrated.csv')
    outputpath = os.path.join(directory, testname + '_RawData_Shifted.csv')
    timespath = os.path.join(directory, testname + '_TimeShifts.csv')
    try:
        LEMS_ShiftTimeSeries(inputpath, outputpath, timespath, logpath, inputmethod)
        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())


def _worker_step7(args):
    """Worker for step 7: subtract background."""
    import matplotlib
    matplotlib.use('Agg')
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    inputpath = os.path.join(directory, testname + '_RawData_Shifted.csv')
    energyinputpath = os.path.join(directory, testname + '_EnergyInputs.csv')
    ucpath = os.path.join(directory, testname + '_UCInputs.csv')
    outputpath = os.path.join(directory, testname + '_TimeSeries.csv')
    aveoutputpath = os.path.join(directory, testname + '_Averages.csv')
    timespath = os.path.join(directory, testname + '_PhaseTimes.csv')
    bkgmethodspath = os.path.join(directory, testname + '_BkgMethods.csv')
    savefig1 = os.path.join(directory, testname + '_subtractbkg1.png')
    savefig2 = os.path.join(directory, testname + '_subtractbkg2.png')
    bkgpath = os.path.join(directory, testname + '_BkgOutputs.csv')
    try:
        PEMS_SubtractBkg(inputpath, energyinputpath, ucpath, outputpath, aveoutputpath, timespath,
                         bkgmethodspath, logpath, savefig1, savefig2, inputmethod, bkgpath)
        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())


def _worker_step8(args):
    """Worker for step 8: cut TEOM realtime data based on phases."""
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    inputpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
    outputpath = os.path.join(directory, testname + 'TEOM_TimeSeries.csv')
    aveoutputpath = os.path.join(directory, testname + '_TEOM_Averages.csv')
    timespath = os.path.join(directory, testname + '_TEOMPhaseTimes.csv')
    try:
        LEMS_TEOM_SubtractBkg(inputpath, outputpath, aveoutputpath, timespath, logpath)
        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())


def _worker_step9(args):
    """Worker for step 9: calculate gravimetric PM."""
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    gravinputpath = os.path.join(directory, testname + '_GravInputs.csv')
    aveinputpath = os.path.join(directory, testname + '_Averages.csv')
    timespath = os.path.join(directory, testname + '_PhaseTimes.csv')
    gravoutputpath = os.path.join(directory, testname + '_GravOutputs.csv')
    energypath = os.path.join(directory, testname + '_EnergyOutputs.csv')
    try:
        LEMS_GravCalcs(gravinputpath, aveinputpath, timespath, energypath, gravoutputpath, logpath, inputmethod)
        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())


def _worker_step10(args):
    """Worker for step 10: calculate emission metrics."""
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    inputpath = os.path.join(directory, testname + '_TimeSeries.csv')
    energypath = os.path.join(directory, testname + '_EnergyOutputs.csv')
    gravinputpath = os.path.join(directory, testname + '_GravOutputs.csv')
    aveinputpath = os.path.join(directory, testname + '_Averages.csv')
    timespath = os.path.join(directory, testname + '_PhaseTimes.csv')
    emisoutputpath = os.path.join(directory, testname + '_EmissionOutputs.csv')
    alloutputpath = os.path.join(directory, testname + '_AllOutputs.csv')
    cutoutputpath = os.path.join(directory, testname + '_CutTable.csv')
    outputexcel = os.path.join(directory, testname + '_CutTable.xlsx')
    senserionpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
    fuelpath = os.path.join(directory, testname + '_null.csv')
    exactpath = os.path.join(directory, testname + '_null.csv')
    fuelmetricpath = os.path.join(directory, testname + '_null.csv')
    scalepath = os.path.join(directory, testname + '_FormattedScaleData.csv')
    intscalepath = os.path.join(directory, testname + '_FormattedIntScaleData.csv')
    ascalepath = os.path.join(directory, testname + '_FormattedAdamScaleData.csv')
    cscalepath = os.path.join(directory, testname + '_FormattedCombinedScaleData.csv')
    nanopath = os.path.join(directory, testname + '_FormattedNanoscanData.csv')
    TEOMpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
    sensorpath = os.path.join(directory, testname + '_SensorboxVersion.csv')
    OPSpath = os.path.join(directory, testname + '_FormattedOPSData.csv')
    Picopath = os.path.join(directory, testname + '_FormattedPicoData.csv')
    emissioninputpath = os.path.join(directory, testname + '_EmissionInputs.csv')
    bcpath = os.path.join(directory, testname + '_BCOutputs.csv')
    qualitypath = os.path.join(directory, testname + '_QualityControl.csv')
    bkgpath = os.path.join(directory, testname + '_BkgOutputs.csv')
    try:
        LEMS_EmissionCalcs(inputpath, energypath, gravinputpath, aveinputpath, emisoutputpath, alloutputpath,
                           logpath, timespath, sensorpath, fuelpath, fuelmetricpath, exactpath, scalepath,
                           intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath,
                           emissioninputpath, inputmethod, bcpath, qualitypath, bkgpath)
        LEMS_FormattedL1(alloutputpath, cutoutputpath, outputexcel, testname, logpath)
        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())


def _worker_step11(args):
    """Worker for step 11: calculate canadian efficiency metrics."""
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    input_path = os.path.join(directory, testname + '_TimeSeriesMetrics')
    pemsinputpath = os.path.join(directory, testname + '_TimeSeries_test.csv')
    scaleinputpath = os.path.join(directory, testname + '_FormattedScaleData.csv')
    intscalepath = os.path.join(directory, testname + '_FormattedIntScaleData.csv')
    ascalepath = os.path.join(directory, testname + '_FormattedAdamScaleData.csv')
    energyinputpath = os.path.join(directory, testname + '_EnergyOutputs.csv')
    cuttimepath = os.path.join(directory, testname + '_ThermalEfficiencyCutTimes')
    fuelcutpic = os.path.join(directory, testname + '_ThermalEfficiencyCut')
    outputtimepath = os.path.join(directory, testname + '_TimeSeriesCanThermalEfficiency')
    outputpath = os.path.join(directory, testname + '_CanThermalEfficiency.csv')
    try:
        LEMS_CANThermalEfficiency(input_path, pemsinputpath, scaleinputpath, intscalepath, ascalepath,
                                  energyinputpath, cuttimepath, fuelcutpic, outputtimepath, outputpath,
                                  logpath, inputmethod)
        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())


def _worker_step12(args):
    """Worker for step 12: cut period / realtime averages across all phases."""
    import matplotlib
    matplotlib.use('Agg')
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    energypath = os.path.join(directory, testname + '_EnergyOutputs.csv')
    gravpath = os.path.join(directory, testname + '_GravOutputs.csv')
    phasepath = os.path.join(directory, testname + '_PhaseTimes.csv')
    savefig = os.path.join(directory, testname + '_AveragingPeriod.png')
    fuelpath = os.path.join(directory, testname + '_null.csv')
    exactpath = os.path.join(directory, testname + '_null.csv')
    fuelmetricpath = os.path.join(directory, testname + '_null.csv')
    scalepath = os.path.join(directory, testname + '_FormattedScaleData.csv')
    intscalepath = os.path.join(directory, testname + '_FormattedIntScaleData.csv')
    ascalepath = os.path.join(directory, testname + '_FormattedAdamScaleData.csv')
    cscalepath = os.path.join(directory, testname + '_FormattedCombinedScaleData.csv')
    nanopath = os.path.join(directory, testname + '_FormattedNanoscanData.csv')
    TEOMpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
    senserionpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
    OPSpath = os.path.join(directory, testname + '_FormattedOPSData.csv')
    Picopath = os.path.join(directory, testname + '_FormattedPicoData.csv')

    phases = ['L1', 'hp', 'mp', 'lp', 'L5']
    try:
        for phase in phases:
            inputpath = os.path.join(directory, testname + '_TimeSeriesMetrics_' + phase + '.csv')
            periodpath = os.path.join(directory, testname + '_AveragingPeriod_' + phase + '.csv')
            outputpath = os.path.join(directory, testname + '_AveragingPeriodTimeSeries_' + phase + '.csv')
            averageoutputpath = os.path.join(directory, testname + '_AveragingPeriodAverages_' + phase + '.csv')
            if os.path.isfile(inputpath):
                LEMS_Realtime(inputpath, energypath, gravpath, phasepath, periodpath, outputpath,
                              averageoutputpath, savefig, phase, logpath, inputmethod, fuelpath, fuelmetricpath, exactpath,
                              scalepath, intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath)
        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())


def _worker_step13(args):
    """Worker for step 13: plot processed data across phases."""
    import matplotlib
    matplotlib.use('Agg')
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    fuelpath = os.path.join(directory, testname + '_null.csv')
    exactpath = os.path.join(directory, testname + '_null.csv')
    fuelmetricpath = os.path.join(directory, testname + '_null.csv')
    scalepath = os.path.join(directory, testname + '_FormattedScaleData.csv')
    intscalepath = os.path.join(directory, testname + '_FormattedIntScaleData.csv')
    ascalepath = os.path.join(directory, testname + '_FormattedAdamScaleData.csv')
    cscalepath = os.path.join(directory, testname + '_FormattedCombinedScaleData.csv')
    nanopath = os.path.join(directory, testname + '_FormattedNanoscanData.csv')
    TEOMpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
    senserionpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
    OPSpath = os.path.join(directory, testname + '_FormattedOPSData.csv')
    Picopath = os.path.join(directory, testname + '_FormattedPicoData.csv')
    choices = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']
    try:
        for phase in choices:
            inputpath = os.path.join(directory, testname + '_TimeSeriesMetrics_' + phase + '.csv')
            if os.path.isfile(inputpath):
                plotpath = os.path.join(directory, testname + '_plots_' + phase + '.csv')
                savefig = os.path.join(directory, testname + '_plot_' + phase + '.png')
                names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                    PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath, ascalepath, cscalepath,
                                 nanopath, TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
                PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, nnames, tnames, sennames, opsnames, pnames,
                                    plotpath, savefig)
        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())


def _worker_step14(args):
    """Worker for step 14: plot processed data subplots."""
    import matplotlib
    matplotlib.use('Agg')
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    fuelpath = os.path.join(directory, testname + '_null.csv')
    exactpath = os.path.join(directory, testname + '_null.csv')
    fuelmetricpath = os.path.join(directory, testname + '_null.csv')
    scalepath = os.path.join(directory, testname + '_FormattedScaleData.csv')
    intscalepath = os.path.join(directory, testname + '_FormattedIntScaleData.csv')
    ascalepath = os.path.join(directory, testname + '_FormattedAdamScaleData.csv')
    cscalepath = os.path.join(directory, testname + '_FormattedCombinedScaleData.csv')
    nanopath = os.path.join(directory, testname + '_FormattedNanoscanData.csv')
    TEOMpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
    senserionpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
    OPSpath = os.path.join(directory, testname + '_FormattedOPSData.csv')
    Picopath = os.path.join(directory, testname + '_FormattedPicoData.csv')
    all_phase_data = []
    valid_phases = []
    choices = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']
    try:
        names = units = fnames = fcnames = exnames = snames = isnames = anames = cnames = nnames = tnames = sennames = opsnames = pnames = plotpath = savefig = None
        for phase in choices:
            inputpath = os.path.join(directory, testname + '_TimeSeriesMetrics_' + phase + '.csv')
            if os.path.isfile(inputpath):
                plotpath = os.path.join(directory, testname + '_plots.csv')
                savefig = os.path.join(directory, testname + '_GridPlot.png')
                names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                    PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath,
                                 ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
                all_phase_data.append(data)
                valid_phases.append(phase)
        if len(all_phase_data) > 0:
            PEMS_PlotTimeSeries_Grid(names, units, all_phase_data, valid_phases, fnames, fcnames, exnames,
                                     snames, isnames, anames, cnames, [], nnames, tnames, sennames, opsnames, pnames, plotpath, savefig)
        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())


def _worker_step15(args):
    """Worker for step 15: create custom output table for each test."""
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    inputpath = os.path.join(directory, testname + '_AllOutputs.csv')
    outputpath = os.path.join(directory, testname + '_CustomCutTable.csv')
    outputexcel = os.path.join(directory, testname + '_CustomCutTable.xlsx')
    csvpath = os.path.join(directory, testname + '_CutTableParameters.csv')
    try:
        LEMS_CSVFormatted_L1(inputpath, outputpath, outputexcel, csvpath, testname, logpath)
        return (testname, None)
    except Exception:
        return (testname, traceback.format_exc())

# ==============================================================================

if __name__ == '__main__':
    logs=[]

    # Setting up lists to record the files
    list_input = []
    list_filename = []
    list_directory = []
    list_testname = []
    list_logname = []
    button2 = 'No'
    output = button2

    list_input_LP = []
    list_filename_LP = []
    list_directory_LP = []
    list_testname_LP = []
    list_logname_LP = []

    inputmode = input("Enter cli for command line interface or default to graphical user interface.\n")
    if inputmode == "cli":
        # Prompt user for folder path
        folder_path = input("Enter folder path: ")

        # --- Two-level input loading ---
        # list_input_L3 : UnFormattedDataL2.csv paths (one per group) -> comparison steps 16-28
        # list_input    : per-test paths (all groups flattened)        -> reprocessing steps 1-15
        list_input_L3  = []
        list_input     = []
        list_filename  = []
        list_directory = []
        list_testname  = []
        list_logname   = []
        logs           = []

        meta_csv_path = os.path.join(folder_path, 'UnformattedDataL2FilePaths_DataEntrySheetFilePaths.csv')
        if os.path.exists(meta_csv_path):
            with open(meta_csv_path, 'r', newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row or not row[0].strip():
                        continue
                    group_csv_path = row[0].strip().strip('"')
                    group_dir = os.path.dirname(group_csv_path)

                    # Build L3 comparison list: UnFormattedDataL2.csv in same dir as group CSV
                    unformatted_path = os.path.join(group_dir, 'UnFormattedDataL2.csv')
                    list_input_L3.append(unformatted_path)

                    # Read each group's DataEntrySheetFilePaths.csv -> per-test paths
                    if os.path.exists(group_csv_path):
                        with open(group_csv_path, 'r', newline='') as gf:
                            greader = csv.reader(gf)
                            for grow in greader:
                                if not grow or not grow[0].strip():
                                    continue
                                test_path = grow[0].strip().strip('"')
                                list_input.append(test_path)
                                directory, filename = os.path.split(test_path)
                                datadirectory, testname = os.path.split(directory)
                                logname = testname + '_log.txt'
                                list_filename.append(filename)
                                list_directory.append(directory)
                                list_testname.append(testname)
                                list_logname.append(logname)
                    else:
                        print('Warning: group CSV not found: ' + group_csv_path)
            print('Loaded ' + str(len(list_input)) + ' individual test(s) across '
                  + str(len(list_input_L3)) + ' group(s).')
        else:
            print('Warning: ' + meta_csv_path + ' not found.')
            print('Steps 1-15 (reprocessing) and 16-28 (comparison) will have no input.')

        # Check if UnformattedDataL2FilePaths_lp.csv already exists in main folder
        csv_file_path_LP = os.path.join(folder_path, 'UnformattedDataL2FilePaths_lp.csv')
        if os.path.exists(csv_file_path_LP):
            with open(csv_file_path_LP, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    list_input_LP.append(row[0])
            print('UnformattedDataL2FilePaths_lp.csv exists in main folder')
            print('Existing LP paths found:')
            for path in list_input_LP:
                print(path)
            edit_csv_LP = input('Run all LP tests listed? (y/n): ')
            if edit_csv_LP.lower() == 'n':
                input('Edit UnformattedDataL2FilePaths_lp.csv in main folder and save. Press enter when done.')
                list_input_LP = []
                with open(csv_file_path_LP, 'r', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        list_input_LP.append(row[0])

    else:
        # Prompt user to enter number of test runs done
        # message to be displayed
        text = "Enter number of test runs"
        # window title
        title = "gitrdone"
        # default text
        d_int = 1
        #lower bound
        lower = 0
        #upperbound
        upper = 999
        # creating an enter box
        testnum = integerbox(text, title, d_int, lower, upper)
        # title for the message box
        title = "gitrdone"
        # creating a message
        message = "Enterted Number : " + str(testnum)
        # creating a message box
        msg = msgbox(message, title)


        #Request data entry form for each test (ideally in the future this would just request the general folder and then find the entry form
        testlen = [0] * testnum
        #Need to fix this error handling later

        #Ask for each data entry file for each test and record the file in lists
        for x in testlen:
            line = 'Select Data Entry Form for Test ' + str(x) + ':'
            print(line)

            inputpath = easygui.fileopenbox()
            directory, filename = os.path.split(inputpath)
            datadirectory, testname = os.path.split(directory)
            logname = testname + '_log.txt'
            logpath = os.path.join(directory, logname)
            outputpath = os.path.join(directory, testname+'_FormattedData_L3.csv')
            testnum = x
            list_input.append(inputpath)
            print(list_input[x])
            list_filename.append(filename)
            list_directory.append(directory)
            list_testname.append(testname)
            list_logname.append(logname)

    if 'folder_path' not in locals():
        folder_path = os.path.dirname(list_directory[0]) if list_directory else '.'
    main_logpath = os.path.join(folder_path, 'L3_log.txt')
    logpath = main_logpath

    #######################################################
    inputmethod = input(
        'Enter 1 for interactive mode (default - for first run and changing variables). \n'
        'Enter 2 for reprocessing mode (for reprocessing data with variables already set). \n'
        'Press Enter to accept default [1]: '
    ).strip() or '1'

    if inputmethod == '1':
        line = 'Interactive mode selected - enter variables when prompted'
        print(line)
        logs.append(line)
    elif inputmethod == '2':
        line = 'Reprocessing mode selected - previously entered variables will be used'
        print(line)
        logs.append(line)
    else:
        inputmethod = '1'
        line = "Entered variable doesn't exist, defaulting to interactive mode"
        print(line)
        logs.append(line)
    if inputmethod == '2':
        _default_workers = max(1, (os.cpu_count() or 2) // 2)
        _w = input(f'Enter number of parallel workers [default {_default_workers}]: ').strip()
        max_workers = int(_w) if _w.isdigit() and int(_w) > 0 else _default_workers
        line = f'Parallel reprocessing mode enabled with {max_workers} worker(s)'
        print(line)
        logs.append(line)
    else:
        max_workers = 1

    _log_main("=" * 60, main_logpath)
    _log_main(f"Session started. Loaded {len(list_input)} test(s). Mode: {'Reprocessing (parallel)' if inputmethod == '2' else 'Interactive (sequential)'}, Workers: {max_workers}", main_logpath)
    _log_main("=" * 60, main_logpath)
    #######################################################
    #Run option menu to make output files for each test

    # list of function descriptions in order:
    funs = [
        # --- L2 per-test reprocessing steps (1-15) ---
        'plot raw data',                                         # 1
        'load data entry form',                                  # 2
        'load additional raw data files (heating stoves only)',  # 3
        'calculate energy metrics',                              # 4
        'adjust sensor calibrations',                            # 5
        'correct for response times',                            # 6
        'subtract background',                                   # 7
        'cut TEOM realtime data based on phases',                # 8
        'calculate gravimetric PM',                              # 9
        'calculate emission metrics',                            # 10
        'calculate efficiency metrics',                          # 11
        'calculate averages from a specified cut period',        # 12
        'plot processed data',                                   # 13
        'plot processed data subplots',                          # 14
        'create custom output table for each test',              # 15
        # --- L2 cross-test comparison steps (16-19) ---
        'compare all outputs - unformatted (L2)',                # 16
        'compare all outputs - formatted (L2)',                  # 17
        'compare cut data - unformatted (L2)',                   # 18
        'create custom comparison table (L2)',                   # 19
        # --- L3 cross-test comparison steps (20-32) ---
        'compare all outputs',                                   # 20
        'LP - compare all outputs (UnformattedDataL2FilePaths_lp.csv must be defined)',  # 21
        'compare all outputs, multi-pair',                       # 22
        'create custom boxplot',                                 # 23
        'create multiple boxplots at once',                      # 24
        'create custom bar chart',                               # 25
        'create multiple barcharts at once',                     # 26
        'create custom scatter plot',                            # 27
        'create multiple scatter plots at once',                 # 28
        'create subplots of scatter plots',                      # 29
        'create custom comparison table',                        # 30
        'create formatted custom comparison table',              # 31
        'create formatted custom comparison table of pairs',     # 32
        # --- L2 upload step ---
        'upload processed data (L2)',                            # 33
    ]

    donelist = [''] * len(funs)  # initialize a list that indicates which data processing steps have been done


    # this function updates the donelist when a data processing step is completed
    # Allows for steps to be skipped if files from previous steps already exist
    # To do: currently if files do no exist from skipped steps there is just error. Make user friendly to prompt for missing files
    # Create optional steps and allow for optional steps to be skipped (Optional: adjust calibrations and response time: 3,4)
    line = '\nLEMSDataCruncher_ISO_v0.0\n'
    print(line)
    logs.append(line)

    var = 'unicorn'
    #print(list_testname)
    while var != 'exit':
        print('')
        print('----------------------------------------------------')
        print('Data processing steps:')
        print('0 : update EnergyInputs.csv files from template')
        print('')
        for num, fun in enumerate(funs):  # print the list of data processing steps
            print(donelist[num] + str(num + 1) + ' : ' + fun)
        print('exit : exit program')
        print('')
        var = input("Enter menu option: ")


        if var == '0':  # update EnergyInputs.csv files from template
            def _read_csv_with_fallback(filepath):
                encodings_to_try = []
                try:
                    import chardet
                    with open(filepath, 'rb') as f:
                        raw = f.read(10000)
                    detected = chardet.detect(raw).get('encoding')
                    if detected:
                        encodings_to_try.append(detected)
                except Exception:
                    pass
                for e in ['utf-8-sig', 'utf-8', 'cp1252', 'latin1', 'iso-8859-1']:
                    if e not in encodings_to_try:
                        encodings_to_try.append(e)

                for enc in encodings_to_try:
                    try:
                        with open(filepath, 'r', encoding=enc, newline='') as f:
                            reader = csv.DictReader(f)
                            fieldnames = list(reader.fieldnames) if reader.fieldnames else []
                            rows = list(reader)
                        return enc, fieldnames, rows
                    except (UnicodeDecodeError, LookupError):
                        continue

                with open(filepath, 'r', encoding='latin1', errors='replace', newline='') as f:
                    reader = csv.DictReader(f)
                    fieldnames = list(reader.fieldnames) if reader.fieldnames else []
                    rows = list(reader)
                return 'latin1', fieldnames, rows

            # Template is expected in the same folder_path as the test data
            template_path = os.path.join(folder_path, 'Update_EnergyInputs_template.csv')
            if not os.path.isfile(template_path):
                line = 'Error: template file not found: ' + template_path
                print(line)
                logs.append(line)
            else:
                # Load template into a dict keyed by variable_name
                template_updates = {}  # {variable_name: {'units': ..., 'value': ..., 'uncertainty': ...}}
                try:
                    _, _, template_rows = _read_csv_with_fallback(template_path)
                    for trow in template_rows:
                        vname = trow.get('variable_name', '').strip()
                        if vname:
                            template_updates[vname] = {
                                'units':       trow.get('units', '').strip(),
                                'value':       trow.get('value', '').strip(),
                                'uncertainty': trow.get('uncertainty', '').strip(),
                            }
                except Exception as e:
                    line = 'Error reading template ' + template_path + ': ' + str(e)
                    print(line)
                    logs.append(line)

                line = f'Template loaded: {len(template_updates)} variable(s) to update'
                print(line)
                logs.append(line)

                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test: ' + list_directory[t])
                    energy_path = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
                    if not os.path.isfile(energy_path):
                        line = '  Skipping (EnergyInputs.csv not found): ' + energy_path
                        print(line)
                        logs.append(line)
                        continue
                    try:
                        # Read existing EnergyInputs.csv with auto-detected encoding
                        enc, fieldnames, existing_rows = _read_csv_with_fallback(energy_path)

                        updated_count = 0
                        for row in existing_rows:
                            vname = row.get('variable_name', '').strip()
                            if vname in template_updates:
                                upd = template_updates[vname]
                                # Only overwrite non-empty template fields
                                if upd['value'] != '':
                                    row['value'] = upd['value']
                                if upd['units'] != '' and 'units' in row:
                                    row['units'] = upd['units']
                                if upd['uncertainty'] != '' and 'uncertainty' in row:
                                    row['uncertainty'] = upd['uncertainty']
                                updated_count += 1

                        # Write back updated EnergyInputs.csv using detected encoding
                        write_enc = enc or 'utf-8'
                        with open(energy_path, 'w', encoding=write_enc, errors='replace', newline='') as ef:
                            ewriter = csv.DictWriter(ef, fieldnames=fieldnames)
                            ewriter.writeheader()
                            ewriter.writerows(existing_rows)

                        line = f'  Updated {updated_count} variable(s) in ' + energy_path
                        print(line)
                        logs.append(line)
                    except Exception as e:
                        line = 'Error updating ' + energy_path + ': ' + str(e)
                        print(line)
                        tb = traceback.format_exc()
                        traceback.print_exception(type(e), e, e.__traceback__)
                        logs.append(line)
                        _log_main(f"ERROR updating {energy_path}: {line}\n{tb.strip()}", main_logpath)
                        error = 1

                if error == 1:
                    line = 'step 0: update EnergyInputs.csv from template completed with errors'
                    print(line)
                    logs.append(line)
                    _log_main(line, main_logpath)
                else:
                    line = 'step 0: update EnergyInputs.csv from template done, back to main menu'
                    print(line)
                    logs.append(line)
                    _log_main(line, main_logpath)

        elif var == '1':  # plot raw data
            if inputmethod == '2':
                error = _run_parallel(_worker_step1, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test:' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData.csv')
                    fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    exactpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    fuelmetricpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    scalepath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    intscalepath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    ascalepath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    cscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedCombinedScaleData.csv')
                    nanopath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    TEOMpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    senserionpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    OPSpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    Picopath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    plotpath = os.path.join(list_directory[t], list_testname[t] + '_rawplots.csv')
                    savefig = os.path.join(list_directory[t], list_testname[t] + '_rawplot.png')
                    try:
                        names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                            PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath, ascalepath, cscalepath, nanopath,
                                         TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
                        PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cscalepath, nnames, tnames, sennames, opsnames, pnames, plotpath,
                                            savefig)
                    except Exception as e:
                        _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '2':  # load energy inputs
            if inputmethod == '2':
                error = _run_parallel(_worker_step2, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    inputpath = list_input[t]
                    print('Test:' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
                    try:
                        LEMS_MakeInputFile_EnergyCalcs(inputpath, outputpath, logpath)
                    except Exception as e:
                        _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '3':  # Load scale raw data file
            if inputmethod == '2':
                error = _run_parallel(_worker_step3, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test: ' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_ScaleRawData.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
                    try:
                        LEMS_Scale(inputpath, outputpath, logpath)
                        line = '\nloaded and processed scale data'
                        print(line)
                        logs.append(line)
                    except Exception as e:
                        line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                        print(line)
                        logs.append(line)
                    print('')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_IntScaleRawData.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedIntScaleData.csv')
                    try:
                        LEMS_Int_Scale(inputpath, outputpath, logpath)
                        line = '\nloaded and processed intelligent scale data'
                        print(line)
                        logs.append(line)
                    except Exception as e:
                        line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                        print(line)
                        logs.append(line)
                    print('')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_AdamScaleRawData.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
                    try:
                        LEMS_Adam_Scale(inputpath, outputpath, logpath)
                        line = '\nloaded and processed Adam scale data'
                        print(line)
                        logs.append(line)
                    except Exception as e:
                        line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                        print(line)
                        logs.append(line)
                    print('')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_NanoscanRawData.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedNanoscanData.csv')
                    try:
                        LEMS_Nanoscan(inputpath, outputpath, logpath)
                        line = '\nloaded and processed Nanoscan data'
                        print(line)
                        logs.append(line)
                    except Exception as e:
                        line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                        print(line)
                        logs.append(line)
                    print('')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_TEOMRawData.txt')
                    rawoutputpath = os.path.join(list_directory[t], list_testname[t] + '_TEOMRawData.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
                    try:
                        LEMS_TEOM(inputpath, rawoutputpath, outputpath, logpath)
                        line = '\nloaded and processed TEOM data'
                        print(line)
                        logs.append(line)
                    except Exception as e:
                        line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                        print(line)
                        logs.append(line)
                    print('')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_SenserionRawData.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedSenserionData.csv')
                    senpath = os.path.join(list_directory[t], list_testname[t] + '_SenserionInputs.csv')
                    try:
                        LEMS_Senserion(inputpath, outputpath, senpath, logpath, inputmethod)
                        line = '\nloaded and processed Senserion data'
                        print(line)
                        logs.append(line)
                    except Exception as e:
                        line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                        print(line)
                        logs.append(line)
                    print('')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_OPSRawData.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
                    try:
                        LEMS_OPS(inputpath, outputpath, logpath)
                        line = '\nloaded and processed OPS data'
                        print(line)
                        logs.append(line)
                    except Exception as e:
                        line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                        print(line)
                        logs.append(line)
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_PicoRawData.csv')
                    lemspath = os.path.join(list_directory[t], list_testname[t] + '_RawData.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
                    try:
                        LEMS_Pico(inputpath, lemspath, outputpath, logpath)
                        line = '\nloaded and processed Pico data'
                        print(line)
                        logs.append(line)
                    except Exception as e:
                        line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                        print(line)
                        logs.append(line)
                    scale_path = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
                    adam_scale_path = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
                    if os.path.isfile(scale_path) and os.path.isfile(adam_scale_path):
                        out_path = os.path.join(list_directory[t], list_testname[t] + '_FormattedCombinedScaleData.csv')
                        LEMS_Combined_Scale(scale_path, adam_scale_path, out_path, logpath)
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '4':  # calculate energy metrics
            if inputmethod == '2':
                error = _run_parallel(_worker_step4, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test: ' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
                    try:
                        LEMS_EnergyCalcs(inputpath, outputpath, logpath)
                    except Exception as e:
                        _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '5':  # adjust sensor calibrations
            if inputmethod == '2':
                error = _run_parallel(_worker_step5, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test: ' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Recalibrated.csv')
                    sensorpath = os.path.join(list_directory[t], list_testname[t] + '_SensorboxVersion.csv')
                    headerpath = os.path.join(list_directory[t], list_testname[t] + '_Header.csv')
                    try:
                        LEMS_Adjust_Calibrations(inputpath, sensorpath, outputpath, headerpath, logpath, inputmethod)
                    except Exception as e:
                        _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '6':  # shift timeseries
            if inputmethod == '2':
                error = _run_parallel(_worker_step6, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test: ' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Recalibrated.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Shifted.csv')
                    timespath = os.path.join(list_directory[t], list_testname[t] + '_TimeShifts.csv')
                    try:
                        LEMS_ShiftTimeSeries(inputpath, outputpath, timespath, logpath, inputmethod)
                    except Exception as e:
                        _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '7':  # subtract background
            if inputmethod == '2':
                error = _run_parallel(_worker_step7, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test: ' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_RawData_Shifted.csv')
                    energyinputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
                    ucpath = os.path.join(list_directory[t], list_testname[t] + '_UCInputs.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeries.csv')
                    aveoutputpath = os.path.join(list_directory[t], list_testname[t] + '_Averages.csv')
                    timespath = os.path.join(list_directory[t], list_testname[t] + '_PhaseTimes.csv')
                    bkgmethodspath = os.path.join(list_directory[t], list_testname[t] + '_BkgMethods.csv')
                    savefig1 = os.path.join(list_directory[t], list_testname[t] + '_subtractbkg1.png')
                    savefig2 = os.path.join(list_directory[t], list_testname[t] + '_subtractbkg2.png')
                    bkgpath = os.path.join(list_directory[t], list_testname[t] + '_BkgOutputs.csv')
                    try:
                        PEMS_SubtractBkg(inputpath, energyinputpath, ucpath, outputpath, aveoutputpath, timespath,
                                         bkgmethodspath, logpath, savefig1, savefig2, inputmethod, bkgpath)
                    except Exception as e:
                        _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '8':  # cut TEOM realtime data based on phases
            print('')
            if inputmethod == '2':
                error = _run_parallel(_worker_step8, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + 'TEOM_TimeSeries.csv')
                    aveoutputpath = os.path.join(list_directory[t], list_testname[t] + '_TEOM_Averages.csv')
                    timespath = os.path.join(list_directory[t], list_testname[t] + '_TEOMPhaseTimes.csv')
                    try:
                        LEMS_TEOM_SubtractBkg(inputpath, outputpath, aveoutputpath, timespath, logpath)
                    except Exception as e:
                        _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '9':  # calculate gravimetric data
            if inputmethod == '2':
                error = _run_parallel(_worker_step9, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test: ' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    gravinputpath = os.path.join(list_directory[t], list_testname[t] + '_GravInputs.csv')
                    aveinputpath = os.path.join(list_directory[t], list_testname[t] + '_Averages.csv')
                    timespath = os.path.join(list_directory[t], list_testname[t] + '_PhaseTimes.csv')
                    gravoutputpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
                    energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
                    try:
                        LEMS_GravCalcs(gravinputpath, aveinputpath, timespath, energypath, gravoutputpath, logpath, inputmethod)
                    except Exception as e:
                        _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '10':  # calculate emissions metrics
            if inputmethod == '2':
                error = _run_parallel(_worker_step10, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test: ' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeries.csv')
                    energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
                    gravinputpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
                    aveinputpath = os.path.join(list_directory[t], list_testname[t] + '_Averages.csv')
                    timespath = os.path.join(list_directory[t], list_testname[t] + '_PhaseTimes.csv')
                    emisoutputpath = os.path.join(list_directory[t], list_testname[t] + '_EmissionOutputs.csv')
                    alloutputpath = os.path.join(list_directory[t], list_testname[t] + '_AllOutputs.csv')
                    cutoutputpath = os.path.join(list_directory[t], list_testname[t] + '_CutTable.csv')
                    outputexcel = os.path.join(list_directory[t], list_testname[t] + '_CutTable.xlsx')
                    senserionpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedSenserionData.csv')
                    fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    exactpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    fuelmetricpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    scalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
                    intscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedIntScaleData.csv')
                    ascalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
                    cscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedCombinedScaleData.csv')
                    nanopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedNanoscanData.csv')
                    TEOMpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
                    sensorpath = os.path.join(list_directory[t], list_testname[t] + '_SensorboxVersion.csv')
                    OPSpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
                    Picopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedPicoData.csv')
                    emissioninputpath = os.path.join(list_directory[t], list_testname[t] + '_EmissionInputs.csv')
                    bcpath = os.path.join(list_directory[t], list_testname[t] + '_BCOutputs.csv')
                    qualitypath = os.path.join(list_directory[t], list_testname[t] + '_QualityControl.csv')
                    bkgpath = os.path.join(list_directory[t], list_testname[t] + '_BkgOutputs.csv')
                    try:
                        LEMS_EmissionCalcs(inputpath, energypath, gravinputpath, aveinputpath, emisoutputpath, alloutputpath,
                                           logpath, timespath, sensorpath, fuelpath, fuelmetricpath, exactpath, scalepath,
                                           intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath,
                                           emissioninputpath, inputmethod, bcpath, qualitypath, bkgpath)
                        LEMS_FormattedL1(alloutputpath, cutoutputpath, outputexcel, list_testname[t], logpath)
                    except Exception as e:
                        _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '11':  # calculate canadian efficiency metrics
            if inputmethod == '2':
                error = _run_parallel(_worker_step11, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test: ' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    input_path = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics')
                    pemsinputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeries_test.csv')
                    scaleinputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
                    intscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedIntScaleData.csv')
                    ascalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
                    energyinputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
                    cuttimepath = os.path.join(list_directory[t], list_testname[t] + '_ThermalEfficiencyCutTimes')
                    fuelcutpic = os.path.join(list_directory[t], list_testname[t] + '_ThermalEfficiencyCut')
                    outputtimepath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesCanThermalEfficiency')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_CanThermalEfficiency.csv')
                    try:
                        LEMS_CANThermalEfficiency(input_path, pemsinputpath, scaleinputpath, intscalepath, ascalepath,
                                                  energyinputpath, cuttimepath, fuelcutpic, outputtimepath, outputpath,
                                                  logpath, inputmethod)
                    except Exception as e:
                        _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '12':  # cut period
            print('')
            if inputmethod == '2':
                error = _run_parallel(_worker_step12, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    energypath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
                    gravpath = os.path.join(list_directory[t], list_testname[t] + '_GravOutputs.csv')
                    phasepath = os.path.join(list_directory[t], list_testname[t] + '_PhaseTimes.csv')
                    savefig = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriod.png')
                    fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    exactpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    fuelmetricpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    scalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
                    intscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedIntScaleData.csv')
                    ascalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
                    cscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedCombinedScaleData.csv')
                    nanopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedNanoscanData.csv')
                    TEOMpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
                    senserionpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedSenserionData.csv')
                    OPSpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
                    Picopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedPicoData.csv')

                    if inputmethod == '1':
                        message = 'Select which phases will be graphed'
                        title = 'Gitrdun'
                        phases = ['L1', 'hp', 'mp', 'lp', 'L5']
                        choice = choicebox(message, title, phases)
                        inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + choice + '.csv')
                        periodpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriod_' + choice + '.csv')
                        outputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodTimeSeries_' + choice + '.csv')
                        averageoutputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodAverages_' + choice + '.csv')
                        if os.path.isfile(inputpath):
                            try:
                                LEMS_Realtime(inputpath, energypath, gravpath, phasepath, periodpath, outputpath, averageoutputpath,
                                              savefig, choice, logpath, inputmethod, fuelpath, fuelmetricpath, exactpath,
                                              scalepath, intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath)
                            except Exception as e:
                                _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                                error = 1
                        else:
                            line = inputpath + ' does not exist'
                            print(line)
                    else:
                        phases = ['L1', 'hp', 'mp', 'lp', 'L5']
                        for phase in phases:
                            inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + phase + '.csv')
                            periodpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriod_' + phase + '.csv')
                            outputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodTimeSeries_' + phase + '.csv')
                            averageoutputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodAverages_' + phase + '.csv')
                            if os.path.isfile(inputpath):
                                try:
                                    LEMS_Realtime(inputpath, energypath, gravpath, phasepath, periodpath, outputpath,
                                                  averageoutputpath, savefig, phase, logpath, inputmethod, fuelpath, fuelmetricpath, exactpath,
                                                  scalepath, intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath)
                                except Exception as e:
                                    _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                                    error = 1
                            else:
                                line = inputpath + ' does not exist'
                                print(line)
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '13':  # plot processed data
            if inputmethod == '2':
                error = _run_parallel(_worker_step13, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test: ' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    exactpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    fuelmetricpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    scalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
                    intscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedIntScaleData.csv')
                    ascalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
                    cscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedCombinedScaleData.csv')
                    nanopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedNanoscanData.csv')
                    TEOMpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
                    senserionpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedSenserionData.csv')
                    OPSpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
                    Picopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedPicoData.csv')
                    if inputmethod == '1':
                        message = 'Select which phases will be graphed'
                        title = 'Gitrdun'
                        phases_list = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']
                        choices = multchoicebox(message, title, phases_list)
                    else:
                        choices = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']
                    try:
                        for phase in choices:
                            inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + phase + '.csv')
                            if os.path.isfile(inputpath):
                                plotpath = os.path.join(list_directory[t], list_testname[t] + '_plots_' + phase + '.csv')
                                savefig = os.path.join(list_directory[t], list_testname[t] + '_plot_' + phase + '.png')
                                names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                                    PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath, ascalepath, cscalepath,
                                                 nanopath, TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
                                PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, nnames, tnames, sennames, opsnames, pnames,
                                                    plotpath, savefig)
                                line = '\nopen ' + plotpath + ', update and rerun step ' + var + ' to create a new graph'
                                print(line)
                            else:
                                line = inputpath + ' does not exist and will not be plotted.'
                                print(line)
                    except Exception as e:
                        _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '14':  # plot processed data subplots
            if inputmethod == '2':
                error = _run_parallel(_worker_step14, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test: ' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    fuelpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    exactpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    fuelmetricpath = os.path.join(list_directory[t], list_testname[t] + '_null.csv')
                    scalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
                    intscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedIntScaleData.csv')
                    ascalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
                    cscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedCombinedScaleData.csv')
                    nanopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedNanoscanData.csv')
                    TEOMpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
                    senserionpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedSenserionData.csv')
                    OPSpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
                    Picopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedPicoData.csv')
                    all_phase_data = []
                    valid_phases = []
                    if inputmethod == '1':
                        message = 'Select which phases will be graphed'
                        title = 'Gitrdun'
                        phases_list = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']
                        choices = multchoicebox(message, title, phases_list)
                    else:
                        choices = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']
                    try:
                        for phase in choices:
                            inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + phase + '.csv')
                            if os.path.isfile(inputpath):
                                plotpath = os.path.join(list_directory[t], list_testname[t] + '_plots.csv')
                                savefig = os.path.join(list_directory[t], list_testname[t] + '_GridPlot.png')
                                names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                                    PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath,
                                                 ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
                                all_phase_data.append(data)
                                valid_phases.append(phase)
                                line = '\nLoaded data for phase: ' + phase
                                print(line)
                            else:
                                line = inputpath + ' does not exist and will not be plotted.'
                                print(line)
                        if len(all_phase_data) > 0:
                            PEMS_PlotTimeSeries_Grid(names, units, all_phase_data, valid_phases, fnames, fcnames, exnames,
                                                     snames, isnames, anames, cnames, [], nnames, tnames, sennames, opsnames, pnames, plotpath, savefig)
                            print('\nGrid plot generated: ' + savefig)
                    except Exception as e:
                        _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '15':  # create custom output table for each test
            if inputmethod == '2':
                error = _run_parallel(_worker_step15, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}")
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test: ' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_AllOutputs.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_CustomCutTable.csv')
                    outputexcel = os.path.join(list_directory[t], list_testname[t] + '_CustomCutTable.xlsx')
                    csvpath = os.path.join(list_directory[t], list_testname[t] + '_CutTableParameters.csv')
                    try:
                        LEMS_CSVFormatted_L1(inputpath, outputpath, outputexcel, csvpath, list_testname[t], logpath)
                    except Exception as e:
                        _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '16':  # compare all outputs - unformatted (L2 step 16)
            print('')
            error = 0
            t = 0
            energyinputpath = []
            emissionsinputpath = []
            allpath = []
            for dic in list_directory:
                allpath.append(os.path.join(dic, list_testname[t] + '_AllOutputs.csv'))
                energyinputpath.append(os.path.join(dic, list_testname[t] + '_EnergyOutputs.csv'))
                emissionsinputpath.append(os.path.join(dic, list_testname[t] + '_EmissionOutputs.csv'))
                t += 1
            outputpath = os.path.join(folder_path, 'UnFormattedDataL2.csv')
            try:
                PEMS_L2(allpath, energyinputpath, emissionsinputpath, outputpath, main_logpath)
            except Exception as e:
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '17':  # compare all outputs - formatted (L2 step 17)
            error = 0
            print('')
            t = 0
            energyinputpath = []
            emissioninputpath = []
            for dic in list_directory:
                energyinputpath.append(os.path.join(dic, list_testname[t] + '_EnergyOutputs.csv'))
                emissioninputpath.append(os.path.join(dic, list_testname[t] + '_EmissionOutputs.csv'))
                t += 1
            outputpath = os.path.join(folder_path, 'FormattedDataL2.csv')
            try:
                LEMS_EnergyCalcs_L2(energyinputpath, emissioninputpath, outputpath, list_testname)
                LEMS_BasicOP_L2(energyinputpath, outputpath)
                LEMS_Emissions_L2(emissioninputpath, outputpath)
            except Exception as e:
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '18':  # compare cut data - unformatted (L2 step 18)
            print('')
            error = 0
            phases = ['L1', 'hp', 'mp', 'lp', 'L5']
            energyinputpath = []
            allpath = []
            for phase in phases:
                emissionsinputpath = []
                for t, dic in enumerate(list_directory):
                    p = os.path.join(dic, list_testname[t] + '_AveragingPeriodAverages_' + phase + '.csv')
                    if os.path.isfile(p):
                        emissionsinputpath.append(p)
                if not emissionsinputpath:
                    line = 'No AveragingPeriodAverages files found for phase ' + phase + ', skipping.'
                    print(line)
                    logs.append(line)
                    continue
                outputpath = os.path.join(folder_path, 'UnFormattedDataL2_' + phase + '.csv')
                try:
                    PEMS_L2(allpath, energyinputpath, emissionsinputpath, outputpath, main_logpath)
                except Exception as e:
                    _log_step_error(var, funs[int(var)-1], f'phase {phase}', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                    error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '19':  # create custom comparison table (L2 step 19)
            print('')
            error = 0
            inputpath = []
            for t, dic in enumerate(list_directory):
                inputpath.append(os.path.join(dic, list_testname[t] + '_AllOutputs.csv'))
            outputpath = os.path.join(folder_path, 'CustomCutTable_L2.csv')
            outputexcel = os.path.join(folder_path, 'CustomCutTable_L2.xlsx')
            csvpath = os.path.join(folder_path, 'CutTableParameters_L2.csv')
            write = 1
            try:
                LEMS_CSVFormatted_L2(inputpath, outputpath, outputexcel, csvpath, main_logpath, write)
            except Exception as e:
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '20':  # compare all outputs (L3)
            print('')
            error = 0
            outputpath = os.path.join(folder_path, 'FormattedDataL3.csv')
            try:
                LEMS_FormatData_L3(list_input_L3, outputpath, main_logpath)
            except Exception as e:  # If error in called functions, return error but don't quit
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '21':  # LP - compare all outputs (L3)
            print('')
            error = 0
            outputpath = os.path.join(folder_path, 'FormattedDataL3_lp.csv')
            try:
                LEMS_FormatData_L3(list_input_LP, outputpath, main_logpath)
            except Exception as e:  # If error in called functions, return error but don't quit
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '22':  # compare all outputs, multi-pair (L3)
            print('')
            error = 0
            outputpath = os.path.join(folder_path, 'PairsFormattedDataL3.csv')
            pair_inputs = os.path.join(folder_path, 'PairsUnformattedDataL2FilePaths.csv')
            try:
                LEMS_FormatData_L3Pairs(pair_inputs, outputpath, main_logpath)
            except Exception as e:  # If error in called functions, return error but don't quit
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '23':  # create custom boxplot (L3)
            print('')
            error = 0
            savefigpath = os.path.join(folder_path, 'L3BoxPlot')
            try:
                LEMS_boxplots(list_input_L3, savefigpath, main_logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '24':  # create multiple boxplots at once (L3)
            print('')
            error = 0
            savefigpath = os.path.join(folder_path, 'L3ScatterPlot')
            parameterpath = os.path.join(folder_path, 'PlotSelection.csv')
            try:
                LEMS_multiboxplots(list_input_L3, parameterpath, savefigpath, main_logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '25':  # create custom bar chart (L3)
            print('')
            error = 0
            savefigpath = os.path.join(folder_path, 'L3BarChart')
            try:
                LEMS_barcharts(list_input_L3, savefigpath, main_logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '26':  # create multiple barcharts at once (L3)
            print('')
            error = 0
            savefigpath = os.path.join(folder_path, 'L3ScatterPlot')
            parameterpath = os.path.join(folder_path, 'PlotSelection.csv')
            try:
                LEMS_multibarcharts(list_input_L3, parameterpath, savefigpath, main_logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '27':  # create custom scatter plot (L3)
            print('')
            error = 0
            savefigpath = os.path.join(folder_path, 'L3ScatterPlot')
            try:
                LEMS_scatterplots(list_input_L3, savefigpath, main_logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '28':  # create multiple scatter plots at once (L3)
            print('')
            error = 0
            savefigpath = os.path.join(folder_path, 'L3ScatterPlot')
            parameterpath = os.path.join(folder_path, 'PlotSelection.csv')

            try:
                LEMS_multiscaterplots(list_input_L3, parameterpath, savefigpath, main_logpath)
            except Exception as e:  # If error in called fuctions, return error but don't quit
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '29':  # create subplots of scatter plots (L3)
            print('')
            error = 0
            savefigpath = os.path.join(folder_path, 'L3SubplotScatterPlot.png')
            parameterpath = os.path.join(folder_path, 'SubplotSelection.csv')

            try:
                LEMS_subplotscatterplot(list_input_L3, parameterpath, savefigpath, main_logpath)
            except Exception as e:  # If error in called functions, return error but don't quit
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '30':  # create custom comparison table (L3)
            print('')
            error = 0
            inputpath = list_input_L3
            outputpath = os.path.join(folder_path, 'CustomCutTable_L3.csv')
            outputexcel = os.path.join(folder_path, 'CustomCutTable_L3.xlsx')
            csvpath = os.path.join(folder_path, 'CutTableParameters_L3.csv')
            write = 1
            try:
                LEMS_CSVFormatted_L3(inputpath, outputpath, outputexcel, csvpath, main_logpath, write)
            except Exception as e:  # If error in called functions, return error but don't quit
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '31':  # create custom comparison table, formatted (L3)
            print('')
            error = 0
            inputpath = os.path.join(folder_path, 'FormattedDataL3.csv')
            inputpath_lp = os.path.join(folder_path, 'FormattedDataL3_lp.csv')
            outputpath = os.path.join(folder_path, 'FormattedCustomCutTable_L3.csv')
            outputexcel = os.path.join(folder_path, 'FormattedCustomCutTable_L3.xlsx')
            csvpath = os.path.join(folder_path, 'FormattedCutTableL3_template_md.xlsx')
            try:
                LEMS_CustomFormatted_L3(inputpath, inputpath_lp, outputpath, outputexcel, csvpath, main_logpath)
            except Exception as e:  # If error in called functions, return error but don't quit
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '32':  # create custom comparison table of pairs, formatted (L3)
            print('')
            error = 0
            inputpath = os.path.join(folder_path, 'PairsFormattedDataL3.csv')
            outputpath = os.path.join(folder_path, 'FormattedCustomCutTable_L3Pairs.csv')
            outputexcel = os.path.join(folder_path, 'FormattedCustomCutTable_L3Pairs.xlsx')
            template = os.path.join(folder_path, 'FormattedCutTableL3Pairs_template.xlsx')
            try:
                LEMS_CustomFormatted_L3Pairs(inputpath, outputpath, outputexcel, template, main_logpath)
            except Exception as e:  # If error in called functions, return error but don't quit
                _log_step_error(var, funs[int(var)-1], 'cross-test', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '33':  # upload processed data (L2 step 20)
            print('')
            error = 0
            compdirectory, folder = os.path.split(folder_path)
            try:
                UploadData(folder_path, folder)
            except Exception as e:
                _log_step_error(var, funs[int(var)-1], 'upload', main_logpath, str(e), traceback.format_exc(), main_logpath, logs)
                error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == 'exit':
            _log_main("Session ended (exit chosen).\n", main_logpath)

        else:
            print(var + ' is not a menu option')