"""
A database for temperature sensors. 

The format of the file is 10 concatenated databases of 67.3768MB, one per sensor. The file is pre-allocated and will never grow (unless new sensors are added).

Each database consists of a 100K header, then a 67.2768MB section of fixed-size records. 

The header consists of JSON objects, one per line. The first object is always an integer version number. The final JSON is terminated by a newline, and then padded by zeros to fill the section to 100K total.
    The current version has these objects:
        1. The fixed number 1 (the version)
        2. Metadata about the sensor (mqtt topic, row #, human-readable name)

Then, there are a large number of fixed-size records. Each record corresponds to a 5-minute interal between 2024-01-01 00:00 UTC and 2087-12-31 11:59:59 UTC. The temperature sensors are supposed to report every 10 minutes, or if there's a large temperature or humidity shift.

The format of a temperature record is these 10 bytes:

|_____|_____|_____|_____|_____|_____|_____|_____|_____|_____| Byte
|Ver  |#    |Humidity   |Temp       |Volt       |Link |Batt | Field
             0.01%       0.01C       ?           0-100 1%    Units

Version is always 1.
# is the number of the sensor, from 1-10. If a sensor is repurposed, its number should change.
Voltage is in unknown integer units.

An all-zero record indicates no data.
"""

import json
import math
import os.path
import datetime

SENSOR_LENGTH = 67_376_800
SENSOR_ROWS = 64 * 365 * 24 * int(60/5)
EPOCH = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.UTC)

class Database():
    def __init__(self, sensors, path):
        self.path = path
        if not os.path.exists(path):
            self.make_database(sensors, path)
        self.f = open(path, "r+b")
        self.metadata = self.get_all_metadata()

    def make_database(self, sensors, path):
        # Make a file
        self.f = open(path, "wb")

        # Filled it with zeros
        for i in range(len(sensors)):
            self.f.write(b'\0' * SENSOR_LENGTH)

        # Write the metadata
        for i in range(len(sensors)):
            self.write_metadata(i, [1, sensors[i]])

    def write_metadata(self, n, jsons):
        md = "".join(json.dumps(j) + "\n" for j in jsons)
        md = md.encode('utf8')
        assert len(md) < 100_000
        self.f.seek(SENSOR_LENGTH*n)
        self.f.write(md)

    def count_sensors(self):
        self.f.seek(0, os.SEEK_END)
        length = self.f.tell()
        assert length % SENSOR_LENGTH == 0
        return length // SENSOR_LENGTH

    def get_all_metadata(self):
        return [self.get_metadata(i) for i in range(self.count_sensors())]

    def get_metadata(self, n):
        self.f.seek(SENSOR_LENGTH*n)
        section = self.f.read(100_000)
        section = section.split(b'\n\0', 1)[0]

        # Assert the format is version 1
        assert section.startswith(b'1\n')

        # Decode JSON objects
        parts = section.decode('utf8').split("\n")
        version, md = [json.loads(x) for x in parts]

        return md

    def rownum2ts(self, i):
        return EPOCH + datetime.timedelta(minutes=5*i)

    def ts2rownum(self, ts):
        ROW_SECONDS = 5 * 60
        elapsed = ts - EPOCH
        return math.floor(elapsed.total_seconds() / ROW_SECONDS)

    def read_all_sensor(self, sensor):
        # Iterate over all records for one sensor as (sensor, ts, record) tuples
        # Records go from oldest to newest
        self.f.seek(SENSOR_LENGTH*sensor + 100_000)
        preload = self.f.read(SENSOR_LENGTH - 100_000)
        for rownum, x in enumerate(preload[::10]):
            if x != 0:
                record = preload[rownum*10:rownum*10+10]
                yield (sensor, self.rownum2ts(rownum), record)

    def read_all(self):
        # Iterate over all records as (ts, sensor, record) tuples
        # Records go from oldest to newest within each sensor
        # Sensors may be grouped or interleaved.
        # TODO: n-way merge, return interleaved
        for sensor in range(self.count_sensors()):
            yield from self.read_all_sensor(sensor)

    def read_ts(self, sensor, ts):
        return self.read_rownum(sensor, self.ts2rownum(ts))
        
    def read_rownum(self, sensor, rownum):
        self.f.seek(SENSOR_LENGTH*sensor + 100_000 + rownum*10)
        record = self.f.read(10)
        if record != b'\0\0\0\0\0\0\0\0\0\0':
            return (sensor, self.rownum2ts(rownum), record)

    def write_ts(self, sensor, ts, record10):
        self.write_rownum(sensor, self.ts2rownum(ts), record10)

    def write_rownum(self, sensor, rownum, record10):
        self.f.seek(SENSOR_LENGTH*sensor + 100_000 + rownum*10)
        assert len(record10) == 10
        self.f.write(record10)

    def close(self):
        self.f.close()
