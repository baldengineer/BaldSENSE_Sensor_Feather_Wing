

// wait 60 seconds (testing 10 seconds)
// get the current date/time
// get the temperature and humidity
// put them to sd card

// Date and time functions using a DS3231 RTC connected via I2C and Wire lib
#include <Wire.h>
#include "RTClib.h"

// sht30 (temp/humdity) stuff
#include <Wire.h>
#include "ClosedCube_SHT31D.h"
#include <Adafruit_SleepyDog.h>

// stuff for SD Card
#include <SPI.h>
#include <SD.h>

// APDS-9660 Proximity Sensor
#include <Arduino_APDS9960.h>

ClosedCube_SHT31D sht3xd;

const uint8_t LED_PIN=13;

// Global Stuff
char time_stamp_string[21];
char temp_humd_string[21];
char file_name[30];
char color_sensor_string[21];
File myFile;

// RTC Stuff
RTC_DS3231 rtc;
//char daysOfTheWeek[7][12] = {"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"};

// State Machine stuff
unsigned long previous_print_millis = 0;
unsigned long print_interval = 2500;
int r, g, b, a;

byte init_adps() {
    Serial.print(("ADPS Init..."));
    if (!APDS.begin()) {
      Serial.println("Failed.");
      while (true); // Stop forever
      return 0;
    }
  Serial.println(F("DONE!"));
  return 1;
}

byte init_rtc() {
  if (!rtc.begin()) {
    Serial.println(F("Couldn't find RTC"));
    return 0; // failed to get rtc
  }

  if (rtc.lostPower()) {
    Serial.println(F("RTC lost power, lets set the time!"));
    // following line sets the RTC to the date & time this sketch was compiled
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    // This line sets the RTC with an explicit date & time, for example to set
    // January 21, 2014 at 3am you would call:
    // rtc.adjust(DateTime(2014, 1, 21, 3, 0, 0));
    return 2; // successful return, but know the time changed
  }

  return 1; // successful init
}

byte init_sht30() {
    sht3xd.begin(0x44); // I2C address: 0x44 or 0x45

    Serial.print(F("sht30 serial #: "));
    Serial.println(sht3xd.readSerialNumber());

    return 1;
}

byte init_sdcard() {
    Serial.print(F("Initializing SD card..."));
    if (!SD.begin(A1)) {
        Serial.println(F("failed!"));
        return 0; // fail!
    }

    DateTime now = rtc.now();

    sprintf(file_name, "test-%02d.txt", now.minute());

    Serial.println(F("done."));
    Serial.print(F("Filename: "));
    Serial.println(file_name);
    myFile = SD.open(file_name, FILE_WRITE);

    // if file opened okay:
    if (myFile) {
        Serial.print(F("Writing Header to SD..."));
        myFile.println("DATE, TIME, Temperature, Humidity, R, G, B, Ambient");
        myFile.close();
        Serial.println(F("done!"));
    } else {
        return 0; // couldn't write
    }
    return 1;
}

char *dtostrf (double val, signed char width, unsigned char prec, char *sout) {
  char fmt[20];
  sprintf(fmt, "%%%d.%df", width, prec);
  sprintf(sout, fmt, val);
  return sout;
}

void setup () {
    Wire.begin();
    Serial.begin(9600);

    pinMode(0, OUTPUT);
    digitalWrite(0, LOW);
    pinMode(1, OUTPUT);
    digitalWrite(1, LOW);
    pinMode(LED_PIN, OUTPUT);

    for (int x=0; x<4; x++) {
      digitalWrite(LED_PIN, HIGH);
      delay(250);
      digitalWrite(LED_PIN, LOW);
      delay(250);
    }
   // while(!Serial);

    init_rtc();    // DS3231 
    init_sdcard(); // sd card
    init_sht30();  // temp and humidity
    init_adps();   // color and light
}

void loop () {
      const int meas_wait = 100;
      delay(meas_wait);
      digitalWrite(LED_PIN, LOW);
      int sleepMS = Watchdog.sleep(5000); 
      USBDevice.attach();  // re-attach for M0's USB CDC
      //delay(5000);
      digitalWrite(LED_PIN, HIGH);
  
      delay(meas_wait); 
      digitalWrite(0, HIGH);
       get_time_stamp();
       Serial.print(time_stamp_string);
       Serial.print(F(","));
      digitalWrite(0, LOW);
  
      delay(meas_wait);
      digitalWrite(0, HIGH);
       get_sht30_data();
       Serial.print(temp_humd_string);
      digitalWrite(0, LOW);

    delay(meas_wait);  
    digitalWrite(0, HIGH);
     if (APDS.colorAvailable()) {
       // rrr,ggg,bbb,aaa
       APDS.readColor(r, g, b, a);
       sprintf(color_sensor_string, "%03d, %03d, %03d, %03d", r,g,b,a);
     } else {
       r = 0;
       g = 0;
       b = 0;
       a = 0;
     }
     Serial.print(color_sensor_string);
    digitalWrite(0, LOW);

    delay(meas_wait);
    
    digitalWrite(1, HIGH);
     myFile = SD.open(file_name, FILE_WRITE);
       myFile.print(time_stamp_string);
       myFile.print(",");
       myFile.print(temp_humd_string);
       myFile.print(",");
       myFile.println(color_sensor_string);
     myFile.close();
    digitalWrite(1, LOW);

    Serial.println();
}

void get_time_stamp() {
    DateTime now = rtc.now();

    // 2020-07-08,21:20:57
    sprintf(time_stamp_string, "%d-%02d-%02d,%02d:%02d:%02d",
        now.year(), now.month(), now.day(),
        now.hour(), now.minute(),now.second() );
}


/* This is example for SHT3X-DIS Digital Humidity & Temperature Sensors Arduino Library
ClosedCube SHT31-D [Digital I2C] Humidity and Temperature Sensor Breakout
MIT License
*/
// print_sht30_result("Pooling Mode", sht3xd.readTempAndHumidity(SHT3XD_REPEATABILITY_HIGH, SHT3XD_MODE_POLLING, 50));
void get_sht30_data() {
    SHT31D result = sht3xd.readTempAndHumidity(SHT3XD_REPEATABILITY_HIGH, SHT3XD_MODE_POLLING, 50);
    if (result.error == SHT3XD_NO_ERROR) {
        char temp_str[8];
        dtostrf(result.t, 5, 1, temp_str);

        char humd_str[8];
        dtostrf(result.rh, 5, 1, humd_str);
       // sprintf(temp_humd_string, "%fC,%f%", result.t, result,rh);
        sprintf(temp_humd_string, "%sC,%s%%, ", temp_str, humd_str);
    } else {
        sprintf(temp_humd_string, "ERR:%d, ", result.error);
    }
}
