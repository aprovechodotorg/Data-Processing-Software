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
    Variable, Plotted, Name, Units, % Diff.
    If it exists, ensures '% Diff' column is present.
    Returns True if created or updated, False if already existed unchanged.
    """
    standard_header = ['Variable', 'Plotted', 'Name', 'Units', '% Diff']
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
        col_pct = None
        for cand in ['% diff', '%diff', 'percent diff', 'percent difference', '% change', 'pct diff', 'diff']:
            if cand in header_lower:
                col_pct = header_lower.index(cand)
                break

        if col_pct is None:
            # Append '% Diff' column to existing CSV
            new_rows = []
            header.append('% Diff')
            new_rows.append(header)
            for r in raw_rows[1:]:
                r.append('')
                new_rows.append(r)
            with open(parameterspath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(new_rows)
            return True
        return False

    var = ['Variable']
    for name in names:
        if name != 'time' and name != 'seconds' and name != 'ID':
            var.append(name)
    rows = [standard_header]
    for v in var[1:]:
        u = units.get(v, '') if units else ''
        rows.append([v, 0, '', u, ''])
    with open(parameterspath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    return True


def load_plot_selection_csv(parameterspath, return_pct_diff=False):
    """
    Reads PlotSelection.csv.
    Returns:
      plotnames: list of variable names selected to be plotted (Plotted == 1)
      display_names: dict mapping variable name -> display name (from Name column, or empty string)
      target_units: dict mapping variable name -> target units (from Units column, or empty string)
      pct_diff_flags (if return_pct_diff=True): dict mapping variable name -> bool (% Diff enabled)
    """
    plotnames = []
    display_names = {}
    target_units = {}
    pct_diff_flags = {}
    if not os.path.isfile(parameterspath):
        if return_pct_diff:
            return plotnames, display_names, target_units, pct_diff_flags
        return plotnames, display_names, target_units

    with open(parameterspath, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header_row = None
        col_var = 0
        col_plot = 1
        col_name = 2
        col_unit = 3
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

                    for cand in ['% diff', '%diff', 'percent diff', 'percent difference', '% change', 'pct diff', 'diff']:
                        if cand in header_row:
                            col_pct_diff = header_row.index(cand)
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
            pct_diff_val = row[col_pct_diff].strip() if col_pct_diff is not None and len(row) > col_pct_diff else ''
            is_pct_diff = pct_diff_val.lower() in ('1', 'true', 'yes', 'y', 'on')

            display_names[var_name] = disp_name
            target_units[var_name] = t_unit
            pct_diff_flags[var_name] = is_pct_diff
            if disp_name:
                pct_diff_flags[disp_name] = is_pct_diff

            if plotted_val == '1':
                plotnames.append(var_name)

    if return_pct_diff:
        return plotnames, display_names, target_units, pct_diff_flags
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
                            extra_str = f"\n{info[2]}" if len(info) > 2 and info[2] else ""
                            if "average" in str(name).lower():
                                lines.append(f"{name} = {val_str}{u_str}{extra_str}")
                            else:
                                lines.append(f"{name}\nValue: {val_str}{u_str}{extra_str}")
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
            for g in pair_groups:
                if 'indices' in g and len(g['indices']) == 2:
                    raw_k = g.get('data_key', '') or g.get('name', '')
                    clean_k = raw_k.lstrip('dD')
                    parts = clean_k.split('/')
                    i_code = parts[0].strip() if len(parts) == 2 else idx_to_code.get(g['indices'][0], f"Test {g['indices'][0]+1}")
                    f_code = parts[1].strip() if len(parts) == 2 else idx_to_code.get(g['indices'][1], f"Test {g['indices'][1]+1}")
                    candidate_pairs.append((raw_k, i_code, f_code, g['indices'][0], g['indices'][1]))

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



