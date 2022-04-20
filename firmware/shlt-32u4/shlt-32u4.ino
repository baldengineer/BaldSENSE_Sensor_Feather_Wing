

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

// stuff for SD Card
#include <SPI.h>
#include <SD.h>

ClosedCube_SHT31D sht3xd;


// Global Stuff
char time_stamp_string[21];
char temp_humd_string[16];
File myFile;

// RTC Stuff
RTC_DS3231 rtc;
//char daysOfTheWeek[7][12] = {"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"};

// State Machine stuff
unsigned long previous_print_millis = 0;
unsigned long print_interval = 2500;

byte init_rtc() {
  if (!rtc.begin()) {
    Serial.println("Couldn't find RTC");
    return 0; // failed to get rtc
  }

  if (rtc.lostPower()) {
    Serial.println("RTC lost power, lets set the time!");
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
    Serial.println("ClosedCube SHT3X-D Single Shot Mode Example");
    Serial.println("supports SHT30-D, SHT31-D and SHT35-D");

    sht3xd.begin(0x44); // I2C address: 0x44 or 0x45

    Serial.print("Serial #");
    Serial.println(sht3xd.readSerialNumber());

    return 1;
}

byte init_sdcard() {
    Serial.print("Initializing SD card...");

    if (!SD.begin(A1)) {
        Serial.println("initialization failed!");
        return 0; // fail!
    }
    Serial.println("initialization done.");
    myFile = SD.open("test.txt", FILE_WRITE);

    // if file opened okay:
    if (myFile) {
        Serial.print("Writing Header to SD...");
        myFile.println("DATE, TIME, Temperature, Humidity");
        myFile.close();
        Serial.println("done!");
    } else {
        return 0; // couldn't write
    }
    return 1;
}

void setup () {
    Wire.begin();
    Serial.begin(9600);
    //while(!Serial);

    delay(3000); // wait for console opening

    // connect to sd card
    init_sdcard();

    // connect to SHT30 (temp and sensor)
    init_sht30();

    // connect to DS3231 (real-time clock)
    init_rtc();

}

void loop () {

    unsigned current_millis = millis();
    if (current_millis - previous_print_millis >= print_interval) {
        get_time_stamp();
        Serial.print(time_stamp_string);
        Serial.print(",");

        get_sht30_data();
        Serial.print(temp_humd_string);

        myFile = SD.open("test.txt", FILE_WRITE);
         myFile.print(time_stamp_string);
         myFile.print(",");
         myFile.println(temp_humd_string);
        myFile.close();

        //sht30 stuff.
      //  print_sht30_result("ClockStrech Mode", sht3xd.readTempAndHumidity(SHT3XD_REPEATABILITY_LOW, SHT3XD_MODE_CLOCK_STRETCH, 50));
      //  delay(250);
     //   print_sht30_result("Pooling Mode", sht3xd.readTempAndHumidity(SHT3XD_REPEATABILITY_HIGH, SHT3XD_MODE_POLLING, 50));

        Serial.println();

        // reset the clock
        previous_print_millis = current_millis;
    }

//    delay(3000);
}

void get_time_stamp() {
    DateTime now = rtc.now();

    // 2020-07-08,21:20:57

    sprintf(time_stamp_string, "%d-%02d-%02d,%02d:%02d:%02d",
        now.year(),
        now.month(),
        now.day(),
        now.hour(),
        now.minute(),
        now.second()
        );
/*    
    Serial.print(now.year(), DEC);
    Serial.print('-');
    Serial.print(now.month(), DEC);
    Serial.print('-');
    Serial.print(now.day(), DEC);

    Serial.print(" (");
    Serial.print(daysOfTheWeek[now.dayOfTheWeek()]);
    Serial.print(") ");
    Serial.print(",");
    Serial.print(now.hour(), DEC);
    Serial.print(':');
    Serial.print(now.minute(), DEC);
    Serial.print(':');
    Serial.print(now.second(), DEC);
    Serial.println();
    */


/*    
    Serial.print(" since midnight 1/1/1970 = ");
    Serial.print(now.unixtime());
    Serial.print("s = ");
    Serial.print(now.unixtime() / 86400L);
    Serial.println("d");

   
    // calculate a date which is 7 days and 30 seconds into the future
    DateTime future (now + TimeSpan(7,12,30,6));
    
    Serial.print(" now + 7d + 30s: ");
    Serial.print(future.year(), DEC);
    Serial.print('/');
    Serial.print(future.month(), DEC);
    Serial.print('/');
    Serial.print(future.day(), DEC);
    Serial.print(' ');
    Serial.print(future.hour(), DEC);
    Serial.print(':');
    Serial.print(future.minute(), DEC);
    Serial.print(':');
    Serial.print(future.second(), DEC);
    Serial.println();*/
    
  //  Serial.println();
}


/* This is example for SHT3X-DIS Digital Humidity & Temperature Sensors Arduino Library
ClosedCube SHT31-D [Digital I2C] Humidity and Temperature Sensor Breakout
MIT License
*/

// print_sht30_result("Pooling Mode", sht3xd.readTempAndHumidity(SHT3XD_REPEATABILITY_HIGH, SHT3XD_MODE_POLLING, 50));

void get_sht30_data() {
    SHT31D result = sht3xd.readTempAndHumidity(SHT3XD_REPEATABILITY_HIGH, SHT3XD_MODE_POLLING, 50);
    if (result.error == SHT3XD_NO_ERROR) {
        // 100.0C,100.0%


       // Serial.print(text);
      //  Serial.print(",T=");
//}

/*dtostrf(floatvar, StringLengthIncDecimalPoint, numVarsAfterDecimal, charbuf);

where
floatvar    float variable
StringLengthIncDecimalPoint     This is the length of the string that will be created
numVarsAfterDecimal     The number of digits after the deimal point to print
charbuf     the array to store the results*/

        char temp_str[8];
        dtostrf(result.t, 5, 1, temp_str);

        char humd_str[8];
        dtostrf(result.rh, 5, 1, humd_str);
       // sprintf(temp_humd_string, "%fC,%f%", result.t, result,rh);
        sprintf(temp_humd_string, "%sC,%s%%", temp_str, humd_str);

   /*     Serial.print(",");
        Serial.print(result.t);
        //Serial.print("C, RH=");
        Serial.print("C,");
        Serial.print(result.rh);
        Serial.println("%");*/
    } else {
        //Serial.print(text);
      /*  Serial.print(":[ERROR] Code #");
        Serial.println(result.error);*/
        sprintf(temp_humd_string, "ERR:%d", result.error);
    }
}
