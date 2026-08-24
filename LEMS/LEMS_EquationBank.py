# This file will be for equation bank storage. It will focus on the equationst that are displayed when the uesr hovers over the "i" icon.



def equation_bank(key):

# Emissions and Energy Calculations

    if 'PM_useful_eng_deliver' in key:
        return ("Calculated as:", r"\\frac{\\mathrm{PM\\ total\\ mass}}{\\mathrm{useful\\ energy\\ delivered}} \\times 1000 \\times 1000")

    elif 'CO_useful_eng_deliver' in key:
            return ("Calculated as:",
            r"\\frac{\\mathrm{CO\\ total\\ mass}}{\\mathrm{useful\\ energy\\ delivered}} \\times 1000"
        )

    elif 'CO2_useful_eng_deliver' in key:

        return ( "Calculated as:", r"\\frac{\\mathrm{CO_{2}\\ total\\ mass}}{\\mathrm{useful\\ energy\\ delivered}} \\times 1000")

