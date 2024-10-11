This is a personal project. It ingests and displays data from my zigbee temperature sensors. The setup is

    10x zigbee temperature sensor (running on battery)
        |
        v
    zigbee2mqtt bridge (pi4, USB dongle)
        |
        v
    mqtt broker (running on germinate.za3k.com)
        |
        v
    **monitor.py** (paho-mqtt python client)

The database logs all data, forever. It is a 600MB database, preallocated for 64 years. Each record is 10 bytes long. The exact format is given in **database.py**

A live summary is kept of the database (re-generated on boot), with abbreviated statistics like daily highs and lows per sensor. See **state.py**.

On boot, and whenever new data comes in, the dashboard is updated. The current dashboard is text-only. Statistic calculation and display logic are combined. See **display.py** for report generation.

Or, view live updating temperature here: [celsius](https://status.za3k.com/house-temp.c.txt) [fahrenheit](https://status.za3k.com/house-temp.f.txt)
