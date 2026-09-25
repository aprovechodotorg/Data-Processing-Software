import csv
import glob
import os
import re
from datetime import datetime as dt
from openpyxl import load_workbook
import LEMS_DataProcessing_IO as io

def LEMS_CustomFormatted_L3(inputpath, inputpath_lp, outputpath=None, outputexcel=None, csvpath=None, logpath=None):
    """
    Reads data from source CSVs (FormattedDataL3.csv and FormattedDataL3_lp.csv),
    maps it to a template based on data_keys, and writes formatted Excel/CSV files.
    
    Supports:
      1. Single multi-block templates (e.g. FormattedCutTableL3_template_md.xlsx)
      2. Multiple individual templates (e.g. FormattedCutTableL3_template_md_1.xlsx, _2.xlsx, etc.)
         which are processed individually for isolated debugging and then combined into the final table.
    """

    # Backward compatibility if called with 5 positional arguments:
    if logpath is None and csvpath is None:
        outputpath, outputexcel, csvpath, logpath, inputpath_lp = inputpath_lp, outputpath, outputexcel, csvpath, None

    ver = '1.0'
    timestampobject = dt.now()
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = f'LEMS_CustomFormatted_L3 v{ver}   {timestampstring}'
    print(line)
    logs = [line]

    # Helper functions for retrieval and formatting
    def format_value(val, decimal_places=1):
        if val is None:
            return None
        val_str = str(val).strip()
        if val_str == '' or val_str.lower() == 'nan':
            return None
        try:
            rounded = round(float(val_str), decimal_places)
            return int(rounded) if decimal_places == 0 else rounded
        except (ValueError, TypeError):
            return val_str

    def format_n(val):
        if val is None:
            return None
        val_str = str(val).strip()
        if val_str == '' or val_str.lower() == 'nan':
            return None
        try:
            return int(float(val_str))
        except (ValueError, TypeError):
            return val_str

    def get_source_value(src_dict, sec, d_key, n_key):
        if sec not in src_dict or d_key not in src_dict[sec]:
            return None
        val_dict = src_dict[sec][d_key].get('values', {})
        if n_key in val_dict:
            return val_dict[n_key]
        n_stripped = n_key.strip()
        if n_stripped in val_dict:
            return val_dict[n_stripped]
        # Case-insensitive fallback
        n_lower = n_stripped.lower()
        for k, v in val_dict.items():
            if k.strip().lower() == n_lower:
                return v
        return None

    # Unit conversion lookup table: (from_units, to_units) -> multiply factor
    UNIT_CONVERSIONS = {
        ('g/min', 'lb/hr'):   60 / 453.592,
        ('lb/hr', 'g/min'):   453.592 / 60,
        ('g',     'kg'):      0.001,
        ('kg',    'g'):       1000.0,
        ('g',     'lb'):      1 / 453.592,
        ('lb',    'g'):       453.592,
        ('mg',    'g'):       0.001,
        ('g',     'mg'):      1000.0,
        ('kJ',    'MJ'):      0.001,
        ('MJ',    'kJ'):      1000.0,
        ('kJ/kg', 'MJ/kg'):   0.001,
        ('MJ/kg', 'kJ/kg'):   1000.0,
        ('W',     'kW'):      0.001,
        ('kW',    'W'):       1000.0,
        ('min',   'hr'):      1 / 60,
        ('hr',    'min'):     60.0,
        ('s',     'hr'):      1 / 3600,
        ('hr',    's'):       3600.0,
    }

    def convert_value(val, from_units, to_units):
        """Apply unit conversion to a numeric value. Returns converted value or original if no conversion found."""
        if val is None:
            return val
        from_u = str(from_units).strip() if from_units else ''
        to_u = str(to_units).strip() if to_units else ''
        if not from_u or not to_u or from_u == to_u:
            return val
        factor = UNIT_CONVERSIONS.get((from_u, to_u))
        if factor is None:
            return val
        try:
            return round(float(val) * factor, 4)
        except (ValueError, TypeError):
            return val

    # 1. Load Data and Units from CustomCutTable_L3
    def load_data(path):
        data = {'average': {}, 'confidence': {}, 'n': {}, '_test_codes': set(), '_variables': set()}
        if not path or not os.path.exists(path):
            return data
        with open(path, 'r') as f:
            reader = list(csv.reader(f))
            name_keys = None
            for row in reader:
                if row and row[0].strip().lower() == 'test_code':
                    name_keys = row
                    break
            if name_keys is None:
                if len(reader) > 2:
                    name_keys = reader[2]
                else:
                    name_keys = []

            # Record available test codes from header row
            for idx in range(2, len(name_keys)):
                k = name_keys[idx].strip()
                if k and k.lower() not in ('average', 'percent change', 'percent change high', 'percent change low', 'interval', 'n', 'cov', 'ci'):
                    data['_test_codes'].add(k)

            current_section = None
            for row in reader:
                if not row or len(row) < 2:
                    continue
                first_val = row[0].strip().lower()
                if len(row) > 1 and row[1].strip().lower() == 'units':
                    if first_val in ('average', 'values'):
                        current_section = 'average'
                        continue
                    elif first_val == 'confidence':
                        current_section = 'confidence'
                        continue
                    elif first_val == 'n':
                        current_section = 'n'
                        continue
                if first_val in ('average', 'values', 'confidence', 'n', 'all outputs', 'test_code', 'variable_name'):
                    continue
                if current_section is not None:
                    var_name = row[0].strip()
                    units = row[1].strip()
                    if not var_name:
                        continue
                    data['_variables'].add(var_name)
                    if var_name not in data[current_section]:
                        data[current_section][var_name] = {'units': units, 'values': {}}
                    for i in range(2, min(len(row), len(name_keys))):
                        key = name_keys[i].strip()
                        if key:
                            data[current_section][var_name]['values'][key] = row[i]
        return data

    source_data_main = load_data(inputpath)
    source_data_lp = load_data(inputpath_lp)

    line = f'Loaded input data: {inputpath} ({len(source_data_main["_variables"])} variables, test codes: {sorted(source_data_main["_test_codes"])})'
    print(line)
    logs.append(line)
    if inputpath_lp and os.path.exists(inputpath_lp):
        line = f'Loaded LP input data: {inputpath_lp} ({len(source_data_lp["_variables"])} variables, test codes: {sorted(source_data_lp["_test_codes"])})'
        print(line)
        logs.append(line)

    # 2. Parse Template Block Configurations
    IGNORED_HEADERS = {'metrics', 'operation', 'test_code', 'variable_name', 'all outputs'}

    def parse_template_configs(sheet):
        header_row_idx = None
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value and str(cell.value).strip().lower().startswith('data_key'):
                    header_row_idx = cell.row
                    break
            if header_row_idx is not None:
                break

        if header_row_idx is None:
            return None, []

        data_key_cols = []
        for cell in sheet[header_row_idx]:
            if cell.value and str(cell.value).strip().lower().startswith('data_key'):
                data_key_cols.append(cell.column)
        data_key_cols.sort()

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

            # Determine where test columns end for this block (before next block's metadata starts)
            block_end_col = next_dk_col
            for c in range(last_meta_col + 1, next_dk_col):
                v = sheet.cell(row=header_row_idx, column=c).value
                if v:
                    vs = str(v).strip().lower()
                    if any(vs.startswith(prefix) for prefix in ['units', 'sig_figs', 'data_type', 'data_key', 'data_source']):
                        block_end_col = c
                        break

            # Collect test columns strictly within this block
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

        return header_row_idx, configs

    # 3. Process Single Template
    def process_single_template(t_path, out_excel, out_csv):
        line = f'\n--- Processing template: {t_path} ---'
        print(line)
        logs.append(line)

        wb = load_workbook(t_path)
        sheet = wb.active
        header_row_idx, data_key_configs = parse_template_configs(sheet)

        if header_row_idx is None or not data_key_configs:
            line = f'Warning: no data_key headers found in {t_path}'
            print(line)
            logs.append(line)
            return wb, sheet, []

        all_requested_tests = set()
        for cfg in data_key_configs:
            all_requested_tests.update(cfg['template_name_keys'].keys())

        # Debug checks: verify test codes
        all_src_tests = source_data_main['_test_codes'].union(source_data_lp['_test_codes'])
        line = f'Template requested test code(s): {sorted(all_requested_tests)}'
        print(line)
        logs.append(line)

        for t_code in all_requested_tests:
            # Case-insensitive check
            if not any(t_code.lower() == s.lower() for s in all_src_tests):
                warn = f"Warning: test code '{t_code}' in template does NOT match any test in source CSVs! Available: {sorted(all_src_tests)}"
                print(warn)
                logs.append(warn)

        matched_count = 0
        missing_keys = set()

        for row_cells in sheet.iter_rows(min_row=1):
            row_idx = row_cells[0].row
            if row_idx == header_row_idx:
                continue

            for config in data_key_configs:
                dk_col = config['data_key_col']
                units_col = config['units_col']
                sig_figs_col = config['sig_figs_col']
                data_type_col = config['data_type_col']
                data_source_col = config['data_source_col']
                t_name_keys = config['template_name_keys']

                d_key_val = sheet.cell(row=row_idx, column=dk_col).value
                if d_key_val is None or not str(d_key_val).strip():
                    continue

                d_key_str = str(d_key_val).strip()

                # Determine data_source (main vs lp)
                row_data_source = None
                if data_source_col is not None:
                    ds_val = sheet.cell(row=row_idx, column=data_source_col).value
                    if ds_val is not None:
                        row_data_source = str(ds_val).strip().lower()

                target_source_dict = source_data_lp if row_data_source == 'lp' else source_data_main

                # Resolve d_key against target_source_dict (exact or case-insensitive)
                d_key = None
                for sec in ('average', 'confidence', 'n'):
                    if d_key_str in target_source_dict[sec]:
                        d_key = d_key_str
                        break
                if d_key is None:
                    d_key_lower = d_key_str.lower()
                    for sec in ('average', 'confidence', 'n'):
                        for k in target_source_dict[sec]:
                            if k.lower() == d_key_lower:
                                d_key = k
                                break
                        if d_key is not None:
                            break

                if d_key is None:
                    missing_keys.add(d_key_str)
                    continue

                matched_count += 1

                # Source units
                source_units = None
                for sec in ('average', 'confidence', 'n'):
                    if d_key in target_source_dict[sec] and 'units' in target_source_dict[sec][d_key]:
                        source_units = target_source_dict[sec][d_key]['units']
                        break

                # Target units
                target_units = None
                if units_col is not None:
                    template_units_val = sheet.cell(row=row_idx, column=units_col).value
                    if template_units_val is not None and str(template_units_val).strip():
                        target_units = str(template_units_val).strip()
                    else:
                        target_units = source_units
                        sheet.cell(row=row_idx, column=units_col).value = source_units

                # Sig figs
                row_sig_figs = 1
                if sig_figs_col is not None:
                    sf_val = sheet.cell(row=row_idx, column=sig_figs_col).value
                    if sf_val is not None:
                        try:
                            row_sig_figs = int(sf_val)
                        except (ValueError, TypeError):
                            pass

                # Data type
                row_data_type = 'average'
                if data_type_col is not None:
                    dt_val = sheet.cell(row=row_idx, column=data_type_col).value
                    if dt_val is not None:
                        row_data_type = str(dt_val).strip().lower()

                # Write Values to this block's test columns
                for n_key, col_idx in t_name_keys.items():
                    normalized_dt = row_data_type.replace(' ', '')

                    if ('average' in row_data_type or 'values' in row_data_type) and 'confidence' in row_data_type and '(n)' in normalized_dt:
                        val_avg = get_source_value(target_source_dict, 'average', d_key, n_key)
                        val_conf = get_source_value(target_source_dict, 'confidence', d_key, n_key)
                        val_n = get_source_value(target_source_dict, 'n', d_key, n_key)
                        f_avg = format_value(convert_value(val_avg, source_units, target_units), row_sig_figs)
                        f_conf = format_value(convert_value(val_conf, source_units, target_units), row_sig_figs)
                        f_n = format_n(val_n)

                        if f_avg is not None and f_conf is not None and f_n is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f"{f_avg} ± {f_conf} ({f_n})"
                        elif f_avg is not None and f_conf is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f"{f_avg} ± {f_conf}"
                        elif f_avg is not None and f_n is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f"{f_avg} ({f_n})"
                        elif f_avg is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f_avg
                        else:
                            sheet.cell(row=row_idx, column=col_idx).value = None

                    elif ('average' in row_data_type or 'values' in row_data_type) and 'confidence' in row_data_type:
                        val_avg = get_source_value(target_source_dict, 'average', d_key, n_key)
                        val_conf = get_source_value(target_source_dict, 'confidence', d_key, n_key)
                        f_avg = format_value(convert_value(val_avg, source_units, target_units), row_sig_figs)
                        f_conf = format_value(convert_value(val_conf, source_units, target_units), row_sig_figs)

                        if f_avg is not None and f_conf is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f"{f_avg} ± {f_conf}"
                        elif f_avg is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f_avg
                        elif f_conf is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f_conf
                        else:
                            sheet.cell(row=row_idx, column=col_idx).value = None

                    elif ('average' in row_data_type or 'values' in row_data_type) and '(n)' in normalized_dt:
                        val_avg = get_source_value(target_source_dict, 'average', d_key, n_key)
                        val_n = get_source_value(target_source_dict, 'n', d_key, n_key)
                        f_avg = format_value(convert_value(val_avg, source_units, target_units), row_sig_figs)
                        f_n = format_n(val_n)

                        if f_avg is not None and f_n is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f"{f_avg} ({f_n})"
                        elif f_avg is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f_avg
                        else:
                            sheet.cell(row=row_idx, column=col_idx).value = None

                    elif 'confidence' in row_data_type and '(n)' in normalized_dt:
                        val_conf = get_source_value(target_source_dict, 'confidence', d_key, n_key)
                        val_n = get_source_value(target_source_dict, 'n', d_key, n_key)
                        f_conf = format_value(convert_value(val_conf, source_units, target_units), row_sig_figs)
                        f_n = format_n(val_n)

                        if f_conf is not None and f_n is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f"{f_conf} ({f_n})"
                        elif f_conf is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f_conf
                        else:
                            sheet.cell(row=row_idx, column=col_idx).value = None

                    elif 'confidence' in row_data_type:
                        val = get_source_value(target_source_dict, 'confidence', d_key, n_key)
                        sheet.cell(row=row_idx, column=col_idx).value = format_value(convert_value(val, source_units, target_units), row_sig_figs)
                    elif row_data_type == 'n':
                        val = get_source_value(target_source_dict, 'n', d_key, n_key)
                        sheet.cell(row=row_idx, column=col_idx).value = format_value(val)
                    elif row_data_type in ('average', 'values'):
                        val = get_source_value(target_source_dict, 'average', d_key, n_key)
                        sheet.cell(row=row_idx, column=col_idx).value = format_value(convert_value(val, source_units, target_units), row_sig_figs)
                    else:
                        val = get_source_value(target_source_dict, 'average', d_key, n_key)
                        sheet.cell(row=row_idx, column=col_idx).value = format_value(convert_value(val, source_units, target_units), row_sig_figs)

        # Save individual template outputs
        wb.save(out_excel)
        with open(out_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            for r in sheet.iter_rows(values_only=True):
                writer.writerow(r)

        line = f"Output written: {out_excel} | Matched {matched_count} variable lookups."
        print(line)
        logs.append(line)
        if missing_keys:
            line = f"Debug: {len(missing_keys)} data_key(s) in template not found in source CSV: {sorted(missing_keys)[:10]}{'...' if len(missing_keys) > 10 else ''}"
            print(line)
            logs.append(line)

        return wb, sheet, data_key_configs

    # 4. Combine Multiple Output Workbooks
    def combine_template_outputs(template_runs, final_excel, final_csv):
        """
        Combines individual template outputs side-by-side into a single consolidated workbook.
        template_runs is a list of tuples: (excel_path, data_key_configs)
        """
        if not template_runs:
            return

        base_excel, base_configs = template_runs[0]
        base_wb = load_workbook(base_excel)
        base_sheet = base_wb.active

        header_row_idx = None
        for row in base_sheet.iter_rows():
            for cell in row:
                if cell.value and str(cell.value).strip().lower().startswith('data_key'):
                    header_row_idx = cell.row
                    break
            if header_row_idx is not None:
                break
        if header_row_idx is None:
            header_row_idx = 3

        # Find current last filled column in base_sheet (checking header row)
        current_col = max((c for c in range(1, base_sheet.max_column + 1) if base_sheet.cell(row=header_row_idx, column=c).value is not None), default=base_sheet.max_column)

        line = f"\nCombining {len(template_runs)} outputs into final table: {final_excel}"
        print(line)
        logs.append(line)

        for next_excel, next_configs in template_runs[1:]:
            next_wb = load_workbook(next_excel)
            next_sheet = next_wb.active

            # Find all test columns populated in next_sheet
            for cfg in next_configs:
                for test_name, col_from in cfg['template_name_keys'].items():
                    current_col += 1
                    # Copy all rows for this test column
                    for r in range(1, next_sheet.max_row + 1):
                        source_val = next_sheet.cell(row=r, column=col_from).value
                        base_sheet.cell(row=r, column=current_col).value = source_val
                    line = f"  Appended test column '{test_name}' from {os.path.basename(next_excel)} to column {current_col}"
                    print(line)
                    logs.append(line)

        base_wb.save(final_excel)
        with open(final_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            for r in base_sheet.iter_rows(values_only=True):
                writer.writerow(r)

        line = f"Successfully generated consolidated Custom Cut Table: {final_excel} and {final_csv}"
        print(line)
        logs.append(line)

    # 5. Execution Logic: Multi-Template vs Single Template
    template_dir = os.path.dirname(csvpath) if csvpath else os.path.dirname(outputexcel)
    out_dir = os.path.dirname(outputexcel) if outputexcel else template_dir

    # Search for numbered templates: FormattedCutTableL3_template_md_*.xlsx
    search_dirs = [template_dir]
    if out_dir != template_dir:
        search_dirs.append(out_dir)

    multi_templates = []
    for s_dir in search_dirs:
        found = glob.glob(os.path.join(s_dir, 'FormattedCutTableL3_template_md_*.xlsx'))
        for f in found:
            # Exclude lock files or temporary files
            if not os.path.basename(f).startswith('~$'):
                multi_templates.append(f)

    # Deduplicate and sort naturally by number
    multi_templates = list(set(multi_templates))
    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]
    multi_templates.sort(key=natural_sort_key)

    if len(multi_templates) > 1:
        line = f"Detected {len(multi_templates)} individual templates: {[os.path.basename(t) for t in multi_templates]}"
        print(line)
        logs.append(line)

        template_runs = []
        for idx, t_path in enumerate(multi_templates):
            suffix = os.path.splitext(os.path.basename(t_path))[0].split('template_md_')[-1]
            out_excel_i = os.path.join(out_dir, f'FormattedCustomCutTable_L3_{suffix}.xlsx')
            out_csv_i = os.path.join(out_dir, f'FormattedCustomCutTable_L3_{suffix}.csv')

            wb_i, sheet_i, cfgs_i = process_single_template(t_path, out_excel_i, out_csv_i)
            template_runs.append((out_excel_i, cfgs_i))

        # Combine all intermediate outputs into final outputs
        combine_template_outputs(template_runs, outputexcel, outputpath)

    else:
        # Single template mode (works for FormattedCutTableL3_template_md.xlsx or a single specified template)
        target_template = multi_templates[0] if (multi_templates and not (csvpath and os.path.exists(csvpath))) else csvpath
        process_single_template(target_template, outputexcel, outputpath)

    # 6. Write logfile
    if logpath:
        io.write_logfile(logpath, logs)