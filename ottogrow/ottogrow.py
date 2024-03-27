#############################################################################
##                              ottogrow                                    ##
#############################################################################
# Command line tool to consolidate several DHL labels 
# for printing with less waste

import os
import sys
import glob
import time

import context  # Ensures paho is in PYTHONPATH
import paho.mqtt.client as mqtt

#############################################################################
##                           Global variables                              ##
#############################################################################
# General


# MQTT
mqttBroker      = "127.0.0.1"
mqttPort        = "1883"
mqttClientId    = "ottogrow"
mqttUsername    = "Username"
mqttPassword    = "Password"
mqttTopicOutput = "ottogrow/outputs/#"
mqttTopicInput  = "ottogrow/inputs/#"

# Machine parameters, set through recipe or MQTT outputs
controlMode     = "local"
airTempSet      = 20    # Air Temperature setpoint in C
airTempHyst     = 1     # Hysterysis for AirTemperature contoller
airHumMax       = 90    # Maximum air humidity in % before ventilation starts
SoilMoistSet    = 50    # Soil moisture setpoint in %
WateringPulseOn = 10    # How long the water can be turned on
WateringPulseOff= 30    # How long the water needs to be off
AirCircDuration = 30    # Duration of air circulation when triggered
AirCircTime     = 60    # Time in minutes between air circulations
LightSet        = 2000  # Target brightness in Lux
LightOn         = 1     # Binary output of Light switch. TODO Only controlled via MQTT for now
CameraTime      = 15    # Time in minutes between camera pictures

# Machine thinkinge
lastCameraSnap  = 0
lastAirCirc     = 0
runFan          = 0
runHeater       = 0
runLight        = 0

#############################################################################
##                               Helpers                                   ##
#############################################################################
# Paho connection established
def on_connect(client, userdata, flags, rc, properties=None):
    print("Connection established")

# Callback on received message
def callback(client, userdata, message):
    print("Message received: " + str(message.payload.decode("utf-8")))

# Subscription successful
def on_subscribe(client, userdata, mid, granted_ops, properties=None):
    print("On subscribe called!!")

# Paho setup
def pahoSetup():
    mqttc = mqtt.Client(callback_api_version = mqtt.CallbackAPIVersion.VERSION2, client_id=clientId)
    mqttc.on_message = callback
    mqttc.on_connect = on_connect
    mqttc.on_subscribe = on_subscribe
    mqttc.username_pw_set(mqttUsername, mqttPassword)
    mqttc.connect(mqttBroker, mqttPort)
    mqttc.subscribe(mqttTopicOutput, qos=1)
    # Start the mqtt loop, no intension to ever end
    mqttc.loop_start()


# Actual machine code
def machineCode():
    # Remember timestamp
    now = time.time()

    # Camera Snapshot
    # TODO
    if now > lastCameraSnap + (CameraTime * 60):
        # Snap a pic
        lastCameraSnap = now

    # Heater
    # TODO

    # Circulation
    # If time since last circulation exceeded the setpoint:
    if now > lastAirCirc + (AirCircTime * 60):
        # Turn fan on
        runFan = 1
        # If time since last circulation exceeded the setpoint + fan duration:
        if now > lastAirCirc + (AirCircTime * 60) + (AirCircDuration):
            # Turn fan off and remember circulation time
            runFan = 0
            lastAirCirc = now

    # Venting
    # TODO

    # Lighting
    # TODO

    # Watering (Blocking so we don't risk keeping water on)
    # TODO

#############################################################################
##                               main()                                    ##
#############################################################################
def main():
    print("---------------------")
    print("--Starting Ottogrow--")
    print("---------------------")

    # Paho setup
    pahoSetup()

    # Machine code
    while(1):
        machineCode()
        time.sleep(1)


#############################################################################
##                         main() idiom                                    ##
#############################################################################
if __name__ == "__main__":
    main()
