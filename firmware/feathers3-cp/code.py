import time, gc, os
import neopixel
import board, digitalio, busio
import feathers3

# Sensors
import adafruit_sht31d
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_apds9960 import colorutility

print("\nbaldSENSE FeatherS3 A")
print("\n---------------------")

print ("Enable Sense") # Sense Enable is IO11 (D13)
sense_enable = digitalio.DigitalInOut(board.D13)
sense_enable.direction = digitalio.Direction.OUTPUT
sense_enable.value = True

print("Enable I2C")
try:
    i2c = busio.I2C(board.SCL, board.SDA)
except Exception as e:
    print(e)
    raise e
    print("I2C Failed, is shield connected?")
    while(True):
        pass

# SHT30, 31, and 35 vary in accuracy
# BaldSENSE has a SHT30 (+/-0.2 from 0 to 65C)
def get_temperature(sensor): #sht30
    try:
        reading = sensor.temperature
    except Exception as e:
        print(e)
        reading = None
    return reading

def get_humidity(sensor): #sht30
    try:
        reading = sensor.relative_humidity
    except Exception as e:
        print(e)
        reading = None
    return reading

def get_color_data(sensor): #adps9660
    #print ("Getting color data.")
    sensor.enable_color = True
    while not sensor.color_data_ready:
        time.sleep(0.005)
    
    # get the data
    return sensor.color_data

def get_color_temp(color_data):
    r, g, b, c = color_data
    color_temp = colorutility.calculate_color_temperature(r, g, b)
    #print("color temp {}".format(color_temp))
    return color_temp

def get_light_lux(color_data):
    r, g, b, c = color_data
    lux = colorutility.calculate_lux(r, g, b)
    #print("light lux {}".format(lux))
    return lux

def main():
    # Temperature / Humidity
    sht30 = adafruit_sht31d.SHT31D(i2c) 
    sht30.heater = False # draws up to 33 mW when on

    # Light
    apds = APDS9960(i2c)
    apds.enable_proximity = True
    get_color_data(apds)

    while True:
        print("\nTemperature : %0.1f C" % get_temperature(sht30))
        print("Humidity    : %0.1f %%" % get_humidity(sht30))

        print(f"Proximity  : {apds.proximity}")
        print(f"Color Temp : {get_color_temp(get_color_data(apds))}")
        print(f"Light Lux  : {get_light_lux(get_color_data(apds))}")

        time.sleep(2)

if (__name__ == '__main__'):
    main()