# v0.1 Python3

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

import csv
import math
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
from datetime import datetime as dt


def has_uncertainty_columns(csv_path):
    """Return True if the first header row of ``csv_path`` includes any ``_uc`` column."""
    try:
        with open(csv_path, 'r', encoding='utf-8-sig', errors='replace') as csvfile:
            header = next(csv.reader(csvfile), [])
        return any(col.strip().endswith('_uc') for col in header)
    except Exception:
        return False


def _lighten_color(color, factor=0.6):
    """Lighten an RGBA/hex/named color toward white by ``factor`` (0..1)."""
    try:
        rgb = mcolors.to_rgb(color)
        return tuple(1.0 - factor * (1.0 - c) for c in rgb)
    except Exception:
        return (0.7, 0.7, 0.7)


def _load_plot_config(plotpath):
    """Read plots.csv (Variable, Plotted, Scale, Colors) and return plotted channels and metadata."""
    plotted = []
    scale_factors = {}
    colors = {}

    with open(plotpath, 'r', encoding='utf-8-sig', errors='replace') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader, None)
        for row in reader:
            if not row:
                continue
            name = row[0].strip()
            if not name or '_uc' in name:
                continue
            is_plotted = row[1].strip() if len(row) > 1 else '0'
            if is_plotted != '1':
                continue
            scale_raw = row[2].strip() if len(row) > 2 else '1'
            try:
                scale_val = float(scale_raw) if scale_raw != '' else 1.0
            except ValueError:
                scale_val = 1.0
            color_val = row[3].strip() if len(row) > 3 else ''
            plotted.append(name)
            scale_factors[name] = scale_val
            colors[name] = color_val

    return plotted, scale_factors, colors


def _resolve_x_key(name, fnames, fcnames, exnames, snames, isnames, anames,
                   cnames, mnames, nnames, tnames, sennames, opsnames, pnames):
    """Return the matching datenumbers key in ``data`` for channel ``name``."""
    groups = (
        (fnames, 'fdatenumbers'),
        (fcnames, 'fcdatenumbers'),
        (exnames, 'exdatenumbers'),
        (snames, 'sdatenumbers'),
        (isnames, 'isdatenumbers'),
        (anames, 'adatenumbers'),
        (cnames, 'cdatenumbers'),
        (mnames, 'mdatenumbers'),
        (nnames, 'ndatenumbers'),
        (tnames, 'tdatenumbers'),
        (sennames, 'sendatenumbers'),
        (opsnames, 'opsdatenumbers'),
        (pnames, 'pdatenumbers'),
    )
    for group_names, key in groups:
        if group_names and name in group_names:
            return key
    return 'datenumbers'


def _extract_series_with_uncertainty(name, data, x_key, scale_factor):
    """Extract aligned (x_vals, y_vals, y_upper, y_lower) lists for a channel."""
    raw_y = data.get(name, [])
    raw_uc = data.get(name + '_uc', [])
    raw_x = data.get(x_key) or data.get('datenumbers') or data.get('seconds') or list(range(len(raw_y)))

    x_vals = []
    y_vals = []
    x_uc = []
    y_upper = []
    y_lower = []

    n_points = min(len(raw_x), len(raw_y))
    for i in range(n_points):
        xv = raw_x[i]
        yv = raw_y[i]
        try:
            xf = float(xv.n if hasattr(xv, 'n') else xv)
        except (ValueError, TypeError):
            continue
        if math.isnan(xf):
            continue

        if hasattr(yv, 'n'):
            yf_raw = float(yv.n)
            uc_raw = abs(float(yv.s))
            has_point_uc = True
        else:
            try:
                yf_raw = float(yv)
            except (ValueError, TypeError):
                continue
            uc_raw = None
            has_point_uc = False
            if i < len(raw_uc) and raw_uc[i] != '':
                try:
                    uc_raw = abs(float(raw_uc[i]))
                    if not math.isnan(uc_raw):
                        has_point_uc = True
                except (ValueError, TypeError):
                    has_point_uc = False

        if math.isnan(yf_raw):
            continue

        yf = yf_raw * scale_factor
        x_vals.append(xf)
        y_vals.append(yf)

        if has_point_uc and uc_raw is not None and not math.isnan(uc_raw):
            scaled_uc = uc_raw * abs(scale_factor)
            x_uc.append(xf)
            y_upper.append(yf + scaled_uc)
            y_lower.append(yf - scaled_uc)

    return x_vals, y_vals, x_uc, y_upper, y_lower, (x_key != 'seconds' and 'datenumbers' in data)


def _plot_data_onto_axes(ax, plotted, scale_factors, colors, units, data,
                         fnames, fcnames, exnames, snames, isnames, anames,
                         cnames, mnames, nnames, tnames, sennames, opsnames, pnames):
    """Plot each selected channel and its dashed +-uncertainty band onto ``ax``."""
    used_dates = False
    for name in plotted:
        if name not in data:
            continue
        x_key = _resolve_x_key(
            name, fnames, fcnames, exnames, snames, isnames, anames,
            cnames, mnames, nnames, tnames, sennames, opsnames, pnames
        )
        sf = scale_factors.get(name, 1.0)
        x_vals, y_vals, x_uc, y_upper, y_lower, is_date = _extract_series_with_uncertainty(
            name, data, x_key, sf
        )
        if not x_vals:
            continue
        used_dates = used_dates or is_date

        unit_str = units.get(name, '')
        scale_prefix = f'{sf:g}x ' if sf != 1.0 else ''
        label = f'{scale_prefix}{name} ({unit_str})' if unit_str else f'{scale_prefix}{name}'

        plot_kwargs = {'label': label, 'linewidth': 1.2}
        specified_color = colors.get(name, '')
        if specified_color:
            plot_kwargs['color'] = specified_color

        lines = ax.plot(x_vals, y_vals, **plot_kwargs)
        line_color = lines[0].get_color()

        if x_uc:
            uc_color = _lighten_color(line_color, factor=0.6)
            ax.plot(x_uc, y_upper, linestyle='--', linewidth=0.9, alpha=0.85, color=uc_color, label=f'{name} +/- UC')
            ax.plot(x_uc, y_lower, linestyle='--', linewidth=0.9, alpha=0.85, color=uc_color)

    if used_dates:
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax.grid(True, alpha=0.3)
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(fontsize=8, loc='best')


def PEMS_PlotUncertainty(names, units, data, fnames, fcnames, exnames, snames, isnames,
                         anames, cnames, mnames, nnames, tnames, sennames, opsnames,
                         pnames, plotpath, savefig):
    """Plot time-series channels with dashed uncertainty envelopes for a single phase/test."""
    ver = '0.1'
    timestampstring = dt.now().strftime("%Y%m%d %H:%M:%S")
    print('PEMS_PlotUncertainty v' + ver + '   ' + timestampstring)

    plotted, scale_factors, colors = _load_plot_config(plotpath)

    fig, ax = plt.subplots(figsize=(12, 6))
    _plot_data_onto_axes(
        ax, plotted, scale_factors, colors, units, data,
        fnames, fcnames, exnames, snames, isnames, anames,
        cnames, mnames, nnames, tnames, sennames, opsnames, pnames
    )
    ax.set_xlabel('Time')
    ax.set_ylabel('Value')
    ax.set_title('Real-Time Time Series with Uncertainty')
    fig.autofmt_xdate()
    fig.tight_layout()

    if savefig:
        fig.savefig(savefig, dpi=200)
        print('Saved uncertainty plot to: ' + savefig)

    if matplotlib.get_backend().lower() != 'agg':
        plt.show()
    else:
        plt.close(fig)


def PEMS_PlotUncertainty_Grid(names, units, all_data, phases, fnames, fcnames, exnames,
                              snames, isnames, anames, cnames, mnames, nnames, tnames,
                              sennames, opsnames, pnames, plotpath, savefig):
    """Plot a multi-phase grid of time-series channels with dashed uncertainty envelopes."""
    ver = '0.1'
    timestampstring = dt.now().strftime("%Y%m%d %H:%M:%S")
    print('PEMS_PlotUncertainty_Grid v' + ver + '   ' + timestampstring)

    if not all_data:
        return

    plotted, scale_factors, colors = _load_plot_config(plotpath)
    n_phases = len(all_data)
    fig, axes = plt.subplots(n_phases, 1, figsize=(12, max(4, 3.5 * n_phases)), squeeze=False)

    for idx, phase_data in enumerate(all_data):
        ax = axes[idx, 0]
        _plot_data_onto_axes(
            ax, plotted, scale_factors, colors, units, phase_data,
            fnames, fcnames, exnames, snames, isnames, anames,
            cnames, mnames, nnames, tnames, sennames, opsnames, pnames
        )
        phase_label = phases[idx] if idx < len(phases) else f'Phase {idx + 1}'
        ax.set_title(f'Phase: {phase_label}')
        ax.set_ylabel('Value')

    axes[-1, 0].set_xlabel('Time')
    fig.autofmt_xdate()
    fig.tight_layout()

    if savefig:
        fig.savefig(savefig, dpi=200)
        print('Saved uncertainty grid plot to: ' + savefig)

    if matplotlib.get_backend().lower() != 'agg':
        plt.show()
    else:
        plt.close(fig)
