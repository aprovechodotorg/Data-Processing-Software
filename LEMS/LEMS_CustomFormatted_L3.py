import csv
from openpyxl import load_workbook
import LEMS_DataProcessing_IO as io
from datetime import datetime as dt

def LEMS_CustomFormatted_L3(inputpath, outputpath, outputexcel, csvpath, logpath):
    """
    Reads data from a source CSV, maps it to a template based on data_keys,
    and writes to new CSV/Excel files.
    """

    #Function intakes list of inputpaths and creates comparison between values in list.
    ver = '0.0'

    timestampobject = dt.now()  # get timestamp from operating system for log file
    timestampstring = timestampobject.strftime("%Y%m%d %H:%M:%S")

    line = 'LEMS_CustomFormatted_L3 v' + ver + '   ' + timestampstring  # Add to log
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

    def get_source_value(sec, d_key, n_key):
        if sec not in source_data or d_key not in source_data[sec]:
            return None
        val_dict = source_data[sec][d_key]['values']
        if n_key in val_dict:
            return val_dict[n_key]
        elif n_key.strip() in val_dict:
            return val_dict[n_key.strip()]
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
            line = f'Warning: no unit conversion found for {from_u!r} -> {to_u!r}, writing raw value'
            print(line)
            logs.append(line)
            return val
        try:
            return round(float(val) * factor, 4)
        except (ValueError, TypeError):
            return val

    # 1. Load Data and Units from CustomCutTable_L3
    # Dictionary structure:
    # source_data = {
    #     'average': {variable: {'units': '...', 'values': {name_key: value}}},
    #     'confidence': {variable: {'units': '...', 'values': {name_key: value}}},
    #     'n': {variable: {'units': '...', 'values': {name_key: value}}}
    # }
    source_data = {
        'average': {},
        'confidence': {},
        'n': {}
    }
    with open(inputpath, 'r') as f:
        reader = list(csv.reader(f))
        
        # Find the row containing 'test_code' to define column mappings (name_keys)
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

        current_section = None
        for row in reader:
            if not row or len(row) < 2:
                continue
            
            # Check for section headers (e.g. 'average'/'values', 'confidence', 'N')
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

            # Skip header/metadata rows within sections
            if first_val in ('average', 'values', 'confidence', 'n', 'all outputs', 'test_code', 'variable_name'):
                continue

            # Read variable data if inside a section
            if current_section is not None:
                var_name = row[0].strip()
                units = row[1].strip()
                if not var_name:
                    continue
                
                if var_name not in source_data[current_section]:
                    source_data[current_section][var_name] = {'units': units, 'values': {}}
                
                for i in range(2, min(len(row), len(name_keys))):
                    key = name_keys[i].strip()
                    if key:
                        source_data[current_section][var_name]['values'][key] = row[i]

    line = 'loaded input data: ' + inputpath
    print(line)
    logs.append(line)

    # 2. Load Template and Map Data
    # We use the openpyxl library to handle the .xlsx template formatting
    wb = load_workbook(csvpath)

    line = 'loaded output template: ' + csvpath
    print(line)
    logs.append(line)

    sheet = wb.active

    # Find the header row (containing name_keys) and the data_key columns
    header_row_idx = None
    for row in sheet.iter_rows():
        for cell in row:
            if cell.value and str(cell.value).startswith('data_key'):
                header_row_idx = cell.row
                break
        if header_row_idx is not None:
            break

    data_key_cols = []
    if header_row_idx is not None:
        for cell in sheet[header_row_idx]:
            if cell.value and str(cell.value).startswith('data_key'):
                data_key_cols.append(cell.column)
        data_key_cols.sort()

    # Map each data_key column to its units, data_type, and template_name_keys
    data_key_configs = []
    for idx, dk_col in enumerate(data_key_cols):
        # Determine the boundaries set by the next data_key column
        next_dk_col = data_key_cols[idx + 1] if idx + 1 < len(data_key_cols) else float('inf')

        # Determine data_type_col, units_col, and sig_figs_col by scanning columns to the left of dk_col
        data_type_col = None
        units_col = None
        sig_figs_col = None
        for col_idx in range(dk_col - 1, 0, -1):
            if idx > 0 and col_idx <= data_key_cols[idx - 1]:
                break
            val_in_header = sheet.cell(row=header_row_idx, column=col_idx).value
            if val_in_header:
                val_header_str = str(val_in_header).strip().lower()
                if val_header_str.startswith('data_type') and data_type_col is None:
                    data_type_col = col_idx
                elif val_header_str.startswith('units') and units_col is None:
                    units_col = col_idx
                elif val_header_str.startswith('sig_figs') and sig_figs_col is None:
                    sig_figs_col = col_idx

        t_name_keys = {}
        for col_cell in sheet[header_row_idx]:
            c_col = col_cell.column
            # Only include columns strictly between dk_col and next_dk_col
            if dk_col < c_col < next_dk_col and col_cell.value:
                val_str = str(col_cell.value).strip()
                val_str_lower = val_str.lower()
                is_metadata = (
                    val_str_lower.startswith('units')
                    or val_str_lower.startswith('data_type')
                    or val_str_lower.startswith('sig_figs')
                    or val_str_lower.startswith('data_key')
                )
                if not is_metadata:
                    t_name_keys[val_str] = c_col

        data_key_configs.append({
            'data_key_col': dk_col,
            'units_col': units_col,
            'sig_figs_col': sig_figs_col,
            'data_type_col': data_type_col,
            'template_name_keys': t_name_keys
        })

    # 3. Fill the template with data and units
    for row_cells in sheet.iter_rows(min_row=1):
        row_idx = row_cells[0].row
        if row_idx == header_row_idx:
            continue

        for config in data_key_configs:
            dk_col = config['data_key_col']
            units_col = config['units_col']
            sig_figs_col = config['sig_figs_col']
            data_type_col = config['data_type_col']
            t_name_keys = config['template_name_keys']

            d_key_val = sheet.cell(row=row_idx, column=dk_col).value

            # Resolve d_key against source_data keys
            d_key = None
            if d_key_val is not None:
                d_key_str = str(d_key_val).strip()
                for sec in ('average', 'confidence', 'n'):
                    if d_key_str in source_data[sec]:
                        d_key = d_key_str
                        break
                    elif d_key_val in source_data[sec]:
                        d_key = d_key_val
                        break

            if d_key is not None:
                # Get source units from CSV data
                source_units = None
                for sec in ('average', 'confidence', 'n'):
                    if d_key in source_data[sec] and 'units' in source_data[sec][d_key]:
                        source_units = source_data[sec][d_key]['units']
                        break

                # Determine target units and whether conversion is needed
                target_units = None
                if units_col is not None:
                    template_units_val = sheet.cell(row=row_idx, column=units_col).value
                    if template_units_val is not None and str(template_units_val).strip():
                        # Template has a pre-filled target unit — keep it and convert
                        target_units = str(template_units_val).strip()
                    else:
                        # Template units cell is empty — write source units and don't convert
                        target_units = source_units
                        sheet.cell(row=row_idx, column=units_col).value = source_units

                # Get sig_figs for this row (default 1 if blank)
                row_sig_figs = 1
                if sig_figs_col is not None:
                    sf_val = sheet.cell(row=row_idx, column=sig_figs_col).value
                    if sf_val is not None:
                        try:
                            row_sig_figs = int(sf_val)
                        except (ValueError, TypeError):
                            pass  # keep default of 1

                # Get data_type from template row (default to 'average')
                row_data_type = 'average'
                if data_type_col is not None:
                    dt_val = sheet.cell(row=row_idx, column=data_type_col).value
                    if dt_val is not None:
                        row_data_type = str(dt_val).strip().lower()

                # Write Values
                for n_key, col_idx in t_name_keys.items():
                    # Normalize string for bracket checks: 'average +- confidence (n)' -> 'average+-confidence(n)'
                    normalized_dt = row_data_type.replace(' ', '')
                    
                    if ('average' in row_data_type or 'values' in row_data_type) and 'confidence' in row_data_type and '(n)' in normalized_dt:
                        val_avg = get_source_value('average', d_key, n_key)
                        val_conf = get_source_value('confidence', d_key, n_key)
                        val_n = get_source_value('n', d_key, n_key)
                        f_avg = format_value(convert_value(val_avg, source_units, target_units), row_sig_figs)
                        f_conf = format_value(convert_value(val_conf, source_units, target_units), row_sig_figs)
                        f_n = format_n(val_n)  # counts are never converted
                        
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
                        val_avg = get_source_value('average', d_key, n_key)
                        val_conf = get_source_value('confidence', d_key, n_key)
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
                        val_avg = get_source_value('average', d_key, n_key)
                        val_n = get_source_value('n', d_key, n_key)
                        f_avg = format_value(convert_value(val_avg, source_units, target_units), row_sig_figs)
                        f_n = format_n(val_n)  # counts are never converted
                        
                        if f_avg is not None and f_n is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f"{f_avg} ({f_n})"
                        elif f_avg is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f_avg
                        else:
                            sheet.cell(row=row_idx, column=col_idx).value = None

                    elif 'confidence' in row_data_type and '(n)' in normalized_dt:
                        val_conf = get_source_value('confidence', d_key, n_key)
                        val_n = get_source_value('n', d_key, n_key)
                        f_conf = format_value(convert_value(val_conf, source_units, target_units), row_sig_figs)
                        f_n = format_n(val_n)  # counts are never converted
                        
                        if f_conf is not None and f_n is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f"{f_conf} ({f_n})"
                        elif f_conf is not None:
                            sheet.cell(row=row_idx, column=col_idx).value = f_conf
                        else:
                            sheet.cell(row=row_idx, column=col_idx).value = None

                    elif 'confidence' in row_data_type:
                        val = get_source_value('confidence', d_key, n_key)
                        sheet.cell(row=row_idx, column=col_idx).value = format_value(convert_value(val, source_units, target_units), row_sig_figs)
                    elif row_data_type == 'n':
                        val = get_source_value('n', d_key, n_key)
                        sheet.cell(row=row_idx, column=col_idx).value = format_value(val)  # counts are never converted
                    elif row_data_type in ('average', 'values'):
                        val = get_source_value('average', d_key, n_key)
                        sheet.cell(row=row_idx, column=col_idx).value = format_value(convert_value(val, source_units, target_units), row_sig_figs)
                    else:
                        # Default fallback to average
                        val = get_source_value('average', d_key, n_key)
                        sheet.cell(row=row_idx, column=col_idx).value = format_value(convert_value(val, source_units, target_units), row_sig_figs)

    # 4. Save Outputs
    # Save Excel version
    wb.save(outputexcel)
    # Log the action
    line = 'Formatted Custom Cut Table created: ' + outputexcel
    print(line)
    logs.append(line)

    # Save CSV version (using logic from your write_timeseries function)
    with open(outputpath, 'w', newline='') as f:
        writer = csv.writer(f)
        for row in sheet.iter_rows(values_only=True):
            writer.writerow(row)

    # Log the action
    line = 'Formatted Custom Cut Table created: ' + outputpath
    print(line)
    logs.append(line)

    # print to log file
    io.write_logfile(logpath, logs)