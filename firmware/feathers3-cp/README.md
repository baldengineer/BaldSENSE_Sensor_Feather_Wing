# FeatherS3 Circuit Python

This code uses all of the intended BaldSENSE functions.

Couple of notes:
- Developed with a [FeatherS3](https://unexpectedmaker.com/shop.html#!/FeatherS3/p/577111310/category=0)
- Based on CircuitPython 9.x. 
- Publishes data to [Adafruit IO](https://io.adafruit.com)
    - It uses more feeds than the free version allows

## settings.toml.example
Remove the `.example` and place in the root directory of the `CIRCUITPY` mass storage device. 

### Required Settings:
- `WIFI_SSID` and `WIFI_PASSWORD` (your access point)
- `AIO_USERNAME` and `AIO_KEY` (Adafruit IO credentials)

### Optional, but recommended:
These settings have default values but you should set them.
- `BALDSENSE_ID` -> a unique identifier (defaults to `UNKNOWN`)
- `SLEEP_SECONDS` -> how long MCU goes to sleep between sampling (defaults to `600`)
- `WDT_SECONDS` -> watchdog timeout (defaults to `60`)
- `VUSB_THRESHOLD` -> voltage divider steps to detect when connected to power (defaults to `10000`)
- `UPDATE_TIME` -> force NTP update when connected to power. "No" or commented out skips this update.

### Not used (yet):
- `RUN_MODE` eventually to change behavior during devel or deploy
- `TIMEZONE` for setting timezone. current NTP method uses geo_ip
- `MQTT_BROKER` will use again in future to allow private broker


## Required Libraries
These are the required libraries. Dependencies are shown. The libraries listed with `.mpy` are single files and the others are directories in the [Adafruit CircuitPython (Library) Bundle](https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases). This code needs the `9.x` bundle.

### Sensors:
- adafruit_apds9960
- adafruit_ds3231.mpy
    - adafruit_register
- adafruit_sht31d.mpy

### AIO / MQTT:
- adafruit_io
- adafruit_minimqtt
    - adafruit_ticks.mpy
- adafruit_requests.mpy
    - adafruit_connection_manager


## mqtt_logger.py
Simple script to log MQTT messages to a file. Works well on Linux. 

## generate_time_string.py
Simple script to create a string with the system's current time to update the RTC. Copy/paste the string and press enter (line return). (You may need to re-enable the `while True` loop to get the timing right.)

Alternatively, when connected to USB, the code will check a NTP server.

## Sponsor
The PCB, components, and assembly for rev 3 have been provided by [MacroFab](https://macrofab.com).