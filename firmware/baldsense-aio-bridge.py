#!/usr/bin/python

# import standard python modules.
import time
from Adafruit_IO import Client, Feed, RequestError

import paho.mqtt.client as mqtt

# MQTT settings and client
mqtt_broker = "benchpi"
mqtt_port = 1883
mqtt_topic = "pub/balda"
mqtt_client = mqtt.Client()

def on_message(client, userdata, message):
    message_text = message.payload.decode()
    process_payload(message_text)

def process_payload(payload):
    print(payload)
    try:
        fields = payload.split(", ")

        temperature = float(fields[4])
        print('Temp={0:0.1f}*C'.format(temperature))
   
        humidity = float(fields[5])
       # print('Humidity={1:0.1f}%'.format(humidity))
        print(f'Humidity={humidity}%')
   
        lux = fields[8]
        print(f'LUX={lux}')
      
        batt_steps = fields[9]
        print(f'Battery Steps={batt_steps}')
    except RequestError:
        exit()

    # Format sensor data as string for sending to Adafruit IO
    temperature = '%.2f'%(temperature)
    humidity = '%.2f'%(humidity)

    # Send humidity and temperature data to Adafruit IO
    try:
        aio.send(temperature_feed.key, str(temperature))
    except RequestError:
        print(f"Failed to send temperature: {temperature}")
    try:
        aio.send(humidity_feed.key, str(humidity))
    except RequestError:
        print(f"Failed to send temperature: {humidity}")
    try:
        aio.send(lux_feed.key, str(lux))
    except RequestError:
        print(f"Failed to send temperature: {lux}")
    try:        
        aio.send(batt_steps_feed.key, str(batt_steps))
    except RequestError:
        print(f"Failed to send temperature: {batt_steps}")

# setup MQTT callback
mqtt_client.on_message = on_message

# Connect to MQTT broker and subscribe to topic
print(f"Connecting to {mqtt_broker}")
mqtt_client.connect(mqtt_broker, mqtt_port)
print(f"Subscribed to '{mqtt_topic}'")
mqtt_client.subscribe(mqtt_topic)


print("Connecting to AIO")
READ_TIMEOUT = 60
# Adafruit IO Settings
ADAFRUIT_IO_KEY = ''
ADAFRUIT_IO_USERNAME = ''

if (ADAFRUIT_IO_KEY == '' or ADAFRUIT_IO_USERNAME == ''):
    print("Need to set AIO Key and Username")
    exit()

aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)


# Assign a temperature feed, if one exists already
try:
    temperature_feed = aio.feeds('temperature')
except RequestError: # Doesn't exist, create a new feed
    feed_temp = Feed(name="temperature")
    temperature_feed = aio.create_feed(feed_temp)

# Assign a humidity feed, if one exists already
try:
    humidity_feed = aio.feeds('humidity')
except RequestError: # Doesn't exist, create a new feed
    feed_humid = Feed(name="humidity")
    humidity_feed = aio.create_feed(feed_humid)

# Assign a lux feed, if one exists already
try:
    lux_feed = aio.feeds('lux')
except RequestError: # Doesn't exist, create a new feed
    feed_lux = Feed(name="lux")
    lux_feed = aio.create_feed(lux_feed)    

# Assign a voltage steps feed, if one exists already
try:
    batt_steps_feed = aio.feeds('batt-steps')
except RequestError: # Doesn't exist, create a new feed
    feed_batt_steps = Feed(name="batt-steps")
    batt_steps_feed = aio.create_feed(feed_batt_steps)    


print("Going into MQTT loop")
# Start MQTT client loop
mqtt_client.loop_forever()