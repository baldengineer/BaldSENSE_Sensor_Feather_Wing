import time, gc, os
import neopixel
import board, digitalio, busio
import feathers3

# Sensors
import adafruit_sht31d
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_apds9960 import colorutility
import analogio

## PDM (time and board) - Not implemented
# import array
# import math
# import audiobusio # needed for PDM

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

### SHT30, 31, and 35 vary in accuracy
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

### apds-9660
def get_color_data(sensor): 
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

### PDM - not implemented
# Remove DC bias before computing RMS.
# def mean(values):
#     return sum(values) / len(values)


# def normalized_rms(values):
#     minbuf = int(mean(values))
#     samples_sum = sum(
#         float(sample - minbuf) * (sample - minbuf)
#         for sample in values
#     )

#     return math.sqrt(samples_sum / len(values))

### Battery and USBV Checks
def get_adc_levels(meas_pin, enable_pin=None):
    # enable battery voltage divider
    if (enable_pin is not None):
        enable_pin.direction = digitalio.Direction.OUTPUT
        enable_pin.value = True

    adc_levels = meas_pin.value

    # disable battery voltage divider (by going HiZ)
    if (enable_pin is not None):
        enable_pin.direction = digitalio.Direction.INPUT
    return adc_levels

def convert_adc_voltage(adc_levels, div_correction = 2):
    voltage = ((adc_levels * 2.57) / 51000) * div_correction
    return voltage

### Main
def main():
    # Temperature / Humidity
    sht30 = adafruit_sht31d.SHT31D(i2c) 
    sht30.heater = False # draws up to 33 mW when on

    # Light
    apds = APDS9960(i2c)
    apds.enable_proximity = True
    get_color_data(apds)

    # Battery / VUSB
    meas_batt_en = digitalio.DigitalInOut(board.D16)
    batt_meas = analogio.AnalogIn(board.A1)
    vusb_meas = analogio.AnalogIn(board.A0)

    # board.D11 = clock
    # board.D12 = data
    # mic = audiobusio.PDMIn(board.D11, board.D12, sample_rate=000, bit_depth=8)
    # mic_samples = array.array('H', * 160)
    ## goes into loop:
    # mic.record(samples, len(samples))
    # magnitude = normalized_rms(samples)
    # print((magnitude,))

    while True:
        print("\nTemperature : %0.1f C" % get_temperature(sht30))
        print("Humidity    : %0.1f %%" % get_humidity(sht30))
        print(f"Proximity   : {apds.proximity}")
        print(f"Color Temp  : {get_color_temp(get_color_data(apds))}")
        print(f"Light Lux   : {get_light_lux(get_color_data(apds))}")
        batt_level = get_adc_levels(batt_meas, meas_batt_en)
       #batt_level = get_adc_levels(batt_meas)
        print(f"Battery Volt: {batt_level}, {convert_adc_voltage(batt_level)}V")
        VUSB_level = get_adc_levels(vusb_meas)
        print(f"VUSB Volt   : {VUSB_level}, {convert_adc_voltage(VUSB_level)}V")

        time.sleep(2)

if (__name__ == '__main__'):
    main()