import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import os

#function builds a data entry sheet, checks in sheet has previously been created, autopopulates if it has, then prints to csv

# Dictionary to store default units for each variable
default_units = {
    'air_temp': '°C',
    'pressure': 'kPa',
    'RH': '%',
    'wind_velocity': 'm/s',
    'fuel_type': '',
    'fuel_source': '',
    'fuel_dimensions': 'cm x cm',
    'fuel_higher_heating_value': 'kJ/kg',
    'fuel_mc': '%',
    'fuel_Cfrac_db': 'g/g',
}

# List of variables
variables = []

#variables sorted into categories for easy organization
weather = ['air_temp', 'pressure', 'RH', 'wind_velocity']
weathernames = []

for name in weather:
    newname = 'initial_' + name
    weathernames.append(newname)
    default_units[newname] = default_units[name]

for name in weather:
    newname = 'final_' + name
    weathernames.append(newname)
    default_units[newname] = default_units[name]

fuel = ['fuel_type', 'fuel_source', 'fuel_dimensions', 'fuel_mc', 'fuel_higher_heating_value', 'fuel_Cfrac_db']


for name in fuel:
    variables.append(name)
for name in weathernames:
    variables.append(name)


def save_to_csv(entries, units, folder_path):
    # Generate the file path
    file_name = f"{os.path.basename(folder_path)}_EnergyInputs.csv"
    file_path = os.path.join(folder_path, file_name)
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Check if the file is empty, then write the header
        if csvfile.tell() == 0:
            writer.writerow(['variable_name', 'units', 'value'])

        # Write the data
        for variable in newvariables:
            value = entries[variable]
            unit = units[variable]
            writer.writerow([variable, unit, value])

    messagebox.showinfo("Success", f"Data saved to CSV file: {file_path}")

entries = {}
units = {}

newvariables = []
def on_okay():
    # Dictionary to store entered values

    for name in weathernames:
        newvariables.append(name)
    for name in fuelnames:
        newvariables.append(name)

    floaterrornames = []
    blankerrornames = []

    for name in weathernames:
        units[name] = unit_comboboxes[name].get()
        if 'initial' in name:
            try:
                entries[name] = float(entry_widgets[name].get())
            except:
                if entry_widgets[name].get() == '' and 'wind_velocity' not in name:
                    blankerrornames.append(name)
                elif 'wind_velocity' not in name:
                    floaterrornames.append(name)
                else:
                    entries[name] = entry_widgets[name].get()
        if 'final' in name:
            try:
                entries[name] = float(entry_widgets[name].get())
            except:
                if entry_widgets[name].get() == '':
                    entries[name] = entry_widgets[name].get()
                else:
                    floaterrornames.append(name)

    for name in fuelnames:
        units[name] = unit_comboboxes[name].get()
        if 'type' not in name or 'source' not in name or 'dimensions' not in name:
            try:
                entries[name] = float(entry_widgets[name].get())
            except ValueError:
                if entry_widgets[name].get() == '' and '_1' in name:
                    blankerrornames.append(name)
                elif '_1' in name:
                    floaterrornames.append(name)
                else:
                    entries[name] = entry_widgets[name].get()
        else:
            entries[name] = entry_widgets[name].get()

    # Get the selected folder path
    #folder_path = filedialog.askdirectory()

    # Get the selected folder path
    folder_path_str = folder_path_var.get()

    if len(floaterrornames) != 0:
        floatmessage = 'The following variables require a numerical input:'
        for name in floaterrornames:
            floatmessage = floatmessage + ' ' + name
    elif len(blankerrornames) !=0:
        blankmessage = 'The following variables were left blank but require an input:'
        for name in blankerrornames:
            blankmessage = blankmessage + ' ' + name

    try:
        messagebox.showerror("Error",
                             floatmessage, blankmessage)
        return
    except:
        try:
            messagebox.showerror("Error",
                                 floatmessage)
            return
        except:
            try:
                messagebox.showerror("Error",
                                     blankmessage)
                return
            except:
                # Save data to CSV
                save_to_csv(entries, units, folder_path_str)
                root.destroy()  # Close the window after saving data


# Create the main window
root = tk.Tk()
root.title("Weather and Fuel Data Entry")

# Create and pack frames
frame_left = tk.Frame(root)
frame_left.pack(side=tk.LEFT, padx=10, pady=10)

frame_right = tk.Frame(root)
frame_right.pack(side=tk.RIGHT, padx=10, pady=10)

# File Path Entry
tk.Label(frame_left, text="Select Folder:").grid(row=0, column=0)
folder_path_var = tk.StringVar()
folder_path = tk.Entry(frame_left, textvariable=folder_path_var)
folder_path.grid(row=0, column=1)



def read_energy_inputs(folder_path):
    # Generate the file path for _EnergyInputs.csv
    file_name = f"{os.path.basename(folder_path)}_EnergyInputs.csv"
    file_path = os.path.join(folder_path, file_name)

    # Check if the file exists
    if os.path.exists(file_path):
        entries = {}
        with open(file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Read the header

            for row in reader:
                variable = row[0]
                unit = row[1] if len(row) > 1 else ''
                value = row[2] if len(row) > 2 else ''
                entries[variable] = value
                units[variable] = unit

        return entries
    else:
        return None


def browse_folder():
    folder_path = filedialog.askdirectory()
    folder_path_var.set(folder_path)

    # Check if _EnergyInputs.csv file exists
    energy_inputs = read_energy_inputs(folder_path)

    if energy_inputs is not None:
        # Populate variables with entries from the CSV
        for variable in variables:
            try:
                entry_widgets[variable].delete(0, tk.END)  # Clear existing content
                entry_widgets[variable].insert(0, energy_inputs.get(variable, ''))
            except:
                try:
                    test = energy_inputs(variable)
                    if fuel in variable:
                        newvariable = variable + '_1'
                        entry_widgets[newvariable].delete(0, tk.END)  # Clear existing content
                        entry_widgets[newvariable].insert(0, energy_inputs.get(variable, ''))
                        variables.append(newvariable)
                except:
                    c = 1
                    while c <= num_fuels:
                        newvariable = variable + '_' + str(c)
                        entry_widgets[newvariable].delete(0, tk.END)  # Clear existing content
                        entry_widgets[newvariable].insert(0, energy_inputs.get(variable, ''))
                        variables.append(newvariable)
                        c += 1

        # Additional variables, units, and values
        additional_entries = {var: energy_inputs.get(var, '') for var in energy_inputs.keys() if var not in variables}
        for i, (variable, value) in enumerate(additional_entries.items(), start=len(variables)+1):
            tk.Label(frame_left, text=f"{variable.capitalize().replace('_', ' ')}:").grid(row=i, column=0)

            unit_comboboxes[variable] = ttk.Combobox(frame_left, values=units[variable])
            unit_comboboxes[variable].set(units[variable])
            unit_comboboxes[variable].grid(row=i, column=1)

            entry_widgets[variable] = tk.Entry(frame_left)
            entry_widgets[variable].grid(row=i, column=3)
            entry_widgets[variable].insert(0, value)



browse_button = tk.Button(frame_left, text="Browse", command=browse_folder)
browse_button.grid(row=0, column=2)

# Create a canvas with a vertical scrollbar
canvas = tk.Canvas(frame_left, height=500)
scrollbar = tk.Scrollbar(frame_left, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

# Create dictionaries to store entry widgets and unit comboboxes
entry_widgets = {}
unit_comboboxes = {}

rowcount = 1

# Loop through variables to create labels, entry widgets, and unit comboboxes
for i, variable in enumerate(weathernames, start=1):
    tk.Label(frame_left, text=f"{variable.capitalize().replace('_', ' ')}:").grid(row=i, column=0)

    unit_comboboxes[variable] = ttk.Combobox(frame_left, values=default_units[variable])
    unit_comboboxes[variable].set(default_units[variable])
    unit_comboboxes[variable].grid(row=i, column=1)

    # Create entry widget
    entry_widgets[variable] = tk.Entry(frame_left)
    entry_widgets[variable].grid(row=i, column= 3)

    rowcount += 1

# Ask user for the number of fuels
num_fuels = int(input("Enter the number of fuels: "))

# Create fuel variables and boxes
fuelnames = []
c = 1
fuelrows = 0
while c <= num_fuels:
    for i, name in enumerate(fuel, start=1):
        newname = name + '_' + str(c)

        tk.Label(frame_right, text=f"{newname.capitalize().replace('_', ' ')}:").grid(row=i+fuelrows, column=0)
        unit_comboboxes[newname] = ttk.Combobox(frame_right, values=default_units[name])
        unit_comboboxes[newname].set(default_units[name])
        unit_comboboxes[newname].grid(row=i + fuelrows, column=1)
        entry_widgets[newname] = tk.Entry(frame_right)
        entry_widgets[newname].grid(row=i+fuelrows, column=3)
        fuelnames.append(newname)

    c += 1
    fuelrows = fuelrows + len(fuel)


# OK button
ok_button = tk.Button(frame_left, text="OK", command=on_okay)
ok_button.grid(row=rowcount + 1, column=0, columnspan=3, pady=10)

# Run the application
root.mainloop()

