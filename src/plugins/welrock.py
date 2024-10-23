import json
from datetime import datetime

# callback
WELROKPREFIX = "house"
DEVICE_ID = "az_8C264C"
GETWELROKPREFIX = f"{WELROKPREFIX}/{DEVICE_ID}/get"
SETWELROKPREFIX = f"{WELROKPREFIX}/{DEVICE_ID}/set"

GETHAPREFIX = f"{WELROKPREFIX}/termostat/get"
SETHAPREFIX = f"{WELROKPREFIX}/termostat/set"

STATUSHATOPIC = "homeassistant/status"
DISCOVERY_TOPIC = f"homeassistant/climate/{DEVICE_ID}/config"

DISCOVERY = {
    "name": "Корякино",
    "optimistic": "true",
    "object_id": f"{GETHAPREFIX }/welrok",
    "availability_topic": f"{GETHAPREFIX}/available",
    "mode_command_topic": f"{SETHAPREFIX}/mode",
    "mode_state_topic": f"{GETHAPREFIX }/mode",
    "current_temperature_topic": f"{GETHAPREFIX}/floorTemp",
    "temperature_command_topic": f"{SETHAPREFIX }/setTemp",
    "temperature_state_topic": f"{GETHAPREFIX}/setTemp",
    "temperature_unit": "C",
    "max_temp": 45,
    "min_temp": 5,
    "temp_step": 1,
    "modes": ("off", "auto", "heat"),
    "device": {
        "identifiers": DEVICE_ID,
        "name": "Термостат",
        "model": "Welrok AZ"
    }
}

CONFIG_SENSOR_TOPIC = "homeassistant/sensor/XXXIDXXX/config"

SENSOR_setTemp = {
    "object_id": f"{DEVICE_ID}_1",
    "name": "Целевая температура",
    "state_topic": f"{GETWELROKPREFIX}/setTemp",
    "unit_of_measurement": "°C",
    "device_class": "temperature",
    "device": {
        "identifiers": DEVICE_ID
    }
}

SENSOR_floorTemp = {
    "object_id": f"{DEVICE_ID}_2",
    "name": "Температура в комнате",
    "state_topic": f"{GETWELROKPREFIX}/floorTemp",
    "unit_of_measurement": "°C",
    "device_class": "temperature",
    "device": {
        "identifiers": DEVICE_ID
    }
}

SENSOR_load = {
    "object_id": f"{DEVICE_ID}_3",
    "name": "Нагрев 1-вкл",
    "state_topic": f"{GETWELROKPREFIX}/load",
    "device": {
        "identifiers": DEVICE_ID
    }
}
SENSOR_mode = {
    "object_id": f"{DEVICE_ID}_4",
    "name": "Режим 3/5",
    "state_topic": f"{GETWELROKPREFIX}/mode",
    "device": {
        "identifiers": DEVICE_ID
    }
}

SENSOR_powerOff = {
    "object_id": f"{DEVICE_ID}_5",
    "name": "Режим 0-вкл",
    "state_topic": f"{GETWELROKPREFIX}/powerOff",
    "device": {
        "identifiers": DEVICE_ID
    }
}

SENSOR_timestamp = {
    "object_id": f"{DEVICE_ID}_6",
    "name": "Обновление",
    "state_topic": f"{GETHAPREFIX}/timestamp",
    "device": {
        "identifiers": DEVICE_ID
    }
}

SENSOR_timeout = {
    "object_id": f"{DEVICE_ID}_7",
    "name": "Таймаут обновлений",
    "state_topic": f"{GETHAPREFIX }/timeout",
    "device": {
        "identifiers": DEVICE_ID
    }
}


CONFIG_SENSOR = [SENSOR_setTemp, SENSOR_floorTemp, SENSOR_load, SENSOR_mode, SENSOR_powerOff, SENSOR_timestamp, SENSOR_timeout]


class Data:
    protTemp: float
    floorTemp: float
    setTemp: float
    mode: int
    load: int
    powerOff: int
    timestamp: str = "---"

    def set(self, attr, payload):
        if attr in self.__annotations__:
            value = (self.__annotations__[attr])(payload)
            setattr(self, attr, value)
            self.timestamp = datetime.now().strftime("%H:%M:%S")
            return True
        else:
            return False

    def ready(self):
        for attr in self.__annotations__:
            if not hasattr(self, attr):
                return False
        return True

    def process(self):
        if not self.ready():
            return {}

        result = {}
        if self.powerOff == 1:
            result["mode"] = "off"
        elif self.load == 1:
            result["mode"] = "heat"
        else:
            result["mode"] = "auto"

        for attr in "protTemp", "floorTemp", "setTemp":
            result[attr] = round(float(getattr(self, attr)), 1)

        if self.mode == 3:
            result["preset"] = "manual"
        else:
            result["preset"] = "schedule"

        result["src_mode"] = self.mode
        result["src_load"] = self.load
        result["src_powerOff"] = self.powerOff
        result["timestamp"] = self.timestamp

        return result


class Plugin:
    last_update: datetime = datetime.now()

    def __init__(self, logger) -> None:
        self.data = Data()
        self.logger = logger

    def on_timer(self, client):
        delta = datetime.now() - self.last_update
        self.logger.msg_debug(f"Seconds after last update: {delta.seconds}")

        if delta.seconds < 90:
            payload = "online"
        else:
            payload = "offline"
        client.publish(f"{GETHAPREFIX}/available", payload)
        client.publish(f"{GETHAPREFIX}/timeout", delta.seconds)



    def on_connect(self, client, userdata, flags, reason_code, properties):
        for prefix in GETWELROKPREFIX, SETHAPREFIX:
            client.subscribe(f"{prefix}/#")
        client.subscribe(STATUSHATOPIC)
        client.subscribe(f"homeassistant/#")
        self.send_config(client)

    def on_message(self, client, userdata, msg):
        topic = str(msg.topic)
        attr = topic.split("/")[-1]
        if GETWELROKPREFIX in topic:
            self.on_get_message(client, attr, msg.payload)
        if SETHAPREFIX in topic:
            self.on_set_message(client, attr, msg.payload)
        if STATUSHATOPIC in topic:
            self.on_change_status(client, attr, msg.payload)

    def on_change_status(self, client, attr, payload):
        if payload == b"online":
            self.send_config(client)

    def send_config(self, client):
        client.publish(DISCOVERY_TOPIC, json.dumps(DISCOVERY))

        for config in CONFIG_SENSOR:
            topic = CONFIG_SENSOR_TOPIC.replace("XXXIDXXX", config["object_id"])
            client.publish(topic, json.dumps(config))

    def on_get_message(self, client, attr, payload):
        if self.data.set(attr, payload) and self.data.ready():
            self.logger.msg_debug("ready to process")
            self.last_update = datetime.now()
            data = self.data.process()
            for attr in data:
                client.publish(f"{GETHAPREFIX}/{attr}", data[attr])
            self.data = Data()

    def on_set_message(self, client, attr, payload):
        if attr == "mode":
            if payload == b"off":
                client.publish(f"{SETWELROKPREFIX}/powerOff", 1)
            else:
                client.publish(f"{SETWELROKPREFIX}/powerOff", 0)
        elif attr in ("setTemp", "bright"):
            client.publish(f"{SETWELROKPREFIX}/{attr}", payload)


def init(logger):
    return Plugin(logger=logger)
