import time, gc, os
import feathers3
import neopixel
import board, analogio, digitalio, busio
import sys, supervisor

# Sensors
import adafruit_sht31d
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_apds9960 import colorutility
import adafruit_ds3231
import sdcardio, storage # sd card

# Adafruit MQTT broker example
import wifi, socketpool
import adafruit_minimqtt.adafruit_minimqtt as MQTT
#import ssl The S in IoT is for security

# Deep Sleep
import alarm

sense_id = "A"

print(f"\nbaldSENSE FeatherS3 sense_id")
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

# ds3231 (RTC)
print("Enable RTC")
rtc = adafruit_ds3231.DS3231(i2c)

print("Enable SHT30")
# Temperature / Humidity
sht30 = adafruit_sht31d.SHT31D(i2c) 
sht30.heater = False # draws up to 33 mW when on

print("Enable APDS-9660")
# Light
apds = APDS9960(i2c)
apds.enable_proximity = True

print("Enable SPI")
spi = board.SPI()

print("Setup sdcard pins")
sd_cs = board.D19 #sdcardio needs pin object
sd_cd = digitalio.DigitalInOut(board.D18)
sd_cd.direction = digitalio.Direction.INPUT
sd_cd.pull = digitalio.Pull.UP

print("Setup dividers")
# Battery / VUSB
meas_batt_en = digitalio.DigitalInOut(board.D16)
batt_meas = analogio.AnalogIn(board.A1)
vusb_meas = analogio.AnalogIn(board.A0)

print("Connect to MQTT Broker")

mqtt_broker = os.getenv("MQTT_BROKER")
wifi_ssid = os.getenv("WIFI_SSID")
wifi_password = os.getenv("WIFI_PASSWORD")
mqtt_feed = "incoming"
print(f"broker: {mqtt_broker}")
wifi.radio.connect(ssid=wifi_ssid, password=wifi_password)
if (wifi.radio.connected):
    print(f"Wifi Status: {wifi.radio.connected}")
    print(f"ssid: {wifi.radio.ap_info.ssid}")
    print(f"rssi: {wifi.radio.ap_info.rssi}")
    print(f"chan: {wifi.radio.ap_info.channel}")
else:
    print("WiFi failed")

def mqtt_connected(client, userdata, flags, rc):
    # This function will be called when the client is connected
    # successfully to the broker.
    print(f"Connected to {mqtt_broker}!")
    print(f"Listening for topic changes on {mqtt_feed}")

    # Subscribe to all changes on the onoff_feed.
    client.subscribe(mqtt_feed)

def mqtt_disconnected(client, userdata, rc):
    # This method is called when the client is disconnected
    print(f"Disconnected from {mqtt_broker}")

def mqtt_message(client, topic, message):
    # This method is called when a topic the client is subscribed to
    # has a new message.
    print(f"New message on topic {topic}: {message}")


# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)

# Set up a MiniMQTT Client
mqtt_client = MQTT.MQTT(
    broker=mqtt_broker,
    port=1883,
    socket_pool=pool
)

# Setup the callback methods above
mqtt_client.on_connect = mqtt_connected
mqtt_client.on_disconnect = mqtt_disconnected
mqtt_client.on_message = mqtt_message

# Connect the client to the MQTT broker.
print("Connecting to MQTT Broker...")
mqtt_client.connect()

# Modified From todbot's CircuitPython Tricks
# changed if to while so we get the entire string
class USBSerialReader:
    """ Read a line from USB Serial (up to end_char), non-blocking, with optional echo """
    def __init__(self):
        self.s = ''
    def read(self,end_char='\n', echo=True):
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

### RTC
def get_date_time_string(rtc, verbose_date=False):
    t = rtc.datetime
    #print(f"rtc datetime: {t}")
    # days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    date_string = "{:02}-{:02}-{:02}".format(t.tm_year, t.tm_mon, t.tm_mday)
    time_string = "{:02}:{:02}:{:02}".format(t.tm_hour, t.tm_min, t.tm_sec)
    if (verbose_date):    
        print(f"Date        : {date_string}")        
        print(f"Time        : {time_string}")
    return (date_string, time_string)

def get_rtc_temperature(rtc):
    return rtc.temperature

def get_free_memory():
    return gc.mem_free()

def get_flash_size():
    flash = os.statvfs('/')
    flash_size = flash[0] * flash[2]
    flash_free = flash[0] * flash[3]
    return (flash_free, flash_size)

def process_time_string(str):
    global rtc
    params = str.split(",")
    elements = len(params)
    if (elements == 9):
        # yr = params[0]
        # yr = yr[1:]
        # params[0] = yr
        params[0] = params[0].lstrip('t')
        params[0] = params[0].lstrip('T')
        for x in range(9):
            params[x] = int(params[x])
        #params[8] = params[8].strip()
        rtc.datetime = time.struct_time(params)
    else:
        print(f"Time String Contains: {elements} fields")
        print("Time string should contain: tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst")
        #T2024,07,20,17,30,30,6,-1,-1

def shutdown_sensors():
    global sense_enable
    global sht30
    global apds
    global meas_batt_en
    global batt_meas
    global vusb_meas
    global rtc

    # sht30.deinit()
    # apds.deinit()
    # rtc.deinit()
    spi.deinit()
    i2c.deinit()
    meas_batt_en.direction = digitalio.Direction.INPUT
    print("Turning off Wing")
    sense_enable.direction = digitalio.Direction.INPUT
    return

def handle_serial(usb_serial_in):
    incoming_string = usb_serial_in.read()  # read until newline, echo back chars
    #mystr = usb_reader.read(end_char='\t', echo=False) # trigger on tab, no echo
    if incoming_string:
        incoming_string = incoming_string.strip()
        print(f"got:[{incoming_string}]")
        if (len(incoming_string) > 0):
            # do we need to update rtc?
            if (incoming_string[0].upper() == 'T'):
                process_time_string(incoming_string)
            if (incoming_string[0].upper() == 'W'):
                print("WiFi Scan")
                for network in wifi.radio.start_scanning_networks():
                    print(network, network.ssid, network.channel)
                wifi.radio.stop_scanning_networks()
            if (incoming_string.upper() == "STOP"):
                print("Stopping...")
                shutdown_sensors()
                while True:
                    pass


def write_to_sd(str_to_write):
    global spi
    global sd_cd

    # sd_cd.value = False when card is detected
    if (sd_cd.value == False): 
        try:
            sdcard = sdcardio.SDCard(spi,sd_cs)
            vfs = storage.VfsFat(sdcard)
            storage.mount(vfs, "/sd")
            with open("/sd/log.txt","a") as f:
                f.write(f"{str_to_write}\r\n")
            storage.umount(vfs)
            sdcard.deinit()
        except Exception as e:
            print("[!!!] SD Card Mount Failed")
            print(e)
    else:
        print("[!] Card not detected")

def build_csv(values):
    csv_str = ""
    for element in values:
        csv_str = csv_str + "," + str(element)
    #print(csv_str)
    return csv_str.lstrip(",")

### Main
def main():
    global sense_id
    global sense_enable
    global sht30
    global apds
    global meas_batt_en
    global batt_meas
    global vusb_meas
    global rtc

    usb_reader = USBSerialReader()
#    while True:

    handle_serial(usb_reader)
    mqtt_client.loop(timeout=1)

    c_temperature = get_temperature(sht30)
    c_humidity = get_humidity(sht30)
    c_proximity = apds.proximity
    c_color_temp = get_color_temp(get_color_data(apds))
    c_light_lux = get_light_lux(get_color_data(apds))
    c_batt_level = get_adc_levels(batt_meas, meas_batt_en)  
    c_VUSB_level = get_adc_levels(vusb_meas)
    c_rtc_temp = get_rtc_temperature(rtc)
    c_date_string = get_date_time_string(rtc)
    c_supervisor_ticks = supervisor.ticks_ms()

    print(f"\nSuperV Ticks : {c_supervisor_ticks}")
    # sht30
    print("Temperature  : %0.1f C" % c_temperature)
    print("Humidity     : %0.1f %%" % c_humidity)

    # apds-9660
    print(f"Proximity    : {c_proximity}")
    print(f"Color Temp   : {c_color_temp}")
    print(f"Light Lux    : {c_light_lux}")
    
    # voltage dividers         
    print(f"Battery Volt : {c_batt_level}, {convert_adc_voltage(c_batt_level)}V")
    print(f"VUSB Volt    : {c_VUSB_level}, {convert_adc_voltage(c_VUSB_level)}V")

    # rtc
    print(f"Date / Time  : {c_date_string[0]} {c_date_string[1]}")
    print(f"RTC temp     : {c_rtc_temp} C")

    # other
    print(f"RAM Free     : {get_free_memory():,}")
   
    # do the internet and local things
    current_values = (c_supervisor_ticks,sense_id,c_date_string[0],c_date_string[1], c_temperature,c_humidity,c_proximity,c_color_temp,c_light_lux,c_batt_level,c_VUSB_level,c_rtc_temp,str(get_free_memory()))
    try:
        mqtt_client.publish("pub/balda",str(current_values))
        print("Published to MQTT Successful")
        mqtt_success = 1
    except Exception as e:
        print("Published to MQTT Failed")
        print(e)
        mqtt_success = 0
    current_values = current_values + (mqtt_success,)
    write_to_sd(build_csv(current_values))
   
    #time.sleep(5)
    return


if (__name__ == '__main__'):
    main()
    shutdown_sensors()
    # preserve_dios is available on Espressif Targets...
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 60)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)
