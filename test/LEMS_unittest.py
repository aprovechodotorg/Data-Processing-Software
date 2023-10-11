#v0.2 Python3

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

# Run unittests from project folder using the following:
# python -m unittest test.LEMS_unittest
# or
# python -m unittest <test folder>.<unittest file name>
import unittest
import csv
from pathlib import Path
import sys
import os
#add parent directoy to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from LEMS.LEMS_MakeInputFile_EnergyCalcs import LEMS_MakeInputFile_EnergyCalcs
from LEMS.LEMS_EnergyCalcs import LEMS_EnergyCalcs
from LEMS.LEMS_Adjust_Calibrations import LEMS_Adjust_Calibrations
from LEMS.LEMS_ShiftTimeSeries import LEMS_ShiftTimeSeries
from LEMS.PEMS_SubtractBkg import PEMS_SubtractBkg
from LEMS.LEMS_GravCalcs import LEMS_GravCalcs
from LEMS.LEMS_EmissionCalcs import LEMS_EmissionCalcs


class LEMSunittest(unittest.TestCase):
    def test_energycalcs(self):
        base_path = Path("./test/alcohol_test1")

        known_data_entry_path = base_path / "alcohol_test1_TE_dataEntrySheet.xlsx"

        calculated_energy_inputs_path = base_path / "alcohol_test1_EnergyInputs_test.csv"
        known_energy_inputs_path = base_path / "alcohol_test1_EnergyInputs.csv"

        calculated_energy_outputs_path = base_path / "alcohol_test1_EnergyOutputs_test.csv"
        known_energy_outputs_path = base_path / "alcohol_test1_EnergyOutputs.csv"

        log_path = base_path / "alcohol_test1_log.txt"

        # Create calculated energy inputs
        LEMS_MakeInputFile_EnergyCalcs(str(known_data_entry_path.absolute()),
                                       str(calculated_energy_inputs_path.absolute()), str(log_path.absolute()))

        # Compare calculated vs known energy inputs files
        calculated_file = open(calculated_energy_inputs_path, "r")
        known_file = open(known_energy_inputs_path, "r")

        known_linecount = 0
        calculated_linecount = 0

        known = []
        calculated = []

        for calculated_line in calculated_file:
            calculated.append(calculated_line)
            calculated_linecount += 1
        for known_line in known_file:
            known.append(known_line)
            known_linecount += 1

        self.assertEqual(calculated_linecount, known_linecount,
                         f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for Energy Inputs")

        #for calculated_line, known_line in zip(calculated_file, known_file):
            #self.assertEqual(calculated_line, known_line)

        for n, row in enumerate(known):
            message = ('Row ' + str(n +1) + ' of known energy input file and calculated energy input file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        # Create calculated energy outputs
        LEMS_EnergyCalcs(str(known_energy_inputs_path.absolute()), str(calculated_energy_outputs_path.absolute()), str(log_path.absolute()))

        # Compare calculated vs known energy inputs files
        calculated_file = open(calculated_energy_outputs_path, "r")
        known_file = open(known_energy_outputs_path, "r")

        known_linecount = 0
        calculated_linecount = 0

        known = []
        calculated = []

        for calculated_line in calculated_file:
            calculated.append(calculated_line)
            calculated_linecount += 1
        for known_line in known_file:
            known.append(known_line)
            known_linecount += 1

        if (known_linecount - calculated_linecount) == 1: #There's one known added line in know energy output for SB firmware
            known_linecount = known_linecount - 1
            known.pop(-1)
        self.assertEqual(calculated_linecount, known_linecount, f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for Energy Outputs")

        #for calculated_line, known_line in zip(calculated_file, known_file):
            #self.assertEqual(calculated_line, known_line)

        for n, row in enumerate(known):
            message = ('Row ' + str(n + 1) + ' of known energy output file and calculated energy output file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        pass

    def test_AdjustCalibrations(self):
        base_path = Path("./test/alcohol_test1")

        known_raw_data_path = base_path / "alcohol_test1_RawData.csv"
        known_energy_outputs_path = base_path / "alcohol_test1_EnergyOutputs.csv"

        calculated_recalibrated_path = base_path / "alcohol_test1_RawData_Recalibrated_test.csv"
        known_recalibrated_path = base_path / "alcohol_test1_RawData_Recalibrated.csv"

        calculated_header_path = base_path / "alcohol_test1_Header_test.csv"
        known_header_path = base_path / "alcohol_test1_Header.csv"

        log_path = base_path / "alcohol_test1_log.txt"

        # Create firmware adjusted data
        LEMS_Adjust_Calibrations(str(known_raw_data_path.absolute()), str(known_energy_outputs_path.absolute()),
                                 str(calculated_recalibrated_path.absolute()), str(calculated_header_path.absolute()),
                                 str(log_path.absolute()), inputmethod='2')

        # Compare calculated vs known recalibrated files
        calculated_file = open(calculated_recalibrated_path, "r")
        known_file = open(known_recalibrated_path, "r")

        known_linecount = 0
        calculated_linecount = 0

        known = []
        calculated = []

        for calculated_line in calculated_file:
            calculated.append(calculated_line)
            calculated_linecount += 1
        for known_line in known_file:
            known.append(known_line)
            known_linecount += 1

        self.assertEqual(calculated_linecount, known_linecount,
                         f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for Recalibrated Raw Data")

        # for calculated_line, known_line in zip(calculated_file, known_file):
        # self.assertEqual(calculated_line, known_line)

        for n, row in enumerate(known):
            message = ('Row ' + str(
                n + 1) + ' of known recalibrated file and calculated recalibrated file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        # Compare calculated vs known header files
        calculated_file = open(calculated_header_path, "r")
        known_file = open(known_header_path, "r")

        known_linecount = 0
        calculated_linecount = 0

        known = []
        calculated = []

        for calculated_line in calculated_file:
            calculated.append(calculated_line)
            calculated_linecount += 1
        for known_line in known_file:
            known.append(known_line)
            known_linecount += 1

        self.assertEqual(calculated_linecount, known_linecount,
                         f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for Header")

        # for calculated_line, known_line in zip(calculated_file, known_file):
        # self.assertEqual(calculated_line, known_line)

        for n, row in enumerate(known):
            message = ('Row ' + str(
                n + 1) + ' of known header file and calculated header file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        pass

    def test_shifted_response(self):
        base_path = Path("./test/alcohol_test1")

        known_raw_data_path = base_path / "alcohol_test1_RawData_Recalibrated.csv"

        calculated_shifted_path = base_path / "alcohol_test1_RawData_Shifted_test.csv"
        known_shifted_path = base_path / "alcohol_test1_RawData_Shifted.csv"

        calculated_timeshifts_path = base_path / "alcohol_test1_TimeShifts_test.csv"
        known_timeshifts_path = base_path / "alcohol_test1_TimeShifts.csv"

        log_path = base_path / "alcohol_test1_log.txt"

        # Create response time shifted data
        LEMS_ShiftTimeSeries(str(known_raw_data_path.absolute()), str(calculated_shifted_path.absolute()),
                             str(calculated_timeshifts_path.absolute()), str(log_path.absolute()), inputmethod = '2')

        # Compare calculated vs known shifted files
        calculated_file = open(calculated_shifted_path, "r")
        known_file = open(known_shifted_path, "r")

        known_linecount = 0
        calculated_linecount = 0

        known = []
        calculated = []

        for calculated_line in calculated_file:
            calculated.append(calculated_line)
            calculated_linecount += 1
        for known_line in known_file:
            known.append(known_line)
            known_linecount += 1

        self.assertEqual(calculated_linecount, known_linecount,
                         f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for Shifted Raw Data")

        # for calculated_line, known_line in zip(calculated_file, known_file):
        # self.assertEqual(calculated_line, known_line)

        for n, row in enumerate(known):
            message = ('Row ' + str(
                n + 1) + ' of known shifted file and calculated shifted file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        # Compare calculated vs known header files
        calculated_file = open(calculated_timeshifts_path, "r")
        known_file = open(known_timeshifts_path, "r")

        known_linecount = 0
        calculated_linecount = 0

        known = []
        calculated = []

        for calculated_line in calculated_file:
            calculated.append(calculated_line)
            calculated_linecount += 1
        for known_line in known_file:
            known.append(known_line)
            known_linecount += 1

        self.assertEqual(calculated_linecount, known_linecount,
                         f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for TimeShifts")

        # for calculated_line, known_line in zip(calculated_file, known_file):
        # self.assertEqual(calculated_line, known_line)

        for n, row in enumerate(known):
            message = ('Row ' + str(
                n + 1) + ' of known timeshifts file and calculated timeshifts file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        pass

    def test_bkg_subtract(self):
        base_path = Path("./test/alcohol_test1")

        known_raw_data_path = base_path / "alcohol_test1_RawData_Shifted.csv"
        known_energy_input_path = base_path / "alcohol_test1_EnergyInputs.csv"
        known_phasetime_path = base_path / "alcohol_test1_PhaseTimes.csv"
        known_bkg_methods_path = base_path / "alcohol_test1_BkgMethods.csv"
        known_fig1_path = base_path / "alcohol_test1_subtractbkg1.png"
        known_fig2_path = base_path / "alcohol_test1_subtractbkg2.png"

        known_UC_path = base_path / "alcohol_test1_UCInputs.csv"
        calculated_UC_path = base_path / "alcohol_test1_UCInputs_test.csv"

        calculated_timeseries_path = base_path / "alcohol_test1_test_TimeSeries.csv"
        known_timeseries_path = base_path / "alcohol_test1_TimeSeries.csv"

        calculated_averages_path = base_path / "alcohol_test1_Averages_test.csv"
        known_averages_path = base_path / "alcohol_test1_Averages.csv"

        log_path = base_path / "alcohol_test1_log.txt"

        # Create bkg subtracted data
        PEMS_SubtractBkg(str(known_raw_data_path.absolute()), str(known_energy_input_path.absolute()),
                         str(calculated_UC_path.absolute()), str(calculated_timeseries_path.absolute()),
                         str(calculated_averages_path.absolute()), str(known_phasetime_path.absolute()),
                         str(known_bkg_methods_path.absolute()), str(log_path.absolute()),
                         str(known_fig1_path.absolute()), str(known_fig2_path.absolute()), inputmethod = '2')

        # Compare calculated vs known uncertainty data
        calculated_file = open(calculated_UC_path, "r")
        known_file = open(known_UC_path, "r")

        known_linecount = 0
        calculated_linecount = 0

        known = []
        calculated = []

        for calculated_line in calculated_file:
            calculated.append(calculated_line)
            calculated_linecount += 1
        for known_line in known_file:
            known.append(known_line)
            known_linecount += 1

        self.assertEqual(calculated_linecount, known_linecount,
                         f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for UC Inputs")

        # for calculated_line, known_line in zip(calculated_file, known_file):
        # self.assertEqual(calculated_line, known_line)

        for n, row in enumerate(known):
            message = ('Row ' + str(
                n + 1) + ' of known UC inputs file and calculated UC inputs file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        # Compare calculated vs known timeseries files
        calculated_file = open(calculated_timeseries_path, "r")
        known_file = open(known_timeseries_path, "r")

        known_linecount = 0
        calculated_linecount = 0

        known = []
        calculated = []

        for calculated_line in calculated_file:
            calculated.append(calculated_line)
            calculated_linecount += 1
        for known_line in known_file:
            known.append(known_line)
            known_linecount += 1

        self.assertEqual(calculated_linecount, known_linecount,
                         f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for TimeSeries")

        # for calculated_line, known_line in zip(calculated_file, known_file):
        # self.assertEqual(calculated_line, known_line)

        for n, row in enumerate(known):
            message = ('Row ' + str(
                n + 1) + ' of known timeseries file and calculated timeseries file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        # Compare calculated vs known averages files
        calculated_file = open(calculated_averages_path, "r")
        known_file = open(known_averages_path, "r")

        known_linecount = 0
        calculated_linecount = 0

        known = []
        calculated = []

        for calculated_line in calculated_file:
            calculated.append(calculated_line)
            calculated_linecount += 1
        for known_line in known_file:
            known.append(known_line)
            known_linecount += 1

        self.assertEqual(calculated_linecount, known_linecount,
                         f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for Averages")

        # for calculated_line, known_line in zip(calculated_file, known_file):
        # self.assertEqual(calculated_line, known_line)

        for n, row in enumerate(known):
            message = ('Row ' + str(
                n + 1) + ' of known averages file and calculated averages file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        pass

    def test_grav_calcs(self):
        base_path = Path("./test/alcohol_test1")

        known_grav_input_path = base_path / "alcohol_test1_GravInputs.csv"
        known_averages_path = base_path / "alcohol_test1_Averages.csv"
        known_phasetime_path = base_path / "alcohol_test1_PhaseTimes.csv"
        known_energy_output_path = base_path / "alcohol_test1_EnergyOutputs.csv"

        known_grav_output_path = base_path / "alcohol_test1_GravOutputs.csv"
        calculated_grav_output_path = base_path / "alcohol_test1_GravOutputs_test.csv"

        log_path = base_path / "alcohol_test1_log.txt"

        # Create grav data
        LEMS_GravCalcs(str(known_grav_input_path.absolute()), str(known_averages_path.absolute()),
                       str(known_phasetime_path.absolute()), str(known_energy_output_path.absolute()),
                       str(calculated_grav_output_path.absolute()), str(log_path.absolute()))

        # Compare calculated vs known grav data
        calculated_file = open(calculated_grav_output_path, "r")
        known_file = open(known_grav_output_path, "r")

        known_linecount = 0
        calculated_linecount = 0

        known = []
        calculated = []

        for calculated_line in calculated_file:
            calculated.append(calculated_line)
            calculated_linecount += 1
        for known_line in known_file:
            known.append(known_line)
            known_linecount += 1

        self.assertEqual(calculated_linecount, known_linecount,
                         f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for Grav Outputs")

        # for calculated_line, known_line in zip(calculated_file, known_file):
        # self.assertEqual(calculated_line, known_line)

        for n, row in enumerate(known):
            message = ('Row ' + str(
                n + 1) + ' of known grav outputs file and calculated grav outputs file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        pass

    def test_emission_calcs(self):
        base_path = Path("./test/alcohol_test1")

        known_timeseries_path = base_path / "alcohol_test1_TimeSeries.csv"
        known_grav_output_path = base_path / "alcohol_test1_GravOutputs.csv"
        known_averages_path = base_path / "alcohol_test1_Averages.csv"
        known_energy_output_path = base_path / "alcohol_test1_EnergyOutputs.csv"

        known_emission_output_path = base_path / "alcohol_test1_EmissionOutputs.csv"
        calculated_emission_output_path = base_path / "alcohol_test1_EmissionOutputs_test.csv"

        known_alloutput_path = base_path / "alcohol_test1_AllOutputs.csv"
        calcualted_alloutput_path = base_path / "alcohol_test1_AllOutputs_test.csv"


        log_path = base_path / "alcohol_test1_log.txt"

        # Create emission data
        LEMS_EmissionCalcs(str(known_timeseries_path.absolute()), str(known_energy_output_path.absolute()),
                           str(known_grav_output_path.absolute()), str(known_averages_path.absolute()),
                           str(calculated_emission_output_path.absolute()), str(calcualted_alloutput_path.absolute()),
                           str(log_path.absolute()))

        # Compare calculated vs known emission data
        calculated_file = open(calculated_emission_output_path, "r")
        known_file = open(known_emission_output_path, "r")

        known_linecount = 0
        calculated_linecount = 0

        known = []
        calculated = []

        for calculated_line in calculated_file:
            calculated.append(calculated_line)
            calculated_linecount += 1
        for known_line in known_file:
            known.append(known_line)
            known_linecount += 1

        self.assertEqual(calculated_linecount, known_linecount,
                         f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for Emission Outputs")

        # for calculated_line, known_line in zip(calculated_file, known_file):
        # self.assertEqual(calculated_line, known_line)

        for n, row in enumerate(known):
            message = ('Row ' + str(
                n + 1) + ' of known emission outputs file and calculated emission outputs file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        # Compare calculated vs known all data
        calculated_file = open(calcualted_alloutput_path, "r")
        known_file = open(known_alloutput_path, "r")

        known_linecount = 0
        calculated_linecount = 0

        known = []
        calculated = []

        for calculated_line in calculated_file:
            calculated.append(calculated_line)
            calculated_linecount += 1
        for known_line in known_file:
            known.append(known_line)
            known_linecount += 1

        self.assertEqual(calculated_linecount, known_linecount,
                         f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for All Outputs")

        # for calculated_line, known_line in zip(calculated_file, known_file):
        # self.assertEqual(calculated_line, known_line)

        for n, row in enumerate(known):
            message = ('Row ' + str(
                n + 1) + ' of known all outputs file and calculated all outputs file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()


        pass
