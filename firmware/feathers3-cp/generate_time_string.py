from datetime import datetime

# Get current date and time
now = datetime.now()

# Format the date and time as a string
#formatted_time = now.strftime("%d,%m,%Y,%H,%M,%S")
  #print("Time string should contain: tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst")

# day of the week
# 0 = monday
# 6 = sunday
day_of_week = now.weekday()
formatted_time = now.strftime(f"T%Y,%m,%d,%H,%M,%S,{day_of_week},-1,-1")

print ("Copy and paste this to the serial term:")
print(formatted_time)