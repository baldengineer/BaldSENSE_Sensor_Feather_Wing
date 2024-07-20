import time, gc, os
import neopixel
import board, digitalio, busio
import feathers3
import adafruit_sht31d

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
def get_temperature(sensor):
    try:
        reading = sensor.temperature
    except Exception as e:
        print(e)
        reading = None
    return reading

def get_humidity(sensor):
    try:
        reading = sensor.relative_humidity
    except Exception as e:
        print(e)
        reading = None
    return reading


def main():
    sensor = adafruit_sht31d.SHT31D(i2c) 
    sensor.heater = False # draws up to 33 mW when on

    while True:
        print("\nTemperature: %0.1f C" % sensor.temperature)
        print("Humidity: %0.1f %%" % sensor.relative_humidity)
        time.sleep(2)

if (__name__ == '__main__'):
    main()
