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


def replace_periods(sensor_name):
    return re.sub(r'\W', '_', sensor_name.lower())


class GoogleSheetsLastRowSensor:
    def __init__(self, name, device_class, unit_of_measurement):
        name_replace = replace_periods(name)
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
            "state_topic": self.state_topic,
            "unique_id": self.unique_id,
            "device": self.device
        }
    

def load_sensors_from_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return []


def initialize(json_file_path):
    count = 0
    sensors = load_sensors_from_json(json_file_path)
    if not sensors:
        print("No sensor data available.")
        return

    logger = logging.getLogger(__name__)
    logger.info("Initialization starting...")
    print("Initialization starting...")
    logger.info(f"Total sensors: {len(sensors)}")
    print(f"Total sensors: {len(sensors)}")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(CONST_MQTT_USERNAME,CONST_MQTT_PASSWORD)

    try:
        client.connect(CONST_MQTT_HOST, 1883)
    except Exception as e:
        print(f"Error connecting to MQTT Broker: {e}")
        return

    client.loop_start()

    for sensor in sensors:
        sensor_name = sensor["SensorName"]
        device_class = sensor["DeviceClass"]
        unit_of_measurement = sensor["UnitOfMeasurement"]
        google_sheets_sensor = GoogleSheetsLastRowSensor(sensor_name, device_class, unit_of_measurement)
        # Convert dictionary to JSON string
        serialized_message = json.dumps(google_sheets_sensor.to_json())
        print(f"Sending sensor -> {serialized_message}")
        logger.info(f"Sending sensor -> {serialized_message}")
        topic = f"homeassistant/sensor/googlesheetslastrowfetcher_{sensor_name.lower()}/config"
        print(f"entity: {topic}")
    
        try:
            ret = client.publish(topic, payload=serialized_message, qos=2, retain=True)
            ret.wait_for_publish()
            if ret.rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"Failed to queue message with error code {ret.rc}")
        except Exception as e:
            print(f"Error publishing message: {e}")
        count = count + 1
        
    client.loop_start()
    try:
        client.disconnect()
    except Exception as e:
        print("Error disconnecting from MQTT Broker: " + str(e))

    logger.info(f"Initialization complete...")
    print("Initialization complete...")

def get_spreadsheet_values(column_name):

    url = f"https://sheets.googleapis.com/v4/spreadsheets/{CONST_GOOGLE_SPREADSHEET_ID}/values/{column_name}?alt=json&key={CONST_GOOGLE_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        values = response.json().get('values', [])

        return values[-1] if values else 'No data found.'
    
    except requests.exceptions.HTTPError as err:
        print(err)
        return None

# Example usage:
if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.info(f"I am google_sheets_last_row_fetcher running version {VERSION}")
    print(f"I am google_sheets_last_row_fetcher running version {VERSION}")
    json_file_path = "./sensors.json"
    initialize(json_file_path)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(CONST_MQTT_USERNAME,CONST_MQTT_PASSWORD)

    while True:
        try:
            client.connect(CONST_MQTT_HOST, 1883)
        except Exception as e:
            print("Error connecting to MQTT Broker: " + str(e))

        client.loop_start()

        count = 0
        sensors = load_sensors_from_json(json_file_path)

        for sensor in sensors:

            name_replace = replace_periods(sensor["SensorName"])
            value = get_spreadsheet_values(sensor["SensorColumn"])
            device_class = sensor["DeviceClass"]
            unit_of_measurement = sensor["UnitOfMeasurement"]
            
            if value == None:
                print(f"No sensor value found for {sensor}, so skipping")
                count = count + 1
                continue
            else:
                print(f"{sensor} -> {value[0]} {device_class} {unit_of_measurement}")

                try:
                    ret = client.publish(f"homeassistant/sensor/googlesheetslastrowfetcher_{name_replace.lower()}/state", payload=value[0], qos=2, retain=False) 
                    ret.wait_for_publish()
                    if ret.rc != mqtt.MQTT_ERR_SUCCESS:
                        print(f"Failed to queue message with error code {ret.rc}")
                except Exception as e:
                    print("Error publishing message: " + str(e))

                count = count + 1

        client.loop_stop()
        try:
            client.disconnect()
        except Exception as e:
            print("Error disconnecting from MQTT Broker: " + str(e))

        logger.info(f"It is {datetime.datetime.now()} .. I am sleeping for {CONST_SLEEP_INTERVAL}")
        print(f"It is {datetime.datetime.now()} ... I am sleeping for {CONST_SLEEP_INTERVAL}")
        time.sleep(SLEEP_INTERVAL)
