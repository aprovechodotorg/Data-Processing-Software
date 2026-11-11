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


DEFAULT_L3_GRAV_INPUTS_CSV = """variable,units,value,uncertainty
filterID_SB4014_A_L1,text,4963,
taremass_SB4014_A_L1,g,0.13323,0.00005
grossmass_SB4014_A_L1,g,0.13511,0.00005
start_time_SB4014_A_L1,yyyymmdd hh:mm:ss,20260108 11:48:00,
end_time_SB4014_A_L1,yyyymmdd hh:mm:ss,20260108 12:14:00,
filterID_SB4014_A_hp,text,4964,
taremass_SB4014_A_hp,g,0.13382,0.00005
grossmass_SB4014_A_hp,g,0.13474,0.00005
start_time_SB4014_A_hp,yyyymmdd hh:mm:ss,20260108 12:14:00,
end_time_SB4014_A_hp,yyyymmdd hh:mm:ss,20260108 13:24:00,
filterID_SB4014_A_mp,text,,
taremass_SB4014_A_mp,g,,0.00005
grossmass_SB4014_A_mp,g,,0.00005
start_time_SB4014_A_mp,yyyymmdd hh:mm:ss,,
end_time_SB4014_A_mp,yyyymmdd hh:mm:ss,,
filterID_SB4014_A_lp,text,4965,
taremass_SB4014_A_lp,g,0.13472,0.00005
grossmass_SB4014_A_lp,g,0.13711,0.00005
start_time_SB4014_A_lp,yyyymmdd hh:mm:ss,20260108 13:24:00,
end_time_SB4014_A_lp,yyyymmdd hh:mm:ss,20260108 18:03:08,
filterID_SB4014_A_L5,text,,
taremass_SB4014_A_L5,g,,0.00005
grossmass_SB4014_A_L5,g,,0.00005
start_time_SB4014_A_L5,yyyymmdd hh:mm:ss,,
end_time_SB4014_A_L5,yyyymmdd hh:mm:ss,,
GravFlo1,lpm,16.7,0.167
GravFlo2,lpm,16.7,0.167
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


def ensure_l3_grav_template(folder_path, logpath=None):
    """Ensure L3_GravInputs.csv exists in the L3 root directory; create default if missing."""
    template_path = os.path.join(folder_path, 'L3_GravInputs.csv')
    if not os.path.isfile(template_path):
        with open(template_path, 'w', encoding='utf-8', newline='') as f:
            f.write(DEFAULT_L3_GRAV_INPUTS_CSV)
        msg = f"Created default L3 grav uncertainty template: {template_path}"
        print(msg)
        if logpath:
            io.write_logfile(logpath, [msg])
    return template_path


def update_test_grav_uncertainty(grav_path, template_uncertainties, logpath=None):
    """
    Update ONLY the 'uncertainty' column of an individual test's <testname>_GravInputs.csv
    from the L3_GravInputs.csv template dictionary, preserving each test's own 'value' and 'units'.
    Also deduplicates duplicate rows if previously written by LEMS_GravCalcs.
    """
    if not os.path.isfile(grav_path):
        raise FileNotFoundError(f"GravInputs.csv not found: {grav_path}")

    enc, fieldnames, existing_rows = _read_csv_with_fallback(grav_path)
    if not fieldnames:
        fieldnames = ['variable', 'units', 'value', 'uncertainty']
    elif 'uncertainty' not in fieldnames:
        fieldnames.append('uncertainty')

    key_col = 'variable' if 'variable' in fieldnames else ('variable_name' if 'variable_name' in fieldnames else fieldnames[0])

    # Pre-parse template entries by (prefix, phase) for channel-agnostic fallback
    phase_prefix_map = {}
    phases = {'L1', 'hp', 'mp', 'lp', 'L5'}
    prefixes = ['start_time', 'end_time', 'taremass', 'grossmass', 'filterID']
    for t_name, t_unc in template_uncertainties.items():
        if t_unc != '':
            for pfx in prefixes:
                if t_name.startswith(pfx + '_'):
                    parts = t_name.split('_')
                    if parts[-1] in phases:
                        phase_prefix_map[(pfx, parts[-1])] = t_unc
                    break

    # Deduplicate existing rows by variable name (preserving first occurrence)
    seen_vars = set()
    dedup_rows = []
    updated_count = 0

    for row in existing_rows:
        vname = (row.get(key_col) or '').strip()
        if not vname or vname in seen_vars:
            continue
        seen_vars.add(vname)

        # Resolve uncertainty: 1) exact match, 2) prefix+phase match, 3) GravFlo fallback
        resolved_unc = None
        if vname in template_uncertainties and template_uncertainties[vname] != '':
            resolved_unc = template_uncertainties[vname]
        else:
            for pfx in prefixes:
                if vname.startswith(pfx + '_'):
                    parts = vname.split('_')
                    if parts[-1] in phases:
                        resolved_unc = phase_prefix_map.get((pfx, parts[-1]))
                    break
            if resolved_unc is None and vname == 'GravFlo2':
                resolved_unc = template_uncertainties.get('GravFlo1')

        if resolved_unc is not None:
            row['uncertainty'] = resolved_unc
            updated_count += 1

        dedup_rows.append(row)

    write_enc = enc or 'utf-8'
    with open(grav_path, 'w', encoding=write_enc, errors='replace', newline='') as gf:
        gwriter = csv.DictWriter(gf, fieldnames=fieldnames)
        gwriter.writeheader()
        gwriter.writerows(dedup_rows)

    msg = f"Updated uncertainty for {updated_count} variable(s) in {grav_path} from L3_GravInputs.csv"
    print(f"  {msg}")
    if logpath:
        io.write_logfile(logpath, [msg])
    return updated_count


# ==============================================================================
# L3 Emission Inputs Uncertainty
# ==============================================================================

DEFAULT_L3_EMISSION_INPUTS_CSV = """variable,units,value,uncertainty
Velocity temperature probe,,TC2,
flowgrid_cal_factor,,1,0.02
factory_flow_cal,,62.8,0
duct_diameter,inches,6,0
MSC_default,m^2/g,3,0
static_pressure_dil_tunnel,inH2O,0.75,0.25
Cp,,1.0,0
velocity_traverse,,0.975,0
chimney_dia,in,6,0
re_dia_1,in,,
re_temp_1,,,
re_dia_2,in,,
re_temp_2,,,
"""


def ensure_l3_emission_template(folder_path, logpath=None):
    """Ensure L3_EmissionInputs.csv exists in the L3 root directory; create default if missing."""
    template_path = os.path.join(folder_path, 'L3_EmissionInputs.csv')
    if not os.path.isfile(template_path):
        with open(template_path, 'w', encoding='utf-8', newline='') as f:
            f.write(DEFAULT_L3_EMISSION_INPUTS_CSV)
        msg = f"Created default L3 emission uncertainty template: {template_path}"
        print(msg)
        if logpath:
            io.write_logfile(logpath, [msg])
    return template_path


def update_test_emission_uncertainty(emission_path, template_uncertainties, logpath=None, sensor_version_path=None):
    """
    Update ONLY the 'uncertainty' column of an individual test's <testname>_EmissionInputs.csv
    from the L3_EmissionInputs.csv template dictionary, preserving each test's own 'value' and 'units'.
    If the file does not exist, initialize it first with defaults appropriate for the sensorbox.
    """
    if not os.path.isfile(emission_path):
        # Initialize default EmissionInputs for this test
        firmware_version = ''
        if sensor_version_path and os.path.isfile(sensor_version_path):
            try:
                [vnames, _, vval, _, _] = io.load_constant_inputs(sensor_version_path)
                firmware_version = str(vval.get('SB', ''))
            except Exception:
                pass

        emnames = ['variable']
        emunits = {'variable': 'units'}
        emval = {'variable': 'value'}
        emunc = {'variable': 'uncertainty'}
        emuval = {}

        if any(pv in firmware_version.lower() for pv in ['possum2', 'possum 2']):
            items = [
                ('Cp', '', 1.0, 0),
                ('velocity_traverse', '', 0.975, 0),
                ('flowgrid_cal_factor', '', 1.0, 0.02),
                ('factory_flow_cal', '', 62.8, 0),
                ('duct_diameter', 'inches', 12.0, 0),
                ('MSC_default', 'm^2/g', 3, 0),
                ('static_pressure_dil_tunnel', 'inH2O', 0.75, 0.25),
                ('chimney_dia', 'in', 6, 0),
                ('Velocity temperature probe', '', 'TCnoz', ''),
                ('re_dia_1', 'in', '', ''),
                ('re_temp_1', '', '', ''),
                ('re_dia_2', 'in', '', ''),
                ('re_temp_2', '', '', ''),
            ]
        else:
            items = [
                ('Velocity temperature probe', '', 'TC2', ''),
                ('flowgrid_cal_factor', '', 1.0, 0.02),
                ('factory_flow_cal', '', 15.3, 0),
                ('duct_diameter', 'inches', 6.0, 0),
                ('MSC_default', 'm^2/g', 3, 0),
                ('static_pressure_dil_tunnel', 'inH2O', 0.75, 0.25),
            ]
        for vname, u, val, un in items:
            emnames.append(vname)
            emunits[vname] = u
            emval[vname] = val
            emunc[vname] = un

        io.write_constant_outputs(emission_path, emnames, emunits, emval, emunc, emuval)
        init_msg = f"Initialized missing emission inputs file: {emission_path}"
        print(f"  {init_msg}")
        if logpath:
            io.write_logfile(logpath, [init_msg])

    enc, fieldnames, existing_rows = _read_csv_with_fallback(emission_path)
    if not fieldnames:
        fieldnames = ['variable', 'units', 'value', 'uncertainty']
    elif 'uncertainty' not in fieldnames:
        fieldnames.append('uncertainty')

    key_col = 'variable' if 'variable' in fieldnames else ('variable_name' if 'variable_name' in fieldnames else fieldnames[0])

    updated_count = 0
    for row in existing_rows:
        vname = (row.get(key_col) or '').strip()
        if vname in template_uncertainties:
            row['uncertainty'] = template_uncertainties[vname]
            updated_count += 1

    write_enc = enc or 'utf-8'
    with open(emission_path, 'w', encoding=write_enc, errors='replace', newline='') as ef:
        ewriter = csv.DictWriter(ef, fieldnames=fieldnames)
        ewriter.writeheader()
        ewriter.writerows(existing_rows)

    msg = f"Updated uncertainty for {updated_count} variable(s) in {emission_path} from L3_EmissionInputs.csv"
    print(f"  {msg}")
    if logpath:
        io.write_logfile(logpath, [msg])
    return updated_count


# ==============================================================================
# L3 UCInputs (Sensor / Background) Uncertainty
# ==============================================================================

DEFAULT_L3_UC_INPUTS_CSV = """time,seconds,ID,CO,CO2,PM,Flow,FLUEtemp,H2Otemp,RH,CO_ECtemp
#units:,s,4014,ppm,ppm,Mm^-1,mmH2O,degC,degC,%,degC
absolute uncertainty,0,0,1,1,0,0,0.5,0.5,0,0
relative uncertainty,0,0,0.02,0.02,0,0.01,0,0,0,0
"""

UC_CHANNEL_ALIASES = {
    'co2v': 'CO2',
    'co2hi': 'CO2',
    'cohi': 'CO',
    'cobkg': 'CO',
    'co2bkg': 'CO2',
    'fluetemp': 'FLUEtemp',
    'flue temp': 'FLUEtemp',
    'flue t': 'FLUEtemp',
    'co_ectemp': 'COtemp',
    'cotemp': 'CO_ECtemp',
    'temp': 'COtemp',
    'gas t': 'COtemp',
    'pitot': 'Flow',
    'flue flow': 'Flow',
    'flow': 'Flow',
    'pamb': 'AmbPres',
    'tc h2o': 'H2Otemp',
    'tc': 'H2Otemp',
    'tc pitot': 'TC1',
    'flow pito': 'dP2',
}


def _read_raw_csv_rows(filepath):
    """Read all rows of a CSV file as raw string lists with automatic encoding detection."""
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
                reader = csv.reader(f)
                rows = list(reader)
            return enc, rows
        except (UnicodeDecodeError, LookupError):
            continue

    with open(filepath, 'r', encoding='latin1', errors='replace', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
    return 'latin1', rows


def _get_sensorbox_version(sensor_version_path):
    """Extract sensorbox firmware version string if available."""
    if not sensor_version_path or not os.path.isfile(sensor_version_path):
        return ''
    try:
        [vnames, _, vval, _, _] = io.load_constant_inputs(sensor_version_path)
        return str(vval.get('SB', '')).strip()
    except Exception:
        return ''


def ensure_l3_uc_template(folder_path, list_raw_shifted_paths=None, logpath=None):
    """
    Ensure L3_UCInputs.csv exists in the L3 root directory.
    If missing, write DEFAULT_L3_UC_INPUTS_CSV.
    If existing, inspect all channels across list_raw_shifted_paths (or standard channels),
    and automatically expand the user's L3_UCInputs.csv in the root folder with any missing
    channels (preserving existing channel values/uncertainties).
    """
    template_path = os.path.join(folder_path, 'L3_UCInputs.csv')
    if not os.path.isfile(template_path):
        with open(template_path, 'w', encoding='utf-8', newline='') as f:
            f.write(DEFAULT_L3_UC_INPUTS_CSV)
        msg = f"Created default L3 UC uncertainty template: {template_path}"
        print(msg)
        if logpath:
            io.write_logfile(logpath, [msg])

    # Check for channel expansion
    enc, rows = _read_raw_csv_rows(template_path)
    if len(rows) < 4:
        return template_path

    existing_channels = [c.strip() for c in rows[0]]
    existing_channels_lower = {c.lower(): idx for idx, c in enumerate(existing_channels)}

    # Discover candidate channels from raw shifted paths
    discovered_channels = []  # list of (channel_name, unit)
    if list_raw_shifted_paths:
        for rpath in list_raw_shifted_paths:
            if rpath and os.path.isfile(rpath):
                try:
                    _, rrows = _read_raw_csv_rows(rpath)
                    if len(rrows) >= 2:
                        rnames = [c.strip() for c in rrows[0]]
                        runits = [c.strip() for c in rrows[1]]
                        for i, ch in enumerate(rnames):
                            if not ch:
                                continue
                            unit = runits[i] if i < len(runits) else ''
                            if ch.lower() not in existing_channels_lower:
                                if ch.lower() not in [dc[0].lower() for dc in discovered_channels]:
                                    discovered_channels.append((ch, unit))
                except Exception:
                    pass

    # If any new channels are discovered, append them to the user's template
    if discovered_channels:
        # Load existing uncertainties to resolve alias defaults if applicable
        temp_dict = load_l3_uc_template(template_path)
        added_names = []
        for ch, unit in discovered_channels:
            # Determine default uncertainty
            alias = UC_CHANNEL_ALIASES.get(ch.lower(), '')
            if alias and alias in temp_dict:
                def_abs, def_rel = temp_dict[alias]
            elif ch.lower().startswith('tc'):
                def_abs, def_rel = ('0.5', '0')
            elif ch.lower().startswith('co2'):
                def_abs, def_rel = ('1', '0.02')
            elif ch.lower().startswith('co'):
                def_abs, def_rel = ('1', '0.02')
            else:
                def_abs, def_rel = ('0', '0')

            rows[0].append(ch)
            rows[1].append(unit)
            rows[2].append(str(def_abs))
            rows[3].append(str(def_rel))
            added_names.append(ch)

        write_enc = enc or 'utf-8'
        with open(template_path, 'w', encoding=write_enc, errors='replace', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        msg = f"Auto-expanded {template_path} with {len(added_names)} missing channel(s): {', '.join(added_names)}"
        print(msg)
        if logpath:
            io.write_logfile(logpath, [msg])

    return template_path


def load_l3_uc_template(template_path):
    """
    Load uncertainty values keyed by channel name from a 4-row horizontal UCInputs template CSV.
    Returns: {channel_name: (abs_unc_str, rel_unc_str)}
    """
    _, rows = _read_raw_csv_rows(template_path)
    if len(rows) < 4:
        return {}

    names = [c.strip() for c in rows[0]]
    abs_row = [c.strip() for c in rows[2]]
    rel_row = [c.strip() for c in rows[3]]

    template_uc = {}
    for i, name in enumerate(names):
        if not name:
            continue
        abs_val = abs_row[i] if i < len(abs_row) else '0'
        rel_val = rel_row[i] if i < len(rel_row) else '0'
        template_uc[name] = (abs_val, rel_val)
    return template_uc


def update_test_uc_uncertainty(uc_path, raw_shifted_path, template_uc, logpath=None, folder_path=None, sensor_version_path=None):
    """
    Update ONLY the absolute and relative uncertainty rows of an individual test's <testname>_UCInputs.csv
    from the L3_UCInputs.csv template (or sensorbox-specific L3_UCInputs_<SB>.csv if present in folder_path).
    Preserves each test's exact channel list, column order, and #units: row.
    If <testname>_UCInputs.csv does not exist, initialize it first from <testname>_RawData_Shifted.csv.
    """
    # 1. Resolve effective template (check for sensorbox-specific override)
    effective_template = template_uc
    if folder_path:
        sb_ver = _get_sensorbox_version(sensor_version_path)
        if sb_ver:
            # Check candidate sensorbox names (e.g. SB3002, 3002, Possum2, etc.)
            cand_files = [f"L3_UCInputs_{sb_ver}.csv"]
            for part in sb_ver.replace('.', '_').replace('-', '_').split('_'):
                if part and part.lower() not in ('sb', 'lems'):
                    cand_files.append(f"L3_UCInputs_{part}.csv")
                    cand_files.append(f"L3_UCInputs_SB{part}.csv")
            for cfile in cand_files:
                sb_path = os.path.join(folder_path, cfile)
                if os.path.isfile(sb_path):
                    sb_uc = load_l3_uc_template(sb_path)
                    if sb_uc:
                        effective_template = sb_uc
                        line = f"Using sensorbox-specific UC template {sb_path} for {os.path.basename(uc_path)}"
                        print(f"  {line}")
                        if logpath:
                            io.write_logfile(logpath, [line])
                        break

    # 2. Initialize <testname>_UCInputs.csv if missing
    if not os.path.isfile(uc_path):
        if not os.path.isfile(raw_shifted_path):
            raise FileNotFoundError(f"Neither UCInputs nor RawData_Shifted found for test: {uc_path}")
        # Initialize from RawData_Shifted
        _, rrows = _read_raw_csv_rows(raw_shifted_path)
        if len(rrows) < 2:
            raise ValueError(f"Invalid RawData_Shifted file (less than 2 rows): {raw_shifted_path}")
        names = rrows[0]
        units = rrows[1]
        abs_row = ['absolute uncertainty'] + ['0'] * (len(names) - 1)
        rel_row = ['relative uncertainty'] + ['0'] * (len(names) - 1)
        rows_to_write = [names, units, abs_row, rel_row]
        with open(uc_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows_to_write)
        init_msg = f"Initialized missing UCInputs file from raw shifted data: {uc_path}"
        print(f"  {init_msg}")
        if logpath:
            io.write_logfile(logpath, [init_msg])

    # 3. Read existing UCInputs.csv
    enc, rows = _read_raw_csv_rows(uc_path)
    if len(rows) < 4:
        raise ValueError(f"UCInputs file has invalid format (fewer than 4 rows): {uc_path}")

    names = rows[0]
    # Ensure rows 2 and 3 have at least as many columns as names
    while len(rows[2]) < len(names):
        rows[2].append('0')
    while len(rows[3]) < len(names):
        rows[3].append('0')

    updated_count = 0
    for i, name in enumerate(names):
        clean_name = name.strip()
        if not clean_name or clean_name.lower() in ('time', 'seconds', 'id'):
            continue

        # Look up uncertainty: 1) exact match, 2) alias match
        match = None
        if clean_name in effective_template:
            match = effective_template[clean_name]
        elif clean_name.lower() in [k.lower() for k in effective_template]:
            for k, v in effective_template.items():
                if k.lower() == clean_name.lower():
                    match = v
                    break
        else:
            alias = UC_CHANNEL_ALIASES.get(clean_name.lower())
            if alias and alias in effective_template:
                match = effective_template[alias]

        if match is not None:
            abs_u, rel_u = match
            rows[2][i] = str(abs_u).strip()
            rows[3][i] = str(rel_u).strip()
            updated_count += 1

    write_enc = enc or 'utf-8'
    with open(uc_path, 'w', encoding=write_enc, errors='replace', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    msg = f"Updated uncertainty for {updated_count} channel(s) in {uc_path} from UC template"
    print(f"  {msg}")
    if logpath:
        io.write_logfile(logpath, [msg])
    return updated_count



