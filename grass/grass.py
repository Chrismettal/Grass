#############################################################################
##                              grass                                    ##
#############################################################################
# Command line tool to consolidate several DHL labels 
# for printing with less waste

# Secrets
import mqttsecrets

import os
import sys
import glob
import time
import datetime

# import context  # Ensures paho is in PYTHONPATH
import paho.mqtt.client as mqtt

# Sensors 
import board
from adafruit_seesaw.seesaw import Seesaw
import adafruit_ahtx0
#import libds18b20
import cv2

#############################################################################
##                           Global variables                              ##
#############################################################################
# General
snapLocation     = "~/Grass/Screenshots/"

# MQTT
mqttTopicOutput = "grass/outputs/"
mqttTopicInput  = "grass/inputs/#"
mqttQos         = 2

# Machine parameters, set through recipe or MQTT outputs
controlMode     = "local"
airTempSet      = 20    # Air Temperature setpoint in C
airTempHyst     = 1     # Hysterysis for AirTemperature contoller
airHumMax       = 90    # Maximum air humidity in % before ventilation starts
SoilMoistSet    = 1000  # Soil moisture setpoint in whatever unit Adafruit found appropriate (200 .. 2000)
wateringPulseOn = 10    # How long the water can be turned on
wateringPulseOff= 30    # How long the water needs to be off
airCircDuration = 30    # Duration of air circulation when triggered
airCircTime     = 60    # Time in minutes between air circulations
lightSet        = 2000  # Target brightness in Lux
lightOn         = 1     # Binary output of Light switch. TODO Only controlled via MQTT for now
cameraTime      = 15    # Time in minutes between camera pictures
sensorInterval  = 30    # Interval to measure inputs in seconds

# Machine thinking
lastCameraSnap  = 0
lastAirCirc     = 0
runFan          = 0
runHeater       = 0
runLight        = 0
lastWaterOff    = 0
lastSensors     = 0
soilSensors     = []    # List of soil sensor entities
topic           = ""
payload         = ""

# GPIO mapping

#############################################################################
##                           Global Constants                              ##
#############################################################################
# Stemma soil adresses
SOIL_MOIST_ADR  = [0x36, 0x37, 0x38, 0x39]


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
    print("On subscribe called")


# Paho setup
def pahoSetup():
    mqttc = mqtt.Client(callback_api_version = mqtt.CallbackAPIVersion.VERSION2, client_id=mqttsecrets.ClientId)
    mqttc.on_message = callback
    mqttc.on_connect = on_connect
    mqttc.on_subscribe = on_subscribe
    mqttc.username_pw_set(mqttsecrets.Username, mqttsecrets.Password)
    mqttc.connect(mqttsecrets.Broker, mqttsecrets.Port)
    mqttc.subscribe(mqttTopicOutput, qos=1)
    # Start the mqtt loop, no intension to ever end
    mqttc.loop_start()


# Picture snapper
def snapPicture():
    ret, image = cam.read()
    if not ret:
        print("failed to snap picture")
        return
    cv2.imwrite(snapLocation + datetime.datetime.now(), image)
    cam.release()

# Sensor setup
def sensorSetup():
    # I2C Adafruit
    # TODO correct I2C pins?
    i2c_bus = board.I2C()

    # TODO catch non-present sensors
     
    # Stemma soil moisture sensor
    for address in SOIL_MOIST_ADR:
        ss = Seesaw(i2c_bus, addr=address)
        soilSensors.append(ss)

    # Light sensor
    lightSensor = adafruit_bh1750.BH1750(i2c_bus)
    
    # Temp / Air hum sensor
    airSensor = adafruit_ahtx0.AHTx0(i2c_bus)

    # Camera
    cam = cv2.VideoCapture(0)

# Actual machine code
def machineCode():
    # Remember timestamp
    now = time.time()

    # Camera Snapshot
    if now > lastCameraSnap + (CameraTime * 60):
        # Snap a pic
        lastCameraSnap = now
        print("Taking Snapshot")
        snapPicture()

    # Measure sensors
    if now > lastSensors + SensorInterval:
        lastSensors = now

        # Measure soil humidities and temperatures
        soilMoistAvg = 0
        # Iterate through all connected sensors
        for idx, soilSensor in enumerate(soilSensors):
            # Grab inputs
            soilTemp        = soilSensor.moisture_read()
            soilMoist       = soilSensor.get_temp()
            soilMoistAvg    = soilMoistAvg + soilMoist
            print("Bucket " + str(idx) + ": Temperature: " + str(soilTemp) + ", Moisture: " + str(soilMoist))
            # Send moisture
            topic = mqttTopicOutput + "bucketmoists/" + str(idx)
            mqttc.publish(topic, str(soilMoist), qos=mqttQos)
            # Send temperature
            topic = mqttTopicOutput + "buckettemps/" + str(idx)
            mqttc.publish(topic, str(soilTemp), qos=mqttQos)
            # Wait for publish complete
            infot.wait_for_publish()
        soilMoistAvg = soilMoistAvg / len(soilSensors)

        # Measure water temp
        waterTemp = 69 #ds18b20_read_temp()
        topic = mqttTopicOutput + "watertemp"
        mqttc.publish(topic, str(waterTemp), qos=mqttQos)
        infot.wait_for_publish()

        # Measure light brightness
        print("%.2f Lux" % lightSensor.lux)
        topic = mqttTopicOutput + "brightness"
        mqttc.publish(topic, str(lightSensor.lux), qos=mqttQos)

        # Measure Air temp and humidity
        AirTemp = airSensor.temperature
        AirHum  = airSensor.relative_humidity
        print("Air temperature: %0.1f C" % sensor.temperature)
        print("Air humidity: %0.1f %%" % sensor.relative_humidity)
        # Send humidity
        topic = mqttTopicOutput + "airhum"
        mqttc.publish(topic, str(AirHum), qos=mqttQos)
        # Send temperature
        topic = mqttTopicOutput + "airtemp"
        mqttc.publish(topic, str(AirTemp), qos=mqttQos)
        # Wait for publish complete
        infot.wait_for_publish()

        # Measure water level in reservoir
        # TODO

    # Heater
    if AirTemp < AirTempSet - airTempHyst:
        runHeater = 1
        print("Heater On")
    elif AirTemp < AirtTempSet + airTempHyst:
        runHeater = 0
        print("Heater Off")

    # Circulation
    # If time since last circulation exceeded the setpoint:
    if now > lastAirCirc + (AirCircTime * 60):
        # Turn fan on
        runFan = 1
        print("Circulation fan on")
        # If time since last circulation exceeded the setpoint + fan duration:
        if now > lastAirCirc + (AirCircTime * 60) + (AirCircDuration):
            # Turn fan off and remember circulation time
            runFan = 0
            lastAirCirc = now
            print("Circulation fan off")

    # Venting
    # TODO

    # Lighting
    # TODO also PWM output

    # Watering
    # TODO HwOutputs
    # Never attempt watering if WateringPulseOff hasn't elapsed yet
    if now > lastWaterOff + WateringPulseOff:
        if soilMoistAvg < SoilMoistSet:
            runPump = 1
            print("Water pump on")
            sleep(WateringPulseOn) # (Blocking so we don't risk keeping water on)
            runPump = 0
            print("Water pump off")
            lastWaterOff = now

    # HW Output updates
    # TODO


#############################################################################
##                               main()                                    ##
#############################################################################
def main():
    print("---------------------")
    print("---Starting  Grass---")
    print("---------------------")

    # Paho setup
    # TODO wait here and retry until paho was able to connect
    pahoSetup()

    # Sensor setup
    sensorSetup()

    # Machine code
    while(1):
        machineCode()
        time.sleep(1)

        # TODO if any device is missing, re-call sensorSetup() until it is

#############################################################################
##                         main() idiom                                    ##
#############################################################################
if __name__ == "__main__":
    main()
