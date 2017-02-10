#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson
import urllib
import datetime
import time
import platform
from ConfigParser import SafeConfigParser
import logging
from logging import config
import sys, os

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

# Set up a specific logger with our desired output level
_config_path = os.path.abspath(os.path.dirname(sys.argv[0]))
_config_file = _config_path + "/etc/heizung.conf"
_config_logger = _config_path+'/etc/logging.conf'

print "config heizung: ", _config_file
print "config logger : ", _config_logger

parser = SafeConfigParser()
parser.read(_config_file)
url = parser.get('heizung', 'url')
log2log = parser.get('heizung', 'logger')

print "print2logger  : ", log2log

logging.config.fileConfig(_config_logger)
logger = logging.getLogger('heizung')
logger.propagate = False

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


def logmessage(message):
    if log2log == "True":
        logger.info(message)
    else:
        print message


def start_kessel():
    message = ""
    if raspberry:
        GPIO.output(RelaisHeizung, GPIO.HIGH)
    else:
        message = "...test...: "
    message += "START_KESSEL"
    logmessage(message)


def stop_kessel():
    message = ""
    if raspberry:
        GPIO.output(RelaisHeizung, GPIO.LOW)
    else:
        message = "...test...: "
    message += "STOP_KESSEL"
    logmessage(message)


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
    logmessage("-"*77)
    logmessage("------------- New Test on Measurements: %s -----------------" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logmessage("-"*77)

    data = getMeasurementsFromHttp()

    try:
        heizungs_dict = dict(zip(fields, data[-1]))
        for key, val in sorted(heizungs_dict.items()):
            logmessage('  {0:25} : {1:}'.format(key, val))
        logmessage('  {0:25} : {1:}'.format('datetime',
                                        datetime.datetime.fromtimestamp(heizungs_dict['timestamp']).strftime(
                                            '%Y-%m-%d %H:%M:%S')))
        logmessage("-"*77)

        start_list = {}
        for l in data:
            heizungs_dict = dict(zip(fields, l))
            minutes_ago_since_now = getTimeDifferenceFromNow(heizungs_dict['timestamp'])
            start_kessel = "--"
            if heizungs_dict['speicher_3_kopf'] < 35 and heizungs_dict['speicher_4_mitte'] < 30 and heizungs_dict['speicher_5_boden'] < 30:
                if heizungs_dict['heizung_vl']-heizungs_dict['heizung_rl'] <= 2:
                    # if heizungs_dict['heizung_d'] == 0:
                    #if minutes_ago_since_now < 15: # only if messurements are not so long ago
                        start_kessel = "ON"
            start_list[minutes_ago_since_now]=start_kessel
            logmessage("%r %r %r %.1f %r %r %r" % (
                  datetime.datetime.fromtimestamp(l[0]).strftime('%Y-%m-%d %H:%M:%S')
                , heizungs_dict['heizung_d']
                , heizungs_dict['d_heizung_pumpe']
                , heizungs_dict['heizung_vl']-heizungs_dict['heizung_rl']
                , start_kessel
                , minutes_ago_since_now
                , l
            ))
    except IndexError:
        logmessage("-"*77)
        logmessage("there is nothing to examine...")
    logmessage("-"*77)

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
