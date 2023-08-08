import network
import time
import machine
import dht
import json
from umqtt.simple import MQTTClient
import random

# MQTT Server Parameters
MQTT_CLIENT_ID = "actuatorfour"
MQTT_BROKER    = "broker.mqttdashboard.com"
MQTT_USER      = ""
MQTT_PASSWORD  = ""
MQTT_TOPIC     = "polimi/project-p7a"

clientID = 4

# variable that tells if the client already registered to the PAN coordinator
joined = 0

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
  # If we receive a DATA message, then if the message is for us,
  # we need to modify the intensity of our LED accordingly to the received value 
  if(msg['Type'] == 'DATA'):
    if(msg['Destination'] == clientID):
      print('Received data: '+ str(msg['Content']))
      luminosityLevel = int(1023/100*int(msg['Content']))
      print("setting luminosity level to "+ str(luminosityLevel) + " out of 1023")
      led.duty(luminosityLevel)

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
  # This client just need to listen if a DATA message arrives, no need to send anything