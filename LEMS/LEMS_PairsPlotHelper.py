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
      - Name: test description or pair group name
      - test_code: code of the test (e.g. 1B, 1R2)
      - data_key: data key or difference/pair syntax (e.g. 1B, 1R2, d1B/1R2)
      - path: path to UnFormattedDataL2.csv

    Returns:
      paths: list of UnFormattedDataL2.csv file paths (ordered)
      labels: list of test names/labels corresponding to paths
      groups: list of group dictionaries:
              [{'name': str, 'start': int, 'end': int, 'indices': list, 'data_key': str}, ...]
              where start and end are 0-based indices into paths.
    """
    if not os.path.exists(csv_path):
        return [], [], []

    paths = []
    labels = []
    groups = []
    key_to_idx = {}

    with open(csv_path, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        idx = 0
        raw_rows = []
        for row in reader:
            # normalize row keys
            row_norm = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            raw_rows.append(row_norm)

    # First pass: collect test paths and keys
    for row in raw_rows:
        path = row.get('path', '')
        name = row.get('name', '')
        test_code = row.get('test_code', '')
        data_key = row.get('data_key', '')

        if path:
            paths.append(path)
            label = name if name else (test_code if test_code else f"Test {idx + 1}")
            labels.append(label)
            if data_key:
                key_to_idx[data_key] = idx
            if test_code:
                key_to_idx[test_code] = idx
            idx += 1

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
                    groups.append({
                        'name': group_name,
                        'start': min(indices),
                        'end': max(indices),
                        'indices': indices,
                        'data_key': raw_key
                    })

    return paths, labels, groups


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

        # Top header box with pair name
        if show_titles and group_name:
            box_face = '#e8e8e8' if (g_idx % 2 == 0) else '#ffffff'
            wrapped_title = '\n'.join(textwrap.wrap(group_name, width=16)) if '\n' not in group_name else group_name
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


def ensure_plot_selection_csv(parameterspath, names, units=None):
    """
    Checks if PlotSelection.csv exists; if not, creates it with columns:
    Variable, Plotted, Name, Units
    Returns True if created, False if already existed.
    """
    if os.path.isfile(parameterspath):
        return False
    var = ['Variable']
    for name in names:
        if name != 'time' and name != 'seconds' and name != 'ID':
            var.append(name)
    rows = [['Variable', 'Plotted', 'Name', 'Units']]
    for v in var[1:]:
        u = units.get(v, '') if units else ''
        rows.append([v, 0, '', u])
    with open(parameterspath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    return True


def load_plot_selection_csv(parameterspath):
    """
    Reads PlotSelection.csv.
    Returns:
      plotnames: list of variable names selected to be plotted (Plotted == 1)
      display_names: dict mapping variable name -> display name (from Name column, or empty string)
      target_units: dict mapping variable name -> target units (from Units column, or empty string)
    """
    plotnames = []
    display_names = {}
    target_units = {}
    if not os.path.isfile(parameterspath):
        return plotnames, display_names, target_units

    with open(parameterspath, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header_row = None
        col_var = 0
        col_plot = 1
        col_name = 2
        col_unit = 3

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
                    continue
                else:
                    header_row = []

            var_name = row[col_var].strip() if len(row) > col_var else ''
            if not var_name:
                continue

            plotted_val = row[col_plot].strip() if len(row) > col_plot else '0'
            disp_name = row[col_name].strip() if col_name is not None and len(row) > col_name else ''
            t_unit = row[col_unit].strip() if col_unit is not None and len(row) > col_unit else ''

            display_names[var_name] = disp_name
            target_units[var_name] = t_unit
            if plotted_val == '1':
                plotnames.append(var_name)

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


