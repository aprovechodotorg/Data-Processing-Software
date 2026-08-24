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
