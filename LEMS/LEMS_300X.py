#    Copyright (C) 2026 Aprovecho Research Center
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

# v0.4 Python3 - Universal LEMS Loader (3001, 3002, 3009, 3015, 3016)
import csv
from datetime import datetime, timedelta
from datetime import datetime as dt
import LEMS_DataProcessing_IO as io


def LEMS_300X_Universal(Inputpath, outputpath, logpath, fw_version):
    """
    Standardized loader for LEMS 3000 series (3001, 3002, 3009, 3015, 3016).
    Handles high-performance streaming, error skipping, and firmware-specific mapping.
    """
    ver = '0.4'
    timestampstring = dt.now().strftime("%Y%m%d %H:%M:%S")

    # --- 1. DATA LOAD ---
    try:
        # High-performance streaming load
        names, units, data, A, B, C, D, const, detected_ver = io.load_timeseries_with_header(Inputpath, logpath)

        # Determine version (Priority: User input > File header detection)
        if not fw_version:
            fw_version = str(detected_ver)

        # Simplified version flags
        is_3001 = '3001' in fw_version
        is_3009 = '3009' in fw_version
        is_3015 = any(v in fw_version for v in ['3015', '3016'])
        is_3002 = not (is_3001 or is_3009 or is_3015)  # Default to 3002 mapping

        line = f'LEMS_Universal v{ver} | Mode: {fw_version} | {timestampstring}'
        print(line)
        logs = [line]
        multi = A  # Multipliers from row '# 0'
    except Exception as e:
        return [f"Critical error during load: {e}"]

    # --- 2. DEFINE OUTPUT COLUMNS BY VERSION ---
    if is_3001:
        names_new = ['time', 'seconds', 'CO', 'CO2', 'PM', 'Flow', 'FLUEtemp', 'H2Otemp', 'RH', 'COtemp', 'TC aux',
                     'pd aux', 'O2_1', 'O2_2', 'O2_3', 'O2_4']
    elif is_3009:
        names_new = ['time', 'seconds', 'CO', 'CO2', 'PM', 'Flow', 'FLUEtemp', 'H2Otemp', 'RH', 'TC1', 'TC2', 'O2']
    elif is_3015:
        names_new = ['time', 'seconds', 'CO', 'CO2', 'PM', 'Flow', 'FLUEtemp', 'H2Otemp', 'RH', 'COtemp']
    else:  # 3002
        names_new = ['time', 'seconds', 'CO', 'CO2', 'PM', 'Flow', 'FLUEtemp', 'H2Otemp', 'RH', 'COtemp', 'TC1', 'dP2',
                     'O2_1', 'O2_2', 'O2_3', 'O2_4']

    metric = {}
    scat_eff = 3

    # --- 3. CHANNEL MAPPING & CALCULATIONS ---
    for name in names_new:
        if name == 'time': continue

        # Map standardized names to raw CSV keys
        raw_key = name
        if name == 'CO':
            raw_key = 'co'
        elif name == 'CO2':
            raw_key = 'co2'
        elif name == 'PM':
            raw_key = 'pm'
        elif name == 'Flow':
            raw_key = 'flow' if (is_3009 or is_3015) else 'flue flow'
        elif name == 'FLUEtemp':
            raw_key = 'flue temp' if (is_3009 or is_3015) else 'flue T'
        elif name == 'H2Otemp':
            raw_key = 'tc' if (is_3009 or is_3015) else 'tc h2o'
        elif name == 'COtemp':
            raw_key = 'temp' if is_3015 else 'gas T'
        elif name == 'RH':
            raw_key = 'rh' if is_3015 else ('RH' if is_3009 else 'RH')
        # TC/Aux Mappings
        elif name == 'TC1' and is_3002:
            raw_key = 'tc pitot'
        elif name == 'dP2' and is_3002:
            raw_key = 'flow pito'
        elif name == 'O2' and is_3009:
            raw_key = 'o2'
        elif 'O2_' in name:
            raw_key = name.replace('O2_', 'O2 ch') if not is_3001 else name.replace('O2_', 'O2 ')

        if raw_key in data:
            # Multiplier Logic
            if name in ['CO', 'CO2', 'PM', 'FLUEtemp']:
                m_key = raw_key
                val_list = data[raw_key]
                if name == 'PM':
                    metric[name] = [v * multi.get(m_key, 1) * scat_eff if isinstance(v, (int, float)) else v for v in
                                    val_list]
                else:
                    metric[name] = [v * multi.get(m_key, 1) if isinstance(v, (int, float)) else v for v in val_list]
            elif name in ['Flow', 'dP2', 'pd aux']:
                # All pressure/flow channels convert from inches to mm (25.4)
                metric[name] = [v * 25.4 if isinstance(v, (int, float)) else v for v in data[raw_key]]
            else:
                metric[name] = data[raw_key]
        else:
            metric[name] = ['nan'] * len(data.get('seconds', []))

    # --- 4. TIME SYNCHRONIZATION ---
    # Adjust offsets: 3009 is usually -2/-3, others are -1/-2
    start_offset = 2 if is_3009 else 1
    date_offset = 3 if is_3009 else 2

    start_time_str = ""
    date_str = ""
    with open(Inputpath, 'r') as f:
        reader = csv.reader(f)
        history = []
        for i, row in enumerate(reader):
            history.append(row)
            if row and row[0] == '#headers: ':
                start_time_str = history[i - start_offset][1]
                date_str = history[i - date_offset][1]
                break
            if i > 100: break

    try:
        # Robust Date Parsing (Handles -, /, and : separators)
        date_clean = date_str.replace("-", "/").replace(":", "/").split("/")
        for idx in range(len(date_clean)):
            if len(date_clean[idx]) == 1: date_clean[idx] = '0' + date_clean[idx]

        # Reorder to YYYYMMDD
        if len(date_clean[0]) == 4:
            ds = "".join(date_clean)
        else:
            ds = date_clean[2] + date_clean[0] + date_clean[1]

        base_dt = datetime.strptime(ds + ' ' + start_time_str, '%Y%m%d %H:%M:%S')
        metric['time'] = [str(base_dt + timedelta(seconds=s)).replace("-", "") for s in data['seconds']]
    except:
        logs.append("Warning: Time synchronization failed.")

    # --- 5. UNITS & OUTPUT ---
    # Start with base units common to all 3000-series boxes
    standard_units = {
        'time': 'yyyymmdd hhmmss',
        'seconds': 's',
        'CO': 'ppm',
        'CO2': 'ppm',
        'PM': 'Mm^-1',
        'Flow': 'mmH2O',
        'FLUEtemp': 'C',
        'H2Otemp': 'C',
        'RH': '%',
        'COtemp': 'C'
    }
    units.update(standard_units)

    # Add firmware-specific units
    if is_3001:
        # 3001 specific sensors
        units.update({
            'TC aux': 'C',
            'pd aux': 'mmH2O'
        })
    elif is_3009:
        # 3009 specific sensors
        units.update({
            'TC1': 'C',
            'TC2': 'C',
            'O2': 'lambda'
        })
    elif is_3002:
        # 3002 specific sensors
        units.update({
            'TC1': 'C',
            'dP2': 'mmH2O'
        })

    # Add units for all 4 possible O2 channels (standard for 3001/3002)
    for i in range(1, 5):
        units[f'O2_{i}'] = 'lambda'

    io.write_timeseries(outputpath, names_new, units, metric)
    logs.append(f"Standardized output created: {outputpath}")
    io.write_logfile(logpath, logs)
    return logs