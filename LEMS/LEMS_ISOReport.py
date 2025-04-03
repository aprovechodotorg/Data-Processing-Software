import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
import math

def LEMS_ISOReport (data_values, outputpath):
    """
    Creates a formatted Excel table showing metrics similar to the reference image.

    Parameters:
    data_values (dict): Dictionary containing metrics data from PEMS_L2 function
    output_file_path (str): Path for saving the output Excel file
    """

    # Create a new workbook and select the active sheet
    wb = Workbook()
    ws = wb.active
    ws.title = "ISO Report Table"

    # Define border styles
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Define fills
    header_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")

    # Setup the headers
    ws.merge_cells('A1:A2')
    ws['A1'] = "Metric"
    ws['A1'].fill = header_fill

    ws.merge_cells('B1:E1')
    ws['B1'] = "Test Sequence Phase"
    ws['B1'].fill = header_fill

    ws['B2'] = "High"
    ws['B2'].fill = header_fill
    ws['C2'] = "Medium"
    ws['C2'].fill = header_fill
    ws['D2'] = "Low"
    ws['D2'].fill = header_fill
    ws['E2'] = "Combined"
    ws['E2'].fill = header_fill

    ws.merge_cells('F1:F2')
    ws['F1'] = "Tier Rating"
    ws['F1'].fill = header_fill

    # Set column widths
    ws.column_dimensions['A'].width = 24
    for col in range(2, 7):
        ws.column_dimensions[get_column_letter(col)].width = 12

    # Define the metrics to be included in the table
    metrics = [
        {"name": "Thermal Efficiency without char (%)", "key_base": "eff_wo_char", "tier_key": "tier_eff_wo_char"},
        {"name": "Thermal Efficiency with char (%)", "key_base": "eff_w_char", "tier_key": "tier_eff_w_char"},
        {"name": "Char Energy Productivity (%)", "key_base": "char_energy_productivity", "tier_key": None},
        {"name": "Char Mass Productivity (%)", "key_base": "char_mass_productivity", "tier_key": None},
        {"name": "Cooking Power (W)", "key_base": "cooking_power", "tier_key": None},
        {"name": "Fuel Burning Rate (g/min)", "key_base": "burn_rate", "tier_key": None},
        {"name": "PM2.5 per useful energy (mg/MJ)", "key_base": "PM_useful_eng_deliver", "tier_key": "tier_PM_useful_eng_deliver"},
        {"name": "CO per useful energy (mg/MJ)", "key_base": "CO_useful_eng_deliver", "tier_key": "tier_CO_useful_eng_deliver"},
        {"name": "Safety", "key_base": None, "tier_key": None},
        {"name": "Durability", "key_base": None, "tier_key": None}
    ]

    # Current row index (starting after headers)
    row_idx = 3

    # Phases to include in the table
    phases = ["_hp", "_mp", "_lp", "_weighted"]
    phase_cols = {'_hp': 'B', '_mp': 'C', '_lp': 'D', '_weighted': 'E'}

    # Process each metric
    for metric in metrics:
        # For Safety and Durability metrics (simplified case)
        if metric["key_base"] is None:
            ws[f'A{row_idx}'] = metric["name"]
            ws[f'B{row_idx}'] = "Score"
            for col in ['A', 'B', 'C', 'D', 'E', 'F']:
                ws[f'{col}{row_idx}'].border = thin_border
            ws[f'F{row_idx}'] = "N/A"
            row_idx += 1
            continue

        # For regular metrics with multiple rows
        # First, write the metric name
        ws[f'A{row_idx}'] = metric["name"]

        # Create merge after writing the value
        merge_range = f'A{row_idx}:A{row_idx+2}'
        ws.merge_cells(merge_range)
        ws[f'A{row_idx}'].alignment = Alignment(vertical='center')
        ws[f'A{row_idx}'].border = thin_border

        # Set up tier rating cell
        if metric["tier_key"] and metric["tier_key"] in data_values:
            ws[f'F{row_idx}'] = data_values[metric["tier_key"]]["average"]
        else:
            ws[f'F{row_idx}'] = "N/A"

        merge_range = f'F{row_idx}:F{row_idx + 2}'
        ws.merge_cells(merge_range)
        ws[f'F{row_idx}'].alignment = Alignment(vertical='center', horizontal='center')
        ws[f'F{row_idx}'].border = thin_border

        # Process rows for Mean, SD, and 90% CI
        labels = ["Mean", "SD", "90% CI"]

        for i, label in enumerate(labels):
            curr_row = row_idx + i

            # Process each phase
            for phase in phases:
                key = f"{metric['key_base']}{phase}"
                col = phase_cols[phase]

                # Handle Mean row
                if i == 0:  # Mean
                    if key in data_values and "average" in data_values[key]:
                        value = data_values[key]["average"]
                        ws[f'{col}{curr_row}'] = round(value, 1) if not isinstance(value, str) and not math.isnan(
                            value) else "-"
                    else:
                        ws[f'{col}{curr_row}'] = "-"

                # Handle SD row
                elif i == 1:  # SD
                    if key in data_values and "stdev" in data_values[key]:
                        value = data_values[key]["stdev"]
                        ws[f'{col}{curr_row}'] = round(value, 1) if not isinstance(value, str) and not math.isnan(
                            value) else "-"
                    else:
                        ws[f'{col}{curr_row}'] = "-"

                # Handle 90% CI row
                elif i == 2:  # 90% CI
                    if key in data_values and "high_tier" in data_values[key] and "low_tier" in data_values[key]:
                        high = data_values[key]["high_tier"]
                        low = data_values[key]["low_tier"]

                        if not isinstance(high, str) and not math.isnan(high) and not isinstance(low,
                                                                                                 str) and not math.isnan(
                                low):
                            ws[f'{col}{curr_row}'] = f"{round(high, 1)} - {round(low, 1)}"
                        else:
                            ws[f'{col}{curr_row}'] = "-"
                    else:
                        ws[f'{col}{curr_row}'] = "-"

                # Apply borders to the cells
                ws[f'{col}{curr_row}'].border = thin_border

        # Move to the next metric (after the 3 rows for this metric)
        row_idx += 3

    # Apply borders and alignment to all header cells
    for cell in ['A1', 'B1', 'F1', 'B2', 'C2', 'D2', 'E2']:
        ws[cell].border = thin_border
        ws[cell].alignment = Alignment(horizontal='center', vertical='center')
        ws[cell].font = Font(bold=True)

    # Save the workbook
    wb.save(outputpath)
    print(f"Table saved to {outputpath}")