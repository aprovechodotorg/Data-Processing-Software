#v0.4  Python3

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


import os
import csv
import numpy as np
import math
from uncertainties import ufloat, unumpy, umath
import matplotlib
if matplotlib.get_backend().lower() != 'agg' and not os.environ.get('MPLBACKEND'):
    try:
        matplotlib.use('TkAgg')
    except Exception:
        pass
import matplotlib.pyplot as plt
import easygui
from datetime import datetime as dt, timedelta
import LEMS_DataProcessing_IO as io
import PEMS_SubtractBkg as bkg

########### inputs (only used if this script is run as executable) #############
#Copy and paste input paths with shown ending to run this function individually. Otherwise, use DataCruncher
inputpath='TimeSeriesMetrics.csv'
energypath='EnergyOutputs.csv'
graninputpath = 'GravOutputs.csv'
empath = 'EmissionOutputs.csv'
periodpath = 'AveragingPeriod.csv'
outputpath = 'RealtimeOutputs.csv'
averageoutputpath = 'AveragingPeriodOutputs.csv'
averagecalcoutputpath = 'AveragingPeriodCalcs.csv'
fullaverageoutputpath = 'RealtimeAveragesOutputs.csv'
phasepath = 'PhaseTimes.csv'
savefig = 'averagingperiod.png'
logpath='log.txt'
##################################

def _to_nominal_list(series):
    """Return a list of nominal floats/values suitable for matplotlib plotting."""
    return [v.n if hasattr(v, 'n') else v for v in series]


def _resolve_companion_paths(inputpath, energypath, ucpath='', emissioninputpath=''):
    """Auto-resolve UCInputs, EmissionInputs, and Averages paths alongside a test's files."""
    if energypath and energypath.endswith('_EnergyOutputs.csv'):
        base = energypath[:-len('_EnergyOutputs.csv')]
    elif '_TimeSeriesMetrics_' in inputpath:
        base = inputpath.split('_TimeSeriesMetrics_')[0]
    else:
        base = ''
    resolved_uc = ucpath or (base + '_UCInputs.csv' if base else '')
    resolved_em = emissioninputpath or (base + '_EmissionInputs.csv' if base else '')
    resolved_ave = (base + '_Averages.csv') if base else ''
    return resolved_uc, resolved_em, resolved_ave


def _safe_load_constants(path):
    """Load a constant CSV via IO if it exists, otherwise return empty structures."""
    if path and os.path.isfile(path):
        try:
            return io.load_constant_inputs(path)
        except Exception:
            pass
    return [], {}, {}, {}, {}


def _load_uc_inputs(ucpath):
    """Load wide-format UCInputs.csv if it exists."""
    if ucpath and os.path.isfile(ucpath):
        try:
            ucnames, _, ucinputs = io.load_timeseries(ucpath)
            return ucnames, ucinputs
        except Exception:
            pass
    return [], {}


def _propagate_cut_uncertainty(names, avgdata, choice, ucpath, emissioninputpath, gravpath, energypath, avepath, logs):
    """Ensure cut-period ``avgdata`` carries propagated ufloat uncertainties.

    Called when the input TimeSeriesMetrics CSV had no ``_uc`` columns (for
    example, when Step 10 was run with time-series uncertainty output disabled).
    Uses one correlated unit variable per sensor channel across timestamps so
    systematic uncertainties do not shrink by 1/sqrt(N) on averaging.
    """
    has_any_ufloat = any(
        any(hasattr(v, 's') for v in avgdata.get(name, []))
        for name in names
        if name not in ('time', 'phase', 'seconds', 'datenumbers')
    )
    if has_any_ufloat:
        return

    ucnames, ucinputs = _load_uc_inputs(ucpath)
    _, _, emval, _, emuval = _safe_load_constants(emissioninputpath)
    _, _, gravval, _, gravuval = _safe_load_constants(gravpath)
    _, _, eval_c, _, euval_c = _safe_load_constants(energypath)
    _, _, aveval, _, aveuval = _safe_load_constants(avepath)

    # 1. Apply sensor uncertainty from UCInputs using one shared tag per channel
    skip_cols = {'time', 'seconds', 'ID', 'phase', 'datenumbers'}
    for name in names:
        if name in skip_cols or name not in avgdata:
            continue
        uc_key = name if name in ucnames else ('HC' if (name == 'CH4' and 'HC' in ucnames) else None)
        if uc_key is None:
            continue
        try:
            abs_u = abs(float(ucinputs[uc_key][0]))
        except (ValueError, TypeError, IndexError):
            abs_u = 0.0
        try:
            rel_u = abs(float(ucinputs[uc_key][1]))
        except (ValueError, TypeError, IndexError):
            rel_u = 0.0
        if abs_u == 0.0 and rel_u == 0.0:
            continue
        unit_sigma = ufloat(0.0, 1.0, tag=f'cut_uc_{name}')
        updated = []
        for val in avgdata[name]:
            try:
                fval = float(val)
                if math.isnan(fval):
                    updated.append(fval)
                else:
                    unc_i = abs(fval * rel_u) + abs_u
                    updated.append(fval + unc_i * unit_sigma)
            except (ValueError, TypeError):
                updated.append(val)
        avgdata[name] = updated

    # 2. Build constant ufloat inputs matching LEMS_EmissionCalcs
    stat_press = 0
    if 'static_pressure_dil_tunnel' in emuval:
        try:
            stat_press = emuval['static_pressure_dil_tunnel'] * 248.84
        except Exception:
            stat_press = 0
    elif 'static_pressure' in emuval:
        try:
            stat_press = emuval['static_pressure']
        except Exception:
            stat_press = 0

    p_amb = aveuval.get('P_amb', euval_c.get('initial_pressure', 101325.0))
    if 'P_amb' in aveuval:
        p_duct = p_amb - stat_press
    else:
        try:
            p_duct = (euval_c['initial_pressure'] + euval_c['final_pressure']) * 33.86 / 2 * 100
        except Exception:
            try:
                p_duct = euval_c['initial_pressure'] * 33.86 * 100
            except Exception:
                p_duct = 101325.0

    msc_val = emuval.get('MSC_default', 3.0)
    pm_mass_key = 'PMmass_' + choice
    pm_ave_key = 'PM_' + choice
    if pm_mass_key in gravuval and pm_ave_key in aveuval:
        try:
            if hasattr(gravuval[pm_mass_key], 'n') or isinstance(gravuval[pm_mass_key], (int, float)):
                msc_val = aveuval[pm_ave_key] / gravuval[pm_mass_key]
        except Exception:
            pass

    MW = {
        'C': 12.01, 'CO': 28.01, 'CO2': 44.01, 'CO2v': 44.01,
        'PM': 1.0, 'VOC': 56.11, 'air': 29.0,
    }
    R = 8.314

    def _keep_nominal(target_name, prop_series):
        if target_name not in avgdata or len(avgdata[target_name]) != len(prop_series):
            return
        merged = []
        for orig, prop in zip(avgdata[target_name], prop_series):
            try:
                orig_n = float(orig.n if hasattr(orig, 'n') else orig)
            except (ValueError, TypeError):
                merged.append(orig)
                continue
            if hasattr(prop, 's') and not math.isnan(orig_n):
                merged.append(orig_n + (prop - prop.n))
            else:
                merged.append(orig)
        avgdata[target_name] = merged

    # 3. Propagate derived concentration, flow, ER, EF, firepower, and totmass channels
    if 'FLUEtemp' in avgdata:
        for species in ('CO', 'CO2', 'CO2v', 'PM', 'VOC'):
            conc_name = species + 'mass'
            if species in avgdata and conc_name in avgdata:
                prop = []
                for val, temp in zip(avgdata[species], avgdata['FLUEtemp']):
                    try:
                        if species == 'PM':
                            prop.append(val / msc_val / 1000000.0)
                        else:
                            prop.append(val * MW[species] * p_duct / (temp + 273.15) / 1000000.0 / R)
                    except Exception:
                        prop.append('')
                _keep_nominal(conc_name, prop)

    if 'COmass' in avgdata and 'Cmass' in avgdata:
        co2_conc_key = 'CO2vmass' if 'CO2vmass' in avgdata else ('CO2mass' if 'CO2mass' in avgdata else None)
        if co2_conc_key:
            co2_mw_key = 'CO2v' if co2_conc_key == 'CO2vmass' else 'CO2'
            prop = []
            for co_m, co2_m in zip(avgdata['COmass'], avgdata[co2_conc_key]):
                try:
                    prop.append(co_m * MW['C'] / MW['CO'] + co2_m * MW['C'] / MW[co2_mw_key])
                except Exception:
                    prop.append('')
            _keep_nominal('Cmass', prop)

    if 'MCE' in avgdata and 'CO' in avgdata:
        co2_key = 'CO2v' if 'CO2v' in avgdata else ('CO2' if 'CO2' in avgdata else None)
        if co2_key:
            prop = []
            for co2_v, co_v in zip(avgdata[co2_key], avgdata['CO']):
                try:
                    prop.append(co2_v / (co2_v + co_v))
                except Exception:
                    prop.append('')
            _keep_nominal('MCE', prop)

    if 'density' in avgdata and 'MW_duct' in avgdata and 'FLUEtemp' in avgdata:
        prop = []
        for mw_d, temp in zip(avgdata['MW_duct'], avgdata['FLUEtemp']):
            try:
                prop.append(mw_d * p_duct / (temp + 273.15) / R)
            except Exception:
                prop.append('')
        _keep_nominal('density', prop)

    if 'mass_flow' in avgdata and 'Flow_smooth' in avgdata and 'FLUEtemp' in avgdata:
        fac_cal = emuval.get('factory_flow_cal', emval.get('factory_flow_cal', 15.3))
        fg_cal = emuval.get('flowgrid_cal_factor', emval.get('flowgrid_cal_factor', 1.0))
        prop = []
        for fl_v, temp in zip(avgdata['Flow_smooth'], avgdata['FLUEtemp']):
            try:
                inner = fl_v / 25.4 * p_duct / (temp + 273.15)
                inner_n = inner.n if hasattr(inner, 'n') else inner
                if inner_n <= 0:
                    prop.append(0.0)
                else:
                    root = umath.sqrt(inner) if hasattr(inner, 'n') else math.sqrt(inner)
                    prop.append(fac_cal * fg_cal * root)
            except Exception:
                prop.append('')
        _keep_nominal('mass_flow', prop)

    if 'vol_flow' in avgdata and 'mass_flow' in avgdata and 'density' in avgdata:
        prop = []
        for mf, dens in zip(avgdata['mass_flow'], avgdata['density']):
            try:
                prop.append(mf / dens)
            except Exception:
                prop.append('')
        _keep_nominal('vol_flow', prop)

    if 'mole_flow' in avgdata and 'mass_flow' in avgdata and 'MW_duct' in avgdata:
        prop = []
        for mf, mw_d in zip(avgdata['mass_flow'], avgdata['MW_duct']):
            try:
                prop.append(mf / mw_d)
            except Exception:
                prop.append('')
        _keep_nominal('mole_flow', prop)

    for species in ('CO', 'CO2', 'CO2v', 'PM', 'VOC'):
        conc_key = species + 'mass'
        er_key = species + '_ER'
        if conc_key in avgdata and 'vol_flow' in avgdata and er_key in avgdata:
            prop_er = []
            for cm, vf in zip(avgdata[conc_key], avgdata['vol_flow']):
                try:
                    prop_er.append(cm * vf)
                except Exception:
                    prop_er.append('')
            _keep_nominal(er_key, prop_er)
            for suffix, mult in (('_ER_min', 60.0), ('_ER_hr', 3600.0)):
                k = species + suffix
                if k in avgdata:
                    _keep_nominal(k, [v * mult if v != '' else '' for v in avgdata[er_key]])

    if 'C_ER' in avgdata:
        co2_er_key = 'CO2v_ER' if 'CO2v_ER' in avgdata else ('CO2_ER' if 'CO2_ER' in avgdata else None)
        if co2_er_key and 'CO_ER' in avgdata:
            co2_mw_key = 'CO2v' if co2_er_key == 'CO2v_ER' else 'CO2'
            prop = []
            for co2_er, co_er in zip(avgdata[co2_er_key], avgdata['CO_ER']):
                try:
                    prop.append(co2_er * MW['C'] / MW[co2_mw_key] + co_er * MW['C'] / MW['CO'])
                except Exception:
                    prop.append('')
            _keep_nominal('C_ER', prop)

    if 'C_ER' in avgdata:
        for species in ('CO', 'CO2', 'CO2v', 'PM', 'VOC'):
            er_hr_key = species + '_ER_hr'
            ef_key = species + '_EF'
            if er_hr_key in avgdata and ef_key in avgdata:
                prop = []
                for er_hr, c_er in zip(avgdata[er_hr_key], avgdata['C_ER']):
                    try:
                        c_n = c_er.n if hasattr(c_er, 'n') else c_er
                        denom = (0.001 if c_n == 0 else c_er) * 3600.0 / 1000.0
                        prop.append(er_hr / denom)
                    except Exception:
                        prop.append('')
                _keep_nominal(ef_key, prop)

    if 'firepower_carbon' in avgdata and 'C_ER' in avgdata:
        ehv_val = euval_c.get('fuel_EHV_' + choice, euval_c.get('fuel_heating_value'))
        cfrac_val = euval_c.get('fuel_Cfrac_' + choice, 0.5)
        if ehv_val is not None:
            prop = []
            for c_er in avgdata['C_ER']:
                try:
                    prop.append(c_er / cfrac_val * ehv_val)
                except Exception:
                    prop.append('')
            _keep_nominal('firepower_carbon', prop)

    # Propagate correlated uncertainty onto pre-existing cumulative totals if any
    for tot_key, rate_key in (
        ('totvol', 'vol_flow'),
        ('totvol_ASTM', 'vol_flow_ASTM'),
        ('CO_totmass', 'CO_ER'),
        ('CO2_totmass', 'CO2_ER'),
        ('CO2v_totmass', 'CO2v_ER'),
        ('PM_totmass', 'PM_ER'),
        ('VOC_totmass', 'VOC_ER'),
    ):
        if tot_key in avgdata and rate_key in avgdata and avgdata[rate_key]:
            rate_stds = [float(v.s if hasattr(v, 's') else 0.0) for v in avgdata[rate_key]]
            rate_noms = [abs(float(v.n if hasattr(v, 'n') else v)) for v in avgdata[rate_key] if v != '']
            mean_rel = (sum(rate_stds) / len(rate_stds)) / (sum(rate_noms) / len(rate_noms)) if rate_noms and (sum(rate_noms) > 0) else 0.0
            if mean_rel > 0:
                updated_tot = []
                for orig in avgdata[tot_key]:
                    try:
                        orig_n = float(orig.n if hasattr(orig, 'n') else orig)
                        updated_tot.append(ufloat(orig_n, abs(orig_n) * mean_rel))
                    except (ValueError, TypeError):
                        updated_tot.append(orig)
                avgdata[tot_key] = updated_tot

    logs.append('Propagated fallback cut-period uncertainty from test inputs')


def _compute_and_write_period_outputs(names, units, avgdata, outputpath, averageoutputpath,
                                      sensorpaths, senserionpath, validnames, timeobject,
                                      choice, logs, write_timeseries_uncertainty=False):
    """Write cut-period time-series CSV and compute/write cut-period averages with uncertainties."""
    if write_timeseries_uncertainty:
        io.write_timeseries_with_uncertainty(outputpath, names, units, avgdata)
    else:
        io.write_timeseries_without_uncertainty(outputpath, names, units, avgdata)

    line = 'created: ' + outputpath
    print(line)
    logs.append(line)

    emweightavg = [
        'CO_ER', 'CO2v_ER', 'CO2_ER', 'PM_ER', 'VOC_ER', 'C_ER',
        'CO_ER_min', 'CO2v_ER_min', 'CO2_ER_min', 'PM_ER_min', 'VOC_ER_min',
        'CO_ER_hr', 'CO2v_ER_hr', 'CO2_ER_hr', 'PM_ER_hr', 'VOC_ER_hr',
        'CO_EF', 'CO2v_EF', 'CO2_EF', 'PM_EF', 'VOC_EF',
    ]

    calcavg = {}
    unc = {}
    uval = {}

    for name in names:
        if name in emweightavg:
            continue
        series = avgdata.get(name, [])
        if name == 'seconds':
            try:
                calc = series[-1] - series[0]
                if hasattr(calc, 'n'):
                    calcavg[name] = float(calc.n)
                    unc[name] = float(calc.s)
                    uval[name] = calc
                else:
                    calcavg[name] = calc
                    unc[name] = ''
                    uval[name] = ''
            except Exception:
                calcavg[name] = ''
                unc[name] = ''
                uval[name] = ''
            continue

        if not series or name in ('time', 'phase'):
            calcavg[name] = ''
            unc[name] = ''
            uval[name] = ''
            continue

        try:
            noms = [float(v.n if hasattr(v, 'n') else v) for v in series]
            has_u = any(hasattr(v, 's') for v in series)
            avg_n = sum(noms) / len(noms)
            if has_u:
                stds = [abs(float(v.s if hasattr(v, 's') else 0.0)) for v in series]
                avg_s = sum(stds) / len(stds)
                res = ufloat(avg_n, avg_s)
                calcavg[name] = res.n
                unc[name] = res.s
                uval[name] = res
            else:
                calcavg[name] = avg_n
                unc[name] = ''
                uval[name] = ''
        except (ValueError, TypeError, ZeroDivisionError):
            calcavg[name] = ''
            unc[name] = ''
            uval[name] = ''

    # Emission-weighted averages over cut period (Cmass weighted)
    u_x = ufloat(0.0, 1.0, tag='ew_x')
    u_c = ufloat(0.0, 1.0, tag='ew_c')
    for name in names:
        if name not in emweightavg:
            continue
        series = avgdata.get(name, [])
        cmass_series = avgdata.get('Cmass', [])
        if not series or not cmass_series:
            calcavg[name] = ''
            unc[name] = ''
            uval[name] = ''
            continue
        try:
            weighted_sum = 0.0
            cmass_sum = 0.0
            has_u = False
            for val, cval in zip(series, cmass_series):
                xn = float(val.n if hasattr(val, 'n') else val)
                xs = abs(float(val.s if hasattr(val, 's') else 0.0))
                cn = float(cval.n if hasattr(cval, 'n') else cval)
                cs = abs(float(cval.s if hasattr(cval, 's') else 0.0))
                if xs > 0.0 or cs > 0.0:
                    has_u = True
                weighted_sum = weighted_sum + (xn + xs * u_x) * (cn + cs * u_c)
                cmass_sum = cmass_sum + (cn + cs * u_c)
            calc = weighted_sum / cmass_sum
            calcavg[name] = float(calc.n)
            if has_u:
                res = ufloat(float(calc.n), float(calc.s))
                unc[name] = res.s
                uval[name] = res
            else:
                unc[name] = ''
                uval[name] = ''
        except Exception:
            calcavg[name] = ''
            unc[name] = ''
            uval[name] = ''

    # Add other sensor data streams for cut window
    added_sensor_names = []
    for path in sensorpaths:
        [snames, sunits, sdata] = io.load_timeseries_with_uncertainty(path)

        for n, sname in enumerate(snames):
            if 'TC' in sname:
                newname = 'S' + sname
                snames[n] = newname
                sunits[newname] = sunits.pop(sname)
                sdata[newname] = sdata.pop(sname)

        date = sdata['time'][0][:10]
        snames.append('dateobjects')
        sunits['dateobjects'] = 'date'
        sdata['dateobjects'] = []
        for val in sdata['time']:
            try:
                dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')
            except Exception:
                dateobject = dt.strptime(val, '%Y-%m-%d %H:%M:%S')
            sdata['dateobjects'].append(dateobject)

        snames.append('datenumbers')
        sunits['datenumbers'] = 'date'
        sdatenums = list(matplotlib.dates.date2num(sdata['dateobjects']))
        sdata['datenumbers'] = sdatenums

        samplerate = (sdata['seconds'][1] - sdata['seconds'][0]) * 4
        indices = bkg.findIndices(validnames, timeobject, sdatenums, samplerate)
        try:
            [_, adddata, _] = definePhaseData(snames, sdata, [choice], indices)

            if path == senserionpath:
                senserion_outputpath = outputpath.replace('AveragingPeriodTimeSeries', 'AveragingPeriodSenserion')
                s_avgdata = {}
                s_names_to_write = [sn for sn in snames if sn not in ['dateobjects', 'datenumbers']]
                for sn in s_names_to_write:
                    s_avgdata[sn] = adddata[sn + '_' + choice]
                io.write_timeseries(senserion_outputpath, s_names_to_write, sunits, s_avgdata)
                line = 'created: ' + senserion_outputpath
                print(line)
                logs.append(line)

            for skip_k in ('dateobjects', 'time', 'seconds', 'datenumbers'):
                if skip_k in snames:
                    snames.remove(skip_k)

            for sn in snames:
                try:
                    phasename = sn + '_' + choice
                    s_series = adddata[phasename]
                    s_noms = [float(v.n if hasattr(v, 'n') else v) for v in s_series]
                    has_u = any(hasattr(v, 's') for v in s_series)
                    avg_n = sum(s_noms) / len(s_noms)
                    if has_u:
                        s_stds = [abs(float(v.s if hasattr(v, 's') else 0.0)) for v in s_series]
                        res = ufloat(avg_n, sum(s_stds) / len(s_stds))
                        calcavg[sn] = res.n
                        unc[sn] = res.s
                        uval[sn] = res
                    else:
                        calcavg[sn] = avg_n
                        unc[sn] = ''
                        uval[sn] = ''
                    avgdata[phasename] = s_series
                    units[sn] = sunits[sn]
                    if sn not in names:
                        names.append(sn)
                        added_sensor_names.append(sn)
                except Exception:
                    pass
        except Exception as e:
            print(f"Error processing sensor path {path}: {e}")
            import traceback
            traceback.print_exc()

    io.write_constant_outputs(averageoutputpath, names, units, calcavg, unc, uval)

    for sn in added_sensor_names:
        if sn in names:
            names.remove(sn)

    line = 'created: ' + averageoutputpath
    print(line)
    logs.append(line)
    return calcavg, unc, uval


def LEMS_Realtime(inputpath, energypath, gravpath, phasepath, periodpath, outputpath, averageoutputpath, savefig,
                  choice, logpath, inputmethod, fuelpath, fuelmetricpath, exactpath, scalepath, intscalepath, ascalepath, cscalepath,
                  nanopath, TEOMpath, senserionpath, OPSpath, Picopath,
                  ucpath='', emissioninputpath='', uncertainty_template_dir=None, write_timeseries_uncertainty=False):
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_Realtime v' + ver + '   ' + timestampstring  # Add to log
    print(line)
    logs = [line]

    #################################################
    # read in raw data file (with _uc columns if present)
    [names, units, data] = io.load_timeseries_with_uncertainty(inputpath)

    line = 'loaded: ' + inputpath #add to log
    print(line)
    logs.append(line)

    resolved_ucpath, resolved_empath, resolved_avepath = _resolve_companion_paths(
        inputpath, energypath, ucpath=ucpath, emissioninputpath=emissioninputpath
    )

    # load energy metrics data file
    [enames, eunits, eval, eunc, emetric] = io.load_constant_inputs(energypath)

    line = 'loaded: ' + energypath
    print(line)
    logs.append(line)
    ######################################################################
    sensorpaths = []
    #Read in additional sensor data and add it to dictionary
    if os.path.isfile(fuelpath):
        sensorpaths.append(fuelpath)

    if os.path.isfile(fuelmetricpath):
        sensorpaths.append(fuelmetricpath)

    if os.path.isfile(exactpath):
        sensorpaths.append(exactpath)

    if os.path.isfile(scalepath):
        sensorpaths.append(scalepath)

    if os.path.isfile(intscalepath):
        sensorpaths.append(intscalepath)

    if os.path.isfile(ascalepath):
        sensorpaths.append(ascalepath)

    if os.path.isfile(cscalepath):
        sensorpaths.append(cscalepath)

    if os.path.isfile(nanopath):
        sensorpaths.append(nanopath)

    if os.path.isfile(TEOMpath):
        sensorpaths.append(TEOMpath)

    if os.path.isfile(senserionpath):
        sensorpaths.append(senserionpath)

    if os.path.isfile(OPSpath):
        sensorpaths.append(OPSpath)

    if os.path.isfile(Picopath):
        sensorpaths.append(Picopath)

    #######################################################################
    #Check if average period times file exists
    if os.path.isfile(periodpath):
        line = 'Average Period time file already exists: ' + periodpath
        print(line)
        logs.append(line)
    else:
        # Read in averaging period start and end times (phase start and end time)
        [titlenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(phasepath)

        line = 'loaded: ' + phasepath
        print(line)
        logs.append(line)
        request_entry(logs, choice, eval, eunits, eunc, emetric, periodpath, titlenames, timeunits, timestring, timeunc, timeuval, inputmethod, data=data)
    ##################################################################
    ################################################################
    # Read in averaging period start and end times
    [titlenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(periodpath)

    line = 'loaded: ' + periodpath
    print(line)
    logs.append(line)

    ##################################################################
    # Convert datetime to readable dateobject
    date = data['time'][0][:8]  # pull date

    name = 'dateobjects'
    units[name] = 'date'
    data[name] = []
    for n, val in enumerate(data['time']):
        dateobject = dt.strptime(val, '%Y%m%d %H:%M:%S')
        data[name].append(dateobject)

    name = 'datenumbers'
    units[name] = 'date'
    datenums = matplotlib.dates.date2num(data['dateobjects'])
    datenums = list(datenums)
    data[name] = datenums

    samplerate = data['seconds'][1] - data['seconds'][0] #find sample rate

    [avgdatenums, avgdata, avgmean, validnames, timeobject, phases] = run_functions(titlenames, timestring, date, samplerate, datenums, names, data, periodpath, logs, choice, eval, eunits,
                  eunc, emetric, phasepath, timeunits, timeunc, timeuval, inputmethod)

    for n, name in enumerate(names):
        phasename = name + '_' + choice
        try:
            avgdata[name] = avgdata[phasename]
        except:
            pass

    _propagate_cut_uncertainty(
        names, avgdata, choice, resolved_ucpath, resolved_empath,
        gravpath, energypath, resolved_avepath, logs
    )

    calcavg, unc, uval = _compute_and_write_period_outputs(
        names, units, avgdata, outputpath, averageoutputpath,
        sensorpaths, senserionpath, validnames, timeobject,
        choice, logs, write_timeseries_uncertainty=write_timeseries_uncertainty
    )

    ###############################################################
    #plot timeseries data
    if inputmethod == '1':
        plt.ion() #turn on interactive plot mode

        fig, ax = plt.subplots()

        scalar = 10

        scaledPM = []
        for val in data['PM']:
            v_n = val.n if hasattr(val, 'n') else val
            scaledPM.append(v_n / scalar)

        scaledavgPM = []
        for val in avgdata['PM_' + choice]:
            v_n = val.n if hasattr(val, 'n') else val
            scaledavgPM.append(v_n / scalar)

        #Plot PM
        ax.plot(data['datenumbers'], scaledPM, color = 'yellow', label = 'Full period PM')
        ax.plot(avgdatenums[choice], scaledavgPM, color='blue', label='Cut Period PM')

        CO2v = True

        try:
            # Plot Firepower Carbon - Variable must come from TimeSeriesMetrics (data)
            # TODO: Make variable selection interactive with a popup (e.g. easygui.choicebox)
            ax.plot(data['datenumbers'], _to_nominal_list(data['firepower_carbon']), color = 'red', label = 'Full period Firepower Carbon')
            ax.plot(avgdatenums[choice], _to_nominal_list(avgdata['firepower_carbon_' + choice]), color = 'green', label='Cut Period Firepower Carbon')
        except:
            #variable = easygui.choicebox("Select a variable to plot", choices=allnames)
            ax.plot(data['datenumbers'], _to_nominal_list(data['CO2']), color='red', label=f'Full period CO2')
            ax.plot(avgdatenums[choice], _to_nominal_list(avgdata['CO2' + '_' + choice]), color='green', label=f'Cut Period CO2')
            CO2v = False

        ax.legend()
        ax.set(ylabel='PM(Mm-1)/10, Firepower Carbon (kW)', title='Please confirm the time period displayed is correct')

        #Format x axis to readable times
        xfmt = matplotlib.dates.DateFormatter('%H:%M:%S') #pull and format time data
        ax.xaxis.set_major_formatter(xfmt)
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)

        ################################################################
        #Replot for new inputs
        running = 'fun'

        # Auto-detect gasification phases for interactive preset options / shortcuts
        flame_end, smolder_end = None, None
        try:
            start_val = timestring.get('start_time_' + choice, '')
            end_val = timestring.get('end_time_' + choice, '')
            flame_end, smolder_end = detect_gasification_phase(data, choice, start_val, end_val)
        except Exception as e:
            print(f"Interactive gasification detection error: {e}")

        while (running == 'fun'):

            startname = 'start_time_' + choice
            endname = 'end_time_' + choice

            # GUI box with buttons to easily switch periods or edit manually
            msg_loop = (
                f"Reviewing Averaging Period for phase '{choice}':\n\n"
                f"Current Period: {timestring[startname]}  to  {timestring[endname]}\n\n"
                f"Detected Presets:\n"
                f"  • Burning Only: {flame_end}\n"
                f"  • Include Smoldering: {smolder_end}\n\n"
                f"Click a button to update plot or finish:"
            )
            title_loop = f"Averaging Period - {choice}"
            choices_loop = []
            if flame_end:
                choices_loop.append("Burning Only")
            if smolder_end:
                choices_loop.append("Include Smoldering")
            choices_loop.append("Edit Times Manually")
            choices_loop.append("Confirm & Save")

            action = easygui.buttonbox(msg_loop, title_loop, choices=choices_loop)

            changed = False
            if action == "Burning Only" and flame_end:
                if eval[endname] != flame_end:
                    eval[endname] = flame_end
                    timestring[endname] = flame_end
                    changed = True
            elif action == "Include Smoldering" and smolder_end:
                if eval[endname] != smolder_end:
                    eval[endname] = smolder_end
                    timestring[endname] = smolder_end
                    changed = True
            elif action == "Edit Times Manually":
                fieldnames = titlenames
                currentvals = [timestring[name] for name in fieldnames]
                msg_edit = f"Edit averaging period\nTime format = {timeunits[startname]}\n"
                newvals = easygui.multenterbox(msg_edit, "Edit Times", fieldnames, currentvals)
                if newvals and newvals != currentvals:
                    eval[startname] = newvals[0]
                    eval[endname] = newvals[1]
                    timestring[startname] = newvals[0]
                    timestring[endname] = newvals[1]
                    changed = True
            else:
                # "Confirm & Save", Cancel, or window closed
                running = 'not fun'
                savefigpath = savefig[:-4] + '_' + choice + '.png'
                plt.savefig(savefigpath, bbox_inches='tight')
                plt.close('all')
                plt.ioff()  # turn off interactive plot
                break

            if changed:
                # Record new values in averagingperiod for next time
                io.write_constant_outputs(periodpath, titlenames, eunits, eval, eunc, emetric)
                line = 'Updated averaging period file:' + periodpath
                print(line)
                logs.append(line)

            #####################################################################
            #Updata values of new cut period
            [avgdatenums, avgdata, avgmean, validnames, timeobject, phases] = run_functions(titlenames, timestring, date, samplerate, datenums, names, data, periodpath, logs, choice, eval, eunits,
                  eunc, emetric, phasepath, timeunits, timeunc, timeuval, inputmethod)

            for n, name in enumerate(names):
                phasename = name + '_' + choice
                try:
                    avgdata[name] = avgdata[phasename]
                except:
                    pass

            _propagate_cut_uncertainty(
                names, avgdata, choice, resolved_ucpath, resolved_empath,
                gravpath, energypath, resolved_avepath, logs
            )

            calcavg, unc, uval = _compute_and_write_period_outputs(
                names, units, avgdata, outputpath, averageoutputpath,
                sensorpaths, senserionpath, validnames, timeobject,
                choice, logs, write_timeseries_uncertainty=write_timeseries_uncertainty
            )

            ############################################################################################
            #Update Plot
            scaledPM = []
            for val in data['PM']:
                v_n = val.n if hasattr(val, 'n') else val
                scaledPM.append(v_n / scalar)

            scaledavgPM = []
            for val in avgdata['PM_' + choice]:
                v_n = val.n if hasattr(val, 'n') else val
                scaledavgPM.append(v_n / scalar)

            ax.cla()

            #Plot PM
            ax.plot(data['datenumbers'], scaledPM, color = 'yellow', label = 'Full period PM')
            ax.plot(avgdatenums[choice], scaledavgPM, color = 'blue', label = 'Cut Period PM')

            try:
                # Plot Firepower Carbon - Variable must come from TimeSeriesMetrics (data)
                # TODO: Make variable selection interactive with a popup (e.g. easygui.choicebox)
                ax.plot(data['datenumbers'], _to_nominal_list(data['firepower_carbon']), color = 'red', label = 'Full period Firepower Carbon')
                ax.plot(avgdatenums[choice], _to_nominal_list(avgdata['firepower_carbon_' + choice]), color = 'green', label = 'Cut Period Firepower Carbon')
            except:
                ax.plot(data['datenumbers'], _to_nominal_list(data['CO2']), color='red', label=f'Full period CO2')
                ax.plot(avgdatenums[choice], _to_nominal_list(avgdata['CO2' + '_' + choice]), color='green', label=f'Cut Period CO2')

            ax.legend()
            ax.set(ylabel='PM(Mm-1)/10, Firepower Carbon (kW)', title='Please confirm the time period displayed is correct')

            # Format x axis to readable times
            xfmt = matplotlib.dates.DateFormatter('%H:%M:%S')  # pull and format time data
            ax.xaxis.set_major_formatter(xfmt)
            for tick in ax.get_xticklabels():
                tick.set_rotation(30)

            #fig.canvas.draw()

        plt.close('all')
        plt.ioff()
        # print to log file
        io.write_logfile(logpath, logs)

        return calcavg, units, logs, timestring

def definePhaseData(Names, Data, Phases, Indices):
    Phasedatenums = {}
    Phasedata = {}
    Phasemean = {}
    for Phase in Phases:  # for each test phase
        # make data series of date numbers
        key = 'start_time_' + Phase
        startindex = Indices[key]
        key = 'end_time_' + Phase
        endindex = Indices[key]

        Phasedatenums[Phase] = Data['datenumbers'][startindex:endindex + 1]
        # make phase data series for each data channel
        for Name in Names:
            Phasename = Name + '_' + Phase
            Phasedata[Phasename] = Data[Name][startindex:endindex + 1]

            # calculate average value
            if Name != 'time' and Name != 'phase':
                print(Name)
                try:
                    print('1')
                    if all(np.isnan(Phasedata[Phasename])):
                        pass
                        #Phasemean[Phasename] = np.nan
                    else:
                        ave = np.nanmean(Phasedata[Phasename])
                        if 'datenumbers' in Name:
                            Phasemean[Phasename] = ave
                except:
                    nominals = []
                    print('2')
                    for uval in Phasedata[Phasename]:
                        try:
                            nominals.append(uval.n)
                        except:
                            pass
                    print('3')
                    if all(np.isnan(nominals)):
                        Phasemean[Phasename] = np.nan
                    else:
                        ave = sum(nominals) / len(nominals)
                        if 'datenumbers' in Name:
                            Phasemean[Phasename] = ave

        # time channel: use the mid-point time string
        Phasename = 'datenumbers_' + Phase
        Dateobject = matplotlib.dates.num2date(Phasemean[Phasename])  # convert mean date number to date object
        Phasename = 'time_' + Phase
        Phasemean[Phasename] = Dateobject.strftime('%Y%m%d %H:%M:%S')

        # phase channel: use phase name
        Phasename = 'phase_' + Phase
        Phasemean[Phasename] = Phase

    return Phasedatenums, Phasedata, Phasemean

def loaddatastream(new_names, new_units, new_data, names, units, data):
    for name in new_names:
        # add new values to dictionary
        # Time is already in dictionary, rename to not overwrite data
        if name == 'time':
            newname = type + 'time'
            names.append(newname)
            units[newname] = new_units[name]
            data[newname] = new_data[name]
        # seconds is already in dictionary, rename to not overwrite data
        elif name == 'seconds':
            newname = type + 'seconds'
            names.append(newname)
            units[newname] = new_units[name]
            data[newname] = new_data[name]
        # all other data can be added without ov
        elif 'TC' in name: #senserion data also has TC channels - rename so they don't get mixed up
            newname = 'S' + name
            names.append(newname)
            units[newname] = new_units[name]
            data[newname] = new_data[name]
        else:
            names.append(name)
            data[name] = new_data[name]
            units[name] = new_units[name]

    # Convert date strings to date numbers for plotting
    name = type + 'dateobjects'
    units[name] = 'date'
    data[name] = []
    for n, val in enumerate(data[type + 'time']):
        dateobject = dt.strptime(val, '%Y-%m-%d %H:%M:%S')
        data[name].append(dateobject)

    name = type + 'datenumbers'
    units[name] = 'date'
    datenums = matplotlib.dates.date2num(data[type + 'dateobjects'])
    datenums = list(datenums)
    data[name] = datenums

    return names, units, data


def run_functions(titlenames, timestring, date, samplerate, datenums, names, data, periodpath, logs, choice, eval, eunits,
                  eunc, emetric, phasepath, timeunits, timeunc, timeuval, inputmethod):
    [titlenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(periodpath) 
    # Convert datetime str to readable value time objects
    [validnames, timeobject] = bkg.makeTimeObjects(titlenames, timestring, date)

    # Find 'phase' averging period
    phases = bkg.definePhases(validnames)

    # find indicieds in the data for start and end
    indices = bkg.findIndices(validnames, timeobject, datenums, samplerate)

    try:
        # Define averaging data series
        [avgdatenums, avgdata, avgmean] = definePhaseData(names, data, phases, indices)

    except KeyError as e:
        e = str(e)
        message = f"Variable: {e} was entered incorrectly or is outside of the measured time period\n" \
                  f"* Check that time format was entered as either hh:mm:ss or yyyymmdd hh:mm:ss\n" \
                  f"    * Check that no letters, symbols, or spaces are included in the time entry\n" \
                  f"    * Check that the entered time exist within the data\n" \
                  f"    * Check that the time has not been left blank when there should be an entry.\n"
        if inputmethod == '1':
            title = "ERROR"
            easygui.msgbox(message, title, "OK")
        else:
            print(message)

        request_entry(logs, choice, eval, eunits, eunc, emetric, periodpath, titlenames, timeunits, timestring, timeunc, timeuval, inputmethod, data=data)
        # Read in averaging period start and end times
        [titlenames, timeunits, timestring, timeunc, timeuval] = io.load_constant_inputs(periodpath)

        line = 'loaded: ' + periodpath
        print(line)
        logs.append(line)

        [avgdatenums, avgdata, avgmean, validnames, timeobject, phases] = run_functions(titlenames, timestring, date, samplerate, datenums, names, data, periodpath, logs, choice, eval, eunits,
                  eunc, emetric, phasepath, timeunits, timeunc, timeuval, inputmethod)

    return avgdatenums, avgdata, avgmean, validnames, timeobject, phases

def detect_gasification_phase(data, choice, start_time_str, end_time_str):
    """
    Automatically detects the gasification phase boundaries:
    1. flame_end: End of burning gasification (characterized by high CO2 followed by lower CO2).
    2. smolder_end: End of smoldering gasification (characterized by elevated PM hump after burning gasification, returning to baseline).
    
    Returns:
        flame_end_time (str or None): Formatted timestamp for burning gasification end.
        smolder_end_time (str or None): Formatted timestamp for smoldering gasification end.
    """
    if not data or 'time' not in data:
        return None, None

    time_list = data['time']
    if len(time_list) < 10:
        return None, None

    # Identify CO2 and PM keys in data
    co2_key = None
    for k in ['CO2', 'CO2_' + choice, 'firepower_carbon', 'firepower_carbon_' + choice]:
        if k in data and len(data[k]) == len(time_list):
            co2_key = k
            break
    if not co2_key:
        return None, None

    pm_key = None
    for k in ['PM', 'PM_' + choice]:
        if k in data and len(data[k]) == len(time_list):
            pm_key = k
            break

    # Helper to parse datetime
    def _parse_dt(t_str):
        if not t_str:
            return None
        s = str(t_str).strip()
        for fmt in ('%Y%m%d %H:%M:%S', '%Y-%m-%d %H:%M:%S'):
            try:
                return dt.strptime(s, fmt)
            except ValueError:
                pass
        if len(s) == 8 and ':' in s:
            try:
                return dt.strptime(s, '%H:%M:%S')
            except ValueError:
                pass
        return None

    # Helper to find index in time_list
    def _find_time_idx(t_str):
        if not t_str:
            return None
        s = str(t_str).strip()
        for i, val in enumerate(time_list):
            val_s = str(val).strip()
            if val_s == s or val_s.endswith(s):
                return i
        target_dt = _parse_dt(s)
        if target_dt:
            best_i = None
            min_diff = float('inf')
            for i, val in enumerate(time_list):
                v_dt = _parse_dt(val)
                if v_dt:
                    diff = abs((v_dt - target_dt).total_seconds())
                    if diff < min_diff:
                        min_diff = diff
                        best_i = i
                        if diff == 0:
                            break
            if best_i is not None and min_diff <= 15:
                return best_i
        return None

    # Helper to format output timestamp to match sample string format
    def _format_time_like(dt_obj, sample_str):
        s = str(sample_str).strip()
        if len(s) == 8 and ':' in s:
            return dt_obj.strftime('%H:%M:%S')
        elif '-' in s:
            return dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return dt_obj.strftime('%Y%m%d %H:%M:%S')

    start_idx = _find_time_idx(start_time_str)
    if start_idx is None:
        start_idx = 0

    end_idx = _find_time_idx(end_time_str)
    if end_idx is None:
        end_idx = len(time_list) - 1

    if start_idx >= end_idx or (end_idx - start_idx) < 10:
        return None, None

    # Extract slices
    sub_times = time_list[start_idx : end_idx + 1]

    def _to_clean_float_array(series):
        arr = []
        for v in series:
            try:
                arr.append(float(v.n if hasattr(v, 'n') else v))
            except (ValueError, TypeError):
                arr.append(np.nan)
        arr = np.array(arr, dtype=float)
        nans = np.isnan(arr)
        if np.all(nans):
            return None
        if np.any(nans):
            x = np.arange(len(arr))
            arr[nans] = np.interp(x[nans], x[~nans], arr[~nans])
        return arr

    co2_raw = _to_clean_float_array(data[co2_key][start_idx : end_idx + 1])
    if co2_raw is None or len(co2_raw) < 10:
        return None, None

    pm_raw = _to_clean_float_array(data[pm_key][start_idx : end_idx + 1]) if pm_key else None

    # Sample rate estimation
    dt_sec = 4.0
    if 'seconds' in data and len(data['seconds']) == len(time_list):
        sec_slice = _to_clean_float_array(data['seconds'][start_idx : end_idx + 1])
        if sec_slice is not None and len(sec_slice) > 1:
            diffs = np.diff(sec_slice)
            pos_diffs = diffs[diffs > 0]
            if len(pos_diffs) > 0:
                dt_sec = float(np.median(pos_diffs))

    # Smoothing window: ~60 seconds
    win_pts = max(5, int(round(60.0 / dt_sec)))
    if win_pts % 2 == 0:
        win_pts += 1
    win_pts = min(win_pts, len(co2_raw) // 2 * 2 + 1)
    if win_pts < 3:
        win_pts = 3

    kernel = np.ones(win_pts) / win_pts
    co2_smooth = np.convolve(co2_raw, kernel, mode='same')
    pm_smooth = np.convolve(pm_raw, kernel, mode='same') if pm_raw is not None else None

    # 1. Detect End of Burning Gasification (High CO2 followed by Lower CO2)
    co2_high = float(np.percentile(co2_smooth, 90))
    co2_low = float(np.percentile(co2_smooth, 10))
    delta_co2 = co2_high - co2_low

    if delta_co2 < 30: # Flat or insufficient CO2 variation
        return None, None

    # Threshold for drop from high burning level to lower post-flame level
    co2_mid = co2_low + 0.40 * delta_co2

    # Burning phase typically lasts at least a few minutes, skip initial lighting phase
    min_burn_pts = max(5, int(180 / dt_sec))
    stay_low_pts = max(10, int(600 / dt_sec))
    stay_low_pts = min(stay_low_pts, len(co2_smooth) - min_burn_pts - 1)

    flame_idx = None
    if stay_low_pts > 0:
        for i in range(min_burn_pts, len(co2_smooth) - stay_low_pts):
            if co2_smooth[i] <= co2_mid:
                # Check sustained lower CO2
                if np.mean(co2_smooth[i : i + stay_low_pts]) <= (co2_mid + 0.15 * delta_co2):
                    flame_idx = i
                    break

    if flame_idx is None:
        # Fallback to point of steepest negative derivative after initial burn
        grad = np.gradient(co2_smooth)
        search_region = grad[min_burn_pts : max(min_burn_pts + 1, len(grad) - stay_low_pts)]
        if len(search_region) > 0:
            flame_idx = min_burn_pts + int(np.argmin(search_region))
        else:
            flame_idx = min_burn_pts

    # 2. Detect End of Smoldering Phase
    # Requirements:
    # - The smoldering plus burning phase is ALWAYS strictly longer than burning only.
    # - CO2 combustion logic takes precedent over PM logic.
    min_smolder_pts = max(10, int(300 / dt_sec))  # at least 5 minutes beyond flame_idx

    # CO2 Burnout Knee Detection (CO2 takes precedent)
    # Find where post-flame CO2 decline finishes and flattens out into baseline floor
    slope_win = max(15, int(180 / dt_sec))
    if slope_win % 2 == 0:
        slope_win += 1
    co2_wide = np.convolve(co2_smooth, np.ones(slope_win) / slope_win, mode='same')
    grad_co2 = np.gradient(co2_wide, dt_sec)

    co2_post = co2_smooth[flame_idx:]
    co2_flame = float(co2_smooth[flame_idx])
    co2_tail_min = float(np.percentile(co2_post, 15))
    co2_post_drop = co2_flame - co2_tail_min

    co2_burnout_idx = flame_idx + min_smolder_pts
    if co2_post_drop > 20:
        flat_window = min(max(5, int(300 / dt_sec)), len(co2_smooth) - flame_idx - min_smolder_pts - 1)
        co2_floor_level = co2_tail_min + 0.35 * co2_post_drop
        found_burnout = False
        if flat_window > 0:
            for k in range(flame_idx + min_smolder_pts, len(co2_smooth) - flat_window):
                if co2_smooth[k] <= co2_floor_level and np.mean(grad_co2[k : k + flat_window]) > -0.010:
                    co2_burnout_idx = k
                    found_burnout = True
                    break
        if not found_burnout:
            co2_burnout_idx = flame_idx + int(np.argmin(co2_post))

    # PM Smoldering Hump Detection
    pm_end_idx = None
    if pm_smooth is not None and flame_idx < len(pm_smooth) - min_smolder_pts:
        pm_post = pm_smooth[flame_idx:]
        pm_base = float(np.percentile(pm_smooth, 10))
        pm_peak = float(np.max(pm_post))
        pm_elevation = pm_peak - pm_base

        if pm_elevation > 15.0:
            peak_rel_idx = int(np.argmax(pm_post))
            peak_abs_idx = flame_idx + peak_rel_idx
            decay_thresh = pm_base + max(3.0, 0.05 * pm_elevation)
            stay_base_pts = min(max(5, int(300 / dt_sec)), len(pm_smooth) - peak_abs_idx - 1)

            if stay_base_pts > 0:
                for j in range(max(peak_abs_idx, flame_idx + min_smolder_pts), len(pm_smooth) - stay_base_pts):
                    if pm_smooth[j] <= decay_thresh:
                        if np.mean(pm_smooth[j : j + stay_base_pts]) <= (decay_thresh + 0.03 * pm_elevation):
                            pm_end_idx = j
                            break

    # Reconcile: CO2 takes precedent over PM
    if pm_end_idx is not None:
        if pm_end_idx < co2_burnout_idx:
            # If PM decays while CO2 is still actively dropping, CO2 takes precedent
            if co2_smooth[pm_end_idx] > (co2_tail_min + 0.15 * co2_post_drop):
                smolder_idx = co2_burnout_idx
            else:
                smolder_idx = pm_end_idx
        else:
            # If PM stays elevated after CO2 has reached baseline floor, CO2 takes precedent
            smolder_idx = co2_burnout_idx
    else:
        smolder_idx = co2_burnout_idx

    # Guarantee burning + smoldering is strictly longer than burning only
    smolder_idx = max(smolder_idx, flame_idx + min_smolder_pts)
    smolder_idx = min(smolder_idx, len(co2_smooth) - 1)

    # Format return timestamps
    flame_dt = _parse_dt(sub_times[flame_idx])
    smolder_dt = _parse_dt(sub_times[smolder_idx])

    flame_end_str = _format_time_like(flame_dt, end_time_str) if flame_dt else sub_times[flame_idx]
    smolder_end_str = _format_time_like(smolder_dt, end_time_str) if smolder_dt else sub_times[smolder_idx]

    return flame_end_str, smolder_end_str


def request_entry(logs, choice, eval, eunits, eunc, emetric, periodpath, titlenames, timeunits, timestring, timeunc, timeuval, inputmethod, data=None):

    startname = 'start_time_' + choice
    endname = 'end_time_' + choice

    start = timestring[startname]
    end = timestring[endname]
    periodnames = [startname, endname]

    flame_end, smolder_end = None, None
    if data is not None:
        try:
            flame_end, smolder_end = detect_gasification_phase(data, choice, start, end)
        except Exception as e:
            print(f"Gasification phase detection error: {e}")

    if inputmethod == '1':
        # If gasification phases detected, prompt user with clean button options
        if flame_end or smolder_end:
            msg_opt = (
                f"Gasification phases detected for phase '{choice}':\n\n"
                f"• Start time: {start}\n"
                f"• Burning Gasification (high CO2 only): ends at {flame_end}\n"
                f"• Include Smoldering Phase (burn + smolder): ends at {smolder_end}\n"
                f"• Full Phase: ends at {end}\n\n"
                f"Choose an option to set the averaging period:"
            )
            title_opt = f"Gasification Phase Selection - {choice}"
            choices_opt = []
            if smolder_end:
                choices_opt.append("Include Smoldering")
            if flame_end:
                choices_opt.append("Burning Only")
            choices_opt.append("Full Phase")
            choices_opt.append("Manual Entry")

            btn = easygui.buttonbox(msg_opt, title_opt, choices=choices_opt)
            if btn == "Include Smoldering" and smolder_end:
                end = smolder_end
            elif btn == "Burning Only" and flame_end:
                end = flame_end
            elif btn == "Full Phase":
                end = timestring[endname]
            elif btn == "Manual Entry" or btn is None:
                # Open multenterbox for manual entry
                zeroline = 'Enter start and end times for averaging period\n'
                firstline = 'Time format = ' + eunits[startname] + '\n\n'
                secondline = 'Click OK to confirm entered values\n'
                thirdline = 'Click Cancel to exit\n'
                msg = zeroline + firstline + secondline + thirdline
                title = "Gitrdone"
                fieldnames = ['start_time', 'end_time']
                currentvals = [start, end]
                newvals = easygui.multenterbox(msg, title, fieldnames, currentvals)
                if newvals:
                    start = newvals[0]
                    end = newvals[1]

            eval[startname] = start
            eval[endname] = end
        else:
            # Manual entry when detection not available
            zeroline = 'Enter start and end times for averaging period\n'
            firstline = 'Time format = ' + eunits[startname] + '\n\n'
            secondline = 'Click OK to confirm entered values\n'
            thirdline = 'Click Cancel to exit\n'
            msg = zeroline + firstline + secondline + thirdline
            title = "Gitrdone"
            fieldnames = ['start_time', 'end_time']
            currentvals = [start, end]
            newvals = easygui.multenterbox(msg, title, fieldnames, currentvals)
            if newvals:
                start = newvals[0]
                end = newvals[1]
            eval[startname] = start
            eval[endname] = end
    else:
        # Reprocessing mode: use existing values from disk without prompting
        line = 'Reprocessing mode: using existing averaging period times from ' + periodpath
        print(line)
        logs.append(line)

    # Create new file with start and end times
    io.write_constant_outputs(periodpath, periodnames, eunits, eval, eunc, emetric)
    line = 'Created averaging times input file: ' + periodpath
    print(line)
    logs.append(line)


