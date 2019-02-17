fields = [
### ANALOG ####
    'timestamp',
    'kessel_rl',
    'kessel_d_ladepumpe',
    'kessel_betriebstemperatur',
    'speicher_ladeleitung',
    'aussentemperatur',
    'raum_rasp',
    'speicher_1_kopf',
    'speicher_2_kopf',
    'speicher_3_kopf',
    'speicher_4_mitte',
    'speicher_5_boden',
    'heizung_vl',
    'heizung_rl',
    'heizung_d',
    'solar_strahlung',
    'solar_vl',
    'solar_d_ladepumpe',

### DIGITAL ####
    'd_heizung_pumpe',
    'd_kessel_ladepumpe',
    'd_kessel_freigabe',
    'd_heizung_mischer_auf',
    'd_heizung_mischer_zu',
    'd_kessel_mischer_auf',
    'd_kessel_mischer_zu',
    'd_solar_kreispumpe',
    'd_solar_ladepumpe',
    'd_solar_freigabepumpe']

fields_dict_ein = {
### ANALOG ####
    '9': 'kessel_rl',
    '7': 'kessel_betriebstemperatur',
    '6': 'speicher_ladeleitung',
    '1': 'aussentemperatur',
    '8': 'raum_rasp',
    '2': 'speicher_1_kopf',
    '3': 'speicher_2_kopf',
    '4': 'speicher_3_kopf',
    '16': 'speicher_4_mitte',
    '5': 'speicher_5_boden',
    '10': 'heizung_vl',
    '11': 'heizung_rl',
    '15': 'solar_strahlung',
    '13': 'solar_vl'
}

fields_dict_aus = {
    '2:speed': 'kessel_d_ladepumpe',
    '6:speed': 'heizung_d',
    '7:speed': 'solar_d_ladepumpe',
    '6': 'd_heizung_pumpe',
    '2': 'd_kessel_ladepumpe',
    '5': 'd_kessel_freigabe',
    '10': 'd_heizung_mischer_auf',
    '11': 'd_heizung_mischer_zu',
    '8': 'd_kessel_mischer_auf',
    '9': 'd_kessel_mischer_zu',
    '4': 'd_solar_kreispumpe',
    '3': 'd_solar_ladepumpe',
    '7': 'd_solar_freigabepumpe'}
