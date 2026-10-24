#v0.0  Python3
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

# Stacked density plot of 2 real-time variables across multiple tests (L2).
# Real-time data from every test is pooled and drawn as a 2D frequency
# distribution: each bin's colour/opacity scales with the number of points in it.
# No regression or threshold is computed - the surface is for visual inspection.
#
# Settings are stored in <target_dir>/L2_DensityPlotParameters.csv, one row per plot.
# Interactive mode (inputmethod '1') prompts with pop-ups and writes the config.
# Reprocessing mode (inputmethod '2') reads the config and plots every row headless.

import os
import re
import csv
from datetime import datetime as dt

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
from matplotlib.gridspec import GridSpec
import easygui

ver = '0.0'

CONFIG_NAME = 'L2_DensityPlotParameters.csv'
ALL_PHASES = ['L1', 'hp', 'mp', 'lp', 'L5', 'full']
SOURCES = {
    'TimeSeriesMetrics': '_TimeSeriesMetrics_',            # full phase
    'AveragingPeriodTimeSeries': '_AveragingPeriodTimeSeries_',  # cut period
}

AUX_SUFFIXES = [
    ('_FormattedSenserionData.csv', 'sen'),
    ('_FormattedScaleData.csv', 's'),
    ('_FormattedIntScaleData.csv', 'is'),
    ('_FormattedAdamScaleData.csv', 'a'),
    ('_FormattedCombinedScaleData.csv', 'c'),
    ('_FormattedMTScaleData.csv', 'm'),
    ('_FormattedNanoscanData.csv', 'n'),
    ('_FormattedTEOMData.csv', 't'),
    ('_FormattedOPSData.csv', 'ops'),
    ('_FormattedPicoData.csv', 'p'),
    ('_FormattedFuelData.csv', 'f'),
    ('_FormattedExactData.csv', 'ex'),
]

CONFIG_COLUMNS = ['x_var', 'y_var', 'phases', 'source',
                  'x_lag_s', 'y_lag_s', 'x_reverse', 'y_reverse',
                  'x_bins', 'y_bins', 'x_min', 'x_max', 'y_min', 'y_max',
                  'color_scale', 'smooth', 'colormap']

DEFAULT_ROW = {
    'x_var': 'Chimney_T',
    'y_var': 'PM_EF',
    'phases': 'full',
    'source': 'TimeSeriesMetrics',
    'x_lag_s': '0',
    'y_lag_s': '0',
    'x_reverse': 'n',
    'y_reverse': 'n',
    'x_bins': '60',
    'y_bins': '60',
    'x_min': '',
    'x_max': '',
    'y_min': '',
    'y_max': '',
    'color_scale': 'log',
    'smooth': '0',
    'colormap': 'viridis',
}


# ---------------------------------------------------------------------------
# Config handling
# ---------------------------------------------------------------------------
def read_config(configpath):
    rows = []
    if os.path.isfile(configpath):
        with open(configpath, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for r in reader:
                row = dict(DEFAULT_ROW)
                for k in CONFIG_COLUMNS:
                    if k in r and r[k] is not None:
                        row[k] = r[k].strip()
                if row['x_var'] and row['y_var']:
                    rows.append(row)
    return rows


def write_config(configpath, rows):
    with open(configpath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CONFIG_COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, '') for k in CONFIG_COLUMNS})


def _row_label(i, r):
    return (f"{i + 1}: {r['x_var']} vs {r['y_var']} | phases={r['phases']} | "
            f"source={r['source']}")


def _to_float(val, default=None):
    try:
        if val is None or str(val).strip() == '':
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def _to_int(val, default):
    v = _to_float(val, None)
    return int(v) if v is not None and v > 0 else default


def _is_yes(val):
    return str(val).strip().lower() in ('y', 'yes', 'true', '1')


def _safe(name):
    return re.sub(r'[^A-Za-z0-9_.-]+', '', str(name).replace(' ', '_'))


# ---------------------------------------------------------------------------
# Data loading & Aux stream alignment
# ---------------------------------------------------------------------------
def _read_timeseries(path):
    """Read a LEMS time-series csv (row 1 = names, row 2 = units).
    Returns (DataFrame, units dict)."""
    df = None
    units = {}
    for enc in ('utf-8-sig', 'latin-1', 'ascii'):
        try:
            header = pd.read_csv(path, nrows=1, header=0, encoding=enc)
            df = pd.read_csv(path, header=0, skiprows=[1], encoding=enc, low_memory=False)
            units = {c: (str(header[c].iloc[0]) if c in header.columns and not pd.isna(header[c].iloc[0]) else '')
                     for c in df.columns}
            break
        except Exception:
            continue
    return df, units


def _merge_aux_stream(df_main, df_aux, aux_type):
    """Merge columns from df_aux into df_main based on nearest timestamp / time alignment."""
    if df_aux is None or df_aux.empty or df_main is None or df_main.empty:
        return df_main

    # Rename conflicting channels (e.g. Senserion TC1..TC4 -> STC1..STC4)
    aux_copy = df_aux.copy()
    renames = {}
    for c in aux_copy.columns:
        if aux_type == 'sen' and c.startswith('TC') and c in df_main.columns:
            renames[c] = 'S' + c
    if renames:
        aux_copy.rename(columns=renames, inplace=True)

    # Columns to bring over: only those not already in df_main
    cols_to_add = [c for c in aux_copy.columns if c not in df_main.columns and c not in ('time', 'seconds')]
    if not cols_to_add:
        return df_main

    # Attempt datetime alignment using 'time' column
    if 'time' in df_main.columns and 'time' in aux_copy.columns:
        main_dt = pd.to_datetime(df_main['time'], errors='coerce')
        aux_dt = pd.to_datetime(aux_copy['time'], errors='coerce')

        if main_dt.notna().sum() > 0 and aux_dt.notna().sum() > 0:
            df_main['_dt'] = main_dt
            aux_copy['_dt'] = aux_dt
            orig_order = np.arange(len(df_main))
            df_main['_orig'] = orig_order

            valid_main = df_main[df_main['_dt'].notna()].sort_values('_dt')
            valid_aux = aux_copy[aux_copy['_dt'].notna()].sort_values('_dt')

            merged = pd.merge_asof(
                valid_main,
                valid_aux[['_dt'] + cols_to_add],
                on='_dt',
                direction='nearest',
                tolerance=pd.Timedelta('10s')
            )
            res = df_main[['_orig']].merge(merged[['_orig'] + cols_to_add], on='_orig', how='left').sort_values('_orig')
            for c in cols_to_add:
                df_main[c] = res[c].values
            df_main.drop(columns=['_dt', '_orig'], errors='ignore', inplace=True)
            return df_main

    # Fallback to seconds alignment
    if 'seconds' in df_main.columns and 'seconds' in aux_copy.columns:
        main_sec = pd.to_numeric(df_main['seconds'], errors='coerce')
        aux_sec = pd.to_numeric(aux_copy['seconds'], errors='coerce')
        if main_sec.notna().sum() > 0 and aux_sec.notna().sum() > 0:
            df_main['_sec'] = main_sec
            aux_copy['_sec'] = aux_sec
            orig_order = np.arange(len(df_main))
            df_main['_orig'] = orig_order
            valid_main = df_main[df_main['_sec'].notna()].sort_values('_sec')
            valid_aux = aux_copy[aux_copy['_sec'].notna()].sort_values('_sec')
            merged = pd.merge_asof(
                valid_main,
                valid_aux[['_sec'] + cols_to_add],
                on='_sec',
                direction='nearest',
                tolerance=10.0
            )
            res = df_main[['_orig']].merge(merged[['_orig'] + cols_to_add], on='_orig', how='left').sort_values('_orig')
            for c in cols_to_add:
                df_main[c] = res[c].values
            df_main.drop(columns=['_sec', '_orig'], errors='ignore', inplace=True)
            return df_main

    # Simple row-index alignment fallback if same length or truncated
    min_len = min(len(df_main), len(aux_copy))
    for c in cols_to_add:
        col_vals = [np.nan] * len(df_main)
        col_vals[:min_len] = aux_copy[c].iloc[:min_len]
        df_main[c] = col_vals

    return df_main


class _DataCache:
    """Caches loaded files and auxiliary streams so each test/phase is only read once per run."""

    def __init__(self, list_directory, list_testname, logs):
        self.list_directory = list_directory
        self.list_testname = list_testname
        self.logs = logs
        self.cache = {}
        self.units = {}
        self.aux_cache = {}

    def _get_aux_data(self, t):
        """Load all auxiliary files for test t (cached across phases)."""
        if t in self.aux_cache:
            return self.aux_cache[t]

        aux_dict = {}
        directory = self.list_directory[t]
        testname = self.list_testname[t]

        for suffix, aux_type in AUX_SUFFIXES:
            path = os.path.join(directory, testname + suffix)
            if os.path.isfile(path):
                try:
                    df, units = _read_timeseries(path)
                    if df is not None and not df.empty:
                        aux_dict[aux_type] = (df, units)
                        for k, v in units.items():
                            renamed_k = 'S' + k if aux_type == 'sen' and k.startswith('TC') else k
                            self.units.setdefault(renamed_k, v)
                        line = f'loaded auxiliary data [{testname}]: {os.path.basename(path)}'
                        print(line)
                        self.logs.append(line)
                except Exception as e:
                    line = f'could not read aux file {path}: {e}'
                    print(line)
                    self.logs.append(line)

        self.aux_cache[t] = aux_dict
        return aux_dict

    def get(self, t, phase, source):
        key = (t, phase, source)
        if key not in self.cache:
            directory = self.list_directory[t]
            testname = self.list_testname[t]
            path = os.path.join(directory, testname + SOURCES[source] + phase + '.csv')

            # Fallback check if chosen source doesn't exist
            if not os.path.isfile(path):
                alt_source = 'AveragingPeriodTimeSeries' if source == 'TimeSeriesMetrics' else 'TimeSeriesMetrics'
                alt_path = os.path.join(directory, testname + SOURCES[alt_source] + phase + '.csv')
                if os.path.isfile(alt_path):
                    path = alt_path

            if os.path.isfile(path):
                try:
                    df, units = _read_timeseries(path)
                    if df is not None:
                        for k, v in units.items():
                            self.units.setdefault(k, v)
                        # Merge auxiliary streams for this test
                        aux_dict = self._get_aux_data(t)
                        for aux_type, (df_aux, _) in aux_dict.items():
                            df = _merge_aux_stream(df, df_aux, aux_type)

                        self.cache[key] = df
                        line = 'loaded: ' + path
                    else:
                        self.cache[key] = None
                        line = f'could not parse {path}'
                except Exception as e:
                    self.cache[key] = None
                    line = f'could not read {path}: {e}'
            else:
                self.cache[key] = None
                line = 'missing (skipped): ' + path

            print(line)
            self.logs.append(line)
        return self.cache[key]

    def available_columns(self, phases, source):
        all_cols = []
        seen = set()
        for phase in phases:
            for t in range(len(self.list_directory)):
                df = self.get(t, phase, source)
                if df is None:
                    continue
                for c in df.columns:
                    if c not in seen and c not in ('time', 'seconds', 'dateobjects', 'datenumbers'):
                        seen.add(c)
                        all_cols.append(c)
        return all_cols


def _lag_rows(df, lag_s):
    """Convert a lag in seconds to a number of rows using the 'seconds' column (fallback 1 Hz)."""
    if not lag_s:
        return 0
    dt_s = 1.0
    if 'seconds' in df.columns:
        sec = pd.to_numeric(df['seconds'], errors='coerce').dropna()
        if len(sec) > 2:
            d = np.median(np.diff(sec.values))
            if d > 0:
                dt_s = d
    return int(round(lag_s / dt_s))


def _stack(cache, phase, source, x_var, y_var, x_lag, y_lag):
    """Stack X/Y pairs from all tests for one phase. Lags are applied within each test.
    A positive lag pairs the value recorded lag_s seconds LATER with the current time
    (use it for a sensor that responds slowly)."""
    frames = []
    n_tests = 0
    for t in range(len(cache.list_directory)):
        df = cache.get(t, phase, source)
        if df is None:
            continue
        if x_var not in df.columns or y_var not in df.columns:
            line = f"Test [{cache.list_testname[t]}] phase {phase} does not contain '{x_var}' or '{y_var}'; test skipped."
            print(line)
            cache.logs.append(line)
            continue

        x = pd.to_numeric(df[x_var], errors='coerce')
        y = pd.to_numeric(df[y_var], errors='coerce')
        nx = _lag_rows(df, x_lag)
        ny = _lag_rows(df, y_lag)
        if nx:
            x = x.shift(-nx)
        if ny:
            y = y.shift(-ny)
        sec = pd.to_numeric(df['seconds'], errors='coerce') if 'seconds' in df.columns else pd.Series(np.arange(len(df)))
        part = pd.DataFrame({'test': cache.list_testname[t], 'seconds': sec, 'X': x, 'Y': y})
        part = part.replace([np.inf, -np.inf], np.nan).dropna(subset=['X', 'Y'])
        if len(part):
            frames.append(part)
            n_tests += 1

    if not frames:
        return pd.DataFrame(columns=['test', 'seconds', 'X', 'Y']), 0
    return pd.concat(frames, ignore_index=True), n_tests


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
def _alpha_cmap(name):
    """Colormap whose opacity ramps up with value, so sparse bins are faint and dense bins are opaque."""
    try:
        base = matplotlib.colormaps[name]
    except Exception:
        base = plt.get_cmap(name)
    cols = base(np.linspace(0, 1, 256))
    cols[:, 3] = np.linspace(0.15, 1.0, 256)
    cmap = mcolors.ListedColormap(cols)
    cmap.set_bad((1, 1, 1, 0))     # empty bins fully transparent
    cmap.set_under((1, 1, 1, 0))
    return cmap


def _plot_density(stacked, n_tests, row, phase, units, savepath, show):
    x = stacked['X'].values
    y = stacked['Y'].values

    x_min = _to_float(row['x_min'], np.nanmin(x))
    x_max = _to_float(row['x_max'], np.nanmax(x))
    y_min = _to_float(row['y_min'], np.nanmin(y))
    y_max = _to_float(row['y_max'], np.nanmax(y))
    if x_max <= x_min:
        x_max = x_min + 1
    if y_max <= y_min:
        y_max = y_min + 1

    inrange = (x >= x_min) & (x <= x_max) & (y >= y_min) & (y <= y_max)
    x = x[inrange]
    y = y[inrange]

    x_bins = _to_int(row['x_bins'], 60)
    y_bins = _to_int(row['y_bins'], 60)
    xedges = np.linspace(x_min, x_max, x_bins + 1)
    yedges = np.linspace(y_min, y_max, y_bins + 1)
    counts, _, _ = np.histogram2d(x, y, bins=[xedges, yedges])   # shape (x_bins, y_bins)

    surface = counts.copy()
    smooth = _to_float(row['smooth'], 0) or 0
    if smooth > 0:
        try:
            from scipy.ndimage import gaussian_filter
            surface = gaussian_filter(surface, sigma=smooth)
        except ImportError:
            print('scipy not available - smoothing skipped')

    masked = np.ma.masked_where(surface <= (0.01 if smooth > 0 else 0), surface)
    cmap = _alpha_cmap(row.get('colormap') or 'viridis')
    vmax = masked.max() if masked.count() else 1
    if str(row['color_scale']).lower() == 'log':
        vmin = max(masked.min(), 1e-3) if masked.count() else 1
        if smooth == 0:
            vmin = 1
        norm = mcolors.LogNorm(vmin=vmin, vmax=max(vmax, vmin * 10))
    else:
        norm = mcolors.Normalize(vmin=0, vmax=vmax)

    fig = plt.figure(figsize=(11, 9))
    gs = GridSpec(2, 3, width_ratios=[4, 1, 0.15], height_ratios=[1, 4], wspace=0.05, hspace=0.05, figure=fig)
    ax = fig.add_subplot(gs[1, 0])
    axx = fig.add_subplot(gs[0, 0], sharex=ax)
    axy = fig.add_subplot(gs[1, 1], sharey=ax)
    cax = fig.add_subplot(gs[1, 2])

    mesh = ax.pcolormesh(xedges, yedges, masked.T, cmap=cmap, norm=norm, shading='flat')
    cb = fig.colorbar(mesh, cax=cax)
    cb.set_label('number of points' + (' (smoothed)' if smooth > 0 else ''))

    axx.hist(x, bins=xedges, color='grey', alpha=0.7)
    axy.hist(y, bins=yedges, color='grey', alpha=0.7, orientation='horizontal')
    axx.set_ylabel('count')
    axy.set_xlabel('count')
    plt.setp(axx.get_xticklabels(), visible=False)
    plt.setp(axy.get_yticklabels(), visible=False)

    xu = units.get(row['x_var'], '')
    yu = units.get(row['y_var'], '')
    xlabel = row['x_var'] + (f' ({xu})' if xu else '')
    ylabel = row['y_var'] + (f' ({yu})' if yu else '')
    if _to_float(row['x_lag_s'], 0):
        xlabel += f"  [lag {row['x_lag_s']} s]"
    if _to_float(row['y_lag_s'], 0):
        ylabel += f"  [lag {row['y_lag_s']} s]"
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    if _is_yes(row['x_reverse']):
        ax.invert_xaxis()
    if _is_yes(row['y_reverse']):
        ax.invert_yaxis()
    ax.grid(True, alpha=0.3)

    src = 'cut period' if row['source'] == 'AveragingPeriodTimeSeries' else 'full phase'
    axx.set_title(f"{row['x_var']} vs {row['y_var']} | phase: {phase} ({src}) | "
                  f"{n_tests} tests, {len(x)} points")

    fig.savefig(savepath, dpi=150, bbox_inches='tight')
    if show:
        plt.show()
    plt.close(fig)
    return xedges, yedges, counts


def _write_counts(path, xedges, yedges, counts):
    """Write bin-count grid: rows = Y bins, columns = X bins (edges given)."""
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['y_bin_low', 'y_bin_high'] + [f'{xedges[i]:.6g}..{xedges[i + 1]:.6g}' for i in range(len(xedges) - 1)])
        for j in range(len(yedges) - 1):
            w.writerow([f'{yedges[j]:.6g}', f'{yedges[j + 1]:.6g}'] + [int(c) for c in counts[:, j]])


# ---------------------------------------------------------------------------
# Interactive prompting
# ---------------------------------------------------------------------------
def _choose_index(choices, default):
    try:
        return choices.index(default) if default in choices else 0
    except Exception:
        return 0


def _prompt_row(row, cache):
    """Walk through pop-ups, pre-filled from row. Returns updated row or None if cancelled."""
    row = dict(row)

    src_choices = ['TimeSeriesMetrics (full phase)', 'AveragingPeriodTimeSeries (cut period)']
    pre = 1 if row['source'] == 'AveragingPeriodTimeSeries' else 0
    try:
        src = easygui.choicebox('Select data source', 'Density plot', src_choices, preselect=pre)
    except TypeError:
        src = easygui.choicebox('Select data source', 'Density plot', src_choices)
    if not src:
        return None
    row['source'] = 'AveragingPeriodTimeSeries' if src.startswith('Averaging') else 'TimeSeriesMetrics'

    current = [p for p in row['phases'].split(';') if p in ALL_PHASES]
    pre = [ALL_PHASES.index(p) for p in current] or [ALL_PHASES.index('full')]
    msg = 'Select phases (one figure is made per phase)'
    try:
        phases = easygui.multchoicebox(msg, 'Density plot', ALL_PHASES, preselect=pre)
    except TypeError:
        phases = easygui.multchoicebox(msg, 'Density plot', ALL_PHASES)
    if not phases:
        return None
    row['phases'] = ';'.join(phases)

    names = cache.available_columns(phases, row['source'])
    names = [n for n in names if n not in ('time', 'seconds')]
    if not names:
        easygui.msgbox('No data files found for the selected phases/source.', 'Density plot')
        return None

    try:
        xv = easygui.choicebox('Select X axis variable', 'Density plot', names, preselect=_choose_index(names, row['x_var']))
    except TypeError:
        xv = easygui.choicebox('Select X axis variable', 'Density plot', names)
    if not xv:
        return None
    try:
        yv = easygui.choicebox('Select Y axis variable', 'Density plot', names, preselect=_choose_index(names, row['y_var']))
    except TypeError:
        yv = easygui.choicebox('Select Y axis variable', 'Density plot', names)
    if not yv:
        return None
    row['x_var'] = xv
    row['y_var'] = yv

    fields = ['x_lag_s', 'y_lag_s', 'x_reverse', 'y_reverse', 'x_bins', 'y_bins',
              'x_min', 'x_max', 'y_min', 'y_max', 'color_scale', 'smooth', 'colormap']
    labels = ['X lag (s, + = use later X value)', 'Y lag (s, + = use later Y value)',
              'Reverse X axis (y/n)', 'Reverse Y axis (y/n)',
              'X bins', 'Y bins',
              'X min (blank=auto)', 'X max (blank=auto)', 'Y min (blank=auto)', 'Y max (blank=auto)',
              'Colour scale (log/linear)', 'Smoothing (bins, 0=none)', 'Colormap (e.g. viridis, Blues, magma)']
    vals = easygui.multenterbox('Plot settings', 'Density plot', labels, [row[f] for f in fields])
    if vals is None:
        return None
    for f, v in zip(fields, vals):
        row[f] = (v or '').strip()
    return row


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def LEMS_L2_DensityPlot(list_directory, list_testname, target_dir, logpath, inputmethod='1'):
    timestampstring = dt.now().strftime('%Y%m%d %H:%M:%S')
    line = 'LEMS_L2_DensityPlot v' + ver + '   ' + timestampstring
    print(line)
    logs = [line]

    plt.rcParams['savefig.directory'] = target_dir
    configpath = os.path.join(target_dir, CONFIG_NAME)
    rows = read_config(configpath)
    cache = _DataCache(list_directory, list_testname, logs)
    interactive = (inputmethod != '2')

    if interactive:
        RUN_ALL = 'Run all saved plots (no changes)'
        NEW = 'Add a new plot'
        options = [_row_label(i, r) for i, r in enumerate(rows)] + [NEW]
        if rows:
            options = [RUN_ALL] + options
        if len(options) == 1:
            choice = NEW
        else:
            choice = easygui.choicebox('Select a saved plot to edit/run, run all, or add a new plot.\n'
                                       'Config file: ' + configpath, 'Density plot', options)
        if not choice:
            line = 'Density plot cancelled.'
            print(line)
            logs.append(line)
            _write_log(logpath, logs)
            return []

        if choice == RUN_ALL:
            to_run = rows
        else:
            idx = None if choice == NEW else options.index(choice) - 1  # -1 for RUN_ALL entry
            base = dict(DEFAULT_ROW) if idx is None else rows[idx]
            new_row = _prompt_row(base, cache)
            if new_row is None:
                line = 'Density plot cancelled.'
                print(line)
                logs.append(line)
                _write_log(logpath, logs)
                return []
            if idx is None:
                rows.append(new_row)
            else:
                rows[idx] = new_row
            write_config(configpath, rows)
            line = 'Saved settings to ' + configpath
            print(line)
            logs.append(line)
            to_run = [new_row]
    else:
        if not rows:
            write_config(configpath, [DEFAULT_ROW])
            line = ('No density plot config found. A default config was written to ' + configpath +
                    ' - edit it or run in interactive mode, then rerun.')
            print(line)
            logs.append(line)
            _write_log(logpath, logs)
            raise FileNotFoundError(line)
        to_run = rows

    saved = []
    for row in to_run:
        phases = [p for p in row['phases'].split(';') if p.strip()]
        if row['source'] not in SOURCES:
            row['source'] = 'TimeSeriesMetrics'
        tag = '_cut' if row['source'] == 'AveragingPeriodTimeSeries' else ''
        x_lag = _to_float(row['x_lag_s'], 0) or 0
        y_lag = _to_float(row['y_lag_s'], 0) or 0
        for phase in phases:
            stacked, n_tests = _stack(cache, phase, row['source'], row['x_var'], row['y_var'], x_lag, y_lag)
            if stacked.empty:
                line = f"No {row['x_var']}/{row['y_var']} data for phase {phase} ({row['source']}); skipped."
                print(line)
                logs.append(line)
                continue
            base = os.path.join(target_dir, f"L2_Density_{_safe(row['x_var'])}_vs_{_safe(row['y_var'])}_{phase}{tag}")
            pngpath = base + '.png'
            xedges, yedges, counts = _plot_density(stacked, n_tests, row, phase, cache.units, pngpath, show=interactive)
            _write_counts(base + '_counts.csv', xedges, yedges, counts)
            stacked.to_csv(base + '_stacked.csv', index=False)
            line = (f"Phase {phase}: {n_tests} tests, {len(stacked)} points "
                    f"({int(counts.sum())} inside axis range). Saved: {pngpath}")
            print(line)
            logs.append(line)
            saved.append(pngpath)

    _write_log(logpath, logs)
    return saved


def _write_log(logpath, logs):
    if not logpath:
        return
    try:
        with open(logpath, 'a', encoding='utf-8', errors='replace') as f:
            for line in logs:
                f.write(line + '\n')
    except Exception as e:
        print(f'Warning: could not write log {logpath}: {e}')
