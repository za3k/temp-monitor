import datetime
import pytz
import struct

class Display():
    def __init__(self, sensors):
        pass

    def record2human(self, record):
        struct.unpack
        version, row_id, humid, temp, volt, linkquality, batt = struct.unpack("!BBhhHBB", record)
        humid /= 100
        temp /= 100
        return "v{} #{} -- {}% humid -- {}\x00\xb0C -- {}V -- {} link -- {}% batt".format(version, row_id, humid, temp, volt, linkquality, batt)

    def log(self, event):
        sensor, ts, record = event
        ts = pytz.timezone('US/Eastern').localize(ts).strftime("%-I:%M%P")
        print("{}, Sensor #{}\n  {}\n  {}".format(ts, sensor+1, self.record2human(record), record))

    def update(self, state):
        pass # TODO

    def close(self):
        pass
