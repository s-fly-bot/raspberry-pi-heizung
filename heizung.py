#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson
import urllib2
import datetime
from time import gmtime, strftime, time, sleep
import platform
from ConfigParser import SafeConfigParser
import logging
from logging import config
import sys, os
from htmldom import htmldom
import requests
import re
import html
import json


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

print("config heizung: ", _config_file)
print("config logger : ", _config_logger)

parser = SafeConfigParser()
parser.read(_config_file)
url = parser.get('heizung', 'url')
url_internal = parser.get('heizung', 'url_internal')
blnet_host = parser.get('heizung', 'blnet_host')
operating_mode = parser.get('heizung', 'operating_mode')

log2log = parser.get('heizung', 'logger')

print("print2logger  : ", log2log)

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


def logmessage(message):
    if log2log == "True":
        logger.info(message)
    else:
        print(message)

logmessage("+-----  S T A R T  ----------------------------------")
logmessage("|   %r" % strftime("%Y-%m-%d %H:%M:%S", gmtime()))
logmessage("+----------------------------------------------------")

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

def getResonseResult(url):
    request = urllib2.Request(url)
    response = urllib2.urlopen(request, timeout=30)
    response_result = response.read()

    return response_result

def transferData():
    """
    This method transfers the data from uvr1611 to the api of same project to hosting server
    """
    logmessage('+------------------ transfer data from uvr1611 ------------------------')
    try:
        if raspberry:
#            response = urllib.urlopen(url_internal)
#            data = response.read()

            data = getResonseResult(url_internal)

            if data == "[]":
                message = "| OK: []"
            else:
                message = "| response is not what expected"
        else:
            message="| i'm not on raspberry..."
        logmessage(message)

    except:
        logger.error("| something went wrong while retrieving from %s" % url_internal)

    logmessage('+----------------- transfer done -------------------------------------')


def getMeasurementsFromHttp():
    response = getResonseResult(url)
    data = ''
    if response:
        data = simplejson.loads(response)[-20:]
    return data


def getMeasurementsFromUVR1611():
    # Ausgaenge / not only digital ones
    r = requests.get(
        'http://' + blnet_host + "/580600.htm",
    )

    # Parse  DOM object from HTMLCode
    dom = htmldom.HtmlDom().createDom(r.text)
    # get the element containing the interesting information
    dom = dom.find("div.c")[1]

    # filter out the text
    raw = dom.text().replace('&nbsp;', '')

    # build sections by id
    sections=[]
    section=[]
    for line in raw.split("\n"):
        if not line:
            continue
        if line[0].isdigit():
            if section:
                # sections.append("\n".join(section))
                sections.append(section)
                section=[]
        section.append(line)

    sections.append("\n".join(section))  # grab the last one

    sections = sections[1:11]

    ausgaenge_dict = {}
    raw_ausgaenge_dict = {}

    regex_speed      = re.compile('Drehzahlst.:(?P<speed>\d+)')
    regex_mode_value = re.compile('(?P<mode>(AUTO|HAND))/(?P<value>(AUS|EIN))')
    regex_auf_zu     = re.compile('(?P<mode>(auf|zu)):(?P<value>(AUS|EIN))')

    for num, section in enumerate(sections):
        #  print(num, '=' * 50)
        first_line = True
        speed = None
        mode = None
        value = None
        for line in section:
            if first_line:
                # print("line : ", line)
                id, name = line.split(':', 1)
                first_line = False
            if int(id) < 8:
                match = regex_mode_value.search(line)
                if match:
                    # print(match.groups())
                    mode = match.group('mode')
                    value = match.group('value')
            else:
                match = regex_auf_zu.search(line)
                if match:
                    # print(match.groups())
                    mode = match.group('mode')
                    value = match.group('value')

            if int(id) in [2 , 6, 7]:
                match = regex_speed.search(line)
                if match:
                    speed=match.group('speed')

        raw_ausgaenge_dict[id]={'id': id, 'name': name, 'mode': mode, 'value': value, 'speed': speed}

    result_dict={}
    for id in raw_ausgaenge_dict.keys():
        if int(id) in [2, 6, 7]:
            result_dict[fields_dict_aus[id+':speed']] = raw_ausgaenge_dict[id]['speed']
        if raw_ausgaenge_dict[id]['value'] == 'AUS':
            value = 0
        else:
            value = 1
        result_dict[fields_dict_aus[id]] = value

    """
    Reads all analog values (temperatures, speeds) from the web interface
    and returns list of quadruples of id, name, value, unit of measurement
    """
    r = requests.get(
        'http://' + blnet_host + "580500.htm",
    )

    # Parse  DOM object from HTMLCode
    dom = htmldom.HtmlDom().createDom(r.text)
    # get the element containing the interesting information
    dom = dom.find("div.c")[1]
    # filter out the text
    data_raw = dom.text()

    # collect data in an array
    data = list()

    # search for data by regular expression
    match_iter = re.finditer(
        "(?P<id>\d+):&nbsp;(?P<name>.+)\n" +
        "(&nbsp;){3,6}(?P<value>[^ ]+) " +
        "(?P<unit_of_measurement>.+?)&nbsp;&nbsp;PAR?", data_raw)
    match = next(match_iter, False)
    # parse a dict of the match and save them all in a list
    while match:
        match_dict = match.groupdict()
        # convert html entities to unicode characters
        for key in match_dict.keys():
            match_dict[key] = html.unescape(match_dict[key])
            # also replace decimal "," by "."
            match_dict[key] = match_dict[key].replace(",", ".")
        # and append formatted dict
        data.append(match_dict)
        match = next(match_iter, False)

    for values in data:
        result_dict[fields_dict_ein[values['id']]] = values['value']
    return result_dict

def pushDataToHosting(data):
    """
    Will send data to uvr1611 api to hosting server
    :param data:
    :return:
    """
    pass

def getTimeDifferenceFromNow(timestamp):
    """ :return minutes from now """
    timeDiff = datetime.datetime.now() - datetime.datetime.fromtimestamp(timestamp)
    return int(timeDiff.total_seconds() / 60)


def check_measurements(data=None):
    logmessage("-"*77)
    logmessage("------------- New Test on Measurements: %s -----------------" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logmessage("-"*77)

    if data is None or len(data) == 0:
        data = getMeasurementsFromHttp()

    start_kessel = "--"
    start_list = {}

    try:
        heizungs_dict = dict(zip(fields, data[-1]))
        for key, val in sorted(heizungs_dict.items()):
            logmessage('  {0:25} : {1:}'.format(key, val))
        logmessage('  {0:25} : {1:}'.format('datetime',
                                        datetime.datetime.fromtimestamp(heizungs_dict['timestamp']).strftime(
                                            '%Y-%m-%d %H:%M:%S')))
        logmessage("-"*77)

        for l in data:
            heizungs_dict = dict(zip(fields, l))
            minutes_ago_since_now = getTimeDifferenceFromNow(heizungs_dict['timestamp'])
            start_kessel = "--"

            if heizungs_dict['speicher_3_kopf'] < 35 and heizungs_dict['speicher_4_mitte'] < 30 and heizungs_dict['speicher_5_boden'] < 30:
                if heizungs_dict['heizung_vl']-heizungs_dict['heizung_rl'] <= 2:
                    # if heizungs_dict['heizung_d'] == 0:
                    #if minutes_ago_since_now < 15: # only if messurements are not so long ago
                        start_kessel = "ON"

            if heizungs_dict['speicher_3_kopf'] < 29 and heizungs_dict['speicher_4_mitte'] < 29 and heizungs_dict['speicher_5_boden'] < 29:
                start_kessel = "ON"

            # but if solar rediation is going up..*[]:
            # be optimistic that enough hot water will be produced
            # TODO
            # start_kessel = "--"

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
    if len(sys.argv) > 1 and sys.argv[1] == 'ON':
        logmessage("Start burn-off per comandline...")
        start_kessel()
        logmessage("manually start done....")
        time.sleep(5)
        # better wait some time?
        stop_kessel()

    else:
        while True:
            start = time()
            data=[]
            try:
                data = getMeasurementsFromUVR1611()
                pushDataToHosting(data)

            except:
                logmessage(("Unexpected error in getMeasurementsFromUVR1611(): ", sys.exc_info()[0]))

            # old way to transfer the data to uvr1611
            # Todo implement api call for new "data"
            transferData()

            if operating_mode == 'lumber':
                if check_measurements(data) == "ON":
                    start_kessel()
                else:
                    stop_kessel()
            elif operating_mode == 'pellets':
                pass

            end = time()

            seconds_processing = end - start
            to_sleep = 60 - seconds_processing
            if seconds_processing > 0:
                sleep(to_sleep)  # sleeping time in seconds

if __name__ == '__main__':
    main()
