#!/usr/bin/env python3
import display
import database
import monitor
import state
import sys

# To add a new sensor
# (1) Back up the code and databse
# (2) Add the sensor to the array below. APPEND ONLY. Modify the analysis lists in display.py using the display numbers
# (3) Restart the running service
SENSORS=[
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor10", "row_id":10, "human_readable": "10 - Upstairs - Dining Room"},       # Display: 0
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor02", "row_id": 2, "human_readable": "02 - Outside - Front"},              # Display: 1
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor03", "row_id": 3, "human_readable": "03 - Outside - Back"},               # Display: 2
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor04", "row_id": 4, "human_readable": "04 - Upstairs - Bedroom - Za3k"},    # Display: 3
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor05", "row_id": 5, "human_readable": "05 - Upstairs - Garage"},            # Display: 4
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor06", "row_id": 6, "human_readable": "06 - Basement - Workshop (dead)"},   # Display: 5
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor07", "row_id": 7, "human_readable": "07 - Basement - HVAC/Server"},       # Display: 6
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor08", "row_id": 8, "human_readable": "08 - Upstairs - Bedroom - Master"},  # Display: 7
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor09", "row_id": 9, "human_readable": "09 - Upstairs - Kitchen"},           # Display: 8
    {"mqtt_topic": "zigbee2mqtt/Temperature/REMOVED ", "row_id": 10, "human_readable": "REMOVED"},                          # Display: 9
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor11", "row_id": 11, "human_readable": "11 - Outside - Side"},              # Display: 10
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor12", "row_id": 12, "human_readable": "12 - Outside - AC Exhaust"},        # Display: 11
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor13", "row_id": 13, "human_readable": "13 - Basement - Workshop"},         # Display: 12
]

if __name__ == "__main__":
    db = database.Database(sensors=SENSORS, path="temps.db")
    #self.write_metadata(9, sensors[9])
    state = state.State(db, path="temps.db.cache")
    sensors = state.sensors()
    display = display.Display(sensors, report_dir="/var/www/public/pub/status", report_name="house-temp.{unit}.txt")
    monitor = monitor.Monitor(sensors)

    try:
        monitor.start_background()
        display.update(state)
        print("Loaded.", file=sys.stderr)
        for event in monitor.events():
            #print(event)
            display.log(event)
            db.write_ts(*event)
            state.update(*event)
            display.update(state)
    finally:
        monitor.close()
        state.close()
        db.close()
        display.close()
