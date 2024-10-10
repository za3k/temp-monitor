import paho.mqtt.client
import queue
import datetime

class Monitor():
    def __init__(self):
        self.hostname = "192.168.1.17"
        self.port = 1883
        self.q = queue.Queue()
        self.topics = ["#"]

    def start_background(self):
        self.client = paho.mqtt.client.Client()
        self.client.loop_start()
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.connect_async(self.hostname, self.port)

    def on_connect(self, client, _, connect_flags, properties):
        print("Connected")
        for topic in self.topics:
            self.client.subscribe(topic)

    def on_message(self, client, _, message):
        print(message)
        self.q.put((datetime.datetime.utcnow(), message.topic, message.payload))

    def events(self):
        try:
            while True:
                yield self.q.get()
        except queue.ShutDown:
            pass
        except KeyboardInterrupt:
            self.close()

    def close(self):
        self.client.disconnect()
        self.client.loop_stop()
        self.q.shutdown(immediate=True)

if __name__ == "__main__":
    monitor = Monitor()

    monitor.start_background()
    try:
        for event in monitor.events():
            print(event)
    finally:
        monitor.close()
