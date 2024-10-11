import display
import database
import monitor
import state
import sys

SENSORS=[
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor01", "row_id": 1, "human_readable": "01 - Upstairs - Dining Room"},
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor02", "row_id": 2, "human_readable": "02 - Outside - Front"},
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor03", "row_id": 3, "human_readable": "03 - Outside - Back"},
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor04", "row_id": 4, "human_readable": "04 - Upstairs - Bedroom - Za3k"},
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor05", "row_id": 5, "human_readable": "05 - Upstairs - Garage"},
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor06", "row_id": 6, "human_readable": "06 - Basement - Workshop"},
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor07", "row_id": 7, "human_readable": "07 - Basement - HVAC/Server"},
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor08", "row_id": 8, "human_readable": "08 - Upstairs - Bedroom - Master"},
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor09", "row_id": 9, "human_readable": "09 - Upstairs - Kitchen"},
    {"mqtt_topic": "zigbee2mqtt/Temperature/Sensor10", "row_id":10, "human_readable": "10 - Reserved"},
]

if __name__ == "__main__":
    db = database.Database(sensors=SENSORS, path="test.db")
    state = state.State(db, path="test.db.cache")
    sensors = state.sensors()
    display = display.Display(sensors)
    monitor = monitor.Monitor(sensors)

    try:
        monitor.start_background()
        display.update(state)
        print("Loaded.", file=sys.stderr)
        for event in monitor.events():
            display.log(event)
            db.write_ts(*event)
            state.update(*event)
            display.update(state)
    finally:
        monitor.close()
        state.close()
        db.close()
        display.close()
