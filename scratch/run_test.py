import os
import sys
import openpyxl

# Add LEMS folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../LEMS')))

from LEMS_CustomFormatted_L3 import LEMS_CustomFormatted_L3

def main():
    csvpath = 'FormattedCutTableL3_template_md snippit.xlsx'
    test_template = 'test_template.xlsx'
    
    # Load original template and modify ONLY the keys (col 7) to match CSV snippet variables.
    # We do NOT overwrite the user's custom data_type cell values in column 6!
    wb = openpyxl.load_workbook(csvpath)
    sheet = wb.active
    
    # Map 'fuel_mc_1' (which is in the CSV snippet) to rows 15-24
    sheet.cell(row=5, column=7).value = 'fuel_mc_1'
    sheet.cell(row=15, column=7).value = 'fuel_mc_1'
    sheet.cell(row=16, column=7).value = 'fuel_mc_1'
    sheet.cell(row=21, column=7).value = 'fuel_mc_1'
    sheet.cell(row=22, column=7).value = 'fuel_mc_1'
    sheet.cell(row=23, column=7).value = 'fuel_mc_1'
    sheet.cell(row=23, column=6).value = 'confidence (N)'
    sheet.cell(row=24, column=7).value = 'fuel_mc_1'
    sheet.cell(row=24, column=6).value = 'confidence'
    
    # Also map burn_rate_dry_hp (a key present in CSV that has units g/min) to the
    # burn rate rows so we can verify unit conversion:
    # Rows 27-30 have target unit 'g/min' (same as source -> no conversion expected)
    # Rows 33-36 have target unit 'lb/hr' (different from source -> conversion expected)
    for r in [27, 28, 29, 30, 33, 34, 35, 36]:
        sheet.cell(row=r, column=7).value = 'fuel_mc_1'
    
    wb.save(test_template)
    print("Modified template saved to:", test_template)

    inputpath = 'FormattedDataL3 snippit.csv'
    outputpath = 'test_output_L3.csv'
    outputexcel = 'test_output_L3.xlsx'
    logpath = 'test_log.txt'

    print("Running LEMS_CustomFormatted_L3...")
    LEMS_CustomFormatted_L3(inputpath, outputpath, outputexcel, test_template, logpath)
    print("Execution completed.")

    # Load and print key cells of output Excel to verify
    wb_out = openpyxl.load_workbook(outputexcel)
    sheet_out = wb_out.active

    print("\n--- Verifying Output Excel Sheet ---")
    print("Data type rows:")
    rows_to_check = [1, 5, 15, 16, 21, 22, 23, 24]
    for r in rows_to_check:
        vals = [sheet_out.cell(row=r, column=c).value for c in range(5, 12)]
        print(f"  Row {r:2d}: col5(units)={vals[0]}, col6(data_type)={vals[1]}, col7(data_key)={vals[2]}, col8_to_11={vals[3:]}")

    print("\nUnit conversion rows (burn_rate, source=g/min):")
    for r in [27, 28, 33, 34]:
        vals = [sheet_out.cell(row=r, column=c).value for c in range(5, 12)]
        print(f"  Row {r:2d}: col5(units)={vals[0]}, col6(data_type)={vals[1]}, col7(data_key)={vals[2]}, col8={vals[3]}")

if __name__ == '__main__':
    main()
