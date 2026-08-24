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


# Energy Outputs

    if 'eff_wo_char' in key:
        return ("Calculated as:",
                r"\frac{\mathrm{useful\ energy\ delivered}}{\mathrm{fuel\ mass\ wo\ char} \times \mathrm{fuel\ EHV\ wo\ char}} \times 100")
    if 'eff_w_char' in key:
        return ("Calculated as:",
                r"\frac{\mathrm{useful\ energy\ delivered}}{\mathrm{fuel\ mass} \times \mathrm{fuel\ EHV}} \times 100")
    if 'cooking_power' in key:
        return ("Calculated as:", r"\frac {\frac{\mathrm{useful\ energy\ delivered}}{\mathrm{phase\ time}}}{60}")
    if 'char_energy_productivity' in key or 'char_energy' in key:
        return ("Calculated as:",
                r"\frac{\mathrm{char\ mass} \times \mathrm{char\ lower\ heating\ value}}{\mathrm{fuel\ mass}} \times 100")
    if 'char_mass_productivity' in key:
        return ("Calculated as:", r"\frac{\mathrm{char\ mass}}{\mathrm{fuel\ mass}} \times 100")
    if 'burn_rate_dry' in key:
        return ("Calculated as:", r"\frac{\mathrm{fuel\ dry\ mass}}{\mathrm{phase\ time}} \times 1000")
    if 'burn_rate' in key:
        return ("Calculated as:", r"\frac{\mathrm{fuel\ mass}}{\mathrm{phase\ time}} \times 1000")
    if 'fuel_mass_wo_char' in key:
        return ("Calculated as sum of fuel with a carbon fraction less than 0.75:",
                r"\sum_{i=1}^{n}{\mathrm{fuel\ mass\ wood}_{i}}")
    if 'char_mass' in key and 'initial' not in key and 'final' not in key:
        return ("Calculated as sum of fuel with a carbon fraction more than 0.75:",
                r"\sum_{i=1}^{n}{\mathrm{fuel\ mass\ char}_{i}}")
    if (
            'fuel_mass_hp_' in key or 'fuel_mass_mp_' in key or 'fuel_mass_lp_' in key) and 'initial' not in key and 'final' not in key:
        return ("Calculated as:", r"\mathrm{initial\ fuel\ mass} - \mathrm{final\ fuel\ mass}")
    if 'fuel_mass' in key and 'initial' not in key and 'final' not in key:
        return ("Calculated as:", r"\sum_{i=1}^{n}{\mathrm{fuel\ mass}_{i}}")
    if ('fuel_dry_mass_hp_' in key or 'fuel_dry_mass_mp_' in key or 'fuel_dry_mass_lp_' in key):
        return ("Calculated as:", r"\mathrm{fuel\ mass} \times (1 - \frac{\mathrm{fuel\ mc}}{100})")
    if 'fuel_dry_mass' in key:
        return ("Calculated as:", r"\sum_{i=1}^{n}\mathrm{fuel\ mass}_{i} \times (1 - \frac{\mathrm{fuel\ mc}_{i}}{100})")
    if 'energy_consumed' in key:
        return ("Calculated as:", r"\mathrm{fuel\ mass} \times \mathrm{fuel\ higher\ heating\ value}")
    if 'fuel_net_calorific_value_hp' in key or 'fuel_net_calorific_value_mp' in key or 'fuel_net_calorific_value_lp' in key:
        return ("Calculated as a mass weighted average of all fuel net calorific values:",
                r"\sum_{i=1}^{n}(\frac{\mathrm{fuel\ higher\ heating\ value}_{i} - \mathrm{correction\ value}) \times \mathrm{fuel\ mass}_{i}}{\mathrm{fuel\ mass}}")
    if 'fuel_EHV_wo_char' in key:
        return (
            "Calculated as a mass weighted average of all fuell effective heating values for fuel with a carbon fraction less than 0.75:",
            r"\sum_{i=1}^{n}\frac{(\mathrm{fuel\ net\ calorific\ value}_{i} \times (1 - \frac{\mathrm{fuel\ mc}_{i}}{100}) - 2443 \times \frac{\mathrm{fuel\ mc}_{i}}{100}) * \mathrm{fuel\ mass}_{i}}{\mathrm{fuel\ mass\ wo\ char}}")
    if 'fuel_EHV' in key:
        return ("Calculated as a mass weighted average of all fuell effective heating values:",
                r"\sum_{i=1}^{n}\frac{(\mathrm{fuel\ net\ calorific\ value}_{i} \times (1 - \frac{\mathrm{fuel\ mc}_{i}}{100}) - 2443 \times \frac{\mathrm{fuel\ mc}_{i}}{100}) * \mathrm{fuel\ mass}_{i}}{\mathrm{fuel\ mass}}")
    if 'useful_energy_delivered' in key:
        return ("Calculated as:",
                r"C_{p} \times \mathrm{initial\ water\ mass} \times (\mathrm{max\ water\ temp} - \mathrm{initial\ water\ temp}) + (\mathrm{initial\ water\ mass} - \mathrm{final\ water\ mass}) \times H_{vap}")
    if 'firepower_w_char' in key:
        return ("Calculated as:", r"\frac{\mathrm{fuel\ mass} \times \mathrm{fuel\ EHV}}{\mathrm{phase\ time} \times 60}")
    if 'MSC' in key:
        return ("Calculated as:", r"\frac{PM}{PMmass}")
    if 'MCE' in key:
        return ("Calculated as:", r"\frac{CO_{2}}{CO_{2} + CO}")


# Other remaining functions

    if 'PMsample_mass' in key:
        return ("Calculated as:", r"\mathrm{grossmass} - taremass")
    if 'Qsample' in key:
        return ("Calculated as the sum of flow rates from all gravimetric trains used.", None)

