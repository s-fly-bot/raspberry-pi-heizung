#!/usr/bin/env python
# -*- coding: utf-8 -*-
debug_output = True

import simplejson
import urllib
import datetime
import time
import platform
import os, sys
from ConfigParser import SafeConfigParser
# import logging

_config_file = pathname = os.path.dirname(sys.argv[0]) + "/etc/heizung.ini"
parser = SafeConfigParser()
parser.read(_config_file)

url = parser.get('heizung', 'url')

raspberry = False
if 'raspberrypi' in platform.uname():
    # global raspberry
    raspberry = True
    import RPi.GPIO as GPIO

    RelaisHeizung = 23
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RelaisHeizung,  GPIO.OUT)
    GPIO.output(RelaisHeizung,  GPIO.LOW)


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


def start_kessel():
    if raspberry:
        GPIO.output(RelaisHeizung, GPIO.HIGH)
    else:
        print "..test...:",
    print "START_KESSEL"


def stop_kessel():
    if raspberry:
        GPIO.output(RelaisHeizung, GPIO.LOW)
    else:
        print "...test...:",
    print "STOP_KESSEL"


def getMeasurementsFromHttp():
    response = urllib.urlopen(url)
    data = simplejson.loads(response.read())
    return data[-20:]


def getTimeDifferenceFromNow(timestamp):
    """ :return minutes from now """
    timeDiff = datetime.datetime.now() - datetime.datetime.fromtimestamp(timestamp)
    return int(timeDiff.total_seconds() / 60)


def check_measurements():
    start_kessel = "--"
    print "-"*77
    print "------------- New Test on Measurements: %s -----------------" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print "-"*77

    data = getMeasurementsFromHttp()

    if debug_output:
        heizungs_dict = dict(zip(fields, data[-1]))
        for key, val in sorted(heizungs_dict.items()):
            print '  {0:25} : {1:}'.format(key, val)
        print '  {0:25} : {1:}'.format('datetime',
                                        datetime.datetime.fromtimestamp(heizungs_dict['timestamp']).strftime(
                                            '%Y-%m-%d %H:%M:%S'))
        print "-"*77

    start_list = {}
    for l in data:
        print datetime.datetime.fromtimestamp(l[0]).strftime('%Y-%m-%d %H:%M:%S'),
        heizungs_dict = dict(zip(fields, l))
        minutes_ago_since_now = getTimeDifferenceFromNow(heizungs_dict['timestamp'])
        start_kessel = "--"
        print heizungs_dict['heizung_d'], heizungs_dict['d_heizung_pumpe'], heizungs_dict['heizung_vl']-heizungs_dict['heizung_rl'],
        if heizungs_dict['speicher_3_kopf'] < 35 and heizungs_dict['speicher_4_mitte'] < 30 and heizungs_dict['speicher_5_boden'] < 30:
            if heizungs_dict['heizung_vl']-heizungs_dict['heizung_rl'] <= 2:
                # if heizungs_dict['heizung_d'] == 0:
                #if minutes_ago_since_now < 15: # only if messurements are not so long ago
                    start_kessel = "ON"
        start_list[minutes_ago_since_now]=start_kessel
        print start_kessel,
        print minutes_ago_since_now,
        print l
    print "-" * 77

    # check if kessel start is necessary:
    for minutes_ago_since_now, start in start_list.iteritems():
        if minutes_ago_since_now < 20 and start == "ON":
            start_kessel = "ON"
            break
        else:
            start_kessel = "--"

    return start_kessel


def main():
    while True:
        if check_measurements() == "ON":
            start_kessel()
        else:
            stop_kessel()

        time.sleep(60)


if __name__ == '__main__':
    main()
