#v0 Python3
#Master program to calculate stove test energy metrics following ISO 19867

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
import sys
if sys.platform == 'darwin':
    try:
        import matplotlib
        matplotlib.use('TkAgg')
    except Exception:
        pass
    try:
        import tkinter
        _tk_root = tkinter.Tk()
        _tk_root.withdraw()
    except Exception:
        pass
else:
    import matplotlib
    matplotlib.use('TkAgg')

import easygui
import pandas as pd
from easygui import *
import os
import csv
import traceback
import datetime
from concurrent.futures import ProcessPoolExecutor

from LEMS_MakeInputFile_EnergyCalcs import LEMS_MakeInputFile_EnergyCalcs
from LEMS_EnergyCalcs import LEMS_EnergyCalcs
from LEMS_EnergyCalcs_L2 import LEMS_EnergyCalcs_L2
from LEMS_BasicOp_L2 import LEMS_BasicOP_L2
from LEMS_Emissions_L2 import LEMS_Emissions_L2
from LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from LEMS_Combined_Scale import LEMS_Combined_Scale
from LEMS_ShiftTimeSeries import LEMS_ShiftTimeSeries
from LEMS_SubtractBkg import LEMS_SubtractBkg
from LEMS_GravCalcs import LEMS_GravCalcs
from LEMS_EmissionCalcs import LEMS_EmissionCalcs
from PEMS_SubtractBkg import PEMS_SubtractBkg
from UploadData import UploadData
from PEMS_Plotter1 import PEMS_Plotter
from LEMS_Scale import LEMS_Scale
from LEMS_Int_Scale import LEMS_Int_Scale
from LEMS_FormattedL1 import LEMS_FormattedL1
from LEMS_CSVFormatted_L2 import LEMS_CSVFormatted_L2
from LEMS_CSVFormatted_L1 import LEMS_CSVFormatted_L1
from LEMS_Nanoscan import LEMS_Nanoscan
from LEMS_TEOM import LEMS_TEOM
from LEMS_Sensirion import LEMS_Senserion
from PEMS_PlotTimeSeries import PEMS_PlotTimeSeries
from PEMS_PlotTimeSeries import PEMS_PlotTimeSeries_Grid
from PEMS_PlotUncertainty import (
    PEMS_PlotUncertainty,
    PEMS_PlotUncertainty_Grid,
    has_uncertainty_columns,
)
from LEMS_Realtime import LEMS_Realtime
from LEMS_TEOM_SubtractBkg import LEMS_TEOM_SubtractBkg
from LEMS_OPS import LEMS_OPS
from LEMS_Pico import LEMS_Pico
from LEMS_CANThermalEfficiency import LEMS_CANThermalEfficiency
from LEMS_Adam_Scale import LEMS_Adam_Scale
from PEMS_L2 import PEMS_L2
from LEMS_customscatterplot import LEMS_customscatterplot
from LEMS_L2_DensityPlot import LEMS_L2_DensityPlot
from LEMS_UpdateUncertainty_L3 import (
    ensure_l3_emission_template,
    ensure_l3_energy_template,
    ensure_l3_grav_template,
    ensure_l3_uc_template,
    load_l3_uc_template,
    load_l3_uncertainty_template,
    update_test_energy_uncertainty,
    update_test_uc_uncertainty,
)

# ==============================================================================
# Helper Functions, Logging, & Multi-Process Workers
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
    """Write message to main L2_log.txt with timestamp."""
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
    """Print exception, log to test log and main L2 log."""
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
    """Update donelist, print status to terminal, and append to log."""
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


def _run_parallel(worker_fn, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=None, step_info="", extra_args=()):
    """Submit worker_fn for every test in parallel. Returns 1 if any error, else 0."""
    args_list = [
        (t, list_directory[t], list_testname[t], list_input[t], inputmethod) + tuple(extra_args)
        for t in range(len(list_directory))
    ]
    error = 0
    if main_logpath and step_info:
        _log_main(f"--- Starting {step_info} in parallel ({len(args_list)} tests, {max_workers} worker(s)) ---", main_logpath)

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        for t_idx, testname, err in pool.map(worker_fn, args_list):
            test_dir = list_directory[t_idx] if t_idx < len(list_directory) else ''
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
        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())


def _read_data_entry_paths_csv(csv_file_path):
    """Read non-empty file paths from DataEntrySheetFilePaths.csv."""
    paths = []
    with open(csv_file_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row and row[0].strip():
                paths.append(row[0].strip().strip('"'))
    return paths


def _discover_data_entry_files(folder_path):
    """Find one data entry file (_DataEntrySheet.xlsx, _DataEntryForm.xlsx, or _EnergyInputs.csv) per test folder."""
    discovered = []
    root_abs = os.path.abspath(folder_path)
    for dirpath, dirnames, filenames in os.walk(folder_path):
        dirnames.sort()
        if os.path.abspath(dirpath) == root_abs:
            continue
        excel_match = None
        csv_match = None
        for filename in sorted(filenames):
            if filename.startswith('~$'):
                continue
            if filename.endswith(('_DataEntrySheet.xlsx', '_DataEntryForm.xlsx')) and excel_match is None:
                excel_match = os.path.join(dirpath, filename)
            elif filename.endswith('_EnergyInputs.csv') and filename != 'L3_EnergyInputs.csv' and csv_match is None:
                csv_match = os.path.join(dirpath, filename)
        chosen = excel_match or csv_match
        if chosen:
            discovered.append(chosen)
    return discovered


def _find_excel_data_entry_sheet(directory, testname):
    """Return path to an Excel data entry sheet in directory if present, else None."""
    if not os.path.isdir(directory):
        return None
    preferred = [
        f"{testname}_DataEntrySheet.xlsx",
        f"{testname}_TE_DataEntryForm.xlsx",
        f"{testname}_DataEntryForm.xlsx",
    ]
    for fname in preferred:
        candidate = os.path.join(directory, fname)
        if os.path.isfile(candidate):
            return candidate
    for fname in sorted(os.listdir(directory)):
        if fname.startswith('~$'):
            continue
        if fname.endswith(('_DataEntrySheet.xlsx', '_DataEntryForm.xlsx')):
            candidate = os.path.join(directory, fname)
            if os.path.isfile(candidate):
                return candidate
    return None


def _resolve_template_dir(directory, folder_path, template_filename):
    """Return directory containing template_filename (L1 test dir -> parent dir -> L2 folder_path)."""
    if directory and os.path.isfile(os.path.join(directory, template_filename)):
        return directory
    parent_dir = os.path.dirname(os.path.normpath(directory)) if directory else None
    if parent_dir and os.path.isfile(os.path.join(parent_dir, template_filename)):
        return parent_dir
    if folder_path and os.path.isdir(folder_path):
        return folder_path
    return parent_dir or directory


def _has_uc_template(path):
    """Return True if path contains L3_UCInputs.csv or a sensorbox-specific L3_UCInputs_*.csv."""
    if not path or not os.path.isdir(path):
        return False
    if os.path.isfile(os.path.join(path, 'L3_UCInputs.csv')):
        return True
    try:
        return any(
            fn.startswith('L3_UCInputs_') and fn.endswith('.csv')
            for fn in os.listdir(path)
        )
    except OSError:
        return False


def _resolve_uc_template_dir(directory, folder_path):
    """Return directory containing UC uncertainty template (L1 test dir -> parent dir -> L2 folder_path)."""
    if _has_uc_template(directory):
        return directory
    parent_dir = os.path.dirname(os.path.normpath(directory)) if directory else None
    if _has_uc_template(parent_dir):
        return parent_dir
    if folder_path and os.path.isdir(folder_path):
        return folder_path
    return parent_dir or directory


def _run_step2_for_test(directory, testname, inputpath_t, logpath, folder_path=None):
    """Run Step 2 for a single test; re-extract from Excel whenever present, else use existing EnergyInputs.csv."""
    outputpath = os.path.join(directory, testname + '_EnergyInputs.csv')
    ext = os.path.splitext(inputpath_t)[1].lower()
    if ext in ('.xlsx', '.xlsm', '.xls'):
        excel_path = inputpath_t if os.path.isfile(inputpath_t) else _find_excel_data_entry_sheet(directory, testname)
    else:
        excel_path = _find_excel_data_entry_sheet(directory, testname)

    if excel_path:
        LEMS_MakeInputFile_EnergyCalcs(excel_path, outputpath, logpath)
    elif os.path.isfile(outputpath):
        msg = f"No Excel data entry sheet found in {directory}; using existing {outputpath}"
        print(msg)
        _log_test(logpath, msg)
    else:
        raise FileNotFoundError(
            f"No Excel data entry sheet or existing {outputpath} found for test {testname}."
        )

    tpl_dir = _resolve_template_dir(directory, folder_path, 'L3_EnergyInputs.csv')
    template_path = ensure_l3_energy_template(tpl_dir, logpath)
    template_uncertainties = load_l3_uncertainty_template(template_path)
    update_test_energy_uncertainty(outputpath, template_uncertainties, logpath)


def _worker_step2(args):
    """Worker for step 2: load energy inputs."""
    t, directory, testname, inputpath_t, inputmethod, *rest = args
    folder_path = rest[0] if rest else None
    logpath = os.path.join(directory, testname + '_log.txt')
    try:
        _run_step2_for_test(directory, testname, inputpath_t, logpath, folder_path=folder_path)
        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())


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

        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())


def _worker_step4(args):
    """Worker for step 4: calculate energy metrics."""
    t, directory, testname, inputpath_t, inputmethod, *rest = args
    folder_path = rest[0] if rest else None
    logpath = os.path.join(directory, testname + '_log.txt')
    inputpath = os.path.join(directory, testname + '_EnergyInputs.csv')
    outputpath = os.path.join(directory, testname + '_EnergyOutputs.csv')
    try:
        tpl_dir = _resolve_template_dir(directory, folder_path, 'L3_EnergyInputs.csv')
        template_path = ensure_l3_energy_template(tpl_dir, logpath)
        template_uncertainties = load_l3_uncertainty_template(template_path)
        update_test_energy_uncertainty(inputpath, template_uncertainties, logpath)
        LEMS_EnergyCalcs(inputpath, outputpath, logpath)
        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())


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
        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())


def _worker_step6(args):
    """Worker for step 6: shift timeseries."""
    t, directory, testname, inputpath_t, inputmethod = args
    logpath = os.path.join(directory, testname + '_log.txt')
    inputpath = os.path.join(directory, testname + '_RawData_Recalibrated.csv')
    outputpath = os.path.join(directory, testname + '_RawData_Shifted.csv')
    timespath = os.path.join(directory, testname + '_TimeShifts.csv')
    try:
        LEMS_ShiftTimeSeries(inputpath, outputpath, timespath, logpath, inputmethod)
        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())


def _worker_step7(args):
    """Worker for step 7: subtract background."""
    import matplotlib
    matplotlib.use('Agg')
    t, directory, testname, inputpath_t, inputmethod, *rest = args
    folder_path = rest[0] if rest else None
    logpath = os.path.join(directory, testname + '_log.txt')
    inputpath = os.path.join(directory, testname + '_RawData_Shifted.csv')
    energyinputpath = os.path.join(directory, testname + '_EnergyInputs.csv')
    ucpath = os.path.join(directory, testname + '_UCInputs.csv')
    sensorpath = os.path.join(directory, testname + '_SensorboxVersion.csv')
    outputpath = os.path.join(directory, testname + '_TimeSeries.csv')
    aveoutputpath = os.path.join(directory, testname + '_Averages.csv')
    timespath = os.path.join(directory, testname + '_PhaseTimes.csv')
    bkgmethodspath = os.path.join(directory, testname + '_BkgMethods.csv')
    savefig1 = os.path.join(directory, testname + '_subtractbkg1.png')
    savefig2 = os.path.join(directory, testname + '_subtractbkg2.png')
    bkgpath = os.path.join(directory, testname + '_BkgOutputs.csv')
    try:
        tpl_dir = _resolve_uc_template_dir(directory, folder_path)
        if tpl_dir == folder_path and os.path.isfile(os.path.join(tpl_dir, 'L3_UCInputs.csv')):
            template_path = os.path.join(tpl_dir, 'L3_UCInputs.csv')
        else:
            template_path = ensure_l3_uc_template(tpl_dir, list_raw_shifted_paths=[inputpath, ucpath], logpath=logpath)
        template_uc = load_l3_uc_template(template_path)
        update_test_uc_uncertainty(ucpath, inputpath, template_uc, logpath=logpath, folder_path=tpl_dir, sensor_version_path=sensorpath)
        PEMS_SubtractBkg(inputpath, energyinputpath, ucpath, outputpath, aveoutputpath, timespath,
                         bkgmethodspath, logpath, savefig1, savefig2, inputmethod, bkgpath)
        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())


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
        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())


def _worker_step9(args):
    """Worker for step 9: calculate gravimetric PM."""
    t, directory, testname, inputpath_t, inputmethod, *rest = args
    folder_path = rest[0] if rest else None
    logpath = os.path.join(directory, testname + '_log.txt')
    gravinputpath = os.path.join(directory, testname + '_GravInputs.csv')
    aveinputpath = os.path.join(directory, testname + '_Averages.csv')
    timespath = os.path.join(directory, testname + '_PhaseTimes.csv')
    gravoutputpath = os.path.join(directory, testname + '_GravOutputs.csv')
    energypath = os.path.join(directory, testname + '_EnergyOutputs.csv')
    try:
        tpl_dir = _resolve_template_dir(directory, folder_path, 'L3_GravInputs.csv')
        LEMS_GravCalcs(gravinputpath, aveinputpath, timespath, energypath, gravoutputpath, logpath, inputmethod, uncertainty_template_dir=tpl_dir)
        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())


def _worker_step10(args):
    """Worker for step 10: calculate emission metrics."""
    t, directory, testname, inputpath_t, inputmethod, *rest = args
    recalculate_timeseries = rest[0] if rest else True
    folder_path = rest[1] if len(rest) > 1 else None
    write_timeseries_uncertainty = rest[2] if len(rest) > 2 else False
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
    ucpath = os.path.join(directory, testname + '_UCInputs.csv')
    try:
        tpl_dir = _resolve_template_dir(directory, folder_path, 'L3_EmissionInputs.csv')
        LEMS_EmissionCalcs(inputpath, energypath, gravinputpath, aveinputpath, emisoutputpath, alloutputpath,
                           logpath, timespath, sensorpath, fuelpath, fuelmetricpath, exactpath, scalepath,
                           intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath,
                           emissioninputpath, inputmethod, bcpath, qualitypath, bkgpath,
                           recalculate_timeseries=recalculate_timeseries,
                           uncertainty_template_dir=tpl_dir,
                           ucpath=ucpath,
                           write_timeseries_uncertainty=write_timeseries_uncertainty)
        LEMS_FormattedL1(alloutputpath, cutoutputpath, outputexcel, testname, logpath)
        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())


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
        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())


def _worker_step12(args):
    """Worker for step 12: cut period / realtime averages across all phases."""
    import matplotlib
    matplotlib.use('Agg')
    t, directory, testname, inputpath_t, inputmethod, *rest = args
    write_timeseries_uncertainty = rest[0] if rest else False
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
    ucpath = os.path.join(directory, testname + '_UCInputs.csv')
    emissioninputpath = os.path.join(directory, testname + '_EmissionInputs.csv')

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
                              scalepath, intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath,
                              ucpath=ucpath, emissioninputpath=emissioninputpath,
                              write_timeseries_uncertainty=write_timeseries_uncertainty)
        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())


def _worker_step13(args):
    """Worker for step 13: plot processed data across phases."""
    import matplotlib
    matplotlib.use('Agg')
    t, directory, testname, inputpath_t, inputmethod, *rest = args
    write_timeseries_uncertainty = rest[0] if rest else False
    logpath = os.path.join(directory, testname + '_log.txt')
    fuelpath = os.path.join(directory, testname + '_null.csv')
    exactpath = os.path.join(directory, testname + '_null.csv')
    fuelmetricpath = os.path.join(directory, testname + '_null.csv')
    scalepath = os.path.join(directory, testname + '_FormattedScaleData.csv')
    intscalepath = os.path.join(directory, testname + '_FormattedIntScaleData.csv')
    ascalepath = os.path.join(directory, testname + '_FormattedAdamScaleData.csv')
    cscalepath = os.path.join(directory, testname + '_FormattedCombinedScaleData.csv')
    mscalepath = os.path.join(directory, testname + '_FormattedMTScaleData.csv')
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
                names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, mnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                    PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath, ascalepath, cscalepath, mscalepath,
                                 nanopath, TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
                if write_timeseries_uncertainty and has_uncertainty_columns(inputpath):
                    PEMS_PlotUncertainty(names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, mnames, nnames, tnames, sennames, opsnames, pnames,
                                         plotpath, savefig)
                else:
                    PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, mnames, nnames, tnames, sennames, opsnames, pnames,
                                        plotpath, savefig)
        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())


def _worker_step14(args):
    """Worker for step 14: plot processed data subplots."""
    import matplotlib
    matplotlib.use('Agg')
    t, directory, testname, inputpath_t, inputmethod, *rest = args
    write_timeseries_uncertainty = rest[0] if rest else False
    logpath = os.path.join(directory, testname + '_log.txt')
    fuelpath = os.path.join(directory, testname + '_null.csv')
    exactpath = os.path.join(directory, testname + '_null.csv')
    fuelmetricpath = os.path.join(directory, testname + '_null.csv')
    scalepath = os.path.join(directory, testname + '_FormattedScaleData.csv')
    intscalepath = os.path.join(directory, testname + '_FormattedIntScaleData.csv')
    ascalepath = os.path.join(directory, testname + '_FormattedAdamScaleData.csv')
    cscalepath = os.path.join(directory, testname + '_FormattedCombinedScaleData.csv')
    mscalepath = os.path.join(directory, testname + '_FormattedMTScaleData.csv')
    nanopath = os.path.join(directory, testname + '_FormattedNanoscanData.csv')
    TEOMpath = os.path.join(directory, testname + '_FormattedTEOMData.csv')
    senserionpath = os.path.join(directory, testname + '_FormattedSenserionData.csv')
    OPSpath = os.path.join(directory, testname + '_FormattedOPSData.csv')
    Picopath = os.path.join(directory, testname + '_FormattedPicoData.csv')
    all_phase_data = []
    valid_phases = []
    valid_inputpaths = []
    choices = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']
    try:
        names = units = fnames = fcnames = exnames = snames = isnames = anames = cnames = mnames = nnames = tnames = sennames = opsnames = pnames = plotpath = savefig = None
        for phase in choices:
            inputpath = os.path.join(directory, testname + '_TimeSeriesMetrics_' + phase + '.csv')
            if os.path.isfile(inputpath):
                plotpath = os.path.join(directory, testname + '_plots.csv')
                savefig = os.path.join(directory, testname + '_GridPlot.png')
                names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, mnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                    PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath,
                                 ascalepath, cscalepath, mscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
                all_phase_data.append(data)
                valid_phases.append(phase)
                valid_inputpaths.append(inputpath)
        if len(all_phase_data) > 0:
            if write_timeseries_uncertainty and all(has_uncertainty_columns(p) for p in valid_inputpaths):
                PEMS_PlotUncertainty_Grid(names, units, all_phase_data, valid_phases, fnames, fcnames, exnames,
                                          snames, isnames, anames, cnames, mnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig)
            else:
                PEMS_PlotTimeSeries_Grid(names, units, all_phase_data, valid_phases, fnames, fcnames, exnames,
                                         snames, isnames, anames, cnames, mnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig)
        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())


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
        return (t, testname, None)
    except Exception:
        return (t, testname, traceback.format_exc())

# ==============================================================================

if __name__ == '__main__':
    logs = []

    # Setting up lists to record the files
    list_input = []
    list_filename = []
    list_directory = []
    list_testname = []
    list_logname = []
    button2 = 'No'
    output = button2
    folder_path = None
    datadirectory = None

    inputmode = input("Enter cli for command line interface or default to graphical user interface.\n")
    if inputmode == "cli":
        # Prompt user for folder path
        folder_path = input("Enter folder path: ")

        # Initialize list to store file paths
        list_input = []

        # Check if DataEntrySheetFilePaths.csv already exists in main folder
        csv_file_path = os.path.join(folder_path, 'DataEntrySheetFilePaths.csv')
        if os.path.exists(csv_file_path):
            # If the CSV file exists, read in the file paths
            list_input = _read_data_entry_paths_csv(csv_file_path)

            # Print the existing file paths and prompt the user to edit if desired
            print("DataEntrySheetFilePaths.csv exists in main folder")
            print("Existing data entry sheets found in DataEntrySheetFilePaths.csv:")
            for path in list_input:
                print(path)
            edit_csv = input("Run all tests listed? (y/n): ")
            if edit_csv.lower() == 'n':
                input("Edit DataEntrySheetFilePaths.csv in main folder and save. Press enter when done.")
                # Read in the updated file paths
                list_input = _read_data_entry_paths_csv(csv_file_path)
        else:
            print("DataEntrySheetFilePaths.csv file not found. A new CSV file will be created.")
            list_input = _discover_data_entry_files(folder_path)
            print("Data entry files found:")
            for path in list_input:
                print(path)
            edit_csv = input("Run all tests listed? (y/n): ")
            # Write file paths to csv in main folder
            with open(csv_file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for file_path in list_input:
                    writer.writerow([file_path])
            if edit_csv.lower() == 'n':
                input("Edit DataEntrySheetFilePaths.csv in main folder and save. Press enter when done.")
                # Read in the updated file paths
                list_input = _read_data_entry_paths_csv(csv_file_path)

        # Setting up lists to record the files
        logs = []
        list_filename = []
        list_directory = []
        list_testname = []
        list_logname = []

        for i, inputpath in enumerate(list_input):
            directory, filename = os.path.split(os.path.normpath(inputpath))
            datadirectory, testname = os.path.split(directory)
            logname = testname + '_log.txt'
            list_filename.append(filename)
            list_directory.append(directory)
            list_testname.append(testname)
            list_logname.append(logname)

    else:
        # Prompt user to enter number of test runs done
        text = "Enter number of test runs"
        title = "gitrdone"
        d_int = 1
        lower = 0
        upper = 999
        testnum = integerbox(text, title, d_int, lower, upper)
        title = "gitrdone"
        message = "Entered Number : " + str(testnum)
        msg = msgbox(message, title)

        for x in range(testnum if testnum else 0):
            line = 'Select Data Entry Form for Test ' + str(x) + ':'
            print(line)

            inputpath = easygui.fileopenbox()
            if not inputpath:
                continue
            directory, filename = os.path.split(inputpath)
            datadirectory, testname = os.path.split(directory)
            logname = testname + '_log.txt'
            list_input.append(inputpath)
            print(list_input[-1])
            list_filename.append(filename)
            list_directory.append(directory)
            list_testname.append(testname)
            list_logname.append(logname)

        if datadirectory and not folder_path:
            folder_path = datadirectory

    main_logpath = os.path.join(folder_path, 'L2_log.txt') if folder_path else None

    # Run option menu to make output files for each test
    funs = ['plot raw data',
            'load data entry form',
            'load additional raw data files (heating stoves only)',
            'calculate energy metrics',
            'adjust sensor calibrations',
            'correct for response times',
            'subtract background',
            'cut TEOM realtime data based on phases',
            'calculate gravimetric PM',
            'calculate emission metrics',
            'calculate efficiency metrics',
            'calculate averages from a specified cut period',
            'plot processed data',
            'plot processed data subplots',
            'create custom output table for each test',
            'create scatter plot of 2 variables for each test',
            'compare processed data (unformatted)',
            'compare processed data (formatted)',
            'compare cut data (unformatted)',
            'create custom comparison table',
            'create stacked density plot of 2 variables',
            'upload processed data (optional)']

    donelist = [''] * len(funs)

    #######################################################
    inputmethod = input('Enter 1 for interactive mode (sequential, for first run and changing variables). \n'
                        'Enter 2 for reprocessing mode (multi-process parallel, for reprocessing data with variables already set). \n')

    if inputmethod == '1':
        line = 'Interactive mode selected - enter variables when prompted'
        print(line)
        logs.append(line)
        max_workers = 1
        recalculate_timeseries = True
    elif inputmethod == '2':
        line = 'Reprocessing mode selected - previously entered variables will be used'
        print(line)
        logs.append(line)
        _default_workers = max(1, (os.cpu_count() or 2) // 2)
        _w = input(f'Enter number of parallel workers [default {_default_workers}]: ').strip()
        max_workers = int(_w) if _w.isdigit() and int(_w) > 0 else _default_workers
        line = f'Parallel reprocessing mode enabled with {max_workers} worker(s)'
        print(line)
        logs.append(line)

        _ts = input(
            'Skip time-series recalculation and read EmissionOutputs.csv instead?\n'
            '  (Faster — use when only IDC totals or AllOutputs need updating)\n'
            'Enter y to skip recalculation, press Enter to recalculate [N]: '
        ).strip().lower()
        recalculate_timeseries = (_ts != 'y')
        line = ('Read mode: time-series recalculation SKIPPED (reading pre-existing EmissionOutputs.csv)'
                if not recalculate_timeseries
                else 'Full mode: time-series will be recalculated')
        print(line)
        logs.append(line)
    else:
        inputmethod = '1'
        line = "Entered variable doesn't exist, defaulting to interactive mode"
        print(line)
        logs.append(line)
        max_workers = 1
        recalculate_timeseries = True

    _uc_ts = input(
        'Write and plot real-time time-series uncertainties?\n'
        '  (Adds *_uc columns to TimeSeriesMetrics & AveragingPeriodTimeSeries CSVs and plots +/- UC bands)\n'
        'Enter y to enable, press Enter to disable [N]: '
    ).strip().lower()
    write_timeseries_uncertainty = (_uc_ts == 'y')
    line = f"Time-series uncertainty output/plotting: {'ENABLED' if write_timeseries_uncertainty else 'DISABLED'}"
    print(line)
    logs.append(line)

    if main_logpath:
        _log_main("=" * 60, main_logpath)
        _log_main(f"Session started. Loaded {len(list_input)} test(s). Mode: {'Reprocessing (parallel)' if inputmethod == '2' else 'Interactive (sequential)'}, Workers: {max_workers}", main_logpath)
        _log_main("=" * 60, main_logpath)
    #######################################################

    line = '\nLEMSDataCruncher_ISO_v0.0\n'
    print(line)
    logs.append(line)

    var = 'unicorn'
    while var != 'exit':
        print('')
        print('----------------------------------------------------')
        print(f"Time-series uncertainty output/plotting: {'ON' if write_timeseries_uncertainty else 'OFF'}")
        print('Data processing steps:')
        print('')
        for num, fun in enumerate(funs):
            print(donelist[num] + str(num + 1) + ' : ' + fun)
        print(f"u : toggle time-series uncertainty output/plotting (currently {'ON' if write_timeseries_uncertainty else 'OFF'})")
        print('exit : exit program')
        print('')
        var = input("Enter menu option: ")

        if var == '1':  # plot raw data
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
                if folder_path and any(_resolve_template_dir(d, folder_path, 'L3_EnergyInputs.csv') == folder_path for d in list_directory):
                    ensure_l3_energy_template(folder_path, main_logpath)
                error = _run_parallel(_worker_step2, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}", extra_args=(folder_path,))
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test:' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    try:
                        _run_step2_for_test(list_directory[t], list_testname[t], list_input[t], logpath, folder_path=folder_path)
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

                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_SenserionRawData.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedSenserionData.csv')
                    senpath = os.path.join(list_directory[t], list_testname[t] + '_SenserionInputs.csv')
                    try:
                        LEMS_Senserion(inputpath, outputpath, senpath, logpath, inputmethod)
                        line = '\nloaded and processed Sensirion data'
                        print(line)
                        logs.append(line)
                    except Exception as e:
                        line = "Data file: " + inputpath + " doesn't exist and will not be processed."
                        print(line)
                        logs.append(line)

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
                        try:
                            LEMS_Combined_Scale(scale_path, adam_scale_path, out_path, logpath)
                        except Exception:
                            pass
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '4':  # calculate energy metrics
            if inputmethod == '2':
                if folder_path and any(_resolve_template_dir(d, folder_path, 'L3_EnergyInputs.csv') == folder_path for d in list_directory):
                    ensure_l3_energy_template(folder_path, main_logpath)
                error = _run_parallel(_worker_step4, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}", extra_args=(folder_path,))
            else:
                error = 0
                for t in range(len(list_input)):
                    print('')
                    print('Test: ' + list_directory[t])
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    inputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyInputs.csv')
                    outputpath = os.path.join(list_directory[t], list_testname[t] + '_EnergyOutputs.csv')
                    try:
                        tpl_dir = _resolve_template_dir(list_directory[t], folder_path, 'L3_EnergyInputs.csv')
                        tpl_path = ensure_l3_energy_template(tpl_dir, logpath)
                        template_unc = load_l3_uncertainty_template(tpl_path)
                        update_test_energy_uncertainty(inputpath, template_unc, logpath)
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
            uc_folder_raw = [
                os.path.join(list_directory[t], list_testname[t] + '_RawData_Shifted.csv')
                for t in range(len(list_input))
                if _resolve_uc_template_dir(list_directory[t], folder_path) == folder_path
            ]
            if folder_path and uc_folder_raw:
                ensure_l3_uc_template(folder_path, list_raw_shifted_paths=uc_folder_raw, logpath=main_logpath)
            if inputmethod == '2':
                error = _run_parallel(_worker_step7, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}", extra_args=(folder_path,))
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
                    sensorpath = os.path.join(list_directory[t], list_testname[t] + '_SensorboxVersion.csv')
                    try:
                        tpl_dir = _resolve_uc_template_dir(list_directory[t], folder_path)
                        uc_tpl_path = ensure_l3_uc_template(tpl_dir, list_raw_shifted_paths=[inputpath], logpath=logpath)
                        template_uc = load_l3_uc_template(uc_tpl_path)
                        update_test_uc_uncertainty(ucpath, inputpath, template_uc, logpath=logpath, folder_path=tpl_dir, sensor_version_path=sensorpath)
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
                if folder_path and any(_resolve_template_dir(d, folder_path, 'L3_GravInputs.csv') == folder_path for d in list_directory):
                    ensure_l3_grav_template(folder_path, main_logpath)
                error = _run_parallel(_worker_step9, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}", extra_args=(folder_path,))
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
                        tpl_dir = _resolve_template_dir(list_directory[t], folder_path, 'L3_GravInputs.csv')
                        LEMS_GravCalcs(gravinputpath, aveinputpath, timespath, energypath, gravoutputpath, logpath, inputmethod, uncertainty_template_dir=tpl_dir)
                    except Exception as e:
                        _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '10':  # calculate emissions metrics
            if inputmethod == '2':
                if folder_path and any(_resolve_template_dir(d, folder_path, 'L3_EmissionInputs.csv') == folder_path for d in list_directory):
                    ensure_l3_emission_template(folder_path, main_logpath)
                error = _run_parallel(_worker_step10, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}", extra_args=(recalculate_timeseries, folder_path, write_timeseries_uncertainty))
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
                    ucpath = os.path.join(list_directory[t], list_testname[t] + '_UCInputs.csv')
                    try:
                        tpl_dir = _resolve_template_dir(list_directory[t], folder_path, 'L3_EmissionInputs.csv')
                        LEMS_EmissionCalcs(inputpath, energypath, gravinputpath, aveinputpath, emisoutputpath, alloutputpath,
                                           logpath, timespath, sensorpath, fuelpath, fuelmetricpath, exactpath, scalepath,
                                           intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath,
                                           emissioninputpath, inputmethod, bcpath, qualitypath, bkgpath,
                                           recalculate_timeseries=recalculate_timeseries,
                                           uncertainty_template_dir=tpl_dir,
                                           ucpath=ucpath,
                                           write_timeseries_uncertainty=write_timeseries_uncertainty)
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
                error = _run_parallel(_worker_step12, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}", extra_args=(write_timeseries_uncertainty,))
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
                    ucpath = os.path.join(list_directory[t], list_testname[t] + '_UCInputs.csv')
                    emissioninputpath = os.path.join(list_directory[t], list_testname[t] + '_EmissionInputs.csv')

                    if inputmethod == '1':
                        message = 'Select which phases will be graphed'
                        title = 'Gitrdun'
                        phases = ['L1', 'hp', 'mp', 'lp', 'L5']
                        choice = choicebox(message, title, phases)
                        if choice is None:
                            continue
                        inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + choice + '.csv')
                        periodpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriod_' + choice + '.csv')
                        outputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodTimeSeries_' + choice + '.csv')
                        averageoutputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodAverages_' + choice + '.csv')
                        if os.path.isfile(inputpath):
                            try:
                                LEMS_Realtime(inputpath, energypath, gravpath, phasepath, periodpath, outputpath, averageoutputpath,
                                              savefig, choice, logpath, inputmethod, fuelpath, fuelmetricpath, exactpath,
                                              scalepath, intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath,
                                              ucpath=ucpath, emissioninputpath=emissioninputpath,
                                              write_timeseries_uncertainty=write_timeseries_uncertainty)
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
                                                  scalepath, intscalepath, ascalepath, cscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath,
                                                  ucpath=ucpath, emissioninputpath=emissioninputpath,
                                                  write_timeseries_uncertainty=write_timeseries_uncertainty)
                                except Exception as e:
                                    _log_step_error(var, funs[int(var)-1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                                    error = 1
                            else:
                                line = inputpath + ' does not exist'
                                print(line)
            _finish_step(donelist, var, funs, error, main_logpath, logs)

        elif var == '13':  # plot processed data
            if inputmethod == '2':
                error = _run_parallel(_worker_step13, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}", extra_args=(write_timeseries_uncertainty,))
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
                    mscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedMTScaleData.csv')
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
                        for phase in (choices or []):
                            inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + phase + '.csv')
                            if os.path.isfile(inputpath):
                                plotpath = os.path.join(list_directory[t], list_testname[t] + '_plots_' + phase + '.csv')
                                savefig = os.path.join(list_directory[t], list_testname[t] + '_plot_' + phase + '.png')
                                names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, mnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                                    PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath, ascalepath, cscalepath, mscalepath,
                                                 nanopath, TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
                                if write_timeseries_uncertainty and has_uncertainty_columns(inputpath):
                                    PEMS_PlotUncertainty(names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, mnames, nnames, tnames, sennames, opsnames, pnames,
                                                         plotpath, savefig)
                                else:
                                    if write_timeseries_uncertainty:
                                        print('No _uc columns found in ' + inputpath + '; plotting standard time series.')
                                    PEMS_PlotTimeSeries(names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, mnames, nnames, tnames, sennames, opsnames, pnames,
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
                error = _run_parallel(_worker_step14, list_directory, list_testname, list_input, inputmethod, max_workers, main_logpath=main_logpath, step_info=f"step {var}: {funs[int(var)-1]}", extra_args=(write_timeseries_uncertainty,))
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
                    mscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedMTScaleData.csv')
                    nanopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedNanoscanData.csv')
                    TEOMpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
                    senserionpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedSenserionData.csv')
                    OPSpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
                    Picopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedPicoData.csv')
                    all_phase_data = []
                    valid_phases = []
                    valid_inputpaths = []
                    if inputmethod == '1':
                        message = 'Select which phases will be graphed'
                        title = 'Gitrdun'
                        phases_list = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']
                        choices = multchoicebox(message, title, phases_list)
                    else:
                        choices = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']
                    try:
                        for phase in (choices or []):
                            inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + phase + '.csv')
                            if os.path.isfile(inputpath):
                                plotpath = os.path.join(list_directory[t], list_testname[t] + '_plots.csv')
                                savefig = os.path.join(list_directory[t], list_testname[t] + '_GridPlot.png')
                                names, units, data, fnames, fcnames, exnames, snames, isnames, anames, cnames, mnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig = \
                                    PEMS_Plotter(inputpath, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath,
                                                 ascalepath, cscalepath, mscalepath, nanopath, TEOMpath, senserionpath, OPSpath, Picopath, plotpath, savefig, logpath)
                                all_phase_data.append(data)
                                valid_phases.append(phase)
                                valid_inputpaths.append(inputpath)
                                line = '\nLoaded data for phase: ' + phase
                                print(line)
                            else:
                                line = inputpath + ' does not exist and will not be plotted.'
                                print(line)
                        if len(all_phase_data) > 0:
                            if write_timeseries_uncertainty and all(has_uncertainty_columns(p) for p in valid_inputpaths):
                                PEMS_PlotUncertainty_Grid(names, units, all_phase_data, valid_phases, fnames, fcnames, exnames,
                                                          snames, isnames, anames, cnames, mnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig)
                            else:
                                if write_timeseries_uncertainty:
                                    print('No _uc columns found in one or more phase files; plotting standard time series grid.')
                                PEMS_PlotTimeSeries_Grid(names, units, all_phase_data, valid_phases, fnames, fcnames, exnames,
                                                         snames, isnames, anames, cnames, mnames, nnames, tnames, sennames, opsnames, pnames, plotpath, savefig)
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

        elif var == '16':  # create scatter plot of 2 variables for each test
            print('')
            error = 0
            message = 'Select which phases will be graphed. To look at the cut period of the phase also select cut period'
            title = 'Gitrdun'
            phases = ['L1', 'hp', 'mp', 'lp', 'L5', 'full', 'cut period']
            choices = multchoicebox(message, title, phases)

            if choices:
                is_cut = 'cut period' in choices
                active_phases = [p for p in choices if p != 'cut period']
                if not active_phases:
                    active_phases = ['hp']

                selected_x = None
                selected_y = None

                for t in range(len(list_input)):
                    print('')
                    print(f'Test: {list_directory[t]} ({t + 1}/{len(list_input)})')
                    logpath = os.path.join(list_directory[t], list_testname[t] + '_log.txt')
                    fuelpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedFuelData.csv')
                    exactpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedExactData.csv')
                    scalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedScaleData.csv')
                    intscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedIntScaleData.csv')
                    ascalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedAdamScaleData.csv')
                    cscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedCombinedScaleData.csv')
                    nanopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedNanoscanData.csv')
                    TEOMpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedTEOMData.csv')
                    senserionpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedSenserionData.csv')
                    OPSpath = os.path.join(list_directory[t], list_testname[t] + '_FormattedOPSData.csv')
                    Picopath = os.path.join(list_directory[t], list_testname[t] + '_FormattedPicoData.csv')
                    regressionpath = os.path.join(list_directory[t], list_testname[t] + '_Regressions.csv')
                    mscalepath = os.path.join(list_directory[t], list_testname[t] + '_FormattedMTScaleData.csv')

                    try:
                        for phase in active_phases:
                            if is_cut:
                                savefigpath = os.path.join(list_directory[t], list_testname[t] + '_cut')
                                inputpath = os.path.join(list_directory[t], list_testname[t] + '_AveragingPeriodTimeSeries_' + phase + '.csv')
                            else:
                                savefigpath = os.path.join(list_directory[t], list_testname[t])
                                inputpath = os.path.join(list_directory[t], list_testname[t] + '_TimeSeriesMetrics_' + phase + '.csv')

                            if os.path.isfile(inputpath):
                                ret_x, ret_y, figpath = LEMS_customscatterplot(
                                    inputpath, fuelpath, exactpath, scalepath, intscalepath,
                                    ascalepath, cscalepath, mscalepath, nanopath,
                                    TEOMpath, senserionpath, OPSpath, Picopath,
                                    regressionpath, phase, savefigpath, logpath,
                                    selected_X_variable=selected_x,
                                    selected_Y_variable=selected_y,
                                    testname=list_testname[t]
                                )
                                # Reuse selected variables across all remaining tests/phases
                                if ret_x is not None and selected_x is None:
                                    selected_x = ret_x
                                if ret_y is not None and selected_y is None:
                                    selected_y = ret_y
                            else:
                                line = f'{phase} data does not exist for {list_testname[t]} and will not be plotted.'
                                print(line)
                                logs.append(line)
                    except Exception as e:
                        _log_step_error(var, funs[int(var) - 1], list_testname[t], logpath, str(e), traceback.format_exc(), main_logpath, logs)
                        error = 1
                _finish_step(donelist, var, funs, error, main_logpath, logs)
            else:
                line = 'No phases selected; scatter plot cancelled.'
                print(line)
                logs.append(line)

        elif var == '17':  # Compare data (unformatted)
            print('')
            energyinputpath = []
            emissionsinputpath = []
            allpath = []
            for t_idx, dic in enumerate(list_directory):
                allpath.append(os.path.join(dic, list_testname[t_idx] + '_AllOutputs.csv'))
                energyinputpath.append(os.path.join(dic, list_testname[t_idx] + '_EnergyOutputs.csv'))
                emissionsinputpath.append(os.path.join(dic, list_testname[t_idx] + '_EmissionOutputs.csv'))
            target_dir = folder_path if folder_path else (datadirectory if datadirectory else (list_directory[0] if list_directory else '.'))
            outputpath = os.path.join(target_dir, 'UnFormattedDataL2.csv')
            logpath = main_logpath or os.path.join(target_dir, 'L2_log.txt')
            try:
                PEMS_L2(allpath, energyinputpath, emissionsinputpath, outputpath, logpath)
                updatedonelist(donelist, var)
                line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
                print(line)
                logs.append(line)
                _log_main(line.strip(), main_logpath)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                _log_main(f"ERROR in step {var}: {e}\n{traceback.format_exc()}", main_logpath)
                updatedonelisterror(donelist, var)

        elif var == '18':  # Compare data (formatted)
            print('')
            energyinputpath = []
            emissioninputpath = []
            for t_idx, dic in enumerate(list_directory):
                energyinputpath.append(os.path.join(dic, list_testname[t_idx] + '_EnergyOutputs.csv'))
                emissioninputpath.append(os.path.join(dic, list_testname[t_idx] + '_EmissionOutputs.csv'))
            target_dir = folder_path if folder_path else (datadirectory if datadirectory else (list_directory[0] if list_directory else '.'))
            outputpath = os.path.join(target_dir, 'FormattedDataL2.csv')
            try:
                LEMS_EnergyCalcs_L2(energyinputpath, emissioninputpath, outputpath, list_testname)
                LEMS_BasicOP_L2(energyinputpath, outputpath)
                LEMS_Emissions_L2(emissioninputpath, outputpath)
                updatedonelist(donelist, var)
                line = '\nstep ' + var + ' done, back to main menu'
                print(line)
                logs.append(line)
                _log_main(line.strip(), main_logpath)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                _log_main(f"ERROR in step {var}: {e}\n{traceback.format_exc()}", main_logpath)
                updatedonelisterror(donelist, var)

        elif var == '19':  # Compare cut data (unformatted)
            print('')
            error = 0
            phases = ['L1', 'hp', 'mp', 'lp', 'L5']
            energyinputpath = []
            allpath = []
            target_dir = folder_path if folder_path else (datadirectory if datadirectory else (list_directory[0] if list_directory else '.'))
            logpath = main_logpath or os.path.join(target_dir, 'L2_log.txt')

            for phase in phases:
                emissionsinputpath = []
                for t_idx, dic in enumerate(list_directory):
                    p = os.path.join(dic, list_testname[t_idx] + '_AveragingPeriodAverages_' + phase + '.csv')
                    if os.path.isfile(p):
                        emissionsinputpath.append(p)
                if not emissionsinputpath:
                    line = 'No AveragingPeriodAverages files found for phase ' + phase + ', skipping.'
                    print(line)
                    logs.append(line)
                    continue
                outputpath = os.path.join(target_dir, 'UnFormattedDataL2_' + phase + '.csv')
                try:
                    PEMS_L2(allpath, energyinputpath, emissionsinputpath, outputpath, logpath)
                except Exception as e:
                    line = 'Error: ' + str(e)
                    print(line)
                    traceback.print_exception(type(e), e, e.__traceback__)
                    logs.append(line)
                    _log_main(f"ERROR in step {var} (phase {phase}): {e}\n{traceback.format_exc()}", main_logpath)
                    error = 1

            if error == 1:
                updatedonelisterror(donelist, var)
            else:
                updatedonelist(donelist, var)
                line = '\nstep ' + var + ': ' + funs[int(var) - 1] + ' done, back to main menu'
                print(line)
                logs.append(line)
                _log_main(line.strip(), main_logpath)

        elif var == '20':  # create custom comparison table
            print('')
            inputpath = []
            for t_idx, dic in enumerate(list_directory):
                inputpath.append(os.path.join(dic, list_testname[t_idx] + '_AllOutputs.csv'))
            target_dir = folder_path if folder_path else (datadirectory if datadirectory else (list_directory[0] if list_directory else '.'))
            outputpath = os.path.join(target_dir, 'CustomCutTable_L2.csv')
            outputexcel = os.path.join(target_dir, 'CustomCutTable_L2.xlsx')
            csvpath = os.path.join(target_dir, 'CutTableParameters_L2.csv')
            logpath = main_logpath or os.path.join(target_dir, 'L2_log.txt')
            write = 1
            try:
                LEMS_CSVFormatted_L2(inputpath, outputpath, outputexcel, csvpath, logpath, write)
                updatedonelist(donelist, var)
                line = '\nstep ' + var + ' done, back to main menu'
                print(line)
                logs.append(line)
                _log_main(line.strip(), main_logpath)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                _log_main(f"ERROR in step {var}: {e}\n{traceback.format_exc()}", main_logpath)
                updatedonelisterror(donelist, var)

        elif var == '21':  # create stacked density plot of 2 variables
            print('')
            target_dir = folder_path if folder_path else (datadirectory if datadirectory else (list_directory[0] if list_directory else '.'))
            logpath = main_logpath or os.path.join(target_dir, 'L2_log.txt')
            try:
                LEMS_L2_DensityPlot(list_directory, list_testname, target_dir, logpath, inputmethod)
                updatedonelist(donelist, var)
                line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
                print(line)
                logs.append(line)
                _log_main(line.strip(), main_logpath)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                _log_main(f"ERROR in step {var}: {e}\n{traceback.format_exc()}", main_logpath)
                updatedonelisterror(donelist, var)

        elif var == '22':  # upload data
            print('')
            target_dir = folder_path if folder_path else (datadirectory if datadirectory else (list_directory[0] if list_directory else '.'))
            compdirectory, folder = os.path.split(target_dir)
            try:
                UploadData(target_dir, folder)
                updatedonelist(donelist, var)
                line = '\nstep ' + var + ': ' + funs[int(var)-1] + ' done, back to main menu'
                print(line)
                logs.append(line)
                _log_main(line.strip(), main_logpath)
            except Exception as e:
                line = 'Error: ' + str(e)
                print(line)
                traceback.print_exception(type(e), e, e.__traceback__)
                logs.append(line)
                _log_main(f"ERROR in step {var}: {e}\n{traceback.format_exc()}", main_logpath)
                updatedonelisterror(donelist, var)

        elif var.lower() == 'u':
            write_timeseries_uncertainty = not write_timeseries_uncertainty
            line = f"Time-series uncertainty output/plotting toggled {'ON' if write_timeseries_uncertainty else 'OFF'}"
            print(line)
            logs.append(line)

        elif var == 'exit':
            pass

        else:
            print(var + ' is not a menu option')
