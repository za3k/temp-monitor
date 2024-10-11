from collections import defaultdict
import datetime
import pytz
import statistics
import struct
import os.path

EPOCH = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.UTC)
TZ    = pytz.timezone('US/Eastern')

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

ABOUT = """
Temperature monitoring is via zigbee sensors running on battery.

Source: https://github.com/za3k/temp-monitor
""".strip()

class Display():
    def __init__(self, sensors, report_dir, report_name):
        self.report_dir = report_dir
        self.report_name = report_name

    def update(self, state):
        for unit in ["c", "f"]:
            current_temps = self.current_temps(state, unit)
            high_low = self.high_low(state, unit)
            hourly = self.hourly(state, unit)

            path = os.path.join(self.report_dir, self.report_name.format(unit=unit))
            with open(path, "w") as f:
                f.write("\n-------------\n\n".join([
                    current_temps,
                    hourly,
                    high_low,
                    ABOUT
                ]))

    def log(self, event):
        sensor, ts, record = event
        ts = self.readable_time(ts)
        print("{}, Sensor #{}\n  {}\n  {}".format(ts, sensor+1, self.record2human(record), record))

    def record2human(self, record):
        struct.unpack
        version, row_id, humid, temp, volt, linkquality, batt = struct.unpack("!BBhhHBB", record)
        humid /= 100
        temp /= 100
        return "v{} #{} -- {}% humid -- {}°C -- {}V -- {} link -- {}% batt".format(version, row_id, humid, temp, volt, linkquality, batt)

    def close(self):
        pass

    @staticmethod
    def readable_time(ts):
        return ts.astimezone(TZ).strftime("%Y-%m-%d %-I:%M%P")

    @staticmethod
    def readable_date(d):
        if d == " ":
            return "          "
        return d.strftime("%Y-%m-%d")

    @staticmethod
    def readable_hour(ts):
        if ts == " ":
            return "               "
        return ts.astimezone(TZ).strftime("%Y-%m-%d %I%P").replace(" 0", "  ")

    @staticmethod
    def readable_timedelta(td):
        days = td.days
        hours = td.seconds // 3600
        minutes = (td.seconds - hours*3600) // 60
        if days > 100:
            return "never"
        elif days > 0:
            return "{} days ago".format(days)
        elif hours > 0:
            return "{} hours, {:0>2} min ago".format(hours, minutes)
        else:
            return "{} minutes ago".format(minutes)

    @staticmethod
    def c2f(x):
        return x*9/5+32

    @staticmethod
    def readable_temp(x, unit):
        if x is None:
            return "--------"
        elif x == " ":
            return "        "
        elif unit == "f":
            return "{: >6.2f}°F".format(Display.c2f(x))
        else:
            assert unit == "c"
            return "{: >6.2f}°C".format(x)

    @staticmethod
    def readable_humidity(x):
        if x is None:
            return "-------"
        else:
            return "{: >6.2f}%".format(x)

    @staticmethod
    def readable_temp_range(lo, hi, unit):
        if lo is None or hi is None:
            return "-----------------"
        elif lo == " ":
            return "                 "
        elif unit == "f":
            return "{: >6.2f} - {: >6.2f}°F".format(Display.c2f(lo), Display.c2f(hi))
        else:
            assert unit == "c"
            return "{: >6.2f} - {: >6.2f}°C".format(lo, hi)

    def current_temps(self, state, unit):
        now = datetime.datetime.now(datetime.UTC)

        current_temps = "Current Temperature\n"
        current_temps += "  last updated: {}\n".format(self.readable_time(now))
        current_temps += "\n"
        current_temps += "Sensor                        Temperature  Humidity    Last update\n"
        for sensor in DISPLAY_ORDER:
            temperature = self.readable_temp(state.temps[sensor] or None, unit)
            humidity = self.readable_humidity(state.humid[sensor] or None)
            last_update = state.last_update[sensor]
            elapsed = self.readable_timedelta(now - last_update)
            human_readable = state.db_metadata[sensor]["human_readable"][5:]
            current_temps += "{: <27s}   {}     {}     {: <10s}\n".format(human_readable, temperature, humidity, elapsed)
        return current_temps

    def hourly(self, state, unit):
        now = datetime.datetime.now(datetime.UTC)
        today = now.astimezone(TZ).date()
        yesterday = today - datetime.timedelta(days=1)
        
        hourly = "Hourly Temperature\n"
        hourly += "  last updated: {}\n".format(self.readable_time(now))
        hourly += "\n"

        def hour_bucket(ts):
            return ts.replace(second=0, microsecond=0, minute=0)
        def format_temp(xs):
            if xs is None or len(xs) == 0:
                return self.readable_temp(None, unit)
            else:
                return self.readable_temp(statistics.mean(xs), unit)

        report_hours = {groupname: {} for groupname in GROUPS.keys()}
        buckets = set()
        for groupname, sensors in GROUPS.items():
            for sensor in sensors:
                for ts, temp in state.timeseries[sensor]:
                    hour = hour_bucket(ts)
                    buckets.add(hour)
                    if hour not in report_hours[groupname]:
                        report_hours[groupname][hour] = []

                    report_hours[groupname][hour].append(temp)

        hourly += "{}   ".format(self.readable_hour(" "))
        for groupname in GROUPS.keys():
            hourly += "{: <11s}".format(groupname)
        hourly += "\n"
        for hour in sorted(buckets):
            hourly += "{}   ".format(self.readable_hour(hour))
            for groupname in GROUPS.keys():
                hourly += "{}   ".format(format_temp(
                    report_hours[groupname].get(hour)))
            hourly += "\n"

        return hourly

    def high_low(self, state, unit):
        now = datetime.datetime.now(datetime.UTC)

        high_low = "Historical highs and lows\n"
        high_low += "  last updated: {}\n".format(self.readable_time(now))

        start_date = EPOCH.astimezone(TZ).date()
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
        
        actual_day_count = (max_date-min_date).days+1
        for line, date in enumerate(min_date + datetime.timedelta(n) for n in reversed(range(actual_day_count))):
            if line % 50 == 0:
                high_low += "\n{}   ".format(self.readable_date(" "))
                for g in GROUPS.keys():
                    high_low += "{: <20s}".format(g)
                high_low += "\n"
            high_low += "{}   ".format(self.readable_date(date))
            for groupname in GROUPS.keys():
                high_low += self.readable_temp_range(report_lows[groupname].get(date), report_highs[groupname].get(date), unit) + "   "
            high_low += "\n"
            
        return high_low
