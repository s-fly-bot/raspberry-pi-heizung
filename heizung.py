#!/usr/bin/env python
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
from ta.get_measurements import getMeasurementsFromUVR1611
from ta.fieldlists import fields
# import html
# import json


raspberry = False
if 'raspberrypi' in platform.uname():
    # global raspberry
    raspberry = True
    import RPi.GPIO as GPIO

    # gpio 4 = BCM 23 = Pin 16
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
url             = parser.get('heizung', 'url')
url_internal    = parser.get('heizung', 'url_internal')
blnet_host      = parser.get('heizung', 'blnet_host')
operating_mode  = parser.get('heizung', 'operating_mode')

log2log = parser.get('heizung', 'logger')

print("print2logger  : ", log2log)

logging.config.fileConfig(_config_logger)
logger = logging.getLogger('heizung')
logger.propagate = False


def logmessage(message):
    if log2log == "True":
        logger.info(message)
    else:
        print(message)

logmessage("+-----  S T A R T  ----------------------------------")
logmessage("|   %r" % strftime("%Y-%m-%d %H:%M:%S", gmtime()))
logmessage("+----------------------------------------------------")
logmessage("| operation mode: %s" % operating_mode)


def start_firing():
    """
    closes the relay which start the wood gasifier in firewood mode
    closes the relay which start/keep burning the wood gasifier in pellets mode
    :return:
    """
    message = ""
    if raspberry:
        GPIO.output(RelaisHeizung, GPIO.HIGH)
    else:
        message = "doing : "
    message += "START_KESSEL"
    logmessage(message)


def stop_firing():
    """
    stops burning in pellets mode, stop starting in firewood mode
    :return:
    """
    message = ""
    if raspberry:
        GPIO.output(RelaisHeizung, GPIO.LOW)
    else:
        message = "doing : "
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


def pushDataToHosting(data):
    """
    Will send data to uvr1611 api to hosting server
    :param data:
    :return:
    """
    pass


def getMeasurementsFromHttp():
    response = getResonseResult(url)
    data = ''
    if response:
        data = simplejson.loads(response)[-20:]
    return data


def getTimeDifferenceFromNow(timestamp):
    """ :return minutes from now """
    timeDiff = datetime.datetime.now() - datetime.datetime.fromtimestamp(timestamp)
    return int(timeDiff.total_seconds() / 60)


def check_measurements(uvr_direct_data=None):
    logmessage("-"*77)
    logmessage("------------- New Test on Measurements: %s -----------------" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logmessage("-"*77)

    if uvr_direct_data is None or len(uvr_direct_data) == 0:
        data = getMeasurementsFromHttp()
    else:
        data = [uvr_direct_data]

    do_firing = "OFF"
    start_list = []

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
            do_firing = "--"
            spread = heizungs_dict['heizung_vl'] - heizungs_dict['heizung_rl']

            if heizungs_dict['speicher_3_kopf'] < 29 \
                    and heizungs_dict['speicher_4_mitte'] < 29 \
                    and heizungs_dict['speicher_5_boden'] < 29:
                do_firing = "ON"

            elif heizungs_dict['speicher_3_kopf'] < 35 \
                    and heizungs_dict['speicher_4_mitte'] < 30 \
                    and heizungs_dict['speicher_5_boden'] < 30 \
                    and spread <= 2:
                    # if heizungs_dict['heizung_d'] == 0:
                    #if minutes_ago_since_now < 15: # only if messurements are not so long ago
                        do_firing = "ON"

            if heizungs_dict['speicher_5_boden'] > 75:
                do_firing = "OFF"

            # for a very sunny day exeception should be made here:
            # be optimistic that enough hot water will be produced
            if heizungs_dict['solar_strahlung'] > 400:
                do_firing = "OFF"

            if minutes_ago_since_now < 20:
                start_list.append(do_firing)

            logmessage("%r %r %r %.1f %r %r %r" % (
                  datetime.datetime.fromtimestamp(l[0]).strftime('%Y-%m-%d %H:%M:%S')
                , heizungs_dict['heizung_d']
                , heizungs_dict['d_heizung_pumpe']
                , spread
                , do_firing
                , minutes_ago_since_now
                , l
            ))
    except IndexError:
        logmessage("-"*77)
        logmessage("there is nothing to examine...")
    logmessage("-"*77)

    # check if wood gasifier start is necessary:
    if "OFF" in start_list or not start_list:
        do_firing = "OFF"
    elif "ON" in start_list:
        do_firing = "ON"
    else:
        do_firing = "--"

    return do_firing


def main():
    # blnet = getMeasurementsFromUVR1611(blnet_host, timeout=(3.05, 5), password=None)

    firing_start = None

    # for secure reason stop when started
    stop_firing()

    # this is only for operating_mode firewood!
    if len(sys.argv) > 1 and sys.argv[1] == 'ON':
        logmessage("Start burn-off per comandline...")
        start_firing()
        logmessage("manually start done....")
        sleep(5)
        # better wait some time?
        stop_firing()

    else:
        while True:
            start = time()
            data = []

            # try:
            #     data, result_dict = blnet.get_measurements()
            #     # Todo: pushDataToHosting(data)
            #
            # except:
            #     logmessage(("Unexpected error in getMeasurementsFromUVR1611(): ", sys.exc_info()[0]))
            #     try:
            #         blnet.log_in()
            #     except:
            #         pass

            # old way to transfer the data to uvr1611
            if raspberry:
                transferData()

            result = check_measurements(data)

            if operating_mode == 'firewood':
                if result == "ON":
                    start_firing()
                else:
                    stop_firing()

            elif operating_mode == 'pellets':
                if result == "ON":
                    if firing_start is None:
                        firing_start = time()
                        # start_firing()
                elif result == 'OFF':
                    stop_firing()

                    if firing_start:
                        firing_start = None

                        message = "combustion time: %r hours" % (firing_start - time())/3600
                        logmessage(message)
                    pass
                else: # result == '--'
                    pass

                pass
            end = time()

            seconds_processing = end - start
            to_sleep = 60 - seconds_processing
            if seconds_processing > 0:
                sleep(to_sleep)  # sleeping time in seconds

if __name__ == '__main__':
    main()
