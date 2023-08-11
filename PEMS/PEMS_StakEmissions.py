import math
def PEMS_StakEmissions(data, gravmetric, emetric, names, units, eunits):
    #####################################################################
    # Volumetric flow rate/stack flow rate for PM
    # Currently not handling bkg but taking in bkg subtracted data

    R = 3.14 #Universal gas constant (m^3Pa/mol/K)
    Cp = 1 #J/g/K heat capacity of flue gas
    Tstd = 293 #standard temperature in K
    Pstd = 101325 #standard pressure in Pa

    #Stak species for emission rate eval
    stak_species = ['CO', 'CO2', 'H2O', 'O2', 'N2']

    #Convert to actual conditions from standard
    name = 'Stak_PM' #chimney concentration
    names.append(name)
    units[name] = 'mg/m^3'
    data[name] = []

    '''
    for n, val in enumerate(data['PM']):
        msc = gravmetric['MSC']
        PMstd = val / msc.n / 1000000 #standard condition Mm^-1 to m^-1
        PMstak = PMstd * Tstd / (data['TCnoz'][n] + 273) * data['Pamb'][n] / Pstd #Ideal gas law to convert standard to real
        data[name].append(PMstak)
    '''

    for n, val in enumerate(data['DilFlow']):
        #pmconcstd = data['PM'][n]/gravmetric['MSC']/1000000 #at standard condition convert from Mm^-1 to m^-1
        #pmcon = pmconcstd * Tstd / (data['TCnoz'][n] + 273) * data['Pamb'][n] / Pstd #ideal gas law and pressure correction: Cstak = Cstd * Tstd / Tstak *Pstak/Pstd
        stakstd = gravmetric['PMconc_tot'] / (1 - (val / (data['SampFlow'][n] + data['F1Flow'][n]))) #Could be F2 for some tests
        stak = stakstd * Tstd / (data['TCnoz'][n] + 273) * data['Pamb'][n] / Pstd #Add const Pamb for PEMS
        data[name].append(stak.n)

    if eunits['stak_dia'] == 'in' or eunits['stak_dia'] == 'inch' or eunits['stak_dia'] == 'In' or eunits['stak_dia'] == 'Inch':
        rad = (emetric['stak_dia'].n * 0.0254) / 2  # Inch to meter
    elif eunits['stak_dia'] == 'cm':
        rad = emetric['stak_dia'].n / 100 #cm to m
    elif eunits['stak_dia'] == 'mm':
        rad = emetric['stak_dia'].n / 1000 #mm to m
    area = math.pi * pow(rad, 2)  # m^2

    #Volumetric flow rate
    name = 'VolFlow'
    units[name] = 'm^3/s'
    names.append(name)
    data[name] = []
    vel_default = 1
    for n, val in enumerate(data['StakVel']):
        try:
            flow = val * area * emetric['velocity_pro'] #Velocity profile input in energy inputs
        except:
            flow = val * area * vel_default #Use default if not entered
            default = 1
        data[name].append(flow)
    if default == 1:
        line = 'No velocity profile found in Energy Inputs. Using default value of: ' + str(vel_default)
        print(line)

    #Calculate density
    name = 'StakDensity'
    names.append(name)
    units[name] = 'g/m^3'
    data[name] = []
    for n, val in enumerate(data['MW']):
        dens = (val * data['Pamb'][n]) / (data['TCnoz'][n] + 273) / 1000000 / R
        data[name].append(dens)

    #Calculate mass flow
    name = 'MassFlow'
    names.append(name)
    units[name] = 'g/s'
    data[name] = []
    for n, val in enumerate(data['VolFlow']):
        mflow = val * data['StakDensity'][n]
        data[name].append(mflow)

    #Calculate energy flow
    name = 'EnergyFlow'
    names.append(name)
    units[name] = 'W'
    data[name] = []
    for n, val in enumerate(data['MassFlow']):
        dT = data['TC2'][n] - data['COtemp'][n] #TSamp in R code
        qdot = Cp * val * dT
        data[name].append(qdot)

    #Gas emission rates
    for gas in stak_species:
        stakname = gas + 'stak'
        ername = 'ER' + stakname
        names.append(ername)
        units[ername] = 'g/hr'
        data[ername] = []
        for n, val in enumerate(data['VolFlow']):
            vconc = data[stakname][n] / 100 #fraction vol conc
            mconc = vconc * data['Pamb'][n] / (data['TCnoz'][n] + 273) / R #Mass concentration (g/m^3)
            er = val * mconc * 3600 #g/hr
            data[ername].append(er)

    #Emission rate PM
    name = 'ERPMstak'
    names.append(name)
    units[name] = 'g/hr'
    data[name] = []
    for n, val in enumerate(data['VolFlow']):
        #print(len(data['VolFlow']))
        #print(len(data['Stak_PM']))
        #print(n)
        mconc = data['Stak_PM'][n] / 1000 #mg/m^3 to g/m^3
        er = val * mconc * 3600 #g/hr
        data[name].append(er)

    return data, names, units
