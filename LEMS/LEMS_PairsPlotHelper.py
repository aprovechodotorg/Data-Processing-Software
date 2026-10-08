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


def ensure_plot_selection_csv(parameterspath, names):
    """
    Checks if PlotSelection.csv exists; if not, creates it with columns:
    Variable, Plotted, Name
    Returns True if created, False if already existed.
    """
    if os.path.isfile(parameterspath):
        return False
    var = ['Variable']
    for name in names:
        if name != 'time' and name != 'seconds' and name != 'ID':
            var.append(name)
    rows = [['Variable', 'Plotted', 'Name']]
    for v in var[1:]:
        rows.append([v, 0, ''])
    with open(parameterspath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    return True


def load_plot_selection_csv(parameterspath):
    """
    Reads PlotSelection.csv.
    Returns:
      plotnames: list of variable names selected to be plotted (Plotted == 1)
      display_names: dict mapping variable name -> display name (from Name column, or empty string if not provided)
    """
    plotnames = []
    display_names = {}
    if not os.path.isfile(parameterspath):
        return plotnames, display_names

    with open(parameterspath, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header_skipped = False
        for row in reader:
            if not row or not any(field.strip() for field in row):
                continue
            name = row[0].strip()
            if not header_skipped:
                header_skipped = True
                if name.lower() == 'variable':
                    continue
            plotted_val = row[1].strip() if len(row) > 1 else '0'
            disp_name = row[2].strip() if len(row) > 2 else ''
            display_names[name] = disp_name
            if plotted_val == '1':
                plotnames.append(name)

    return plotnames, display_names


def get_y_axis_label(variable, units, display_names=None):
    """
    Returns formatted y-axis label using display name if available, falling back to variable name.
    Includes (units) if units is non-empty.
    """
    if display_names and variable in display_names and display_names[variable].strip():
        label_name = display_names[variable].strip()
    else:
        label_name = variable

    units_str = str(units).strip() if units is not None else ""
    if units_str:
        return f"{label_name} ({units_str})"
    else:
        return label_name

