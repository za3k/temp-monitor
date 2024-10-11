import datetime
import json
import paho.mqtt.client
import queue
import struct

class Monitor():
    def __init__(self, sensors, topic="zigbee2mqtt/Temperature/#"):
        self.hostname = "192.168.1.17"
        self.port = 1883
        self.sensors = sensors
        self.topic2sensor = {
            d["mqtt_topic"]: i for i,d in enumerate(sensors)
        }
        self.topics = [topic]
        self.q = queue.Queue()
        pass

    def start_background(self):
        self.client = paho.mqtt.client.Client()
        self.client.loop_start()
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.connect_async(self.hostname, self.port)

    def on_connect(self, client, _, connect_flags, properties):
        for topic in self.topics:
            self.client.subscribe(topic)

    def message2record(self, message, ts=None):
        if ts is None:
            ts = datetime.datetime.now(datetime.UTC)
        if message.topic not in self.topic2sensor: return
        i = self.topic2sensor[message.topic]
        payload = json.loads(message.payload)
        batt = payload["battery"]
        humid = payload["humidity"]
        linkquality = payload["linkquality"]
        temp = payload["temperature"]
        volt = payload["voltage"]
        row = struct.pack("!BBhhHBB",
            1,
            self.sensors[i]["row_id"],
            int(humid*100),
            int(temp*100),
            volt,
            linkquality,
            batt, 
        )
        return (i, ts, row)

    def on_message(self, client, _, message):
        record = self.message2record(message)
        if record is None: return
        self.q.put(record)

    def events(self):
        try:
            while True:
                yield self.q.get()
        #except queue.ShutDown:
        #    pass
        except KeyboardInterrupt:
            self.close()

    def close(self):
        self.client.disconnect()
        self.client.loop_stop()
        #self.q.shutdown(immediate=True)
