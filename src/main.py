import sys

try:
    import paho.mqtt.client as mqtt
    import json
    import plugins
    from logger import Logger
    from OpParser import Parser
    from time import sleep, ctime
    from threading import Timer
    from Params import Params
    import codecs

    parser = Parser()
    params = Params(parser.options)
    logger = Logger(params.verbose)
    PLUGINS = plugins.init_plugins(logger)

except ModuleNotFoundError as e:
    print(f"Module not found: {e}")
    sys.exit(5)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(5)


def on_connect(client, userdata, flags, reason_code, properties):
    """ 
        callback  on_connect from mqtt client
    """
    logger.msg_info(f"Connected with result code {reason_code}")
    if reason_code.is_failure:
        logger.msg_error(f"Connection to mqtt server failed. Reason code:{reason_code}")
        sys.exit(8)

    for plugin in PLUGINS:
        plugin.on_connect(client, userdata, flags, reason_code, properties)


def on_timer():
    for plugin in PLUGINS:
        plugin.on_timer(client)
    Timer(10, on_timer).start()


def on_message(client, userdata, msg):
    value = codecs.decode(msg.payload, 'unicode-escape')

    logger.msg_debug(f"Topic: {msg.topic} Payload:{value}")
    for plugin in PLUGINS:
        plugin.on_message(client, userdata, msg)


while True:
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.on_connect = on_connect
        client.on_message = on_message
        if params.username and params.password:
            client.username_pw_set(username=params.username, password=params.password)
        if not params.host:
            raise (Exception("host not specified"))
        client.connect(params.host, params.port, params.timeout)
        on_timer()
        client.loop_forever()
    except Exception as e:
        logger.msg_error(e)
        sleep(5)
