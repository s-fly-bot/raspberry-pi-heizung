from blnet_web import BLNETWeb
import requests
from htmldom import htmldom
import re
from time import time
from fieldlists import fields, fields_dict_aus, fields_dict_ein
import six

class getMeasurementsFromUVR1611(BLNETWeb):
    def __init__(self, blnet_host, timeout=5, password=None):
        BLNETWeb.__init__(self, blnet_host, timeout=timeout, password=password)

    def get_measurements(self):
        # ensure to be logged in
        if not self.log_in():
            return None

        # Ausgaenge / not only digital ones
        try:
            r = requests.get(
                self.ip + "/580600.htm",
                headers=self.cookie_header(),
                timeout=self._timeout)
        except requests.exceptions.RequestException:
            return None

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
        try:
            r = requests.get(
                self.ip + "/580500.htm",
                headers=self.cookie_header(),
                timeout=self._timeout)
        except requests.exceptions.RequestException:
            return None

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
                # Todo this works only in py3 match_dict[key] = html.unescape(match_dict[key])
                # also replace decimal "," by "."
                match_dict[key] = match_dict[key].replace(",", ".").replace('&nbsp;', '')
            # and append formatted dict
            data.append(match_dict)
            match = next(match_iter, False)

        for values in data:
            result_dict[fields_dict_ein[values['id']]] = values['value']

        data = []
        for key in fields:
            if key == 'timestamp':
                data.append(int(time()))
            else:
                value = result_dict[key]
                if isinstance(value, six.string_types):
                    # It's a string !!
                    if '.' in value:
                        value = float(result_dict[key])
                    else:
                        value = int(result_dict[key])
                data.append(value)

        return data, result_dict
