# This example was adapted from the paho MQTT documentation.
# https://pypi.org/project/paho-mqtt/#getting-started

import ssl
import paho.mqtt.client as mqtt

from paho.mqtt.enums import CallbackAPIVersion


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("status_message")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


MQTT_CLIENT_ID = f"EXAMPLE-PROGRAM"  # Tip: use a meaningful name (such as the name of your program).
# Setting this name to something meaningful makes troubleshooting easier.
# The client ID is logged by the MQTT server when the program connects.

# Specify the paths to CA cert, client cert, and private key.
CA_CERT = "./CAs.crt"
CLIENT_CERT = "./user123.crt"
PRIVATE_KEY = "./user123.key"

# create a Client object
client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)

# configure the client to connect using mTLS with the CA cert, client cert, private key.
client.tls_set(
    ca_certs=CA_CERT,
    certfile=CLIENT_CERT,
    keyfile=PRIVATE_KEY,
    tls_version=ssl.PROTOCOL_TLS,
    ciphers=None
)


client.on_connect = on_connect
client.on_message = on_message

client.connect(host ="a3dpdfmwa109lg-ats.iot.us-east-2.amazonaws.com", port = 8883)
client.loop_start()
