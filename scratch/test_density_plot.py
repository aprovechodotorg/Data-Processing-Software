import os
import shutil
import numpy as np
import pandas as pd
import sys

# Ensure LEMS directory is on path
lems_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'LEMS'))
sys.path.insert(0, lems_dir)

from LEMS_L2_DensityPlot import LEMS_L2_DensityPlot, write_config, read_config, CONFIG_NAME

def run_test():
    scratch_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_density_env'))
    if os.path.exists(scratch_dir):
        shutil.rmtree(scratch_dir)
    os.makedirs(scratch_dir)

    test1_dir = os.path.join(scratch_dir, 'test1')
    test2_dir = os.path.join(scratch_dir, 'test2')
    os.makedirs(test1_dir)
    os.makedirs(test2_dir)

    # Create test1 files
    # TimeSeriesMetrics_hp
    ts1 = pd.DataFrame({
        'time': ['2026-04-01 10:00:00', '2026-04-01 10:00:01', '2026-04-01 10:00:02', '2026-04-01 10:00:03'],
        'seconds': [0, 1, 2, 3],
        'PM_EF': [15.0, 14.5, 12.0, 10.0],
        'CO_EF': [50.0, 48.0, 45.0, 40.0]
    })
    units_row1 = pd.DataFrame([['yyyy-mm-dd HH:MM:SS', 's', 'g/kg_C', 'g/kg_C']], columns=ts1.columns)
    df_ts1 = pd.concat([units_row1, ts1], ignore_index=True)
    df_ts1.to_csv(os.path.join(test1_dir, 'test1_TimeSeriesMetrics_hp.csv'), index=False)

    # FormattedSenserionData for test1
    sen1 = pd.DataFrame({
        'time': ['2026-04-01 10:00:00', '2026-04-01 10:00:01', '2026-04-01 10:00:02', '2026-04-01 10:00:03'],
        'seconds': [0, 1, 2, 3],
        'Chimney_T': [150.0, 180.0, 220.0, 260.0],
        'TC1': [100.0, 110.0, 120.0, 130.0]
    })
    units_sen1 = pd.DataFrame([['yyyy-mm-dd HH:MM:SS', 's', 'degC', 'degC']], columns=sen1.columns)
    df_sen1 = pd.concat([units_sen1, sen1], ignore_index=True)
    df_sen1.to_csv(os.path.join(test1_dir, 'test1_FormattedSenserionData.csv'), index=False)

    # Create test2 files
    ts2 = pd.DataFrame({
        'time': ['2026-04-02 11:00:00', '2026-04-02 11:00:01', '2026-04-02 11:00:02'],
        'seconds': [0, 1, 2],
        'PM_EF': [9.5, 9.0, 8.8],
        'CO_EF': [38.0, 36.0, 35.0]
    })
    units_row2 = pd.DataFrame([['yyyy-mm-dd HH:MM:SS', 's', 'g/kg_C', 'g/kg_C']], columns=ts2.columns)
    df_ts2 = pd.concat([units_row2, ts2], ignore_index=True)
    df_ts2.to_csv(os.path.join(test2_dir, 'test2_TimeSeriesMetrics_hp.csv'), index=False)

    # FormattedSenserionData for test2
    sen2 = pd.DataFrame({
        'time': ['2026-04-02 11:00:00', '2026-04-02 11:00:01', '2026-04-02 11:00:02'],
        'seconds': [0, 1, 2],
        'Chimney_T': [280.0, 310.0, 330.0],
        'TC1': [140.0, 150.0, 160.0]
    })
    units_sen2 = pd.DataFrame([['yyyy-mm-dd HH:MM:SS', 's', 'degC', 'degC']], columns=sen2.columns)
    df_sen2 = pd.concat([units_sen2, sen2], ignore_index=True)
    df_sen2.to_csv(os.path.join(test2_dir, 'test2_FormattedSenserionData.csv'), index=False)

    # Create config file for headless run
    config_path = os.path.join(scratch_dir, CONFIG_NAME)
    config_row = {
        'x_var': 'Chimney_T',
        'y_var': 'PM_EF',
        'phases': 'hp',
        'source': 'TimeSeriesMetrics',
        'x_lag_s': '0',
        'y_lag_s': '0',
        'x_reverse': 'y',
        'y_reverse': 'n',
        'x_bins': '10',
        'y_bins': '10',
        'x_min': '100',
        'x_max': '350',
        'y_min': '5',
        'y_max': '20',
        'color_scale': 'linear',
        'smooth': '0',
        'colormap': 'viridis'
    }
    write_config(config_path, [config_row])

    list_dir = [test1_dir, test2_dir]
    list_test = ['test1', 'test2']
    logpath = os.path.join(scratch_dir, 'L2_log.txt')

    print("Running LEMS_L2_DensityPlot in headless mode...")
    saved = LEMS_L2_DensityPlot(list_dir, list_test, scratch_dir, logpath, inputmethod='2')
    print("Saved plots:", saved)

    # Verify outputs
    expected_png = os.path.join(scratch_dir, 'L2_Density_Chimney_T_vs_PM_EF_hp.png')
    expected_counts = os.path.join(scratch_dir, 'L2_Density_Chimney_T_vs_PM_EF_hp_counts.csv')
    expected_stacked = os.path.join(scratch_dir, 'L2_Density_Chimney_T_vs_PM_EF_hp_stacked.csv')

    assert os.path.isfile(expected_png), f"Missing {expected_png}"
    assert os.path.isfile(expected_counts), f"Missing {expected_counts}"
    assert os.path.isfile(expected_stacked), f"Missing {expected_stacked}"

    stacked_df = pd.read_csv(expected_stacked)
    print("Stacked points:")
    print(stacked_df)
    assert len(stacked_df) == 7, f"Expected 7 points from 4+3, got {len(stacked_df)}"
    assert set(stacked_df['test'].unique()) == {'test1', 'test2'}

    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_test()
