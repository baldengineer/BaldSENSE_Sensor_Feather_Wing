#!/usr/bin/python

import paho.mqtt.client as mqtt

# MQTT settings
mqtt_broker = "benchpi"
mqtt_port = 1883
mqtt_topic = "pub/balda"

# MQTT client setup
mqtt_client = mqtt.Client()

def on_message(client, userdata, message):
    message_text = message.payload.decode()
    process_payload(message_text)

def process_payload(payload):
    print(payload)

# Set up MQTT client callbacks
mqtt_client.on_message = on_message

# Connect to MQTT broker and subscribe to topic
print(f"Connecting to {mqtt_broker}")
mqtt_client.connect(mqtt_broker, mqtt_port)
print(f"Subscribed to '{mqtt_topic}'")
mqtt_client.subscribe(mqtt_topic)

# Start MQTT client loop
mqtt_client.loop_forever()



# REST example from:
# https://gist.github.com/Bilka2/5dd2ca2b6e9f3573e0c2defe5d3031b2

# webhook params: https://discord.com/developers/docs/resources/webhook#execute-webhook
# embed params: https://discord.com/developers/docs/resources/channel#embed-object
    # discord_data["embeds"] = [
    #     {
    #         "description" : "text in embed",
    #         "title" : "embed title"
    #     }
    # ]