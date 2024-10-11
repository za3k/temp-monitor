from collections import defaultdict
import copy
import datetime
import pytz
import struct

EPOCH = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.UTC)

# All rooms
UPSTAIRS = [0, 3, 7, 8]
BASEMENT = [5, 6]
GARAGE   = [4]
INSIDE   = UPSTAIRS + BASEMENT
OUTSIDE  = [1, 2]
DISPLAY_ORDER = [1, 2, 0, 3, 7, 8, 4, 6, 5]

GROUPS = {
    "outside": OUTSIDE,
    "inside": INSIDE,
}

class Display():
    def __init__(self, sensors):
        pass

    def record2human(self, record):
        struct.unpack
        version, row_id, humid, temp, volt, linkquality, batt = struct.unpack("!BBhhHBB", record)
        humid /= 100
        temp /= 100
        return "v{} #{} -- {}% humid -- {}°C -- {}V -- {} link -- {}% batt".format(version, row_id, humid, temp, volt, linkquality, batt)

    def log(self, event):
        sensor, ts, record = event
        ts = self.readable_time(ts)
        print("{}, Sensor #{}\n  {}\n  {}".format(ts, sensor+1, self.record2human(record), record))

    @staticmethod
    def readable_time(ts):
        return ts.astimezone(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %-I:%M%P")

    @staticmethod
    def readable_timedelta(td):
        days = td.days
        hours = td.seconds // 3600
        minutes = (td.seconds - hours*3600) // 60
        if days > 100:
            return "offline"
        elif days > 0:
            return "{} days ago".format(days)
        elif hours > 0:
            return "{} hours, {:0>2} min ago".format(hours, minutes)
        else:
            return "{} minutes ago".format(minutes)

    def update(self, state):
        current_temps = self.current_temps(state)
        high_low = self.high_low(state)

        with open("/var/www/public/pub/status/zigbee_temp.txt", "w") as f:
            f.write(current_temps)
            f.write("\n-------------\n\n")
            f.write(high_low)

    def current_temps(self, state):
        now = datetime.datetime.now(datetime.UTC)

        current_temps = "Current Temperatures\n"
        current_temps += "  last updated: {}\n".format(self.readable_time(now))
        current_temps += "\n"
        current_temps += "Sensor                        Temperature  Humidity   Last update\n"
        for sensor in DISPLAY_ORDER:
            temperature = state.temps[sensor]
            humidity = state.humid[sensor]
            last_update = state.last_update[sensor]
            elapsed = self.readable_timedelta(now - last_update)
            human_readable = state.db_metadata[sensor]["human_readable"][5:]
            #current_temps += "Sensor #{: >2} -- {: >5.2f}°C -- {: >6.2f}% humid -- {: <10s} -- {}\n".format(sensor+1, temperature, humidity, elapsed, human_readable)
            current_temps += "{: <27s}   {: >5.2f}°C     {: >6.2f}%     {: <10s}\n".format(human_readable, temperature, humidity, elapsed)
        return current_temps

    def day_graph(self, state):
        now = datetime.datetime.now(datetime.UTC)
        today = now.astimezone(pytz.timezone('US/Eastern')).date()
        yesterday = today - datetime.timedelta(days=1)
        
        hourly = "Hourly Temperature\n"
        hourly += "  last updated: {}\n".format(self.readable_time(now))

        def hour_bucket(ts):
            ts = copy(ts)
            ts.seconds = 0
            ts.microseconds = 0
            ts.minutes = 0
            return ts

    def high_low(self, state):
        now = datetime.datetime.now(datetime.UTC)

        high_low = "Historical highs and lows\n"
        high_low += "  last updated: {}\n".format(self.readable_time(now))

        start_date = EPOCH.astimezone(pytz.timezone('US/Eastern')).date()
        day_count = 365*64

        min_date, max_date = None, None
        report_highs = { groupname: {} for groupname in GROUPS.keys() }
        report_lows = { groupname: {} for groupname in GROUPS.keys() }
        for date in (start_date + datetime.timedelta(n) for n in range(day_count)):
            for groupname, sensors in GROUPS.items():
                highs = report_highs[groupname]
                lows = report_lows[groupname]
                for sensor in sensors:
                    high = state.highs[sensor].get(date)
                    low = state.lows[sensor].get(date)
                    if high and low:
                        if date not in highs or high > highs[date]:
                            highs[date] = high
                        if date not in lows or low < lows[date]:
                            lows[date] = low
                        if min_date is None or date < min_date:
                            min_date = date
                        if max_date is None or date > max_date:
                            max_date = date
        
        def format_temp_range(lo, hi):
            if lo is None or hi is None:
                return "--           "
            else:
                return "{: >5.2f}-{: >5.2f}°C".format(lo, hi)
        actual_day_count = (max_date-min_date).days+1
        for line, date in enumerate(min_date + datetime.timedelta(n) for n in reversed(range(actual_day_count))):
            if line % 50 == 0:
                high_low += "\n2000-00-00   "
                for g in GROUPS.keys():
                    high_low += "{: <16s}".format(g)
                high_low += "\n"
            high_low += "{}   ".format(date.strftime("%Y-%m-%d"))
            for groupname in GROUPS.keys():
                high_low += format_temp_range(report_lows[groupname].get(date), report_highs[groupname].get(date)) + "   "
            high_low += "\n"
            
        return high_low

    def close(self):
        pass
