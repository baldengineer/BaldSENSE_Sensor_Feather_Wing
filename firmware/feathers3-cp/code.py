import time, gc, os
import board, analogio, digitalio, busio
import sys, supervisor, microcontroller, usb_cdc

# Sensors 
import adafruit_sht31d
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_apds9960 import colorutility
import adafruit_ds3231
import sdcardio, storage # sd card

# Adafruit MQTT broker example
import ssl  # this S in IoT is for Security
import socketpool
import wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT

# For updatig the rtc's time
import adafruit_requests

# Deep Sleep
import alarm

# If something happens, give up
microcontroller.on_next_reset(microcontroller.RunMode.SAFE_MODE)

# get the id for this board
# todo, move all environmental varibles to here
sense_id = os.getenv("BALDSENSE_ID")
if (sense_id is None):
    # todo: prevent connecting
    feed_prefix = None #prevent publishing to AIO
    print("SENSE ID not set")
    sense_id = "INVALID"
else:
    feed_prefix = sense_id.lower() + "-"
    print(f"Example feed: {feed_prefix}")
    
VUSB_THRESHOLD = os.getenv("VUSB_THRESHOLD")
if (VUSB_THRESHOLD is None):
    print("VUSB_THRESHOLD not set")
    VUSB_THRESHOLD = 10000
print(f"VUSB_THRESHOLD: {VUSB_THRESHOLD}")

try:
    if os.getenv("AIO_USERNAME") and os.getenv("AIO_KEY"):
        secrets = {
            "aio_username": os.getenv("AIO_USERNAME"),
            "aio_key": os.getenv("AIO_KEY"),
            "ssid": os.getenv("WIFI_SSID"),
            "password": os.getenv("WIFI_PASSWORD"),
        }
except Exception as e:
    print(e)
    print("You need to add AIO stuff to settings.toml")
    while(True):
        pass

sleep_time = int(os.getenv("SLEEP_SECONDS"))
if (sleep_time is None):
    print("Add SLEEP_SECONDS to settings.toml, using 600")
    sleep_time = 600

print(f"\nbaldSENSE FeatherS3 {sense_id}")
print("\n---------------------")

print ("Enable Sense....") # Sense Enable is IO11 (D13)
sense_enable = digitalio.DigitalInOut(board.D13)
sense_enable.direction = digitalio.Direction.OUTPUT
sense_enable.value = True

print("Enable I2C...")
try:
    i2c = busio.I2C(board.SCL, board.SDA)
except Exception as e:
    print(e)
    print("I2C Failed, is shield connected?")
    raise e


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

mqtt_broker = os.getenv("MQTT_BROKER")
wifi_ssid = os.getenv("WIFI_SSID")
wifi_password = os.getenv("WIFI_PASSWORD")
mqtt_feed = "incoming"
print("Connect to WiFi AP")

try:
    wifi.radio.connect(ssid=wifi_ssid, password=wifi_password, timeout=20)
    if (wifi.radio.connected):
        print(f"Wifi Status: {wifi.radio.connected}")
        print(f"ssid: {wifi.radio.ap_info.ssid}")
        wifi_rssi = wifi.radio.ap_info.rssi
        print(f"rssi: {wifi.radio.ap_info.rssi}")
        print(f"chan: {wifi.radio.ap_info.channel}")
        # Create a socket pool
        pool = socketpool.SocketPool(wifi.radio)
    else:
        print("[!] WiFi: AP connect failed")
except Exception as e:
    print(e)
    print("[!] WiFi: WiFi Failed by exception")

def mqtt_connected(client):
    # print(f"Connected to {mqtt_broker}!")
    print("Connected!")
    client.subscribe(mqtt_feed)
#    print(f"Subscribed to {mqtt_feed}")

def mqtt_disconnected(client):
    #print(f"Disconnected from {mqtt_broker}")
    print(f"Disconnected from AIO")

def mqtt_message(client, feed_id, payload):
    print("Feed {0} received new value: {1}".format(feed_id, payload))

def mqtt_subscribe(client, userdata, topic, granted_qos):
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))

def mqtt_unsubscribe(client, userdata, topic, pid):
    print("Unsubscribed from {0} with PID {1}".format(topic, pid))

def mqtt_publish(client, userdata, topic, pid):
    print("Published to {0} with PID {1}".format(topic, pid))
    if userdata is not None:
        print("Published User data: ", end="")
        print(userdata)  


# Connect the client to the MQTT broker.
try:
    if (wifi.radio.connected):
        mqtt_client = MQTT.MQTT(
            broker="io.adafruit.com",
            port=8883, 
            username=secrets["aio_username"],
            password=secrets["aio_key"],
            socket_pool=pool,
            ssl_context=ssl.create_default_context(),
            is_ssl=True,
            connect_retries=3,
        )

        # Init AIO MQTT Client
        io = IO_MQTT(mqtt_client)

        # Connect the callback methods defined above to Adafruit IO
        io.on_connect = mqtt_connected
        io.on_disconnect = mqtt_disconnected
        io.on_message = mqtt_message

        io.on_subscribe = mqtt_subscribe
        io.on_unsubscribe = mqtt_unsubscribe
        
        io.on_publish = mqtt_publish

        # Connect to Adafruit IO
        print("Attempting AIO Connection...")
        io.connect()

    else:
        print("[!] Skipping MQTT, no WiFi")
except Exception as e:
    print(e)
    print("MQTT Connection failed")
    mqtt_client = None

# Modified From todbot's CircuitPython Tricks
# changed if to while so we get the entire string
class USBSerialReader:
    """ Read a line from USB Serial (up to end_char), non-blocking, with optional echo """
    def __init__(self):
        self.s = ''
    def read(self,end_char='\n', echo=True):
        try:
            n = supervisor.runtime.serial_bytes_available
        except:
            n = None
        
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
    # apparently, this sometimes causes a div by 0, lol
    try:
        color_temp = colorutility.calculate_color_temperature(r, g, b)
    except Exception as e:
        print(e)
        print("[!] get_color_temp failed")
        color_temp = 0.0
    #print("color temp {}".format(color_temp))
    return color_temp
def get_light_lux(color_data):
    r, g, b, c = color_data
    try:
        lux = colorutility.calculate_lux(r, g, b)
    except Exception as e:
        print(e)
        print("[!] failed to get lux")
        lux = 0.0
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

def update_rtc_from_aio():  
    global rtc
    global secrets

    # another bit of todbot magic
    pool = socketpool.SocketPool(wifi.radio)
    request = adafruit_requests.Session(pool, ssl.create_default_context())
    response = request.get("http://worldtimeapi.org/api/ip")
    time_data = response.json()    
    tz_hour_offset = int(time_data['utc_offset'][0:3])
    tz_min_offset = int(time_data['utc_offset'][4:6])
    if (tz_hour_offset < 0):
        tz_min_offset *= -1
    unixtime = int(time_data['unixtime'] + (tz_hour_offset * 60 * 60)) + (tz_min_offset * 60)

    print(time_data)
    print("URL time: ", response.headers['date'])

    rtc.datetime = time.localtime( unixtime )

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

    # update time when connected to external power
    c_VUSB_level = get_adc_levels(vusb_meas) 
    
    if (c_VUSB_level >= VUSB_THRESHOLD):
        # connected to usb
        print("Attempting to update RTC")
        update_rtc_from_aio()
    
    usb_reader = USBSerialReader()

    handle_serial(usb_reader)
    if (wifi.radio.connected) and (mqtt_client is not None):
        if (mqtt_client.is_connected()):
            if (mqtt_client.is_connected()):
                mqtt_client.loop(timeout=1)

    c_temperature = get_temperature(sht30)
    c_humidity = get_humidity(sht30)
    c_proximity = apds.proximity
    c_color_temp = get_color_temp(get_color_data(apds))
    c_light_lux = get_light_lux(get_color_data(apds))
    c_batt_level = get_adc_levels(batt_meas, meas_batt_en)  
    c_rtc_temp = get_rtc_temperature(rtc)
    c_date_string = get_date_time_string(rtc)
    c_supervisor_ticks = supervisor.ticks_ms()
    c_ram_free = get_free_memory()

    if (usb_cdc.Serial.connected):
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
        print(f"RAM Free     : {c_ram_free:,}")
    else:
        print("skipped verbose because you aren't connected")
   
    # do the internet and local things
    current_values = (sense_id,c_supervisor_ticks,c_date_string[0],c_date_string[1], c_temperature,c_humidity,c_proximity,c_color_temp,c_light_lux,c_batt_level,c_VUSB_level,c_rtc_temp,str(c_ram_free),wifi_rssi)
    mqtt_success=0
    try: 
        if ((wifi.radio.connected) and (mqtt_client is not None)):
            if ((mqtt_client.is_connected()) and (feed_prefix is not None)):
                print(f"{feed_prefix}temp: {c_temperature}")
                io.publish(f"{feed_prefix}temp", str(c_temperature))

                print(f"{feed_prefix}rh: {c_humidity}")
                io.publish(f"{feed_prefix}rh", str(c_humidity))

                print(f"{feed_prefix}batt-steps: {c_batt_level}")
                io.publish(f"{feed_prefix}batt-steps", str(c_batt_level))

                print(f"{feed_prefix}vusb-steps: {c_VUSB_level}")
                io.publish(f"{feed_prefix}vusb-steps", str(c_VUSB_level))
                
                print(f"{feed_prefix}lux: {c_light_lux}")
                io.publish(f"{feed_prefix}lux", str(c_light_lux))

                print(f"{feed_prefix}rssi: {wifi_rssi}")
                io.publish(f"{feed_prefix}rssi", str(wifi_rssi))

                io.loop() # make sure things get published before we go to sleep
                print("Published to MQTT Successful")
                mqtt_success = 1
                mqtt_client.disconnect()
            else:
                print("[!] Did not published, not connected to broker")
                mqtt_success = 0
    except Exception as e:
        print("Published to MQTT Failed")
        print(e)
        mqtt_success = 0

    current_values = current_values + (mqtt_success,)
    current_values = current_values + (str(wifi.radio.connected),)
    write_to_sd(build_csv(current_values))

    #time.sleep(5)
    return

if (__name__ == '__main__'):
    main()
    shutdown_sensors()
    if (wifi.radio.connected):
        print("Disabling Wi-Fi")
        wifi.radio.enabled = False
    # preserve_dios is available on Espressif Targets...
    print(f"Sleeping for {sleep_time}...")
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_time)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)