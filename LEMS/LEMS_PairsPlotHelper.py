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
    Variable, Plotted, Name, Units, Axis, Plot Number, Sort, Gradient, Outlier.
    If it exists, normalizes it to the exact 9-column schema:
      - Strips any phantom/empty columns or trailing junk.
      - Repairs corrupted/overflow rows.
      - Ensures Axis is 'Left'/'Right', Plot Number is clean, and Sort/Gradient/Outlier are preserved.
      - Appends any missing variables from names with Plotted=0.
    Returns True if created or updated with new columns/variables, False if existed unchanged.
    """
    standard_header = ['Variable', 'Plotted', 'Name', 'Units', 'Axis', 'Plot Number', 'Sort', 'Gradient', 'Outlier', '% Diff']
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

        col_sort = None
        for cand in ['sort', 'sorting', 'sort order', 'sort_order']:
            if cand in header_lower:
                col_sort = header_lower.index(cand)
                break

        col_gradient = None
        for cand in ['gradient', 'gradient color', 'gradient_color', 'color gradient', 'color']:
            if cand in header_lower:
                col_gradient = header_lower.index(cand)
                break

        col_outlier = None
        for cand in ['outlier', 'outliers', 'outlier filter', 'outlier_filter', 'rejection', 'outlier rejection']:
            if cand in header_lower:
                col_outlier = header_lower.index(cand)
                break

        col_pct_diff = None
        for cand in ['% diff', '%diff', 'percent diff', 'percent difference', '% change', 'pct diff', 'diff']:
            if cand in header_lower:
                col_pct_diff = header_lower.index(cand)
                break

        file_updated = False
        if header != standard_header:
            file_updated = True

        clean_rows = []
        existing_vars = set()

        for r in raw_rows[1:]:
            var_name = r[col_var].strip() if len(r) > col_var else ''
            disp_name = r[col_name].strip() if col_name is not None and len(r) > col_name else ''
            if (not var_name and not disp_name) or var_name.lower() in ('variable',):
                continue

            plotted = r[col_plot].strip() if len(r) > col_plot else '0'
            if plotted not in ('0', '1'):
                plotted = '1' if plotted.lower() in ('true', 'yes', '1') else '0'

            u = r[col_unit].strip() if col_unit is not None and len(r) > col_unit else ''

            # Axis determination
            axis = 'Left'
            if col_axis is not None and len(r) > col_axis:
                cand_axis = r[col_axis].strip().lower()
                if cand_axis in ('right', 'r'):
                    axis = 'Right'
                elif cand_axis in ('left', 'l'):
                    axis = 'Left'

            # Plot number determination
            plot_num = ''
            if col_plot_num is not None and len(r) > col_plot_num:
                cand_pnum = r[col_plot_num].strip()
                if cand_pnum and cand_pnum.lower() not in ('left', 'right', '0', 'none', 'nan', 'null'):
                    plot_num = cand_pnum

            # Sort determination
            sort_val = ''
            if col_sort is not None and len(r) > col_sort:
                cand_sort = r[col_sort].strip()
                if cand_sort.lower() in ('smallest', 'small', 'asc', 'ascending'):
                    sort_val = 'Smallest'
                elif cand_sort and cand_sort.lower() not in ('0', 'none', 'nan', 'null', 'no'):
                    sort_val = cand_sort.capitalize()

            # Gradient determination
            gradient_val = ''
            if col_gradient is not None and len(r) > col_gradient:
                cand_grad = r[col_gradient].strip()
                if cand_grad and cand_grad.lower() not in ('0', 'none', 'nan', 'null', 'no'):
                    gradient_val = cand_grad.capitalize()

            # Outlier determination
            outlier_val = ''
            if col_outlier is not None and len(r) > col_outlier:
                cand_out = r[col_outlier].strip()
                if cand_out and cand_out.lower() not in ('0', 'none', 'nan', 'null', 'no'):
                    outlier_val = cand_out

            # % Diff determination
            pct_diff_val = ''
            if col_pct_diff is not None and len(r) > col_pct_diff:
                cand_pdiff = r[col_pct_diff].strip()
                if cand_pdiff in ('1', '0'):
                    pct_diff_val = cand_pdiff
                elif cand_pdiff.lower() in ('true', 'yes', 'y', 'on'):
                    pct_diff_val = '1'
                elif cand_pdiff.lower() in ('false', 'no', 'n', 'off'):
                    pct_diff_val = '0'

            expected_row = [var_name, plotted, disp_name, u, axis, plot_num, sort_val, gradient_val, outlier_val, pct_diff_val]
            if len(r) != 10 or r[:10] != expected_row:
                file_updated = True

            clean_rows.append(expected_row)
            if var_name:
                existing_vars.add(var_name.lower())
            if disp_name:
                existing_vars.add(disp_name.lower())

        for name in names:
            if name != 'time' and name != 'seconds' and name != 'ID' and name.strip().lower() not in existing_vars:
                u_val = units.get(name, '') if units else ''
                disp_name = 'Firepower Carbon (Cut LP)' if name == 'firepower_carbon_cut_lp' else ''
                clean_rows.append([name, '0', disp_name, u_val, 'Left', '', '', '', '', ''])
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
        rows.append([v, '0', disp_name, u, 'Left', '', '', '', '', ''])
    with open(parameterspath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    return True


def find_equivalent_metric_pairs(plotnames):
    """
    Identifies pairs of equivalent metrics in plotnames:
      - Lambda & O2_1 (with matching phase suffix, e.g. '', '_hp', '_lp', '_mp', '_L1', etc.)
      - SenO2Percent & O2_1_per (with matching phase suffix)
    Returns list of tuples: (var_primary, var_secondary, family, suffix)
    """
    pairs = []
    name_map = {name.strip().lower(): name for name in plotnames}

    # Family 1: Lambda & O2_1
    for name in plotnames:
        lower_name = name.strip().lower()
        if lower_name.startswith('lambda'):
            suffix = lower_name[6:]  # part after 'lambda'
            target_key = f"o2_1{suffix}"
            if target_key in name_map:
                o2_name = name_map[target_key]
                pairs.append((name, o2_name, 'lambda', suffix))

    # Family 2: SenO2Percent & O2_1_per
    for name in plotnames:
        lower_name = name.strip().lower()
        if lower_name.startswith('seno2percent'):
            suffix = lower_name[12:]  # part after 'seno2percent'
            target_key = f"o2_1_per{suffix}"
            if target_key in name_map:
                o2_name = name_map[target_key]
                pairs.append((name, o2_name, 'o2_percent', suffix))

    return pairs

_find_equivalent_metric_pairs = find_equivalent_metric_pairs


def _group_axis_variables(var_list):
    """
    Groups variables in var_list, identifying equivalent metric pairs
    (e.g. Lambda & O2_1, or SenO2Percent & O2_1_per).
    Returns a list of items, where each item is either:
      - ('single', var_name)
      - ('combined', var_a, var_b, family, suffix)
    """
    pairs = find_equivalent_metric_pairs(var_list)
    consumed = set()
    grouped = []
    for var_a, var_b, family, suffix in pairs:
        grouped.append(('combined', var_a, var_b, family, suffix))
        consumed.add(var_a)
        consumed.add(var_b)
    for v in var_list:
        if v not in consumed:
            grouped.append(('single', v))
    return grouped


def load_plot_selection_csv(parameterspath, return_plot_configs=False, return_sort=False, return_pct_diff=False):
    """
    Reads PlotSelection.csv.
    Returns:
      plotnames: list of variable names selected to be plotted (Plotted == 1)
      display_names: dict mapping variable name -> display name (from Name column, or empty string)
      target_units: dict mapping variable name -> target units (from Units column, or empty string)
      plot_configs (if return_plot_configs=True): list of plot config dicts for rendering:
        - {'type': 'dual', 'plot_num': str, 'left': var_left, 'right': var_right, 'sort': str, 'sort_var': str,
           'gradient_left': str, 'gradient_right': str, 'outlier_left': str, 'outlier_right': str,
           'pct_diff_left': bool, 'pct_diff_right': bool}
        - {'type': 'single', 'plot_num': str, 'variable': var, 'axis': str, 'sort': str, 'gradient': str,
           'outlier': str, 'pct_diff': bool}
      sort_orders (if return_sort=True): dict mapping variable name -> sort order (e.g. 'Smallest')
      pct_diff_flags (if return_pct_diff=True): dict mapping variable name -> bool (% Diff enabled)
    """
    plotnames = []
    display_names = {}
    target_units = {}
    sort_orders = {}
    gradient_colors = {}
    outlier_filters = {}
    pct_diff_flags = {}
    plot_configs = []
    if not os.path.isfile(parameterspath):
        res = [plotnames, display_names, target_units]
        if return_plot_configs:
            res.append(plot_configs)
        if return_sort:
            res.append(sort_orders)
        if return_pct_diff:
            res.append(pct_diff_flags)
        return tuple(res)

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
        col_sort = None
        col_gradient = None
        col_outlier = None
        col_pct_diff = None

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

                    for cand in ['sort', 'sorting', 'sort order', 'sort_order']:
                        if cand in header_row:
                            col_sort = header_row.index(cand)
                            break

                    for cand in ['gradient', 'gradient color', 'gradient_color', 'color gradient', 'color']:
                        if cand in header_row:
                            col_gradient = header_row.index(cand)
                            break

                    for cand in ['outlier', 'outliers', 'outlier filter', 'outlier_filter', 'rejection', 'outlier rejection']:
                        if cand in header_row:
                            col_outlier = header_row.index(cand)
                            break

                    for cand in ['% diff', '%diff', 'percent diff', 'percent difference', '% change', 'pct diff', 'diff']:
                        if cand in header_row:
                            col_pct_diff = header_row.index(cand)
                            break
                    continue
                else:
                    header_row = []

            var_name = row[col_var].strip() if len(row) > col_var else ''
            disp_name = row[col_name].strip() if col_name is not None and len(row) > col_name else ''
            if not var_name and not disp_name:
                continue

            var_key = var_name if var_name else disp_name

            plotted_val = row[col_plot].strip() if len(row) > col_plot else '0'
            t_unit = row[col_unit].strip() if col_unit is not None and len(row) > col_unit else ''

            axis_val = row[col_axis].strip() if col_axis is not None and len(row) > col_axis else ''
            axis = 'Right' if axis_val.lower() in ('right', 'r') else 'Left'

            p_num = row[col_plot_num].strip() if col_plot_num is not None and len(row) > col_plot_num else ''
            if p_num and p_num.lower() in ('0', 'none', 'nan', 'null', 'left', 'right'):
                p_num = ''

            sort_val = row[col_sort].strip() if col_sort is not None and len(row) > col_sort else ''
            if sort_val and sort_val.lower() in ('0', 'none', 'nan', 'null', 'no'):
                sort_val = ''

            gradient_val = row[col_gradient].strip() if col_gradient is not None and len(row) > col_gradient else ''
            if gradient_val and gradient_val.lower() in ('0', 'none', 'nan', 'null', 'no'):
                gradient_val = ''

            outlier_val = row[col_outlier].strip() if col_outlier is not None and len(row) > col_outlier else ''
            if outlier_val and outlier_val.lower() in ('0', 'none', 'nan', 'null', 'no'):
                outlier_val = ''

            pct_diff_val = row[col_pct_diff].strip() if col_pct_diff is not None and len(row) > col_pct_diff else ''
            is_pct_diff = pct_diff_val.lower() in ('1', 'true', 'yes', 'y', 'on')

            display_names[var_key] = disp_name if disp_name else var_key
            target_units[var_key] = t_unit
            sort_orders[var_key] = sort_val
            gradient_colors[var_key] = gradient_val
            outlier_filters[var_key] = outlier_val
            pct_diff_flags[var_key] = is_pct_diff
            if var_name:
                pct_diff_flags[var_name] = is_pct_diff
            if disp_name:
                pct_diff_flags[disp_name] = is_pct_diff

            if plotted_val == '1':
                plotnames.append(var_key)
                if p_num:
                    if p_num not in grouped_numbered:
                        grouped_numbered[p_num] = {'left': [], 'right': []}
                        ordered_plot_nums.append(p_num)
                    if axis == 'Right':
                        grouped_numbered[p_num]['right'].append(var_key)
                    else:
                        grouped_numbered[p_num]['left'].append(var_key)
                else:
                    unnumbered.append((var_key, axis))

    # Build plot_configs
    # 1. Numbered plots
    for p_num in ordered_plot_nums:
        group = grouped_numbered[p_num]
        lefts = group['left']
        rights = group['right']
        if lefts and rights:
            left_items = _group_axis_variables(lefts)
            right_items = _group_axis_variables(rights)
            # Dual Y-axis plot(s) for this plot number
            for l_item in left_items:
                for r_item in right_items:
                    if l_item[0] == 'combined':
                        _, l_var_a, l_var_b, l_family, l_suffix = l_item
                        l_var = l_var_a
                        left_combined = (l_var_a, l_var_b, l_family, l_suffix)
                        sort_l = sort_orders.get(l_var_a, '').strip() or sort_orders.get(l_var_b, '').strip()
                        pct_diff_l = pct_diff_flags.get(l_var_a, False) or pct_diff_flags.get(l_var_b, False)
                        grad_l = gradient_colors.get(l_var_a, '').strip() or gradient_colors.get(l_var_b, '').strip()
                        outlier_l = outlier_filters.get(l_var_a, '').strip() or outlier_filters.get(l_var_b, '').strip()
                    else:
                        l_var = l_item[1]
                        left_combined = None
                        sort_l = sort_orders.get(l_var, '').strip()
                        pct_diff_l = pct_diff_flags.get(l_var, False)
                        grad_l = gradient_colors.get(l_var, '').strip()
                        outlier_l = outlier_filters.get(l_var, '').strip()

                    if r_item[0] == 'combined':
                        _, r_var_a, r_var_b, r_family, r_suffix = r_item
                        r_var = r_var_a
                        right_combined = (r_var_a, r_var_b, r_family, r_suffix)
                        sort_r = sort_orders.get(r_var_a, '').strip() or sort_orders.get(r_var_b, '').strip()
                        pct_diff_r = pct_diff_flags.get(r_var_a, False) or pct_diff_flags.get(r_var_b, False)
                        grad_r = gradient_colors.get(r_var_a, '').strip() or gradient_colors.get(r_var_b, '').strip()
                        outlier_r = outlier_filters.get(r_var_a, '').strip() or outlier_filters.get(r_var_b, '').strip()
                    else:
                        r_var = r_item[1]
                        right_combined = None
                        sort_r = sort_orders.get(r_var, '').strip()
                        pct_diff_r = pct_diff_flags.get(r_var, False)
                        grad_r = gradient_colors.get(r_var, '').strip()
                        outlier_r = outlier_filters.get(r_var, '').strip()

                    plot_sort = ''
                    sort_var = ''
                    if sort_l.lower() in ('smallest', 'small', 'asc', 'ascending'):
                        plot_sort = 'Smallest'
                        sort_var = l_var
                    elif sort_r.lower() in ('smallest', 'small', 'asc', 'ascending'):
                        plot_sort = 'Smallest'
                        sort_var = r_var

                    show_pct = pct_diff_l or pct_diff_r

                    plot_configs.append({
                        'type': 'dual',
                        'plot_num': p_num,
                        'left': l_var,
                        'left_combined': left_combined,
                        'right': r_var,
                        'right_combined': right_combined,
                        'sort': plot_sort,
                        'sort_var': sort_var,
                        'gradient_left': grad_l,
                        'gradient_right': grad_r,
                        'outlier_left': outlier_l,
                        'outlier_right': outlier_r,
                        'pct_diff_left': show_pct,
                        'pct_diff_right': show_pct,
                    })
        elif lefts:
            left_items = _group_axis_variables(lefts)
            for l_item in left_items:
                if l_item[0] == 'combined':
                    _, l_var_a, l_var_b, l_family, l_suffix = l_item
                    plot_configs.append({
                        'type': 'single',
                        'plot_num': p_num,
                        'variable': l_var_a,
                        'combined': (l_var_a, l_var_b, l_family, l_suffix),
                        'axis': 'Left',
                        'sort': sort_orders.get(l_var_a, '').strip() or sort_orders.get(l_var_b, '').strip(),
                        'gradient': gradient_colors.get(l_var_a, '').strip() or gradient_colors.get(l_var_b, '').strip(),
                        'outlier': outlier_filters.get(l_var_a, '').strip() or outlier_filters.get(l_var_b, '').strip(),
                        'pct_diff': pct_diff_flags.get(l_var_a, False) or pct_diff_flags.get(l_var_b, False),
                    })
                else:
                    l_var = l_item[1]
                    plot_configs.append({
                        'type': 'single',
                        'plot_num': p_num,
                        'variable': l_var,
                        'combined': None,
                        'axis': 'Left',
                        'sort': sort_orders.get(l_var, '').strip(),
                        'gradient': gradient_colors.get(l_var, '').strip(),
                        'outlier': outlier_filters.get(l_var, '').strip(),
                        'pct_diff': pct_diff_flags.get(l_var, False),
                    })
        elif rights:
            right_items = _group_axis_variables(rights)
            for r_item in right_items:
                if r_item[0] == 'combined':
                    _, r_var_a, r_var_b, r_family, r_suffix = r_item
                    plot_configs.append({
                        'type': 'single',
                        'plot_num': p_num,
                        'variable': r_var_a,
                        'combined': (r_var_a, r_var_b, r_family, r_suffix),
                        'axis': 'Right',
                        'sort': sort_orders.get(r_var_a, '').strip() or sort_orders.get(r_var_b, '').strip(),
                        'gradient': gradient_colors.get(r_var_a, '').strip() or gradient_colors.get(r_var_b, '').strip(),
                        'outlier': outlier_filters.get(r_var_a, '').strip() or outlier_filters.get(r_var_b, '').strip(),
                        'pct_diff': pct_diff_flags.get(r_var_a, False) or pct_diff_flags.get(r_var_b, False),
                    })
                else:
                    r_var = r_item[1]
                    plot_configs.append({
                        'type': 'single',
                        'plot_num': p_num,
                        'variable': r_var,
                        'combined': None,
                        'axis': 'Right',
                        'sort': sort_orders.get(r_var, '').strip(),
                        'gradient': gradient_colors.get(r_var, '').strip(),
                        'outlier': outlier_filters.get(r_var, '').strip(),
                        'pct_diff': pct_diff_flags.get(r_var, False),
                    })

    # 2. Unnumbered plots (independent single plots)
    for var_name, axis in unnumbered:
        plot_configs.append({
            'type': 'single',
            'plot_num': '',
            'variable': var_name,
            'axis': axis,
            'sort': sort_orders.get(var_name, '').strip(),
            'gradient': gradient_colors.get(var_name, '').strip(),
            'outlier': outlier_filters.get(var_name, '').strip(),
            'pct_diff': pct_diff_flags.get(var_name, False),
        })

    res = [plotnames, display_names, target_units]
    if return_plot_configs:
        res.append(plot_configs)
    if return_sort:
        res.append(sort_orders)
    if return_pct_diff:
        res.append(pct_diff_flags)
    return tuple(res)


def get_sorted_group_indices(series_values, sort_order=None, pair_groups=None):
    """
    Returns indices for ordering test groups along the x-axis.
    - If pair_groups is present and non-empty, sorting is disabled (returns original order).
    - If sort_order is 'smallest' (or 'ascending', etc.), returns indices sorted from
      smallest to largest value from left to right.
    - series_values is a list corresponding to each test group. Each element can be:
        - a single numeric value (e.g. average/mean for bar charts)
        - a list/array of numeric values (e.g. data points for box plots / scatter plots)
      For lists of values, the mean of the numeric entries is used as the representative value.
      Empty/NaN values are sorted to the end.
    """
    num_groups = len(series_values)
    original_indices = list(range(num_groups))

    if pair_groups:
        return original_indices

    if not sort_order or not isinstance(sort_order, str):
        return original_indices

    s = sort_order.strip().lower()
    if s not in ('smallest', 'small', 'asc', 'ascending'):
        return original_indices

    def _get_metric_val(item):
        if isinstance(item, (list, tuple)):
            valid = []
            for x in item:
                try:
                    if x is not None and str(x).strip().lower() not in ('nan', '', 'none', 'null'):
                        valid.append(float(x))
                except (ValueError, TypeError):
                    pass
            if valid:
                return (0, sum(valid) / len(valid))
            return (1, 0)
        else:
            try:
                if item is not None and str(item).strip().lower() not in ('nan', '', 'none', 'null'):
                    return (0, float(item))
            except (ValueError, TypeError):
                pass
            return (1, 0)

    return sorted(original_indices, key=lambda idx: _get_metric_val(series_values[idx]))


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


def compute_gradient_range(all_values, outlier_spec=None):
    """
    Computes (vmin, vmax, outlier_count) for a list/array of numeric values.
    If outlier_spec is specified (e.g. '5x', '5sd', '3.5x'), parses the multiplier k
    and excludes points with |y - mean| > k * std when determining vmin and vmax.
    Non-outlier points are used to set the color scale min (vmin) and max (vmax).
    """
    import re
    import math

    valid_vals = []
    for v in all_values:
        try:
            if v is not None and str(v).strip().lower() not in ('nan', '', 'none', 'null'):
                vf = float(v)
                if not math.isnan(vf) and not math.isinf(vf):
                    valid_vals.append(vf)
        except (ValueError, TypeError):
            pass

    if not valid_vals:
        return 0.0, 1.0, 0

    if len(valid_vals) == 1:
        return valid_vals[0] - 1.0, valid_vals[0] + 1.0, 0

    # Parse outlier_spec if present (e.g. '5x' -> 5.0)
    k_mult = None
    if outlier_spec and isinstance(outlier_spec, str) and outlier_spec.strip():
        m = re.search(r'([0-9]+(?:\.[0-9]+)?)', outlier_spec.strip())
        if m:
            try:
                k_mult = float(m.group(1))
            except ValueError:
                k_mult = None

    if k_mult is not None and k_mult > 0:
        mean_y = sum(valid_vals) / len(valid_vals)
        variance = sum((y - mean_y) ** 2 for y in valid_vals) / (len(valid_vals) - 1 if len(valid_vals) > 1 else 1)
        std_y = math.sqrt(variance)

        if std_y > 1e-12:
            threshold = k_mult * std_y
            filtered_vals = [y for y in valid_vals if abs(y - mean_y) <= threshold]
            outlier_count = len(valid_vals) - len(filtered_vals)
            if filtered_vals:
                vmin = min(filtered_vals)
                vmax = max(filtered_vals)
                if vmin == vmax:
                    vmax = vmin + 1.0
                return vmin, vmax, outlier_count

    vmin = min(valid_vals)
    vmax = max(valid_vals)
    if vmin == vmax:
        vmax = vmin + 1.0
    return vmin, vmax, 0


def attach_hover_labels(fig, hover_items):
    """
    Attaches interactive hover tooltips to a matplotlib Figure.
    hover_items: list of (scatter_collection, point_info_list, units_str)
                 where point_info_list has entries like (name, value) or "label_str".
    Supports both single axes and dual Y-axes (twinx).
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
        if event.x is None or event.y is None:
            return

        # Determine all candidate axes that enclose the cursor
        # (Crucial for twinx where event.inaxes only points to the top axes)
        candidate_axes = []
        if event.inaxes in ax_scatters:
            candidate_axes.append(event.inaxes)
        for ax in ax_scatters:
            if ax not in candidate_axes:
                try:
                    if ax.bbox.contains(event.x, event.y):
                        candidate_axes.append(ax)
                except Exception:
                    pass

        if not candidate_axes:
            changed = False
            for annot in ax_annot_map.values():
                if annot.get_visible():
                    annot.set_visible(False)
                    changed = True
            if changed:
                fig.canvas.draw_idle()
            return

        # Check for hit across candidate axes
        hit = False
        hit_ax = None
        for cand_ax in candidate_axes:
            for sc, labels, units in ax_scatters[cand_ax]:
                cont, ind = sc.contains(event)
                if cont:
                    offsets = sc.get_offsets()
                    indices = ind.get('ind', [])
                    if len(indices) == 0:
                        continue
                    pos = offsets[indices[0]]
                    current_annot = ax_annot_map[cand_ax]
                    current_annot.xy = (pos[0], pos[1])

                    lines = []
                    for k in indices:
                        if k < len(labels):
                            info = labels[k]
                            if isinstance(info, (tuple, list)):
                                name, val = info[0], info[1]
                                val_str = f"{val:.4g}" if isinstance(val, (int, float)) else str(val)
                                u_str = f" {units}".rstrip() if units else ""
                                extra_str = f"\n{info[2]}" if len(info) >= 3 and info[2] else ""
                                if "average" in str(name).lower():
                                    lines.append(f"{name} = {val_str}{u_str}{extra_str}")
                                else:
                                    lines.append(f"{name}\nValue: {val_str}{u_str}{extra_str}")
                            else:
                                lines.append(str(info))

                    tooltip_text = "\n---\n".join(lines) if len(lines) > 1 else (lines[0] if lines else "")
                    current_annot.set_text(tooltip_text)

                    # Adjust offset so tooltip stays inside visible axes
                    xlim = cand_ax.get_xlim()
                    ylim = cand_ax.get_ylim()
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

                    hit = True
                    hit_ax = cand_ax
                    break
            if hit:
                break

        # Hide annotations on any other axes
        changed = False
        for ax, annot in ax_annot_map.items():
            if ax != hit_ax and annot.get_visible():
                annot.set_visible(False)
                changed = True

        if hit or changed:
            fig.canvas.draw_idle()

    cid = fig.canvas.mpl_connect('motion_notify_event', on_hover)
    fig._hover_cid = cid
    return cid


def enable_dual_axis_keyboard_zoom(fig, ax1, ax2, initial_active='right'):
    """
    Enables keyboard toggling between dual Y-axes for interactive Matplotlib navigation
    (Zoom-to-Rectangle, Pan, and reset tools).

    Keybindings:
      '1' or 'l' / 'L': Target the LEFT Y-axis (ax1)
      '2' or 'r' / 'R': Target the RIGHT Y-axis (ax2)

    When an axis is active, toolbar interactions (drag-to-zoom, pan) specifically
    modify that axis's Y limits without changing the other Y-axis.
    """
    if not hasattr(fig, 'canvas'):
        return None

    # Transparent background patches so switching z-orders doesn't mask either axis
    ax1.patch.set_visible(False)
    ax2.patch.set_visible(False)

    badge_style = dict(boxstyle='round,pad=0.35', lw=1.0, alpha=0.92)

    status_text = fig.text(
        0.5, 0.015,
        "",
        ha='center', va='bottom', fontsize=8.5, fontweight='bold',
        bbox=badge_style,
        zorder=2000
    )

    def update_state(active):
        if active == 'left':
            ax1.set_zorder(10)
            ax2.set_zorder(9)
            status_text.set_text("Active Toolbar Axis: [1] LEFT (Blue)  |  Press '1' (Left) or '2' (Right) to switch")
            status_text.set_color('#0b4f8a')
            status_text.set_bbox(dict(boxstyle='round,pad=0.35', fc='#d1ecf1', ec='#1f77b4', lw=1.0, alpha=0.92))
            msg = "[Dual-Axis Zoom] Toolbar active on: LEFT axis (ax1)"
        else:
            ax2.set_zorder(10)
            ax1.set_zorder(9)
            status_text.set_text("Active Toolbar Axis: [2] RIGHT (Orange)  |  Press '1' (Left) or '2' (Right) to switch")
            status_text.set_color('#a04000')
            status_text.set_bbox(dict(boxstyle='round,pad=0.35', fc='#ffe8d6', ec='#ff7f0e', lw=1.0, alpha=0.92))
            msg = "[Dual-Axis Zoom] Toolbar active on: RIGHT axis (ax2)"

        if getattr(fig.canvas, 'manager', None) is not None:
            try:
                cur_title = fig.canvas.manager.get_window_title() or "Plot"
                base_title = cur_title.split("  [Active:")[0]
                tag = "LEFT Y (1)" if active == 'left' else "RIGHT Y (2)"
                fig.canvas.manager.set_window_title(f"{base_title}  [Active: {tag}]")
            except Exception:
                pass

        fig.canvas.draw_idle()
        print(msg)

    # Set initial state
    update_state('left' if initial_active == 'left' else 'right')

    def on_key(event):
        if event.key in ('1', 'l', 'L'):
            update_state('left')
        elif event.key in ('2', 'r', 'R'):
            update_state('right')

    cid = fig.canvas.mpl_connect('key_press_event', on_key)
    fig._dual_axis_key_cid = cid
    return cid


def find_template_file(folder_path):
    """
    Looks in folder_path for FormattedCutTableL3_template_md.xlsx or similar template files.
    Returns the absolute path if found, or None.
    """
    if not folder_path or not os.path.isdir(folder_path):
        return None

    preferred = [
        os.path.join(folder_path, 'FormattedCutTableL3_template_md.xlsx'),
        os.path.join(folder_path, 'FormattedCutTableL3_template.xlsx'),
        os.path.join(folder_path, 'FormattedCutTableL3_template_md_1.xlsx'),
    ]
    for p in preferred:
        if os.path.isfile(p):
            return p

    import glob
    candidates = glob.glob(os.path.join(folder_path, '*FormattedCutTableL3*template*.xlsx'))
    candidates = [c for c in candidates if not os.path.basename(c).startswith('~$')]
    if candidates:
        return candidates[0]
    return None


def resolve_template_variables(template_path, inputpath, test_labels, data_values, names, units, pairs_csv_path=None, logs=None):
    """
    Reads FormattedCutTableL3_template_md.xlsx to identify rows where a custom variable name
    is assigned to different thermocouples/variables per stove model / test block.

    For each such row (matched by the 'Name' or 'Metrics' column in the template):
      - Determines which variable is defined for each test in inputpath
      - Assembles the values and statistics from data_values across tests into a unified composite entry
      - Inserts the composite variable into data_values, names, and units.

    Returns:
      list of added composite variable names.
    """
    if not template_path or not os.path.isfile(template_path):
        return []

    import openpyxl
    try:
        wb = openpyxl.load_workbook(template_path, data_only=True)
    except Exception as e:
        msg = f"Notice: Could not load template {template_path}: {e}"
        print(msg)
        if logs is not None:
            logs.append(msg)
        return []

    sheet = wb.active
    header_row_idx = None
    for r in range(1, min(15, sheet.max_row + 1)):
        for c in range(1, sheet.max_column + 1):
            v = sheet.cell(row=r, column=c).value
            if v and str(v).strip().lower().startswith('data_key'):
                header_row_idx = r
                break
        if header_row_idx is not None:
            break

    if header_row_idx is None:
        return []

    # Find data_key columns
    data_key_cols = []
    for c in range(1, sheet.max_column + 1):
        v = sheet.cell(row=header_row_idx, column=c).value
        if v and str(v).strip().lower().startswith('data_key'):
            data_key_cols.append(c)
    data_key_cols.sort()

    if not data_key_cols:
        return []

    IGNORED_HEADERS = {'metrics', 'operation', 'test_code', 'variable_name', 'all outputs', 'name', 'units', 'data_key', 'data_source', 'sig_figs', 'data_type'}

    configs = []
    for idx, dk_col in enumerate(data_key_cols):
        next_dk_col = data_key_cols[idx + 1] if idx + 1 < len(data_key_cols) else sheet.max_column + 1

        units_col = None
        sig_figs_col = None
        data_type_col = None
        data_source_col = None

        # Look backwards up to 5 cols for units, sig_figs, data_type
        for c in range(max(1, dk_col - 5), dk_col):
            v = sheet.cell(row=header_row_idx, column=c).value
            if v:
                vs = str(v).strip().lower()
                if vs.startswith('units'):
                    units_col = c
                elif vs.startswith('sig_figs'):
                    sig_figs_col = c
                elif vs.startswith('data_type'):
                    data_type_col = c

        # Look forwards up to 3 cols for data_source
        last_meta_col = dk_col
        for c in range(dk_col + 1, min(next_dk_col, dk_col + 4)):
            v = sheet.cell(row=header_row_idx, column=c).value
            if v:
                vs = str(v).strip().lower()
                if vs.startswith('data_source'):
                    data_source_col = c
                    last_meta_col = max(last_meta_col, c)

        block_end_col = next_dk_col
        for c in range(last_meta_col + 1, next_dk_col):
            v = sheet.cell(row=header_row_idx, column=c).value
            if v:
                vs = str(v).strip().lower()
                if any(vs.startswith(prefix) for prefix in ['units', 'sig_figs', 'data_type', 'data_key', 'data_source']):
                    block_end_col = c
                    break

        t_name_keys = {}
        for c in range(last_meta_col + 1, block_end_col):
            cell_val = sheet.cell(row=header_row_idx, column=c).value
            if cell_val is not None:
                vs = str(cell_val).strip()
                if vs and vs.lower() not in IGNORED_HEADERS:
                    t_name_keys[vs] = c

        configs.append({
            'data_key_col': dk_col,
            'units_col': units_col,
            'sig_figs_col': sig_figs_col,
            'data_type_col': data_type_col,
            'data_source_col': data_source_col,
            'template_name_keys': t_name_keys
        })

    # Find Name column
    name_col = None
    metrics_col = None
    phase_col = None
    for c in range(1, data_key_cols[0]):
        for r in range(1, header_row_idx + 1):
            cv = sheet.cell(row=r, column=c).value
            if cv:
                cs = str(cv).strip().lower()
                if cs == 'name' and name_col is None:
                    name_col = c
                elif cs in ('metrics', 'metric') and metrics_col is None:
                    metrics_col = c
                elif cs in ('phase', 'operation') and phase_col is None:
                    phase_col = c

    if name_col is None:
        name_col = metrics_col
    if phase_col is None and metrics_col is not None and metrics_col + 1 < data_key_cols[0]:
        phase_col = metrics_col + 1

    # Load pairs info if pairs_csv_path exists
    pairs_info = []
    if pairs_csv_path and os.path.isfile(pairs_csv_path):
        try:
            with open(pairs_csv_path, 'r', newline='', encoding='utf-8-sig') as pf:
                for row in csv.DictReader(pf):
                    if row.get('path'):
                        pairs_info.append({
                            'path': row.get('path', '').strip(),
                            'test_code': row.get('test_code', '').strip(),
                            'name': row.get('Name', '').strip(),
                            'group': row.get('Group', '').strip(),
                            'data_key': row.get('data_key', '').strip()
                        })
        except:
            pass

    # Map each test index i in inputpath to a config in configs
    test_idx_to_config = {}
    for i, p in enumerate(inputpath):
        p_norm = os.path.normpath(p).lower()
        test_code = ''
        p_name = ''
        p_group = ''
        p_data_key = ''
        for pi in pairs_info:
            if os.path.normpath(pi['path']).lower() == p_norm:
                test_code = pi['test_code']
                p_name = pi['name']
                p_group = pi['group']
                p_data_key = pi['data_key']
                break
        if not test_code and i < len(pairs_info):
            test_code = pairs_info[i]['test_code']
            p_name = pairs_info[i]['name']
            p_group = pairs_info[i]['group']
            p_data_key = pairs_info[i]['data_key']

        lbl = str(test_labels[i]).strip() if (test_labels and i < len(test_labels)) else ''
        folder_name = os.path.basename(os.path.dirname(p)).strip()

        matched_cfg = None
        # Try matching test_code or data_key or label
        for cfg in configs:
            keys_lower = {k.lower(): k for k in cfg['template_name_keys']}
            for cand in [test_code, p_data_key, lbl, p_name, folder_name]:
                if cand and cand.lower() in keys_lower:
                    matched_cfg = cfg
                    break
            if matched_cfg:
                break

        # Check rows 1 and 2 of template above the columns of this block
        if not matched_cfg:
            for cfg in configs:
                for col_idx in cfg['template_name_keys'].values():
                    for top_r in range(1, header_row_idx):
                        cell_v = str(sheet.cell(row=top_r, column=col_idx).value or '').strip().lower()
                        for cand in [lbl, p_name, p_group, folder_name]:
                            if cand and cand.lower() == cell_v:
                                matched_cfg = cfg
                                break
                        if matched_cfg:
                            break
                    if matched_cfg:
                        break
                if matched_cfg:
                    break

        # Fallback: by index if count matches
        if not matched_cfg and i < len(configs):
            matched_cfg = configs[i]

        test_idx_to_config[i] = matched_cfg

    added_variables = []
    # Scan template rows for non-empty Name or Metrics
    for r in range(header_row_idx + 1, sheet.max_row + 1):
        name_val = sheet.cell(row=r, column=name_col).value if name_col else None
        if not name_val and metrics_col and metrics_col != name_col:
            name_val = sheet.cell(row=r, column=metrics_col).value

        if not name_val:
            continue

        row_name = str(name_val).strip()
        if not row_name or row_name.lower() in IGNORED_HEADERS:
            continue

        # Check if there is any data_key value in this row
        has_data_key = any(
            sheet.cell(row=r, column=cfg['data_key_col']).value for cfg in configs
        )
        if not has_data_key:
            continue

        phase_str = ''
        if phase_col:
            pv = sheet.cell(row=r, column=phase_col).value
            if pv:
                phase_str = str(pv).strip().lower()

        phase_suffix = ''
        if 'cold start' in phase_str or phase_str == 'l1':
            phase_suffix = '_L1'
        elif 'high power' in phase_str or phase_str == 'hp':
            phase_suffix = '_hp'
        elif 'medium power' in phase_str or phase_str == 'mp':
            phase_suffix = '_mp'
        elif 'low power' in phase_str or phase_str == 'lp':
            phase_suffix = '_lp'
        elif 'l5' in phase_str:
            phase_suffix = '_L5'

        comp_values = []
        comp_averages = []
        comp_confidences = []
        comp_Ns = []
        comp_stdevs = []
        comp_highs = []
        comp_lows = []
        comp_covs = []
        comp_cis = []
        comp_unit = ''

        for i in range(len(inputpath)):
            cfg = test_idx_to_config.get(i)
            if not cfg:
                comp_values.append([''])
                comp_averages.append('')
                comp_confidences.append('')
                comp_Ns.append('')
                comp_stdevs.append('')
                comp_highs.append('')
                comp_lows.append('')
                comp_covs.append('')
                comp_cis.append('')
                continue

            var_key_cell = sheet.cell(row=r, column=cfg['data_key_col']).value
            if not var_key_cell:
                comp_values.append([''])
                comp_averages.append('')
                comp_confidences.append('')
                comp_Ns.append('')
                comp_stdevs.append('')
                comp_highs.append('')
                comp_lows.append('')
                comp_covs.append('')
                comp_cis.append('')
                continue

            var_key_str = str(var_key_cell).strip()
            ds = ''
            if cfg.get('data_source_col'):
                dsv = sheet.cell(row=r, column=cfg['data_source_col']).value
                if dsv:
                    ds = str(dsv).strip().lower()

            candidates = [var_key_str]
            if ds == 'lp':
                candidates.insert(0, f"{var_key_str}_cut_lp")
                candidates.insert(1, f"{var_key_str}_lp")
            if phase_suffix and not var_key_str.endswith(phase_suffix):
                candidates.append(f"{var_key_str}{phase_suffix}")
                if ds == 'lp':
                    candidates.insert(0, f"{var_key_str}_cut{phase_suffix}")

            matched_var = None
            for cand in candidates:
                if cand in data_values:
                    matched_var = cand
                    break
                cand_lower = cand.lower()
                for k in data_values:
                    if k.lower() == cand_lower:
                        matched_var = k
                        break
                if matched_var:
                    break

            if matched_var:
                if not comp_unit and data_values[matched_var].get('units'):
                    comp_unit = data_values[matched_var]['units']

                v_list = data_values[matched_var]['values'][i] if i < len(data_values[matched_var]['values']) else ['']
                comp_values.append(v_list)
                comp_averages.append(data_values[matched_var]['average'][i] if i < len(data_values[matched_var]['average']) else '')
                comp_confidences.append(data_values[matched_var]['confidence'][i] if i < len(data_values[matched_var]['confidence']) else '')
                comp_Ns.append(data_values[matched_var]['N'][i] if i < len(data_values[matched_var]['N']) else '')
                comp_stdevs.append(data_values[matched_var]['stdev'][i] if i < len(data_values[matched_var]['stdev']) else '')
                comp_highs.append(data_values[matched_var]['High Tier'][i] if i < len(data_values[matched_var]['High Tier']) else '')
                comp_lows.append(data_values[matched_var]['Low Tier'][i] if i < len(data_values[matched_var]['Low Tier']) else '')
                comp_covs.append(data_values[matched_var]['COV'][i] if i < len(data_values[matched_var]['COV']) else '')
                comp_cis.append(data_values[matched_var]['CI'][i] if i < len(data_values[matched_var]['CI']) else '')
            else:
                comp_values.append([''])
                comp_averages.append('')
                comp_confidences.append('')
                comp_Ns.append('')
                comp_stdevs.append('')
                comp_highs.append('')
                comp_lows.append('')
                comp_covs.append('')
                comp_cis.append('')

        # Template units check
        if configs[0].get('units_col'):
            u_val = sheet.cell(row=r, column=configs[0]['units_col']).value
            if u_val and str(u_val).strip() and str(u_val).strip() != '#':
                comp_unit = str(u_val).strip()

        data_values[row_name] = {
            "units": comp_unit,
            "values": comp_values,
            "average": comp_averages,
            "confidence": comp_confidences,
            "N": comp_Ns,
            "stdev": comp_stdevs,
            "High Tier": comp_highs,
            "Low Tier": comp_lows,
            "COV": comp_covs,
            "CI": comp_cis
        }
        if row_name not in names:
            names.append(row_name)
        units[row_name] = comp_unit
        added_variables.append(row_name)

        log_line = f"Resolved template variable '{row_name}' with units '{comp_unit}' across {len(inputpath)} tests."
        print(log_line)
        if logs is not None:
            logs.append(log_line)

    return added_variables


def load_step22_pair_diffs(folder_path, variable_name, pair_groups=None, test_averages=None, test_labels=None, pairs_csv_path=None):
    """
    Loads percent difference calculations from Step 22 output (PairsFormattedDataL3.csv)
    for a given variable_name. If PairsFormattedDataL3.csv is missing or does not contain
    the variable, falls back to computing % change on-the-fly using pair_groups /
    PairsUnformattedDataL2FilePaths.csv and test_averages.

    Returns:
      diffs_by_final_idx: dict mapping final_idx (0-based) -> list of diff dicts:
        [{
          'pair_key': str (e.g. 'd1B/1R1'),
          'init_code': str (e.g. '1B'),
          'final_code': str (e.g. '1R1'),
          'init_idx': int,
          'final_idx': int,
          'init_label': str,
          'final_label': str,
          'pct': float or None,
          'high': float or None,
          'low': float or None,
        }, ...]
      all_diffs: flat list of all diff dicts.
    """
    all_diffs = []
    diffs_by_final_idx = {}

    if not folder_path or not variable_name:
        return diffs_by_final_idx, all_diffs

    if pairs_csv_path is None:
        pairs_csv_path = os.path.join(folder_path, 'PairsUnformattedDataL2FilePaths.csv')

    key_to_idx = {}
    code_to_name = {}
    idx_to_code = {}
    pair_defs_from_csv = []

    if os.path.isfile(pairs_csv_path):
        try:
            with open(pairs_csv_path, 'r', newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                test_idx = 0
                for row in reader:
                    row_norm = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                    path_val = row_norm.get('path', '')
                    t_code = row_norm.get('test_code', '')
                    d_key = row_norm.get('data_key', '')
                    name_val = row_norm.get('name', '')

                    if path_val:
                        if d_key:
                            key_to_idx[d_key] = test_idx
                            code_to_name[d_key] = name_val or t_code or d_key
                        if t_code:
                            key_to_idx[t_code] = test_idx
                            code_to_name[t_code] = name_val or t_code
                        idx_to_code[test_idx] = t_code or d_key or f"Test {test_idx + 1}"
                        test_idx += 1
                    else:
                        raw_k = d_key or t_code
                        if '/' in raw_k or raw_k.lower().startswith('d'):
                            clean_k = raw_k.lstrip('dD')
                            parts = clean_k.split('/')
                            if len(parts) == 2:
                                pair_defs_from_csv.append((raw_k, parts[0].strip(), parts[1].strip()))
        except Exception as e:
            print(f"Notice: Failed to parse pairs CSV {pairs_csv_path}: {e}")

    # Pass 1: Try reading from PairsFormattedDataL3.csv (Step 22 output)
    step22_path = os.path.join(folder_path, 'PairsFormattedDataL3.csv')
    found_in_step22 = False

    if os.path.isfile(step22_path):
        try:
            with open(step22_path, 'r', newline='', encoding='utf-8-sig') as f:
                reader = list(csv.reader(f))

            if reader:
                header_row = reader[0]
                pair_col_map = {}
                for c_idx, col_name in enumerate(header_row):
                    c_name = col_name.strip()
                    if c_name.endswith('% Change'):
                        pkey = c_name[:-len('% Change')].strip()
                        pair_col_map.setdefault(pkey, {})['pct_col'] = c_idx
                    elif c_name.endswith('High'):
                        pkey = c_name[:-len('High')].strip()
                        pair_col_map.setdefault(pkey, {})['high_col'] = c_idx
                    elif c_name.endswith('Low'):
                        pkey = c_name[:-len('Low')].strip()
                        pair_col_map.setdefault(pkey, {})['low_col'] = c_idx

                target_norm = variable_name.strip().lower()
                target_clean = target_norm.split('(')[0].strip()

                for row in reader[1:]:
                    if not row or len(row) < 2:
                        continue
                    var_cell = row[0].strip()
                    if var_cell.lower() in ('confidence', 'n', 'interval'):
                        break

                    var_cell_norm = var_cell.lower()
                    var_cell_clean = var_cell_norm.split('(')[0].strip()

                    suffixes = ('_l1', '_hp', '_mp', '_lp', '_l5', '_full')
                    v_base = var_cell_clean
                    t_base = target_clean
                    for s in suffixes:
                        if v_base.endswith(s):
                            v_base = v_base[:-len(s)]
                        if t_base.endswith(s):
                            t_base = t_base[:-len(s)]

                    is_match = (
                        var_cell_norm == target_norm or
                        var_cell_clean == target_clean or
                        v_base == t_base or
                        target_norm.startswith(var_cell_clean) or
                        var_cell_clean.startswith(target_clean)
                    )

                    if is_match:
                        found_in_step22 = True
                        for pkey, cols in pair_col_map.items():
                            pct_col = cols.get('pct_col')
                            pct_val = None
                            if pct_col is not None and pct_col < len(row):
                                pct_str = row[pct_col].strip()
                                try:
                                    pct_val = float(pct_str)
                                except (ValueError, TypeError):
                                    pct_val = None

                            high_val = None
                            high_col = cols.get('high_col')
                            if high_col is not None and high_col < len(row):
                                try:
                                    high_val = float(row[high_col].strip())
                                except (ValueError, TypeError):
                                    pass

                            low_val = None
                            low_col = cols.get('low_col')
                            if low_col is not None and low_col < len(row):
                                try:
                                    low_val = float(row[low_col].strip())
                                except (ValueError, TypeError):
                                    pass

                            clean_k = pkey.lstrip('dD')
                            parts = clean_k.split('/')
                            if len(parts) == 2:
                                init_code, final_code = parts[0].strip(), parts[1].strip()
                                init_idx = key_to_idx.get(init_code)
                                final_idx = key_to_idx.get(final_code)

                                if (init_idx is None or final_idx is None) and pair_groups:
                                    for g in pair_groups:
                                        gk = (g.get('data_key', '') or g.get('name', '')).lstrip('dD')
                                        if gk == clean_k and len(g.get('indices', [])) == 2:
                                            init_idx = g['indices'][0]
                                            final_idx = g['indices'][1]
                                            break

                                if init_idx is not None and final_idx is not None:
                                    diff_info = {
                                        'pair_key': pkey,
                                        'init_code': init_code,
                                        'final_code': final_code,
                                        'init_idx': init_idx,
                                        'final_idx': final_idx,
                                        'init_label': (test_labels[init_idx] if test_labels and init_idx < len(test_labels)
                                                       else code_to_name.get(init_code, init_code)),
                                        'final_label': (test_labels[final_idx] if test_labels and final_idx < len(test_labels)
                                                        else code_to_name.get(final_code, final_code)),
                                        'pct': pct_val,
                                        'high': high_val,
                                        'low': low_val,
                                    }
                                    all_diffs.append(diff_info)
                                    diffs_by_final_idx.setdefault(final_idx, []).append(diff_info)
                        break
        except Exception as e:
            print(f"Notice: Failed reading Step 22 pair differences from {step22_path}: {e}")

    # Pass 2: Fallback to on-the-fly calculation if not found in Step 22 file
    if not found_in_step22 and test_averages is not None:
        candidate_pairs = []
        if pair_defs_from_csv:
            for raw_k, i_code, f_code in pair_defs_from_csv:
                i_idx = key_to_idx.get(i_code)
                f_idx = key_to_idx.get(f_code)
                if i_idx is not None and f_idx is not None:
                    candidate_pairs.append((raw_k, i_code, f_code, i_idx, f_idx))
        elif pair_groups:
            for g_num, g in enumerate(pair_groups):
                if isinstance(g, dict):
                    indices = g.get('indices', [])
                    if len(indices) == 2:
                        raw_k = g.get('data_key', '') or g.get('name', '')
                        clean_k = raw_k.lstrip('dD')
                        parts = clean_k.split('/')
                        i_code = parts[0].strip() if len(parts) == 2 else idx_to_code.get(indices[0], f"Test {indices[0]+1}")
                        f_code = parts[1].strip() if len(parts) == 2 else idx_to_code.get(indices[1], f"Test {indices[1]+1}")
                        candidate_pairs.append((raw_k, i_code, f_code, indices[0], indices[1]))
                    elif len(indices) > 2:
                        raw_k = g.get('data_key', '') or g.get('name', '')
                        base_idx = indices[0]
                        base_code = idx_to_code.get(base_idx, f"Test {base_idx+1}")
                        for f_idx in indices[1:]:
                            f_code = idx_to_code.get(f_idx, f"Test {f_idx+1}")
                            pair_key = f"d{base_code}/{f_code}"
                            candidate_pairs.append((pair_key, base_code, f_code, base_idx, f_idx))
                elif isinstance(g, str):
                    i_idx = g_num * 2
                    f_idx = g_num * 2 + 1
                    i_code = idx_to_code.get(i_idx, f"Test {i_idx+1}")
                    f_code = idx_to_code.get(f_idx, f"Test {f_idx+1}")
                    raw_k = f"d{i_code}/{f_code}"
                    candidate_pairs.append((raw_k, i_code, f_code, i_idx, f_idx))

        for pkey, init_code, final_code, init_idx, final_idx in candidate_pairs:
            if init_idx < len(test_averages) and final_idx < len(test_averages):
                avg_i = test_averages[init_idx]
                avg_f = test_averages[final_idx]
                pct_val = None
                if avg_i is not None and avg_f is not None:
                    try:
                        avg_i_f = float(avg_i)
                        avg_f_f = float(avg_f)
                        if avg_i_f != 0:
                            pct_val = round(((avg_f_f - avg_i_f) / avg_i_f) * 100.0, 1)
                    except (ValueError, TypeError, ZeroDivisionError):
                        pass

                diff_info = {
                    'pair_key': pkey,
                    'init_code': init_code,
                    'final_code': final_code,
                    'init_idx': init_idx,
                    'final_idx': final_idx,
                    'init_label': (test_labels[init_idx] if test_labels and init_idx < len(test_labels)
                                   else code_to_name.get(init_code, init_code)),
                    'final_label': (test_labels[final_idx] if test_labels and final_idx < len(test_labels)
                                    else code_to_name.get(final_code, final_code)),
                    'pct': pct_val,
                    'high': None,
                    'low': None,
                }
                all_diffs.append(diff_info)
                diffs_by_final_idx.setdefault(final_idx, []).append(diff_info)

    return diffs_by_final_idx, all_diffs


def draw_pair_percent_diffs(ax, diffs_by_final_idx, test_averages, x_offset=1, x_delta=0.0,
                            text_color='#222222', box_edge_color='#cccccc', box_face_color='#ffffff',
                            fontsize=8.0):
    """
    Renders an annotation badge above each comparison test's average marker.

    Parameters:
      ax: matplotlib Axes
      diffs_by_final_idx: dict mapping final_idx -> list of diff dicts
      test_averages: list of average y-values [avg_0, avg_1, ...]
      x_offset: coordinate base (1 for 1-based scatter plots)
      x_delta: horizontal offset for dual-axis (e.g. -0.12 for Left, +0.12 for Right)
      text_color: color of the annotation text
      box_edge_color: border color of the badge
      box_face_color: background fill color of the badge
      fontsize: size of badge font
    """
    if not diffs_by_final_idx or not test_averages:
        return

    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0] if ylim[1] != ylim[0] else 1.0

    for final_idx, diff_list in diffs_by_final_idx.items():
        if final_idx >= len(test_averages):
            continue
        avg_y = test_averages[final_idx]
        if avg_y is None:
            continue
        try:
            avg_y_val = float(avg_y)
        except (ValueError, TypeError):
            continue

        lines = []
        for d in diff_list:
            pct = d.get('pct')
            if pct is None:
                continue
            if abs(pct - round(pct)) < 0.05:
                pct_str = f"{int(round(pct))}%"
            else:
                pct_str = f"{pct:.1f}%"
            lines.append(f"Δ {pct_str}")

        if not lines:
            continue

        badge_text = "\n".join(lines)
        x_pos = (final_idx + x_offset) + x_delta

        is_near_top = (avg_y_val - ylim[0]) > 0.88 * y_range
        y_offset_pts = -14 if is_near_top else 14
        va = 'top' if is_near_top else 'bottom'

        ax.annotate(
            badge_text,
            xy=(x_pos, avg_y_val),
            xytext=(0, y_offset_pts),
            textcoords='offset points',
            ha='center',
            va=va,
            fontsize=fontsize,
            fontweight='bold',
            color=text_color,
            bbox=dict(
                boxstyle='round,pad=0.22',
                facecolor=box_face_color,
                edgecolor=box_edge_color,
                alpha=0.90,
                linewidth=0.8
            ),
            zorder=10
        )






