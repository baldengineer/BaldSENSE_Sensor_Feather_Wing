import time, gc, os
import neopixel
import board, digitalio, busio
import feathers3

# Sensors
import adafruit_sht31d
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_apds9960 import colorutility
import analogio
import adafruit_ds3231

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

# Modified From todbot's CircuitPython Tricks
# changed if to while so we get the entire string
class USBSerialReader:
    """ Read a line from USB Serial (up to end_char), non-blocking, with optional echo """
    def __init__(self):
        self.s = ''
    def read(self,end_char='\n', echo=True):
        import sys, supervisor
        n = supervisor.runtime.serial_bytes_available
        
        while(n > 0):                # we got bytes!
            s = sys.stdin.read(n)    # actually read it in
            if echo: sys.stdout.write(s)  # echo back to human
            self.s = self.s + s      # keep building the string up
            if s.endswith(end_char): # got our end_char!
                rstr = self.s        # save for return
                self.s = ''          # reset str to beginning
                return rstr
            n = supervisor.runtime.serial_bytes_available # update n
        return None                  # no end_char yet

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

    # ds3231 (RTC)
    rtc = adafruit_ds3231.DS3231(i2c)
    usb_reader = USBSerialReader()

   # days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

    while True:
        print("\nTemperature  : %0.1f C" % get_temperature(sht30))
        print("Humidity     : %0.1f %%" % get_humidity(sht30))

        print(f"Proximity    : {apds.proximity}")
        print(f"Color Temp   : {get_color_temp(get_color_data(apds))}")
        print(f"Light Lux    : {get_light_lux(get_color_data(apds))}")
        batt_level = get_adc_levels(batt_meas, meas_batt_en)
       #batt_level = get_adc_levels(batt_meas)
        
        print(f"Battery Volt: {batt_level}, {convert_adc_voltage(batt_level)}V")
        VUSB_level = get_adc_levels(vusb_meas)
        print(f"VUSB Volt    : {VUSB_level}, {convert_adc_voltage(VUSB_level)}V")

        t = rtc.datetime
        #print(f"rtc datetime: {t}")
        date_string = "{}/{}/{}".format(t.tm_mday, t.tm_mon, t.tm_year)
        print(f"Date        : {date_string}")
        time_string = "{}:{:02}:{:02}".format(t.tm_hour, t.tm_min, t.tm_sec)
        print(f"Time        : {time_string}")
        print(f"rtc temp    : {rtc.temperature}")

        mystr = usb_reader.read()  # read until newline, echo back chars
        #mystr = usb_reader.read(end_char='\t', echo=False) # trigger on tab, no echo
        if mystr:
            print("got:",mystr)

        time.sleep(10)

if (__name__ == '__main__'):
    main()