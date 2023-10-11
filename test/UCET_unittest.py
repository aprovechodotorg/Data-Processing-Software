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
# python -m unittest test.UCET_unittest
# or
# python -m unittest <test folder>.<unittest file name>
import unittest
import csv
from pathlib import Path
from LEMS_MakeInputFile_EnergyCalcs import LEMS_MakeInputFile_EnergyCalcs
from PEMS_L2 import PEMS_L2
from UCET_EnergyCalcs import UCET_EnergyCalcs
from LEMS_FormatData_L3 import LEMS_FormatData_L3

class UCETunittest(unittest.TestCase):
    def test_energycalcs(self):
        base_path = Path("./test/UCET/Gyapa/GyapaC1T1")
        known_data_entry_path = base_path / "GyapaC1T1_DataEntrySheet.xlsx"

        calculated_energy_inputs_path = base_path / "GyapaC1T1_EnergyInputs_test.csv"
        known_energy_inputs_path = base_path / "GyapaC1T1_EnergyInputs.csv"

        known_energy_outputs_path = base_path / "GyapaC1T1_EnergyOutputs.csv"
        calculated_energy_outputs_path = base_path / "GyapaC1T1_EnergyOutputs_test.csv"

        log_path = base_path / "GyapaC1T1_log.txt"

        # Create calculated energy inputs
        LEMS_MakeInputFile_EnergyCalcs(str(known_data_entry_path.absolute()), str(calculated_energy_inputs_path.absolute()), str(log_path.absolute()))

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

        self.assertEqual(calculated_linecount, known_linecount, f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for Energy Inputs")

        '''
        for calculated_line, known_line in zip(calculated_file, known_file):
            self.assertEqual(calculated_line, known_line)
        '''

        for n, row in enumerate(known):
            message = ('Row ' + str(n +1) + ' of known energy input file and calculated energy input file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        # Create calculated energy outputs
        UCET_EnergyCalcs(str(known_energy_inputs_path.absolute()), str(calculated_energy_outputs_path.absolute()), str(log_path.absolute()))

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

        self.assertEqual(calculated_linecount, known_linecount, f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for Energy Outputs")

        #for calculated_line, known_line in zip(calculated_file, known_file):
            #self.assertEqual(calculated_line, known_line)

        for n, row in enumerate(known):
            message = ('Row ' + str(n + 1) + ' of known energy output file and calculated energy output file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        pass


    def test_L2calcs(self):
        base_path = Path("./test/UCET/Gyapa")
        known_energyoutput_path = []
        known_energyoutput_path.append(base_path / "GyapaC1T1/GyapaC1T1_EnergyOutputs.csv")
        known_energyoutput_path.append(base_path / "GyapaC1T2/GyapaC1T2_EnergyOutputs.csv")
        known_energyoutput_path.append(base_path / "GyapaC1T3/GyapaC1T3_EnergyOutputs.csv")
        known_energyoutput_path.append(base_path / "GyapaC2T1/GyapaC2T1_EnergyOutputs.csv")
        known_energyoutput_path.append(base_path / "GyapaC2T2/GyapaC2T2_EnergyOutputs.csv")
        known_energyoutput_path.append(base_path / "GyapaC2T3/GyapaC2T3_EnergyOutputs.csv")

        known_emissionoutput_path = ['N/A','N/A','N/A','N/A','N/A','N/A']

        list_testname = ['GyapaC1T1', 'GyapaC1T2', 'GyapaC1T3', 'GyapaC2T1', 'GyapaC2T2', 'GyapaC2T3',]

        known_L2_output_path = base_path/ "FormattedDataL2.csv"

        calculated_L2_outputpath = base_path/ "FormattedDataL2_test.csv"

        PEMS_L2(known_energyoutput_path, known_emissionoutput_path, calculated_L2_outputpath, list_testname)

        # Compare calculated vs known energy inputs files
        calculated_file = open(calculated_L2_outputpath, "r")
        known_file = open(known_L2_output_path, "r")

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
                         f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for Level 2 Outputs")

        #for calculated_line, known_line in zip(calculated_file, known_file):
            #self.assertEqual(calculated_line, known_line)

        for n, row in enumerate(known):
            message = ('Row ' + str(n + 1) + ' of known L2 file and calculated L2 file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        pass

    def test_L3calcs(self):
        base_path = Path("./test/UCET")

        known_L2_path = []
        known_L2_path.append(base_path / "Gyapa/FormattedDataL2.csv")
        known_L2_path.append(base_path / "Traditional/FormattedDataL2.csv")
        known_L2_path.append(base_path / "TraditionalAluminum/FormattedDataL2.csv")

        for n, val in enumerate(known_L2_path):
            known_L2_path[n] = str(known_L2_path[n].absolute())

        known_L2_output_path = base_path / "FormattedDataL3.csv"

        calculated_L2_outputpath = base_path / "FormattedDataL3_test.csv"

        log_path = base_path / "UCET_log.txt"

        LEMS_FormatData_L3(known_L2_path, str(calculated_L2_outputpath.absolute()), str(log_path.absolute()))

        # Compare calculated vs known energy inputs files
        calculated_file = open(calculated_L2_outputpath, "r")
        known_file = open(known_L2_output_path, "r")

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
                         f"Known inputs file line count ({known_linecount}) does not match calculated inputs file line count ({calculated_linecount}) for Level 3 Outputs")

        #for calculated_line, known_line in zip(calculated_file, known_file):
            #self.assertEqual(calculated_line, known_line)
        for n, row in enumerate(known):
            message = ('Row ' + str(n + 1) + ' of known L3 file and calculated L3 file are not equal.')
            self.assertEqual(row, calculated[n], message)

        calculated_file.close()
        known_file.close()

        pass


