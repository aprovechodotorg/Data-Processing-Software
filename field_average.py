
import LEMS_DataProcessing_IO as io
import csv

inputpath = 'C:\\Users\\Jaden\\Documents\\GitHub\\2023_1_24_7_36_22_RealtimeISO.csv'
outputpath = 'C:\\Users\\Jaden\\Documents\\GitHub\\2023_1_24_7_36_22_average.csv'

def field_average(inputpath, outputpath):
    # read in raw data file
    [names, units, data] = io.load_timeseries(inputpath)

    #avg_names = names
    #avg_names.remove('time')
    #avg_names.remove('seconds')
    #avg_names.remove('ID')


    for name in names: #Read in realtime data and average each, skip over time stamp and ID values
        try:
            # Average from the first time stamp to the last
            #NOTE: Change to time entry ID
            avg = (sum(data[name])) / (data['seconds'][-1] - data['seconds'][0])
            data[name] = avg
        except:
            names.remove(name)
            del data[name]
            del units[name]

    ##########################################################
    #ISO standard averages: Average the PPM measurement and calc all others from that
    P = 101325  # standard pressure Pa
    MWco = 28.01  # molecular weight CO g/mol
    MWco2 = 44.01 # molecular weight CO2 g/mol
    MWc = 12.01 # molecular weight C g/mol
    R = 8.314  # ideal gas constant m^3Pa/K/mal
    T = 293.15  # standard temperature K

    Cco_ISOavg = (data['COhi'] * P * MWco) / (1000000 * R * T)
    Cco2_ISOavg = (data['CO2hi'] * P * MWco2) / (1000000 * R * T)
    Cc_ISOavg = (Cco_ISOavg * (MWc/MWco)) + (Cco2_ISOavg * (MWc/MWco2))
    ERCco_ISOavg = Cco_ISOavg / Cc_ISOavg
    ERCco2_ISOavg = Cco2_ISOavg / Cc_ISOavg
    Cfrac = 0.5
    EFcomass_ISOavg = ERCco_ISOavg * Cfrac * 1000
    EFco2mass_ISOavg = ERCco2_ISOavg * Cfrac * 1000
    EHV = 15431  # effective heating value MJ/kg TEMPORARY VALUE
    EFcoenergy_ISOavg = (data['EFcoenergy'] * Cfrac * 1000) / EHV
    EFco2energy_ISOavg = (data['EFco2energy'] * Cfrac * 1000) / EHV


    names.append('Cco_ISOavg')
    names.append('Cco2_ISOavg')
    names.append('Cc_ISOavg')
    names.append('EFcomass_ISOavg')
    names.append('EFco2mass_ISOavg')
    data['Cco_ISOavg'] = Cco_ISOavg
    data['Cco2_ISOavg'] = Cco2_ISOavg
    data['Cc_ISOavg'] = Cc_ISOavg
    data['EFcomass_ISOavg'] = EFcomass_ISOavg
    data['EFco2mass_ISOavg'] = EFco2mass_ISOavg
    units['Cco_ISOavg'] = 'g/m^3'
    units['Cco2_ISOavg'] = 'g/m^3'
    units['Cc_ISOavg'] = 'g/m^3'
    units['EFcomass_ISOavg'] = 'g/kg'
    units['EFco2mass_ISOavg'] = 'g/kg'

    names.append('EFcoenergy_ISOavg')
    names.append('EFco2energy_ISOavg')
    data['EFcoenergy_ISOavg'] = EFcoenergy_ISOavg
    data['EFco2energy_ISOavg'] = EFco2energy_ISOavg
    units['EFcoenergy_ISOavg'] = 'g/MJ'
    units['EFco2energy_ISOavg'] = 'g/MJ'

    names.remove('seconds')
    names.remove('ID')
    del data['seconds']
    del data['ID']
    del units['seconds']
    del units['ID']


    total = []

    for name in names:
        list = []
        list.append(name)
        list.append(units[name])
        list.append(data[name])
        total.append(list)

    #with open(outputpath, 'w', newline='') as csvfile:
        #writer = csv.DictWriter(csvfile, fieldnames=names)
        #writer.writeheader()
        #writer = csv.writer(csvfile)
        #for key, value in data.items():
                #writer.writerow([key, value])

    with open(outputpath, 'w', newline='') as csvfile:
        write = csv.writer(csvfile)
        write.writerows(total)


#####################################################################
#the following two lines allow this function to be run as an executable
if __name__ == "__main__":
    field_average(inputpath, outputpath)



