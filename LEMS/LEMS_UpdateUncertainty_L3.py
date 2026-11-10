#v0.1 Python3

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
import os
import LEMS_DataProcessing_IO as io


DEFAULT_L3_ENERGY_INPUTS_CSV = """variable_name,units,value,uncertainty
fuel_type_1,--,df dry,
fuel_source_1,--,,
fuel_dimensions_1,cmxcmxcm,,
fuel_mc_1,%,17.5,1
fuel_higher_heating_value_1,kJ/kg,20634,206.34
fuel_Cfrac_db_1,g/g,0.5,0.05
fuel_type_2,--,char,
fuel_source_2,--,,
fuel_dimensions_2,cmxcmxcm,,
fuel_mc_2,%,0,0
fuel_higher_heating_value_2,kJ/kg,32500,325
fuel_Cfrac_db_2,g/g,0.9,0.05
fuel_type_3,--,maple,
fuel_source_3,--,,
fuel_dimensions_3,cmxcmxcm,,
fuel_mc_3,%,22,1
fuel_higher_heating_value_3,kJ/kg,20634,206.34
fuel_Cfrac_db_3,g/g,0.5,0.05
char_higher_heating_value,kJ/kg,32500,325
boil_temp,ºC,99.29867353,
pot1_dry_mass,lb,0,
pot2_dry_mass,kg,-,
pot3_dry_mass,kg,,
pot4_dry_mass,kg,,
initial_air_temp,ºC,19,
initial_RH,%,64.7,
initial_pressure,in Hg,29.18,0.1
initial_wind_velocity,m/s,0,
start_time_L1,hh:mm:ss,20260108 11:48:00,
initial_fuel_mass_1_L1,lb,9.21,0
initial_fuel_mass_2_L1,lb,0,0
initial_fuel_mass_3_L1,lb,0,0
initial_water_temp_pot1_L1,ºC,,
initial_water_temp_pot2_L1,ºC,,
initial_water_temp_pot3_L1,ºC,,
initial_water_temp_pot4_L1,ºC,,
initial_pot1_mass_L1,lb,,
initial_pot2_mass_L1,kg,,
initial_pot3_mass_L1,kg,,
initial_pot4_mass_L1,kg,,
initial_char_mass_L1,lb,,
fire_start_material_L1,--,,
boil_time_L1,hh:mm:ss,,
weight_L1,,34,
weight_hp,,0,
weight_mp,,0,
weight_lp,,1040,
weight_L5,,,
weight_total,,1074,
final_air_temp,ºC,24,
final_RH,%,23.6,
final_pressure,in Hg,29.12,
final_wind_velocity,m/s,0,
end_time_L1,hh:mm:ss,20260108 12:14:00,
final_fuel_mass_1_L1,lb,0,0.2
final_fuel_mass_2_L1,lb,3.1,0.2
final_fuel_mass_3_L1,lb,0,0
max_water_temp_pot1_L1,ºC,,
max_water_temp_pot2_L1,ºC,,
max_water_temp_pot3_L1,ºC,,
max_water_temp_pot4_L1,ºC,,
final_pot1_mass_L1,lb,,
final_pot2_mass_L1,kg,,
final_pot3_mass_L1,kg,,
final_pot4_mass_L1,kg,,
final_char_mass_L1,lb,,
start_time_hp,hh:mm:ss,20260108 12:14:00,
initial_fuel_mass_1_hp,lb,7.163,0.2
initial_fuel_mass_2_hp,lb,3.1,0.2
initial_fuel_mass_3_hp,lb,0,0
initial_water_temp_pot1_hp,ºC,,
initial_water_temp_pot2_hp,ºC,,
initial_water_temp_pot3_hp,ºC,,
initial_water_temp_pot4_hp,ºC,,
initial_pot1_mass_hp,lb,,
initial_pot2_mass_hp,kg,,
initial_pot3_mass_hp,kg,,
initial_pot4_mass_hp,kg,,
initial_char_mass_hp,lb,,
fire_start_material_hp,--,,
boil_time_hp,hh:mm:ss,,
end_time_hp,hh:mm:ss,20260108 13:24:00,
final_fuel_mass_1_hp,lb,0,0.2
final_fuel_mass_2_hp,lb,1.8,0.2
final_fuel_mass_3_hp,lb,0,0
max_water_temp_pot1_hp,ºC,,
max_water_temp_pot2_hp,ºC,,
max_water_temp_pot3_hp,ºC,,
max_water_temp_pot4_hp,ºC,,
final_pot1_mass_hp,lb,,
final_pot2_mass_hp,kg,,
final_pot3_mass_hp,kg,,
final_pot4_mass_hp,kg,,
final_char_mass_hp,lb,,
start_time_mp,hh:mm:ss,,
initial_fuel_mass_1_mp,lb,0,0
initial_fuel_mass_2_mp,lb,0,0
initial_fuel_mass_3_mp,lb,0,0
initial_water_temp_pot1_mp,ºC,,
initial_water_temp_pot2_mp,ºC,,
initial_water_temp_pot3_mp,ºC,,
initial_water_temp_pot4_mp,ºC,,
initial_pot1_mass_mp,lb,,
initial_pot2_mass_mp,kg,,
initial_pot3_mass_mp,kg,,
initial_pot4_mass_mp,kg,,
initial_char_mass_mp,lb,,
fire_start_material_mp,--,,
boil_time_mp,hh:mm:ss,,
end_time_mp,hh:mm:ss,,
final_fuel_mass_1_mp,lb,0,0
final_fuel_mass_2_mp,lb,0,0
final_fuel_mass_3_mp,lb,0,0
max_water_temp_pot1_mp,ºC,,
max_water_temp_pot2_mp,ºC,,
max_water_temp_pot3_mp,ºC,,
max_water_temp_pot4_mp,ºC,,
final_pot1_mass_mp,lb,,
final_pot2_mass_mp,kg,,
final_pot3_mass_mp,kg,,
final_pot4_mass_mp,kg,,
final_char_mass_mp,lb,,
start_time_lp,hh:mm:ss,20260108 13:24:00,
initial_fuel_mass_1_lp,lb,25.534,0.2
initial_fuel_mass_2_lp,lb,1.8,0.2
initial_fuel_mass_3_lp,lb,0,0
initial_water_temp_pot1_lp,ºC,,
initial_water_temp_pot2_lp,ºC,,
initial_water_temp_pot3_lp,ºC,,
initial_water_temp_pot4_lp,ºC,,
initial_pot1_mass_lp,lb,,
initial_pot2_mass_lp,kg,,
initial_pot3_mass_lp,kg,,
initial_pot4_mass_lp,kg,,
initial_char_mass_lp,lb,,
fire_start_material_lp,--,,
boil_time_lp,hh:mm:ss,,
end_time_lp,hh:mm:ss,20260108 18:03:08,
final_fuel_mass_1_lp,lb,0,0.2
final_fuel_mass_2_lp,lb,0,0.2
final_fuel_mass_3_lp,lb,0,0
max_water_temp_pot1_lp,ºC,,
max_water_temp_pot2_lp,ºC,,
max_water_temp_pot3_lp,ºC,,
max_water_temp_pot4_lp,ºC,,
final_pot1_mass_lp,lb,,
final_pot2_mass_lp,kg,,
final_pot3_mass_lp,kg,,
final_pot4_mass_lp,kg,,
final_char_mass_lp,lb,,
start_time_L5,hh:mm:ss,,
initial_fuel_mass_1_L5,lb,,
initial_fuel_mass_2_L5,lb,,
initial_fuel_mass_3_L5,lb,,
initial_water_temp_pot1_L5,ºC,,
initial_water_temp_pot2_L5,ºC,,
initial_water_temp_pot3_L5,ºC,,
initial_water_temp_pot4_L5,ºC,,
initial_pot1_mass_L5,lb,,
initial_pot2_mass_L5,kg,,
initial_pot3_mass_L5,kg,,
initial_pot4_mass_L5,kg,,
initial_char_mass_L5,lb,,
fire_start_material_L5,--,,
boil_time_L5,hh:mm:ss,,
end_time_L5,hh:mm:ss,,
final_fuel_mass_1_L5,lb,,
final_fuel_mass_2_L5,lb,,
final_fuel_mass_3_L5,lb,,
max_water_temp_pot1_L5,ºC,,
max_water_temp_pot2_L5,ºC,,
max_water_temp_pot3_L5,ºC,,
max_water_temp_pot4_L5,ºC,,
final_pot1_mass_L5,lb,,
final_pot2_mass_L5,kg,,
final_pot3_mass_L5,kg,,
final_pot4_mass_L5,kg,,
final_char_mass_L5,lb,,
"""


def _read_csv_with_fallback(filepath):
    """Read a CSV file as DictReader rows with automatic encoding detection and fallback."""
    encodings_to_try = []
    try:
        import chardet
        with open(filepath, 'rb') as f:
            raw = f.read(10000)
        detected = chardet.detect(raw).get('encoding')
        if detected:
            encodings_to_try.append(detected)
    except Exception:
        pass
    for e in ['utf-8-sig', 'utf-8', 'cp1252', 'latin1', 'iso-8859-1']:
        if e not in encodings_to_try:
            encodings_to_try.append(e)

    for enc in encodings_to_try:
        try:
            with open(filepath, 'r', encoding=enc, newline='') as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames) if reader.fieldnames else []
                rows = list(reader)
            return enc, fieldnames, rows
        except (UnicodeDecodeError, LookupError):
            continue

    with open(filepath, 'r', encoding='latin1', errors='replace', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        rows = list(reader)
    return 'latin1', fieldnames, rows


def ensure_l3_energy_template(folder_path, logpath=None):
    """Ensure L3_EnergyInputs.csv exists in the L3 root directory; create default if missing."""
    template_path = os.path.join(folder_path, 'L3_EnergyInputs.csv')
    if not os.path.isfile(template_path):
        with open(template_path, 'w', encoding='utf-8', newline='') as f:
            f.write(DEFAULT_L3_ENERGY_INPUTS_CSV)
        msg = f"Created default L3 energy uncertainty template: {template_path}"
        print(msg)
        if logpath:
            io.write_logfile(logpath, [msg])
    return template_path


def load_l3_uncertainty_template(template_path):
    """Load uncertainty values keyed by variable name from an L3 template CSV."""
    _, fieldnames, template_rows = _read_csv_with_fallback(template_path)
    key_col = 'variable_name'
    if fieldnames and 'variable_name' not in fieldnames and 'variable' in fieldnames:
        key_col = 'variable'

    template_uncertainties = {}
    for trow in template_rows:
        vname = (trow.get(key_col) or '').strip()
        if vname:
            template_uncertainties[vname] = (trow.get('uncertainty') or '').strip()
    return template_uncertainties


def update_test_energy_uncertainty(energy_path, template_uncertainties, logpath=None):
    """
    Update ONLY the 'uncertainty' column of an individual test's <testname>_EnergyInputs.csv
    from the L3_EnergyInputs.csv template dictionary, preserving each test's own 'value' and 'units'.
    """
    if not os.path.isfile(energy_path):
        raise FileNotFoundError(f"EnergyInputs.csv not found: {energy_path}")

    enc, fieldnames, existing_rows = _read_csv_with_fallback(energy_path)
    if not fieldnames:
        fieldnames = ['variable_name', 'units', 'value', 'uncertainty']
    elif 'uncertainty' not in fieldnames:
        fieldnames.append('uncertainty')

    key_col = 'variable_name' if 'variable_name' in fieldnames else fieldnames[0]

    updated_count = 0
    for row in existing_rows:
        vname = (row.get(key_col) or '').strip()
        if vname in template_uncertainties:
            row['uncertainty'] = template_uncertainties[vname]
            updated_count += 1

    write_enc = enc or 'utf-8'
    with open(energy_path, 'w', encoding=write_enc, errors='replace', newline='') as ef:
        ewriter = csv.DictWriter(ef, fieldnames=fieldnames)
        ewriter.writeheader()
        ewriter.writerows(existing_rows)

    msg = f"Updated uncertainty for {updated_count} variable(s) in {energy_path} from L3_EnergyInputs.csv"
    print(f"  {msg}")
    if logpath:
        io.write_logfile(logpath, [msg])
    return updated_count

