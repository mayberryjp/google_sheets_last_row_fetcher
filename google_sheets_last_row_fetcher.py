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

from const import VERSION, SLEEP_INTERVAL, IS_CONTAINER
if (IS_CONTAINER):
    CONST_MQTT_HOST=os.getenv("MQTT_HOST","192.168.49.80")
    CONST_MQTT_PASSWORD=os.getenv("MQTT_PASSWORD","")
    CONST_MQTT_USERNAME=os.getenv("MQTT_USERNAME","frigate")
    CONST_SLEEP_INTERVAL=os.getenv("SLEEP_INTERVAL",SLEEP_INTERVAL)
    CONST_GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY","")
    CONST_GOOGLE_SPREADSHEET_ID=os.getenv("GOOGLE_SPREADSHEET_ID","")
    NAMES=os.getenv("NAMES","")
    DEVICE_CLASS=os.getenv("DEVICE_CLASS","")
    UNIT_OF_MEASUREMENT=os.getenv("UNIT_OF_MEASUREMENT","")
    COLUMNS=os.getenv("COLUMNS","")

def replace_periods(sensor_name):
    return re.sub(r'\W', '_', sensor_name.lower() )

def on_publish(client, userdata, mid, reason_code, properties):
    print("Message published.")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully.")
    else:
        print("Connection failed with error code " + str(rc))

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")

class GoogleSheetsLastRowSensor:
    def __init__(self, name, device_class, unit_of_measurement):
        name_replace=replace_periods(name)
        self.name = f"googlesheetslastrowfetcher_{name_replace}"
        self.device_class = device_class
        self.unit_of_measurement = unit_of_measurement
        self.state_topic = f"homeassistant/sensor/googlesheetslastrowfetcher_{name_replace}/state"
        self.unique_id = f"googlesheetslastrowfetcher_{name_replace}"
        self.device = {
            "identifiers": [f"googlesheetslastrowfetcher_{name_replace}"][0],
            "name": f"Google Sheets Response For {name}"
        }

    def to_json(self):
        return {
            "name": self.name,
            "device_class": self.device_class,
            "unit_of_measurement": self.unit_of_measurement,
            "device_class": self.device_class,
            "state_topic": self.state_topic,
            "unique_id": self.unique_id,
            "device": self.device
        }


def initialize():
    count = 0
    DEVICE_CLASS_LIST=DEVICE_CLASS.split(',')
    UNIT_OF_MEASUREMENT_LIST=UNIT_OF_MEASUREMENT.split(',')
    logger = logging.getLogger(__name__)
    logger.info(f"Initialization starting...")
    print("Initialization starting...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_publish = on_publish
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.username_pw_set(CONST_MQTT_USERNAME,CONST_MQTT_PASSWORD)

    try:
      client.connect(CONST_MQTT_HOST, 1883)
    except Exception as e:
        print("Error connecting to MQTT Broker: " + str(e))

    for sensor in NAMES.split(','):
        google_sheets_sensor=GoogleSheetsLastRowSensor(sensor,DEVICE_CLASS_LIST[count],UNIT_OF_MEASUREMENT_LIST[count])
        # Convert dictionary to JSON string
        serialized_message = json.dumps(google_sheets_sensor.to_json())
        print(f"Sending sensor -> {serialized_message}")
        logger.info(f"Sending sensor -> {serialized_message}")
        print(f"entity: homeassistant/sensor/googlesheetslastrowfetcher_{sensor.lower()}/config")
    
        try:
            ret = client.publish(f"homeassistant/sensor/googlesheetslastrowfetcher_{sensor.lower()}/config", payload=serialized_message, qos=0, retain=True)
            if ret == mqtt.MQTT_ERR_SUCCESS:
                print("Message queued successfully.")
            else:
                print("Failed to queue message with error code " + str(ret))
        except Exception as e:
            print("Error publishing message: " + str(e))
        count = count + 1
        
    try:
        client.disconnect()
    except Exception as e:
        print("Error disconnecting from MQTT Broker: " + str(e))

    logger.info(f"Initialization complete...")
    print("Initialization complete...")

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
    initialize()
    COLUMNS_LIST=COLUMNS.split(',')
    DEVICE_CLASS_LIST=DEVICE_CLASS.split(',')
    UNIT_OF_MEASUREMENT_LIST=UNIT_OF_MEASUREMENT.split(',')
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(CONST_MQTT_USERNAME,CONST_MQTT_PASSWORD)
    logger = logging.getLogger(__name__)
    while True:
        count = 0
        for sensor in NAMES.split(','):
            name_replace=replace_periods(sensor)
            value = get_spreadsheet_values(COLUMNS_LIST[count])
            print(f"{sensor} -> {value[0]} {DEVICE_CLASS_LIST[count]} {UNIT_OF_MEASUREMENT_LIST[count]}")
            client.connect(CONST_MQTT_HOST, 1883)
            client.publish(f"homeassistant/sensor/googlesheetslastrowfetcher_{name_replace.lower()}/state", payload=value[0], qos=0, retain=False)    
            client.disconnect()
            count = count + 1

        logger.info(f"It is {datetime.datetime.now()} .. I am sleeping for {CONST_SLEEP_INTERVAL}")
        print(f"It is {datetime.datetime.now()} ... I am sleeping for {CONST_SLEEP_INTERVAL}")
        time.sleep(SLEEP_INTERVAL)
