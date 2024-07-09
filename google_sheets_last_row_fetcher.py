import requests
import requests
import paho.mqtt.client as mqtt
import logging
import json
import re
import logging
import time
import os
from random import randrange
import datetime

from const import VERSION, SLEEP_INTERVAL, IS_CONTAINER, NAMES, COLUMNS, UNIT_OF_MEASUREMENT, DEVICE_CLASS

def replace_periods(ip_address):
    return re.sub(r'\W', '_', ip_address)

class GoogleSheetsLastRowSensor:
    def __init__(self, name):
        name_replace=replace_periods(name)
        self.name = f"googlesheetslastrowfetcher_{name_replace}"
        self.device_class = None
        self.state_topic = f"homeassistant/sensor/googlesheetslastrowfetcher_{name_replace}/state"
        self.unique_id = f"googlesheetslastrowfetcher_{name_replace}"
        self.device = {
            "identifiers": [f"googlesheetslastrowfetcher_{name_replace}"],
            "name": f"Google Sheets Response For {name}"
        }

    def to_json(self):
        return {
            "name": self.name,
            "device_class": self.device_class,
            "state_topic": self.state_topic,
            "unique_id": self.unique_id,
            "device": self.device
        }

if (IS_CONTAINER):
    CONST_MQTT_HOST=os.getenv("MQTT_HOST","earthquake.832-5.jp")
    CONST_MQTT_PASSWORD=os.getenv("MQTT_PASSWORD","earthquake")
    CONST_MQTT_USERNAME=os.getenv("MQTT_USERNAME","japan")
    CONST_SLEEP_INTERVAL=os.getenv("SLEEP_INTERVAL",SLEEP_INTERVAL)
    CONST_GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY","AIzaSyCrHqwbt8hAxuTXFcPlb6mt0nGljXA7NDs")
    CONST_GOOGLE_SPREADSHEET_ID=os.getenv("GOOGLE_SPREADSHEET_ID","1z4TW2HLZrD3obstC3ICqzxOPAZXwZzeoo7jsix9PWEo")


def get_spreadsheet_values(column_name):
    range_name = column_name
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{CONST_GOOGLE_SPREADSHEET_ID}/values/{range_name}?alt=json&key={CONST_GOOGLE_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        values = response.json().get('values', [])

        if not values:
            print('No data found.')
            return 'No data found.'
        else:
            last_row = len(values)
           # print(f"{last_row}, {values[-1]}")
            return values[-1]
    except requests.exceptions.HTTPError as err:
        print(err)
        return str(err)

# Example usage:
if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.info(f"I am google_sheets_last_row_fetcher running version {VERSION}")
    print(f"I am google_sheets_last_row_fetcher running version {VERSION}")
 #   initialize()
    COLUMNS_LIST=COLUMNS.split(',')
    DEVICE_CLASS_LIST=DEVICE_CLASS.split(',')
    UNIT_OF_MEASUREMENT_LIST=UNIT_OF_MEASUREMENT.split(',')

    while True:
        count = 0
        for sensor in NAMES.split(','):

            last_value = get_spreadsheet_values(COLUMNS_LIST[count])
            print(f"{sensor} -> {last_value[0]} {DEVICE_CLASS_LIST[count]} {UNIT_OF_MEASUREMENT_LIST[count]}")
            count = count + 1

        logger.info(f"It is {datetime.datetime.now()} .. I am sleeping for {CONST_SLEEP_INTERVAL}")
        print(f"It is {datetime.datetime.now()} ... I am sleeping for {CONST_SLEEP_INTERVAL}")
        time.sleep(SLEEP_INTERVAL)
