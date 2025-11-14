# v0.2 Python3

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

###inputs:
# firmware_version = SB4003.16
# names: list of channel names
# A_old: dictionary keys are variable names, values are A (span) parameters from the raw data file header
# B_old = dictionary keys are variable names, values are B (offset) parameters from the raw data file header
# const_old: dictionary keys are constant variable names (C parameters), values are constant variable values (D parameters) from the raw data file header
# data_old: dictionary keys are variable names, values are lists of time series data from the raw data file
# A_new: dictionary keys are variable names, values are new A (span) parameters defined in the header input file
# B_new: dictionary keys are constant variable names, values are new B (offset) parameters defined in the header input file
# const_new: dictionary keys are constant variable names (C parameters), values are constant variable values (D parameters) from the header input file

###output:
# data_new: dictionary keys are variable names, values are lists of recalculated time series data
# updated_channels: list of channel names that were updated

import math


def RedoFirmwareCalcs(firmware_version, names, A_old, B_old, const_old, data_old, A_new, B_new, const_new):
    # This function inputs time series data, and recalculates firmware calculations with updated calibration parameters
    # called by LEMS_Adjust_Calibrations()

    Pstd = 101325  # Pascals              define standard pressure for NozVel channel
    Tstd = 293  # K                               define standard temperature for NozVel channel

    data_new = {}
    updated_channels = []
    ###  possum1.2 ##############################
    if firmware_version == 'possum1.2':
        calculated_channels = ['StakVel', 'Nozvel', 'PMmass',
                               'DilRat']  # define list of calculated channels that are not a function of A and B
        for name in names:
            data_new[name] = []  # initialize a list to fill with the new data series
            if name not in calculated_channels:
                if A_old[name] == A_new[name] and B_old[name] == B_new[name] or math.isnan(A_old[name]) and math.isnan(
                        A_new[name]) and math.isnan(B_old[name]) and math.isnan(
                        B_new[name]):  # if A the B parameter did not change
                    data_new[name] = data_old[name]  # copy the old time series to the new time series
                else:  # if A or B did change
                    updated_channels.append(name)
                    # recalculate data values using the following formula: CO=A*(CO_raw+B)
                    for n in range(len(data_old[name])):  # for each point in the old data series
                        oldval = data_old[name][n]  # grab the old value
                        # back-calculate to raw data (ADC bits) using the old cal parameters and then apply new cal parameters
                        newval = A_new[name] * (oldval / A_old[name] - B_old[name] + B_new[name])
                        data_new[name].append(newval)  # append the new value to the new data list
                    print(name, ' updated')

        # calculated channels:
        name = 'StakVel'
        updated_channels.append(name)
        # StakVel=Cp*Kp*sqrt(Pres1*(TCnoz+273)/Pamb/MolWt)
        data_new[name] = []
        Kp = float(129)
        Cpitot = const_new['Cpitot(-)']
        MolWt = const_new['MolWt(g/mol)']
        for n in range(len(data_old[name])):
            Pres1val = float(data_new['Pitot'][n])
            try:
                Pambval = float(data_new['Pamb'][n])
            except:
                Pambval = 100000
            TCnozval = data_new['TCnoz'][n]
            if TCnozval == 'nan':
                newval = 'nan'
            else:
                TCnozval = float(TCnozval)
                if Pres1val < 0:
                    Pres1val = -Pres1val
                    newval = -Cpitot * Kp * math.sqrt(Pres1val * (TCnozval + 273.15) / Pambval / MolWt)
                else:
                    newval = Cpitot * Kp * math.sqrt(Pres1val * (TCnozval + 273.15) / Pambval / MolWt)
            data_new[name].append(newval)
        print(name + ' recalculated')

        name = 'NozVel'  # NozVel=(F1Flow+F2Flow+GasFlow+IsoFlow-DilFlow)*Pstd/Pamb*(TCnoz+273)/293/60*4/pi/NozDiam^2
        data_new[name] = []
        updated_channels.append(name)
        NozDiam = const_new['NozDiam(mm)']
        for n in range(len(data_old[name])):
            F1Flowval = float(data_new['F1Flow'][n])
            try:
                F2Flowval = float(data_new['F2Flow'][n])
            except:
                F2Flowval = 0
            GasFlowval = float(data_new['SampFlow'][n])
            IsoFlowval = float(data_new['USampFlow'][n])
            DilFlowval = float(data_new['DilFlow'][n])
            nozzleflow = F1Flowval + F2Flowval + GasFlowval + IsoFlowval - DilFlowval
            try:
                Pambval = float(data_new['Pamb'][n])
            except:
                Pambval = 100000
            TCnozval = data_new['TCnoz'][n]
            if TCnozval == 'nan':
                newval = 'nan'
            else:
                TCnozval = float(TCnozval)
                newval = nozzleflow * Pstd / Pambval * (TCnozval + 273) / Tstd / 60 * 4 / math.pi / math.pow(NozDiam, 2)
            data_new[name].append(newval)
        print(name + ' recalculated')

        name = 'PMmass'
        # PMmass=PM*F1Flow/MSC/60000000+PMmass_previous
        data_new[name] = []
        updated_channels.append(name)
        newvalprev = 0
        MSC = const_new['MSC(m2/g)']
        for n in range(len(data_old[name])):
            PMval = float(data_new['PM'][n])
            F1Flowval = float(data_new['F1Flow'][n])
            newval = PMval * F1Flowval / MSC / 60000000 + newvalprev
            data_new[name].append(newval)
            newvalprev = newval
        print(name + ' recalculated')

        name = 'DilRat'
        # DilRat=DilFlow/(F1Flow+F2Flow+GasFlow-DilFlow)
        data_new[name] = []
        updated_channels.append(name)
        for n in range(len(data_old[name])):
            F1Flowval = float(data_new['F1Flow'][n])
            try:
                F2Flowval = float(data_new['F2Flow'][n])
            except:
                F2Flowval = 0
            GasFlowval = float(data_new['SampFlow'][n])
            DilFlowval = float(data_new['DilFlow'][n])
            denominator = F1Flowval + F2Flowval + GasFlowval - DilFlowval
            if denominator == 0:
                newval = float(0.001)
            else:
                newval = DilFlowval / (F1Flowval + F2Flowval + GasFlowval - DilFlowval)
            data_new[name].append(newval)
        print(name + ' recalculated')

    ###  possum1.4 and possum1.5 ##############################
    elif firmware_version == 'possum1.4' or firmware_version == 'possum1.5':
        calculated_channels = ['StakVel', 'Nozvel', 'PMmass',
                               'DilRat']  # ,'RedRat','GrnRat','BluRat','RedAbs','GrnAbs','BluAbs'] #define list of calculated channels that are not a function of A and B
        for name in names:
            data_new[name] = []  # initialize a list to fill with the new data series
            if name not in calculated_channels:
                if A_old[name] == A_new[name] and B_old[name] == B_new[name] or math.isnan(A_old[name]) and math.isnan(
                        A_new[name]) and math.isnan(B_old[name]) and math.isnan(
                        B_new[name]):  # if A the B parameter did not change
                    # if A_old[name] == A_new[name] and B_old[name] == B_new[name] : #if A the B parameter did not change
                    data_new[name] = data_old[name]  # copy the old time series to the new time series
                else:  # if A or B did change
                    updated_channels.append(name)
                    # recalculate data values using the following formula: CO=A*(CO_raw+B)
                    for n in range(len(data_old[name])):  # for each point in the old data series
                        oldval = data_old[name][n]  # grab the old value
                        # back-calculate to raw data (ADC bits) using the old cal parameters and then apply new cal parameters
                        newval = A_new[name] * (oldval / A_old[name] - B_old[name] + B_new[name])
                        data_new[name].append(newval)  # append the new value to the new data list
                    print(name, ' updated')

        # calculated channels:
        name = 'StakVel'
        updated_channels.append(name)
        # StakVel=Cp*Kp*sqrt(Pres1*(TCnoz+273)/Pamb/MolWt)
        data_new[name] = []
        Kp = float(129)
        Cpitot = const_new['Cpitot(-)']
        MolWt = const_new['MolWt(g/mol)']
        for n in range(len(data_old[name])):
            Pres1val = float(data_new['Pitot'][n])
            try:
                Pambval = float(data_new['Pamb'][n])
            except:
                Pambval = 100000
            TCnozval = data_new['TCnoz'][n]
            if TCnozval == 'nan':
                newval = 'nan'
            else:
                TCnozval = float(TCnozval)
                if Pres1val < 0:
                    Pres1val = -Pres1val
                    newval = -Cpitot * Kp * math.sqrt(Pres1val * (TCnozval + 273.15) / Pambval / MolWt)
                else:
                    newval = Cpitot * Kp * math.sqrt(Pres1val * (TCnozval + 273.15) / Pambval / MolWt)
            data_new[name].append(newval)
        print(name + ' recalculated')

        name = 'NozVel'  # NozVel=(F1Flow+F2Flow+GasFlow+TAPflow+IsoFlow-DilFlow)*101325/Pamb*(TCnoz+273)/293/60*4/pi/NozDiam^2
        data_new[name] = []
        updated_channels.append(name)
        NozDiam = const_new['NozDiam(mm)']
        for n in range(len(data_old[name])):
            F1Flowval = float(data_new['F1Flow'][n])
            try:
                F2Flowval = float(data_new['F2Flow'][n])
            except:
                F2Flowval = 0
            GasFlowval = float(data_new['SampFlow'][n])
            TAPflowval = float(data_new['TAPflow'][n])
            IsoFlowval = float(data_new['USampFlow'][n])
            DilFlowval = float(data_new['DilFlow'][n])
            nozzleflow = F1Flowval + F2Flowval + GasFlowval + TAPflowval + IsoFlowval - DilFlowval
            try:
                Pambval = float(data_new['Pamb'][n])
            except:
                Pambval = 100000
            TCnozval = data_new['TCnoz'][n]
            if TCnozval == 'nan':
                newval = 'nan'
            else:
                TCnozval = float(TCnozval)
                newval = nozzleflow * Pstd / Pambval * (TCnozval + 273) / Tstd / 60 * 4 / math.pi / math.pow(NozDiam, 2)
            data_new[name].append(newval)
        print(name + ' recalculated')

        name = 'PMmass'
        # PMmass=PM*F1Flow/MSC/60000000+PMmass_previous
        data_new[name] = []
        updated_channels.append(name)
        newvalprev = 0
        MSC = const_new['MSC(m2/g)']
        for n in range(len(data_old[name])):
            PMval = float(data_new['PM'][n])
            F1Flowval = float(data_new['F1Flow'][n])
            newval = PMval * F1Flowval / MSC / 60000000 + newvalprev
            data_new[name].append(newval)
            newvalprev = newval
        print(name + ' recalculated')

        name = 'DilRat'
        # DilRat=DilFlow/(F1Flow+F2Flow+GasFlow+TAPflow-DilFlow)
        data_new[name] = []
        updated_channels.append(name)
        for n in range(len(data_old[name])):
            F1Flowval = float(data_new['F1Flow'][n])
            try:
                F2Flowval = float(data_new['F2Flow'][n])
            except:
                F2Flowval = 0
            GasFlowval = float(data_new['SampFlow'][n])
            TAPflowval = float(data_new['TAPflow'][n])
            DilFlowval = float(data_new['DilFlow'][n])
            denominator = F1Flowval + F2Flowval + GasFlowval + TAPflowval - DilFlowval
            if denominator == 0:
                newval = float(0.001)
            else:
                newval = DilFlowval / (F1Flowval + F2Flowval + GasFlowval + TAPflowval - DilFlowval)
            data_new[name].append(newval)
        print(name + ' recalculated')

        doTAP = 0
        if doTAP != 0:
            name = 'RedRat'
            # RedRat=(red-drk)/(redref-drkref)
            data_new[name] = []
            updated_channels.append(name)
            for n in range(len(data_old[name])):
                val = float(data_new['red'][n])
                refval = float(data_new['redref'][n])
                drkval = float(data_new['drk'][n])
                drkrefval = float(data_new['drkref'][n])
                try:
                    newval = (val - drkval) / (refval - drkrefval)
                except:
                    newval = 'nan'
                data_new[name].append(newval)
            print(name + ' recalculated')

            name = 'GrnRat'
            # RedRat=(red-drk)/(redref-drkref)
            data_new[name] = []
            updated_channels.append(name)
            for n in range(len(data_old[name])):
                val = float(data_new['grn'][n])
                refval = float(data_new['grnref'][n])
                drkval = float(data_new['drk'][n])
                drkrefval = float(data_new['drkref'][n])
                try:
                    newval = (val - drkval) / (refval - drkrefval)
                except:
                    newval = 'nan'
                data_new[name].append(newval)
            print(name + ' recalculated')

            name = 'BluRat'
            # RedRat=(red-drk)/(redref-drkref)
            data_new[name] = []
            updated_channels.append(name)
            for n in range(len(data_old[name])):
                val = float(data_new['blu'][n])
                refval = float(data_new['bluref'][n])
                drkval = float(data_new['drk'][n])
                drkrefval = float(data_new['drkref'][n])
                try:
                    newval = (val - drkval) / (refval - drkrefval)
                except:
                    newval = 'nan'
                data_new[name].append(newval)
            print(name + ' recalculated')

            name = 'RedAbs'
            data_new[name] = []
            updated_channels.append(name)
            spot_area = 0.25281  # cm^2
            dt = float(1 / 60)  # min
            for n in range(len(data_old[name])):
                TAPflowval = float(data_new['TAPflow'][n])
                try:
                    rat = float(data_new['RedRat'][n])
                    ratprev = float(data_new['RedRat'][n - 1])
                    snake = spot_area / TAPflowval / dt / math.pow(10, -8)
                    abs = snake * math.log(ratprev / rat)
                except:
                    abs = 'nan'
                data_new[name].append(abs)
            print(name + ' recalculated')

            name = 'GrnAbs'
            data_new[name] = []
            updated_channels.append(name)
            spot_area = 0.25281  # cm^2
            dt = float(1 / 60)  # min
            for n in range(len(data_old[name])):
                TAPflowval = float(data_new['TAPflow'][n])
                try:
                    rat = float(data_new['GrnRat'][n])
                    ratprev = float(data_new['GrnRat'][n - 1])
                    snake = spot_area / TAPflowval / dt / math.pow(10, -8)
                    abs = snake * math.log(ratprev / rat)
                except:
                    abs = 'nan'
                data_new[name].append(abs)
            print(name + ' recalculated')

            name = 'BluAbs'
            data_new[name] = []
            updated_channels.append(name)
            spot_area = 0.25281  # cm^2
            dt = float(1 / 60)  # min
            for n in range(len(data_old[name])):
                TAPflowval = float(data_new['TAPflow'][n])
                try:
                    rat = float(data_new['RedRat'][n])
                    ratprev = float(data_new['RedRat'][n - 1])
                    snake = spot_area / TAPflowval / dt / math.pow(10, -8)
                    abs = snake * math.log(ratprev / rat)
                except:
                    abs = 'nan'
                data_new[name].append(abs)
            print(name + ' recalculated')
    ###  SB4003.16   ##############################
    elif firmware_version == 'SB4003.16':
        calculated_channels = ['O2_ave']  # define list of calculated channels that are not a function of A and B
        for name in names:
            data_new[name] = []  # initialize a list to fill with the new data series
            if name not in calculated_channels:
                if A_old[name] == A_new[name] and B_old[name] == B_new[name] or math.isnan(A_old[name]) and math.isnan(
                        A_new[name]) and math.isnan(B_old[name]) and math.isnan(
                        B_new[name]):  # if A the B parameter did not change
                    data_new[name] = data_old[name]  # copy the old time series to the new time series
                else:  # if A or B did change
                    updated_channels.append(name)
                    # recalculate data values using the following formula: CO=A*(CO_raw+B)
                    for n in range(len(data_old[name])):  # for each point in the old data series
                        oldval = data_old[name][n]  # grab the old value
                        # back-calculate to raw data (ADC bits) using the old cal parameters and then apply new cal parameters
                        newval = A_new[name] * (oldval / A_old[name] - B_old[name] + B_new[name])
                        data_new[name].append(newval)  # append the new value to the new data list
                    print(name, ' updated')

        # calculated channels:
        name = 'O2_ave'
        changed = 0  # initialize flag to see any values changed
        for n in range(len(data_old[name])):  # for each point in the old data series
            oldval = data_old[name][n]
            newval = (data_new['O2_1'][n] + data_new['O2_2'][n] + data_new['O2_3'][n] + data_new['O2_4'][n]) / 4
            data_new[name].append(newval)  # append the new value to the new data list
            if not math.isclose(oldval, newval,
                                rel_tol=0.005):  # if the value changed (adjust rel_tol to ignore roundoff error)
                changed = 1  # set changed flag
        if changed == 1:
            updated_channels.append(name)

    #################################
    elif firmware_version == 'PEMSPC' or firmware_version == 'Pemspc' or firmware_version == 'pemspc':
        calculated_channels = ['F1Flow', 'F2Flow', 'SampFlow', 'USampFlow', 'DilFlow']
        for name in names:
            data_new[name] = []  # initialize a list to fill with the new data series
            if name not in calculated_channels:
                if A_old[name] == A_new[name] and B_old[name] == B_new[name] or math.isnan(A_old[name]) and math.isnan(
                        A_new[name]) and math.isnan(B_old[name]) and math.isnan(
                        B_new[name]):  # if A the B parameter did not change
                    data_new[name] = data_old[name]  # copy the old time series to the new time series
                else:  # if A or B did change
                    updated_channels.append(name)
                    # recalculate data values using the following formula: CO=A*(CO_raw+B)
                    for n in range(len(data_old[name])):  # for each point in the old data series
                        oldval = data_old[name][n]  # grab the old value
                        # back-calculate to raw data (ADC bits) using the old cal parameters and then apply new cal parameters
                        newval = A_new[name] * (oldval / A_old[name] - B_old[name] + B_new[name])
                        data_new[name].append(newval)  # append the new value to the new data list
                    print(name, ' updated')
        # calculated channels: The following corrections were gained from GP3 3.7.23 at the start of the test when flows are off
        name = 'F1Flow'
        changed = 0  # initialize flag to see any values changed
        for n in range(len(data_old[name])):  # for each point in the old data series
            oldval = data_old[name][n]
            newval = data_old[name][n] - 0.2  # Subtract the offset
            data_new[name].append(newval)  # append the new value to the new data list
            if not math.isclose(oldval, newval,
                                rel_tol=0.005):  # if the value changed (adjust rel_tol to ignore roundoff error)
                changed = 1  # set changed flag
        if changed == 1:
            updated_channels.append(name)

        name = 'F2Flow'
        changed = 0  # initialize flag to see any values changed
        for n in range(len(data_old[name])):  # for each point in the old data series
            oldval = data_old[name][n]
            newval = data_old[name][n] + 0.15909  # Add the offset
            data_new[name].append(newval)  # append the new value to the new data list
            if not math.isclose(oldval, newval,
                                rel_tol=0.005):  # if the value changed (adjust rel_tol to ignore roundoff error)
                changed = 1  # set changed flag
        if changed == 1:
            updated_channels.append(name)

        name = 'SampFlow'
        changed = 0  # initialize flag to see any values changed
        for n in range(len(data_old[name])):  # for each point in the old data series
            oldval = data_old[name][n]
            newval = data_old[name][n] + 0.19545  # Add the offset
            data_new[name].append(newval)  # append the new value to the new data list
            if not math.isclose(oldval, newval,
                                rel_tol=0.005):  # if the value changed (adjust rel_tol to ignore roundoff error)
                changed = 1  # set changed flag
        if changed == 1:
            updated_channels.append(name)

        name = 'USampFlow'
        changed = 0  # initialize flag to see any values changed
        for n in range(len(data_old[name])):  # for each point in the old data series
            oldval = data_old[name][n]
            newval = data_old[name][n] + 0.35  # Add the offset
            data_new[name].append(newval)  # append the new value to the new data list
            if not math.isclose(oldval, newval,
                                rel_tol=0.005):  # if the value changed (adjust rel_tol to ignore roundoff error)
                changed = 1  # set changed flag
        if changed == 1:
            updated_channels.append(name)

        name = 'DilFlow'
        changed = 0  # initialize flag to see any values changed
        for n in range(len(data_old[name])):  # for each point in the old data series
            oldval = data_old[name][n]
            newval = data_old[name][n] + 0.36818  # Add the offset
            data_new[name].append(newval)  # append the new value to the new data list
            if not math.isclose(oldval, newval,
                                rel_tol=0.005):  # if the value changed (adjust rel_tol to ignore roundoff error)
                changed = 1  # set changed flag
        if changed == 1:
            updated_channels.append(name)
    #################################

    else:  # for all other firmware versions without any channels that have special calculations
        for name in names:
            data_new[name] = []  # initialize a list to fill with the new data series
            if A_old[name] == A_new[name] and B_old[name] == B_new[name] or math.isnan(A_old[name]) and math.isnan(
                    A_new[name]) and math.isnan(B_old[name]) and math.isnan(
                    B_new[name]):  # if A the B parameter did not change
                data_new[name] = data_old[name]  # copy the old time series to the new time series
            else:  # if A or B did change
                updated_channels.append(name)
                # recalculate data values using the following formula: CO=A*(CO_raw+B)
                for n in range(len(data_old[name])):  # for each point in the old data series
                    oldval = data_old[name][n]  # grab the old value
                    # back-calculate to raw data (ADC bits) using the old cal parameters and then apply new cal parameters
                    newval = A_new[name] * (oldval / A_old[name] - B_old[name] + B_new[name])
                    data_new[name].append(newval)  # append the new value to the new data list
                print(name, ' updated')

    return data_new, updated_channels

