import network
import time
import machine
import dht
import json
from umqtt.simple import MQTTClient
import random

# MQTT Server Parameters
MQTT_CLIENT_ID = "ffc1" # change it accordingly to your client
MQTT_BROKER    = "broker.mqttdashboard.com"
MQTT_USER      = ""
MQTT_PASSWORD  = ""
MQTT_TOPIC     = "polimi/project-p7a"
CLIENT_TYPE    = "ALL" #HUMIDITY or LED or ALL

clientID = 1 # change accordingly to your client. If the client is HUMIDITY, this should be set
             # to either 1 or 2, and will send to a random among 3 or 4. Vice versa if this is
             # LED. Be sure if you want to use the ALL type clients, to set correctly clients ID
             # (with ALL type clients, still if the client is 1 or 2 will send to 3 or 4, and 
             # vice versa).

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
      # If the client is of type humidity or all, we need for sure to wait our turn before sending the 
      # humidity value. We need to compute our turn according to the information contained in the 
      # beacon message.
      if(CLIENT_TYPE == "HUMIDITY" or CLIENT_TYPE == "ALL"):
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
  # If we receive a DATA message, then if we are a LED (or ALL) type client, and the message is for us,
  # then we need to modify the intensity of our LED accordingly to the received value 
  if(msg['Type'] == 'DATA'):
    if(msg['Destination'] == clientID and (CLIENT_TYPE == "LED" or CLIENT_TYPE == "ALL")):
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
  # If we are a client of type HUMIDITY or ALL, then we need to check the timestamp (in order to be 
  # sure to be in our reserved slot in the CAP), and then we need to send the message.
  if (timestampToSend != 0 and time.time() >= timestampToSend and (CLIENT_TYPE == "HUMIDITY" or CLIENT_TYPE == "ALL")):
    sensor.measure()
    # As specified above, 1 and 2 sends to 3 and 4, and vice versa.
    if(clientID == 1 or clientID == 2):
      destination = random.randint(3,3)
    else:
      destination = random.randint(1,1)
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