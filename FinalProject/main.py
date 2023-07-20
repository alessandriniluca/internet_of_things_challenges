import network
import time
import machine
import dht
import json
from umqtt.simple import MQTTClient
import random

# MQTT Server Parameters
MQTT_CLIENT_ID = "testb" # change it accordingly to your client
MQTT_BROKER    = "broker.mqttdashboard.com"
MQTT_USER      = ""
MQTT_PASSWORD  = ""
MQTT_TOPIC     = "polimi/project-p7a"
CLIENT_TYPE    = "LED" #HUMIDITY or LED

clientID = 3 # change accordingly to your client

joined = 0

timestampToSend = 0

led = machine.PWM(machine.Pin(13), freq=1000)
led.duty(0)
sensor = dht.DHT22(machine.Pin(15))

def incomingProcessing(topic,msg):
  global joined
  global timestampToSend
  msg = json.loads(msg)
  print(msg['type'])
  if(msg['type'] == 'BEACON'):
    if(joined == 0):
      waitingTime = float(msg['slotDuration'])
      print('wait for: ' + str(waitingTime))
      time.sleep(waitingTime)
      message = json.dumps({
        "type": "REGISTER",
        "address": clientID
      })
      client.publish(MQTT_TOPIC, message)
      joined =1
    else:
      print( msg['timestamp'])
      print(time.time())
      print(msg['CFPReservation'])
      res = json.loads(msg['CFPReservation'])
      if(clientID in res):
        print(res.index(clientID))
        waitingTime = float(msg['slotDuration'])*(1+int((msg['CAPSlots']))+res.index(clientID))
        print('wait for: ' + str(waitingTime))
        timestampToSend = time.time() + waitingTime
  if(msg['type'] == 'DATA'):
    if(msg['destination'] == clientID and CLIENT_TYPE == "LED"):
      print('Received data: '+ str(msg['content']))
      luminosityLevel = int(1023/100*int(msg['content']))
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
  if (timestampToSend != 0 and time.time() >= timestampToSend and CLIENT_TYPE == "HUMIDITY"):
    sensor.measure()
    message = json.dumps({
      "type": "DATA",
      "destination": random.randint(1,1),
      "content": sensor.humidity()
    })
    client.publish(MQTT_TOPIC, message)
    print('sending' + message)
    timestampToSend =0