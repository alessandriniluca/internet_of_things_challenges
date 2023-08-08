import network
import time
import machine
import dht
import json
from umqtt.simple import MQTTClient
import random

# MQTT Server Parameters
MQTT_CLIENT_ID = "sensortwo"
MQTT_BROKER    = "broker.mqttdashboard.com"
MQTT_USER      = ""
MQTT_PASSWORD  = ""
MQTT_TOPIC     = "polimi/project-p7a"

clientID = 2

# variable that tells if the client already registered to the PAN coordinator
joined = 0

timestampToSend = 0

led = machine.PWM(machine.Pin(13), freq=1000)
led.duty(0)
sensor = dht.DHT22(machine.Pin(15))

def incomingProcessing(topic,msg):
  global joined
  global timestampToSend
  msg = json.loads(msg)
  print(msg['Type'])
  if(msg['Type'] == 'BEACON'):
    # If the client has not joined yet the networ, when receiving a beacon needs to send the register request
    if(joined == 0):
      # supposing the beacon arrives in the same time in which it is sent, we need to wait the slot reserved to the beacon.
      # after that slot, the CAP start, and we can send the registering request.
      waitingTime = float(msg['SlotDuration']*random.randint(0,(msg['CAPSlots']-1)))
      print('wait for: ' + str(waitingTime))
      time.sleep(waitingTime)
      message = json.dumps({
        "Type": "REGISTER",
        "From": clientID
      })
      client.publish(MQTT_TOPIC, message)
      joined =1
    else:
      # We need to wait our turn before sending the humidity value. We need to compute our turn 
      # according to the information contained in the beacon message.
      print(time.time())
      print(msg['CFPReservation'])
      res = json.loads(msg['CFPReservation'])
      if(clientID in res):
        print(res.index(clientID))
        # For the waiting time we do not consider the slot reserved to the beacon, since when we are able to decode 
        # it, the slot of the beacon has already finished, and the CAP has just started
        waitingTime = float(msg['SlotDuration'])*(int((msg['CAPSlots']))+res.index(clientID))
        print('wait for: ' + str(waitingTime))
        timestampToSend = time.time() + waitingTime

print("Connecting to WiFi", end="")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('Wokwi-GUEST', '')
while not sta_if.isconnected():
  print(".", end="")
  time.sleep(0.1)
print(" Connected!")

print("Connecting to MQTT server... ", end="")
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, user=MQTT_USER, password=MQTT_PASSWORD, ssl= False)

client.set_callback(incomingProcessing)
client.connect(False)

print("Connected!")


client.subscribe(MQTT_TOPIC)
while True:
  client.check_msg()
  # If we are a client of type humidity, then we need to check the timestamp (in order to be 
  # sure to be in our reserved slot in the CAP), and then we need to send the message.
  if (timestampToSend != 0 and time.time() >= timestampToSend):
    sensor.measure()
    # As specified above, 1 and 2 sends to 3 and 4.
    destination = random.randint(3,4)
    # The message will be a data message with the actual value of the humidity read of the sensor
    message = json.dumps({
      "Type": "DATA",
      "From": clientID,
      "Destination": destination,
      "Content": sensor.humidity()
    })
    client.publish(MQTT_TOPIC, message)
    print('sending' + message)
    timestampToSend =0