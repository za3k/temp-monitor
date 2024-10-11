import datetime
import struct
import pytz

EPOCH = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.UTC)
TZ = pytz.timezone('US/Eastern')

class RollingTimeseries():
    def __init__(self, duration=datetime.timedelta(days=2)):
        self.t = []
        self.duration = duration

    def add(self, ts, point):
        now = datetime.datetime.now(datetime.UTC)
        cutoff = now - self.duration
        if ts >= cutoff:
            self.t.append((ts, point))

    def __iter__(self):
        self._prune()
        return iter(self.t)

    def _prune(self):
        now = datetime.datetime.now(datetime.UTC)
        cutoff = now - self.duration
        self.t = [x for x in self.t if x[0] >= cutoff]

class State():
    def __init__(self, db, path=None):
        if path is None: path = db.path + ".cache"

        self.db_metadata = db.get_all_metadata()
        self.num_sensors = len(self.db_metadata)
        sensors = range(self.num_sensors)

        # Data
        self.temps = [0 for _ in sensors]
        self.humid = [0 for _ in sensors]
        self.last_update = [EPOCH for _ in sensors]
        # TODO
        self.highs = [{} for _ in sensors]
        self.lows = [{} for _ in sensors]
        self.timeseries = [RollingTimeseries() for _ in sensors] # Cover the last 24 hours

        # TODO: Load from cache
        self.load_from_db(db)

    def load_from_db(self, db):
        for e in db.read_all():
            self.update(*e)

    def sensors(self):
        return self.db_metadata

    def update(self, sensor, ts, record):
        # Load the data
        version, row_id, humid, temp, volt, linkquality, batt = struct.unpack("!BBhhHBB", record)
        humid /= 100
        temp /= 100
        
        self._update(sensor, ts, humid, temp)

    def _update(self, sensor, ts, humid, temp):
        self.temps[sensor] = temp
        self.humid[sensor] = humid
        self.last_update[sensor] = ts

        date = ts.astimezone(TZ).date()
        if date not in self.highs[sensor]:
            self.highs[sensor][date] = temp
        else:
            self.highs[sensor][date] = max(self.highs[sensor][date], temp)
        if date not in self.lows[sensor]:
            self.lows[sensor][date] = temp
        else:
            self.lows[sensor][date] = min(self.lows[sensor][date], temp)

        self.timeseries[sensor].add(ts, temp)

    def close(self):
        # TODO: Save to cache
        pass
