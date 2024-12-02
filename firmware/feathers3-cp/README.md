# FeatherS3 Circuit Python

This code is based on CircuitPython 9.x. It provides a basic test of all of the BaldSENSE functionality. When used with a [FeatherS3](https://unexpectedmaker.com/shop.html#!/FeatherS3/p/577111310/category=0), it transmits data via WiFi. 

## settings.toml.example
Remove the `.example` and place in the root directory of the `CIRCUITPY` mass storage device. Edit it with your prefered Wi-Fi SSID and Password. The `SLEEP_SECONDS` parameter changes how often the device sleeps.

## Required Libraries
You'll need a bunch of CircuitPython libraries from Adafruit to support the sensors, Wi-Fi, and MQTT. 

- List TBD

## mqtt_logger.py
Simple script to log MQTT messages to a file. Works well on Linux. 

## generate_time_string.py
Simple script to create a string with the system's current time to update the RTC. Copy/paste the string and press enter (line return). (You may need to re-enable the `while True` loop to get the timing right.)

## Sponsor
The PCB, components, and assembly for rev 3 have been provided by [MacroFab](https://macrofab.com).