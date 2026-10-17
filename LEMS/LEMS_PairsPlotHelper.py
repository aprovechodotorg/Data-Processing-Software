# Helper utilities for pair-aware plotting in LEMS L3 (Steps 23-29)
import os
import csv
import textwrap
import matplotlib
import matplotlib.pyplot as plt


def load_pairs_csv(csv_path):
    """
    Parses PairsUnformattedDataL2FilePaths.csv.

    Expected CSV columns (case-insensitive):
      - Group: test group name (e.g. US Stove VG2020)
      - Name: test description or pair group name
      - test_code: code of the test (e.g. 1B, 1R2)
      - data_key: data key or difference/pair syntax (e.g. 1B, 1R2, d1B/1R2)
      - path: path to UnFormattedDataL2.csv

    Returns:
      paths: list of UnFormattedDataL2.csv file paths (ordered)
      labels: list of test names/labels corresponding to paths
      pair_groups: list of pair group dictionaries:
              [{'name': str, 'start': int, 'end': int, 'indices': list, 'data_key': str}, ...]
              where start and end are 0-based indices into paths.
      test_groups: list of group dictionaries formed from the Group column:
              [{'name': str, 'start': int, 'end': int, 'indices': list, 'data_key': ''}, ...]
    """
    if not os.path.exists(csv_path):
        return [], [], [], []

    paths = []
    labels = []
    pair_groups = []
    test_groups = []
    key_to_idx = {}
    current_test_group = None

    with open(csv_path, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        idx = 0
        raw_rows = []
        for row in reader:
            # normalize row keys
            row_norm = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            raw_rows.append(row_norm)

    # First pass: collect test paths, labels, keys, and group spans
    for row in raw_rows:
        path = row.get('path', '')
        name = row.get('name', '')
        test_code = row.get('test_code', '')
        data_key = row.get('data_key', '')
        group_col = row.get('group', '').strip()

        if path:
            paths.append(path)
            label = name if name else (test_code if test_code else f"Test {idx + 1}")
            labels.append(label)
            if data_key:
                key_to_idx[data_key] = idx
            if test_code:
                key_to_idx[test_code] = idx

            # Track contiguous runs of identical non-empty Group values
            if group_col:
                if current_test_group and current_test_group['name'] == group_col:
                    current_test_group['end'] = idx
                    current_test_group['indices'].append(idx)
                else:
                    if current_test_group:
                        test_groups.append(current_test_group)
                    current_test_group = {
                        'name': group_col,
                        'start': idx,
                        'end': idx,
                        'indices': [idx],
                        'data_key': ''
                    }
            else:
                # Blank group becomes its own individual 1-test block
                if current_test_group:
                    test_groups.append(current_test_group)
                    current_test_group = None
                test_groups.append({
                    'name': '',
                    'start': idx,
                    'end': idx,
                    'indices': [idx],
                    'data_key': ''
                })

            idx += 1

    if current_test_group:
        test_groups.append(current_test_group)

    # Second pass: collect pair definitions
    for row in raw_rows:
        path = row.get('path', '')
        name = row.get('name', '')
        test_code = row.get('test_code', '')
        data_key = row.get('data_key', '')

        if not path and (data_key or test_code):
            raw_key = data_key or test_code
            # Match pair syntax like d1B/1R2 or 1B/1R2
            if '/' in raw_key or raw_key.lower().startswith('d'):
                clean_key = raw_key.lstrip('dD')
                member_codes = [c.strip() for c in clean_key.split('/') if c.strip()]
                indices = [key_to_idx[c] for c in member_codes if c in key_to_idx]
                if indices:
                    group_name = name if name else raw_key
                    pair_groups.append({
                        'name': group_name,
                        'start': min(indices),
                        'end': max(indices),
                        'indices': indices,
                        'data_key': raw_key
                    })

    return paths, labels, pair_groups, test_groups


def format_plot_labels(labels, max_width=18):
    """Wraps text in labels for cleaner display on x-axis."""
    formatted = []
    for lbl in labels:
        s = str(lbl).strip()
        if '\n' in s:
            formatted.append(s)
        else:
            wrapped = '\n'.join(textwrap.wrap(s, width=max_width))
            formatted.append(wrapped)
    return formatted


def apply_pair_shading(ax, pair_groups, x_offset=1, num_tests=None, shade_color='#f2f2f2', show_titles=True):
    """
    Applies alternating shading, divider lines, and top pair header boxes to a matplotlib Axes.

    Parameters:
      ax: matplotlib.axes.Axes
      pair_groups: list of group dicts with 'name', 'start', 'end'
      x_offset: 1 for 1-based coordinates (boxplots, scatter), 0 for 0-based coordinates (barcharts)
      num_tests: total count of tests; if None, derived from pair_groups
      shade_color: background color for alternating shaded pairs
      show_titles: whether to place group names in top header boxes
    """
    if not pair_groups:
        return

    if num_tests is None:
        num_tests = max(g['end'] for g in pair_groups) + 1

    # Set x limits flush with pair boundaries
    x_min = (0 if x_offset == 0 else 1) - 0.5
    x_max = num_tests - 0.5 + (0 if x_offset == 0 else 1)
    ax.set_xlim(x_min, x_max)

    trans = matplotlib.transforms.blended_transform_factory(ax.transData, ax.transAxes)

    for g_idx, group in enumerate(pair_groups):
        start_idx = group['start']
        end_idx = group['end']
        group_name = group['name']

        x_left = (start_idx + x_offset) - 0.5
        x_right = (end_idx + x_offset) + 0.5
        x_center = (x_left + x_right) / 2.0

        # Alternating shading
        if g_idx % 2 == 0:
            ax.axvspan(x_left, x_right, facecolor=shade_color, edgecolor='none', zorder=0)

        # Vertical divider between groups
        if g_idx < len(pair_groups) - 1:
            ax.axvline(x=x_right, color='#d0d0d0', linestyle='-', linewidth=1.0, zorder=1)

        # Top header box with group / pair name
        if show_titles and group_name:
            box_face = '#e8e8e8' if (g_idx % 2 == 0) else '#ffffff'
            span_count = max(1, end_idx - start_idx + 1)
            wrap_width = 10 if span_count == 1 else max(16, 14 * span_count)
            wrapped_title = '\n'.join(textwrap.wrap(group_name, width=wrap_width)) if '\n' not in group_name else group_name
            ax.text(
                x_center, 1.02, wrapped_title,
                transform=trans,
                ha='center', va='bottom',
                fontsize=8.5, fontweight='bold', color='#333333',
                bbox=dict(
                    boxstyle='square,pad=0.25',
                    facecolor=box_face,
                    edgecolor='#cccccc',
                    linewidth=0.8
                )
            )


# Unit conversion lookup table matching Step 31 (LEMS_CustomFormatted_L3.py)
UNIT_CONVERSIONS = {
    ('g/min', 'lb/hr'):   60.0 / 453.592,
    ('lb/hr', 'g/min'):   453.592 / 60.0,
    ('g',     'kg'):      0.001,
    ('kg',    'g'):       1000.0,
    ('g',     'lb'):      1.0 / 453.592,
    ('lb',    'g'):       453.592,
    ('kg',    'lb'):      1.0 / 0.45359237,
    ('lb',    'kg'):      0.45359237,
    ('mg',    'g'):       0.001,
    ('g',     'mg'):      1000.0,
    ('mg',    'kg'):      1e-6,
    ('kg',    'mg'):      1e6,
    ('mg/min','g/min'):   0.001,
    ('g/min', 'mg/min'):  1000.0,
    ('mg/hr', 'g/hr'):    0.001,
    ('g/hr',  'mg/hr'):   1000.0,
    ('kJ',    'MJ'):      0.001,
    ('MJ',    'kJ'):      1000.0,
    ('J',     'kJ'):      0.001,
    ('kJ',    'J'):       1000.0,
    ('J',     'MJ'):      1e-6,
    ('MJ',    'J'):       1e6,
    ('kJ/kg', 'MJ/kg'):   0.001,
    ('MJ/kg', 'kJ/kg'):   1000.0,
    ('W',     'kW'):      0.001,
    ('kW',    'W'):       1000.0,
    ('min',   'hr'):      1.0 / 60.0,
    ('hr',    'min'):     60.0,
    ('s',     'hr'):      1.0 / 3600.0,
    ('hr',    's'):       3600.0,
    ('s',     'min'):     1.0 / 60.0,
    ('min',   's'):       60.0,
    ('g/hr',  'lb/hr'):   1.0 / 453.592,
    ('lb/hr', 'g/hr'):    453.592,
    ('mg/MJ', 'g/MJ'):    0.001,
    ('g/MJ',  'mg/MJ'):   1000.0,
    ('mg/m3', 'ug/m3'):   1000.0,
    ('ug/m3', 'mg/m3'):   0.001,
    ('ppm',   '%'):       0.0001,
    ('%',     'ppm'):     10000.0,
}


def convert_value(val, from_units, to_units):
    """
    Apply unit conversion to a numeric value matching step 31 logic.
    Returns converted float value or original val if no conversion is needed or found.
    """
    if val is None or val == '':
        return val
    from_u = str(from_units).strip() if from_units else ''
    to_u = str(to_units).strip() if to_units else ''
    if not from_u or not to_u or from_u.lower() == to_u.lower():
        try:
            return float(val)
        except (ValueError, TypeError):
            return val
    factor = UNIT_CONVERSIONS.get((from_u, to_u))
    if factor is None:
        # Check case-insensitive / trimmed match
        from_clean = from_u.replace(' ', '').lower()
        to_clean = to_u.replace(' ', '').lower()
        for (f, t), fac in UNIT_CONVERSIONS.items():
            if f.replace(' ', '').lower() == from_clean and t.replace(' ', '').lower() == to_clean:
                factor = fac
                break
    if factor is None:
        try:
            return float(val)
        except (ValueError, TypeError):
            return val
    try:
        return float(val) * factor
    except (ValueError, TypeError):
        return val


def find_lp_file_for_path(path, lp_inputpath=None):
    """
    Finds the corresponding UnFormattedDataL2_lp.csv for a given UnFormattedDataL2.csv path.
    1. Checks adjacent UnFormattedDataL2_lp.csv in the same directory (case-insensitive).
    2. Checks lp_inputpath list for a matching group directory or normalized path.
    """
    if not path:
        return None
    parent_dir = os.path.dirname(path)
    for fname in ('UnFormattedDataL2_lp.csv', 'UnformattedDataL2_lp.csv'):
        cand = os.path.join(parent_dir, fname)
        if os.path.isfile(cand):
            return cand

    if lp_inputpath:
        norm_parent = os.path.normcase(os.path.normpath(parent_dir))
        for lp_p in lp_inputpath:
            if not lp_p:
                continue
            lp_parent = os.path.normcase(os.path.normpath(os.path.dirname(lp_p)))
            if lp_parent == norm_parent and os.path.isfile(lp_p):
                return lp_p
            if os.path.basename(lp_parent).strip().lower() == os.path.basename(norm_parent).strip().lower() and os.path.isfile(lp_p):
                return lp_p
    return None


def merge_lp_cut_data_for_group(path, new_names, new_units, values, data, lp_inputpath=None, logs=None):
    """
    Checks for an LP cut data file (UnFormattedDataL2_lp.csv) corresponding to path.
    If found, loads metrics and adds them to new_names, new_units, values, and data
    with suffix '_cut_lp'. Specifically, firepower_carbon -> firepower_carbon_cut_lp.
    """
    import LEMS_DataProcessing_IO as io_helper

    lp_file = find_lp_file_for_path(path, lp_inputpath)
    if not lp_file:
        return []

    line = 'loaded LP cut data: ' + lp_file
    print(line)
    if logs is not None:
        logs.append(line)

    try:
        lp_names, lp_units, lp_vals, lp_dat = io_helper.load_L2_constant_inputs(lp_file)
    except Exception as e:
        err_line = f"Warning: could not load LP cut data from {lp_file}: {e}"
        print(err_line)
        if logs is not None:
            logs.append(err_line)
        return []

    skip_set = {
        'all outputs', 'variable_name', 'test_name', 'test_number', 'date',
        'name_of_tester', 'location', 'stove_type/model', 'general_comments',
        'high_power_comments', 'medium_power_comments', 'low_power_comments',
        'fuel_type_1', 'fuel_type_2', 'time', 'seconds', 'id', 'phase', 'units',
        'datenumbers', 'average', 'test_code', 'emissions outputs cut periods'
    }

    added_vars = []
    for var in lp_names:
        if not var or var.strip().lower() in skip_set:
            continue
        renamed = f"{var}_cut_lp"
        if renamed not in new_names:
            new_names.append(renamed)
        added_vars.append(renamed)

        new_units[renamed] = lp_units.get(var, '')

        val_list = lp_vals.get(var, [])
        if not isinstance(val_list, list):
            val_list = [val_list]
        values[renamed] = val_list

        for stat in ('average', 'Interval', 'N', 'stdev', 'High Tier', 'Low Tier', 'COV', 'CI'):
            if stat in data and isinstance(data[stat], dict):
                data[stat][renamed] = lp_dat.get(stat, {}).get(var, '')

    return added_vars


def ensure_plot_selection_csv(parameterspath, names, units=None):
    """
    Checks if PlotSelection.csv exists; if not, creates it with columns:
    Variable, Plotted, Name, Units, Axis, Plot Number.
    If it exists, normalizes it to the exact 6-column schema:
      - Strips any phantom/empty columns or trailing junk.
      - Repairs corrupted/overflow rows.
      - Ensures Axis is 'Left'/'Right' and Plot Number is clean.
      - Appends any missing variables from names with Plotted=0.
    Returns True if created or updated with new columns/variables, False if existed unchanged.
    """
    standard_header = ['Variable', 'Plotted', 'Name', 'Units', 'Axis', 'Plot Number']
    if os.path.isfile(parameterspath):
        raw_rows = []
        with open(parameterspath, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            for r in reader:
                if r and any(field.strip() for field in r):
                    raw_rows.append(r)

        if not raw_rows:
            raw_rows = [standard_header]

        header = raw_rows[0]
        header_lower = [c.strip().lower() for c in header]

        col_var = header_lower.index('variable') if 'variable' in header_lower else 0
        col_plot = header_lower.index('plotted') if 'plotted' in header_lower else 1
        col_name = header_lower.index('name') if 'name' in header_lower else 2
        col_unit = None
        if 'units' in header_lower:
            col_unit = header_lower.index('units')
        elif 'unit' in header_lower:
            col_unit = header_lower.index('unit')
        else:
            col_unit = 3

        col_axis = None
        for cand in ['axis', 'y-axis', 'y axis', 'yaxis']:
            if cand in header_lower:
                col_axis = header_lower.index(cand)
                break

        col_plot_num = None
        for cand in ['plot number', 'plot_number', 'plot no', 'plot no.', 'plot num', 'plot id', 'plot']:
            if cand in header_lower:
                col_plot_num = header_lower.index(cand)
                break

        file_updated = False
        if header != standard_header:
            file_updated = True

        clean_rows = []
        existing_vars = set()

        for r in raw_rows[1:]:
            var_name = r[col_var].strip() if len(r) > col_var else ''
            if not var_name or var_name.lower() in ('variable',):
                continue

            plotted = r[col_plot].strip() if len(r) > col_plot else '0'
            if plotted not in ('0', '1'):
                plotted = '1' if plotted.lower() in ('true', 'yes', '1') else '0'

            disp_name = r[col_name].strip() if col_name is not None and len(r) > col_name else ''
            u = r[col_unit].strip() if col_unit is not None and len(r) > col_unit else ''

            # Axis determination
            axis = 'Left'
            if col_axis is not None and len(r) > col_axis:
                cand_axis = r[col_axis].strip().lower()
                if cand_axis in ('right', 'r'):
                    axis = 'Right'
                elif cand_axis in ('left', 'l'):
                    axis = 'Left'
                # If cand_axis was '0', junk, or empty, safely defaults to 'Left'

            # Plot number determination
            plot_num = ''
            if col_plot_num is not None and len(r) > col_plot_num:
                cand_pnum = r[col_plot_num].strip()
                if cand_pnum and cand_pnum.lower() not in ('left', 'right', '0', 'none', 'nan', 'null'):
                    plot_num = cand_pnum

            expected_row = [var_name, plotted, disp_name, u, axis, plot_num]
            if len(r) != 6 or r[:6] != expected_row:
                file_updated = True

            clean_rows.append(expected_row)
            existing_vars.add(var_name.lower())

        for name in names:
            if name != 'time' and name != 'seconds' and name != 'ID' and name.strip().lower() not in existing_vars:
                u_val = units.get(name, '') if units else ''
                disp_name = 'Firepower Carbon (Cut LP)' if name == 'firepower_carbon_cut_lp' else ''
                clean_rows.append([name, '0', disp_name, u_val, 'Left', ''])
                existing_vars.add(name.strip().lower())
                file_updated = True

        if file_updated:
            with open(parameterspath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(standard_header)
                writer.writerows(clean_rows)
            return True
        return False

    var = ['Variable']
    for name in names:
        if name != 'time' and name != 'seconds' and name != 'ID':
            var.append(name)
    rows = [standard_header]
    for v in var[1:]:
        u = units.get(v, '') if units else ''
        disp_name = 'Firepower Carbon (Cut LP)' if v == 'firepower_carbon_cut_lp' else ''
        rows.append([v, '0', disp_name, u, 'Left', ''])
    with open(parameterspath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    return True


def load_plot_selection_csv(parameterspath, return_plot_configs=False):
    """
    Reads PlotSelection.csv.
    Returns:
      plotnames: list of variable names selected to be plotted (Plotted == 1)
      display_names: dict mapping variable name -> display name (from Name column, or empty string)
      target_units: dict mapping variable name -> target units (from Units column, or empty string)
      plot_configs (if return_plot_configs=True): list of plot config dicts for rendering:
        - {'type': 'dual', 'plot_num': str, 'left': var_left, 'right': var_right}
        - {'type': 'single', 'plot_num': str, 'variable': var, 'axis': str}
    """
    plotnames = []
    display_names = {}
    target_units = {}
    plot_configs = []
    if not os.path.isfile(parameterspath):
        if return_plot_configs:
            return plotnames, display_names, target_units, plot_configs
        return plotnames, display_names, target_units

    grouped_numbered = {}  # plot_num -> {'left': [], 'right': []}
    ordered_plot_nums = []
    unnumbered = []

    with open(parameterspath, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header_row = None
        col_var = 0
        col_plot = 1
        col_name = 2
        col_unit = 3
        col_axis = None
        col_plot_num = None

        for row in reader:
            if not row or not any(field.strip() for field in row):
                continue
            name = row[0].strip()
            if header_row is None:
                # First non-empty row: check if header
                if name.lower() == 'variable':
                    header_row = [c.strip().lower() for c in row]
                    if 'variable' in header_row:
                        col_var = header_row.index('variable')
                    if 'plotted' in header_row:
                        col_plot = header_row.index('plotted')
                    if 'name' in header_row:
                        col_name = header_row.index('name')
                    if 'units' in header_row:
                        col_unit = header_row.index('units')
                    elif 'unit' in header_row:
                        col_unit = header_row.index('unit')
                    else:
                        col_unit = 3 if len(header_row) > 3 else None

                    for cand in ['axis', 'y-axis', 'y axis', 'yaxis']:
                        if cand in header_row:
                            col_axis = header_row.index(cand)
                            break

                    for cand in ['plot number', 'plot_number', 'plot no', 'plot no.', 'plot num', 'plot id', 'plot']:
                        if cand in header_row:
                            col_plot_num = header_row.index(cand)
                            break
                    continue
                else:
                    header_row = []

            var_name = row[col_var].strip() if len(row) > col_var else ''
            if not var_name:
                continue

            plotted_val = row[col_plot].strip() if len(row) > col_plot else '0'
            disp_name = row[col_name].strip() if col_name is not None and len(row) > col_name else ''
            t_unit = row[col_unit].strip() if col_unit is not None and len(row) > col_unit else ''

            axis_val = row[col_axis].strip() if col_axis is not None and len(row) > col_axis else ''
            axis = 'Right' if axis_val.lower() in ('right', 'r') else 'Left'

            p_num = row[col_plot_num].strip() if col_plot_num is not None and len(row) > col_plot_num else ''
            if p_num and p_num.lower() in ('0', 'none', 'nan', 'null', 'left', 'right'):
                p_num = ''

            display_names[var_name] = disp_name
            target_units[var_name] = t_unit
            if plotted_val == '1':
                plotnames.append(var_name)
                if p_num:
                    if p_num not in grouped_numbered:
                        grouped_numbered[p_num] = {'left': [], 'right': []}
                        ordered_plot_nums.append(p_num)
                    if axis == 'Right':
                        grouped_numbered[p_num]['right'].append(var_name)
                    else:
                        grouped_numbered[p_num]['left'].append(var_name)
                else:
                    unnumbered.append((var_name, axis))

    # Build plot_configs
    # 1. Numbered plots
    for p_num in ordered_plot_nums:
        group = grouped_numbered[p_num]
        lefts = group['left']
        rights = group['right']
        if lefts and rights:
            # Dual Y-axis plot(s) for this plot number
            for l_var in lefts:
                for r_var in rights:
                    plot_configs.append({
                        'type': 'dual',
                        'plot_num': p_num,
                        'left': l_var,
                        'right': r_var,
                    })
        elif lefts:
            for l_var in lefts:
                plot_configs.append({
                    'type': 'single',
                    'plot_num': p_num,
                    'variable': l_var,
                    'axis': 'Left',
                })
        elif rights:
            for r_var in rights:
                plot_configs.append({
                    'type': 'single',
                    'plot_num': p_num,
                    'variable': r_var,
                    'axis': 'Right',
                })

    # 2. Unnumbered plots (independent single plots)
    for var_name, axis in unnumbered:
        plot_configs.append({
            'type': 'single',
            'plot_num': '',
            'variable': var_name,
            'axis': axis,
        })

    if return_plot_configs:
        return plotnames, display_names, target_units, plot_configs
    return plotnames, display_names, target_units


def get_y_axis_label(variable, units, display_names=None, target_units=None):
    """
    Returns formatted y-axis label using display name if available, falling back to variable name.
    Uses target_units if specified and non-empty, otherwise units (source units).
    Includes (units) if effective unit is non-empty.
    """
    if display_names and variable in display_names and display_names[variable].strip():
        label_name = display_names[variable].strip()
    else:
        label_name = variable

    eff_units = ""
    if target_units and variable in target_units and target_units[variable].strip():
        eff_units = target_units[variable].strip()
    elif units is not None:
        eff_units = str(units).strip()

    if eff_units:
        return f"{label_name} ({eff_units})"
    else:
        return label_name


def extract_individual_test_names(new_names, values):
    """
    Extracts individual test names from an L2 data dictionary.
    Uses column header from new_names[0] and test_name row if available.
    """
    header_key = new_names[0] if new_names else None
    col_names = values.get(header_key, []) if header_key else []
    desc_names = values.get('test_name', [])

    result = []
    for idx, cname in enumerate(col_names):
        cname_str = str(cname).strip() if cname is not None else ''
        desc_str = str(desc_names[idx]).strip() if (desc_names and idx < len(desc_names) and desc_names[idx] is not None) else ''
        if cname_str and desc_str and desc_str != cname_str and desc_str.lower() != 'nan':
            result.append(f"{cname_str} ({desc_str})")
        elif cname_str:
            result.append(cname_str)
        elif desc_str and desc_str.lower() != 'nan':
            result.append(desc_str)
        else:
            result.append(f"Test {idx + 1}")
    return result


def attach_hover_labels(fig, hover_items):
    """
    Attaches interactive hover tooltips to a matplotlib Figure.
    hover_items: list of (scatter_collection, point_info_list, units_str)
                 where point_info_list has entries like (name, value) or "label_str".
    When hovering over a data point:
      - For individual test points: shows "{test_name}\nValue: {value} {units}"
      - For group average points: shows "{group_name} Average = {value} {units}"
    """
    if not hover_items or not hasattr(fig, 'canvas'):
        return None

    ax_scatters = {}
    ax_annot_map = {}
    for item in hover_items:
        if len(item) == 2:
            sc, labels = item
            units = ""
        else:
            sc, labels, units = item
        ax = getattr(sc, 'axes', None)
        if ax is None:
            continue
        ax_scatters.setdefault(ax, []).append((sc, labels, units))

    for ax in ax_scatters:
        annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(15, 15),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.4", fc="#ffffdd", ec="#555555", lw=0.8, alpha=0.95),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0", color="#555555", lw=0.8),
            fontsize=9,
            zorder=1000,
        )
        annot.set_visible(False)
        ax_annot_map[ax] = annot

    def on_hover(event):
        if event.inaxes is None or event.inaxes not in ax_scatters:
            changed = False
            for annot in ax_annot_map.values():
                if annot.get_visible():
                    annot.set_visible(False)
                    changed = True
            if changed:
                fig.canvas.draw_idle()
            return

        current_ax = event.inaxes
        current_annot = ax_annot_map[current_ax]

        # Hide annotations in all other subplots
        changed = False
        for ax, annot in ax_annot_map.items():
            if ax != current_ax and annot.get_visible():
                annot.set_visible(False)
                changed = True

        hit = False
        for sc, labels, units in ax_scatters[current_ax]:
            cont, ind = sc.contains(event)
            if cont:
                offsets = sc.get_offsets()
                indices = ind.get('ind', [])
                if len(indices) == 0:
                    continue
                pos = offsets[indices[0]]
                current_annot.xy = (pos[0], pos[1])

                lines = []
                for k in indices:
                    if k < len(labels):
                        info = labels[k]
                        if isinstance(info, (tuple, list)):
                            name, val = info[0], info[1]
                            val_str = f"{val:.4g}" if isinstance(val, (int, float)) else str(val)
                            u_str = f" {units}".rstrip() if units else ""
                            if "average" in str(name).lower():
                                lines.append(f"{name} = {val_str}{u_str}")
                            else:
                                lines.append(f"{name}\nValue: {val_str}{u_str}")
                        else:
                            lines.append(str(info))

                tooltip_text = "\n---\n".join(lines) if len(lines) > 1 else (lines[0] if lines else "")
                current_annot.set_text(tooltip_text)

                # Adjust offset so tooltip stays inside visible axes
                xlim = current_ax.get_xlim()
                ylim = current_ax.get_ylim()
                x_span = xlim[1] - xlim[0]
                y_span = ylim[1] - ylim[0]
                x_norm = (pos[0] - xlim[0]) / x_span if x_span != 0 else 0.5
                y_norm = (pos[1] - ylim[0]) / y_span if y_span != 0 else 0.5

                x_off = -15 if x_norm > 0.7 else 15
                y_off = -15 if y_norm > 0.7 else 15
                current_annot.set_position((x_off, y_off))
                current_annot.set_ha('right' if x_norm > 0.7 else 'left')
                current_annot.set_va('top' if y_norm > 0.7 else 'bottom')

                if not current_annot.get_visible():
                    current_annot.set_visible(True)
                fig.canvas.draw_idle()
                hit = True
                break

        if not hit and current_annot.get_visible():
            current_annot.set_visible(False)
            fig.canvas.draw_idle()

    cid = fig.canvas.mpl_connect('motion_notify_event', on_hover)
    fig._hover_cid = cid
    return cid



