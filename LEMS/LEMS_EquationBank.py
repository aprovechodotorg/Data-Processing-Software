# This file will be for equation bank storage. It will focus on the equationst that are displayed when the uesr hovers over the "i" icon.



def equation_bank(key):

# Emissions and Energy Calculations

    if 'PM_useful_eng_deliver' in key:
        return ("Calculated as:", r"\\frac{\\mathrm{PM\\ total\\ mass}}{\\mathrm{useful\\ energy\\ delivered}} \\times 1000 \\times 1000")

    elif 'CO_useful_eng_deliver' in key:
            return ("Calculated as:",
            r"\\frac{\\mathrm{CO\\ total\\ mass}}{\\mathrm{useful\\ energy\\ delivered}} \\times 1000")

    elif 'CO2_useful_eng_deliver' in key:

        return ( "Calculated as:", r"\\frac{\\mathrm{CO_{2}\\ total\\ mass}}{\\mathrm{useful\\ energy\\ delivered}} \\times 1000")


# Mass Calculations

    if 'COmass' in key:
        return ("Calculated as:", r"\frac{\frac{\frac{CO \times MW_{CO} \times \mathrm{P\ duct}}{FLUEtemp + 273.15}}{1000000}}{R}")
    if 'CO2mass' in key:
        return ("Calculated as:", r"\frac{\frac{\frac{CO2 \times MW_{CO2} \times \mathrm{P\ duct}}{FLUEtemp + 273.15}}{1000000}}{R}")
    if 'PMmass' in key:
        return ("Calculated as:", r"\frac{\frac{PM}{MSC}}{1000000}")
    if 'Cmass' in key:
        return ("Calculated as:", r"\frac{COmass \times MW_{C}}{MW_{CO}} + \frac{CO2mass \times MW_{C}}{MW_{CO2}}")


# Energy and Fuel Calculations

    if 'CO_fuel_dry_mass' in key:
        return ("Calculated as:", r"\frac{\mathrm{CO\ total\ mass}}{\mathrm{fuel\ dry\ mass}}")
    if 'CO2_fuel_dry_mass' in key:
        return ("Calculated as:", r"\frac{\mathrm{CO2\ total\ mass}}{\mathrm{fuel\ dry\ mass}}")
    if 'PM_fuel_dry_mass' in key:
        return ("Calculated as:", r"\frac{\mathrm{PM\ total\ mass}}{\mathrm{fuel\ dry\ mass}}")

    if 'CO_fuel_energy_w_char' in key:
        return ("Calculated as:",
                r"\frac{\mathrm{CO\ total\ mass}}{\mathrm{fuel\ mass} \times \mathrm{fuel\ heating\ value}}  - \mathrm{char\ mass} \times \mathrm{char\ heating\ value} \times 1000")
    if 'CO2_fuel_energy_w_char' in key:
        return ("Calculated as:",
                r"\frac{\mathrm{CO2\ total\ mass}}{\mathrm{fuel\ mass} \times \mathrm{fuel\ heating\ value}}  - \mathrm{char\ mass} \times \mathrm{char\ heating\ value} \times 1000")
    if 'PM_fuel_energy_w_char' in key:
        return ("Calculated as:",
                r"\frac{\mathrm{PM\ total\ mass}}{\mathrm{fuel\ mass} \times \mathrm{fuel\ heating\ value}}  - \mathrm{char\ mass} \times \mathrm{char\ heating\ value} \times 1000")

    if 'CO_fuel_energy' in key:
        return ("Calculated as:",
                r"\frac{\frac{\mathrm{CO\ total\ mass}}{\mathrm{fuel\ mass}}}{\mathrm{fuel\ heating\ value}} \times 1000")
    if 'CO2_fuel_energy' in key:
        return ("Calculated as:",
                r"\frac{\frac{\mathrm{CO2\ total\ mass}}{\mathrm{fuel\ mass}}}{\mathrm{fuel\ heating\ value}} \times 1000")
    if 'PM_fuel_energy' in key:
        return ("Calculated as:",
                r"\frac{\frac{\mathrm{PM\ total\ mass}}{\mathrm{fuel\ mass}}}{\mathrm{fuel\ heating\ value}} \times 1000")

# Emissions Factors (value that shows how a specific activity releases a certain quantity of pollution)

    if 'CO_EF' in key:
        return ("Calculated as:", r"\frac{\mathrm{CO\ mass\ time}}{\frac{\mathrm{C\ mass\ time}}{1000}}")
    if 'CO2_EF' in key:
        return ("Calculated as:", r"\frac{\mathrm{CO2\ mass\ time}}{\frac{\mathrm{C\ mass\ time}}{1000}}")
    if 'PM_EF' in key:
        return ("Calculated as:", r"\frac{\frac{\mathrm{PM\ mass\ time}}{1000}}{\frac{\mathrm{C\ mass\ time}}{1000}}")



# Carbon Calculations

    if 'firepower_carbon' in key:
        return ("Calculated as:", r"\frac{\mathrm{C\ ER}}{\mathrm{fuel\ Cfrac} \times \mathrm{fuel\ EHV}}")
    if 'carbon_in' in key:
        return ("Calculated as:", r"\mathrm{fuel\ Cfrac} \times \mathrm{fuel\ mass} \times 1000")
    if 'carbon_out' in key:
        return ("Calculated as:",
                r"\frac{\mathrm{CO\ total\ mass} \times MW_{C}}{MW_{CO}} + \frac{\mathrm{CO2\ total\ mass} \times MW_{C}}{MW_{CO2}} + 0.91 \times \mathrm{PM\ total\ mass}")
    if 'C_Out_In' in key:
        return ("Calculated as:", r"\frac{\mathrm{carbon\ out}}{\mathrm{carbon\ in}}")