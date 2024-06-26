#############################################################################
##                               GRASS                                     ##
#############################################################################
# PiPLC / Raspberry Pi based controller for a growtent

# Secrets
import mqttsecrets
# General libraries
import os
import sys
import glob
import time
import datetime
import logging
# GPIO
import RPi.GPIO as GPIO
# MQTT
import paho.mqtt.client as mqtt
# Sensors 
import board
from adafruit_seesaw.seesaw import Seesaw
import adafruit_ahtx0
import adafruit_bh1750

#############################################################################
##                           Global variables                              ##
#############################################################################
# General
energyPath      = os.getenv('HOME') + "/GrassEnergyUsed.txt"
logPath         = os.getenv('HOME') + "/GrassLog.txt"
THERMAL_PATH    = "/sys/class/thermal/thermal_zone0/temp"
logger          = logging.getLogger(__name__)

# MQTT
mqttTopicOutput = "grass/outputs/"
mqttTopicInput  = "grass/inputs/#"
mqttQos         = 2

# Machine parameters, set through recipe or MQTT outputs
controlMode     = "local"
airTempSet      = 20    # Air Temperature setpoint in C
airTempHyst     = 0.5   # Hysterysis for AirTemperature contoller
airHumMax       = 90    # Maximum air humidity in % before ventilation starts
soilMoistSet    = 1000  # Soil moisture setpoint in whatever unit Adafruit found appropriate (200 .. 2000)
wateringPulseOn = 10    # How long the water can be turned on
wateringPulseOff= 30    # How long the water needs to be off
airCircDuration = 60    # Duration of air circulation when triggered
airCircTime     = 30    # Time in minutes between air circulations
lightSet        = 2000  # Target brightness in Lux
lightOn         = 1     # Binary output of Light switch
sensorInterval  = 60    # Interval to measure inputs in seconds
slowInterval    = 3600  # Interval for slow stuff
s0kWhPerPulse   = 0.001 # kWH to be added to total counter per pulse

# Machine thinking
lastAirCirc         = 0
runFan              = False
runHeater           = False
runLight            = False
runExhaust          = False
lastWaterOff        = 0
lastSensors         = 0
lastSlow            = 0
soilSensors         = []    # List of soil sensor entities
topic               = ""
payload             = ""
lightOnTime         = 3     # Hour at which light is switched on 
lightOffTime        = 21    # Hour at which light is switched off
lastRunLight        = False
energyUsed          = 0.0   # Total energy used in kwh
waterRequested      = False
exhaustRequested    = False

# Sensor states
mqttOK          = False
allStemmasOK    = True
lightSensorOK   = True
airSensorOK     = True

###################
# GPIO mapping
###################
# Pin Config
digitalInputs   = [17, 27, 22, 10,  9, 11, 13, 26]  # I1 - I8
digitalOutputs  = [24, 25,  8,  7, 12, 16, 20, 21]  # Q1 - Q8
pwmOutputs      = [18, 19]
oneWire         = [23]

# Digital Inputs
S0counter       = 17

# Relays
relayLight      = 24    # Q1
relayHeater     = 25    # Q2
relayExhaust    =  8    # Q3
relayWater      = 12    # Q5
relayCirc       = 16    # Q6

# PWM
pwmCircFan      = 18    # PWM 1 

#############################################################################
##                           Global Constants                              ##
#############################################################################
# Stemma soil adresses. 0x38 can't be used as 0x38 is already used by AHT20 and unchangeable
SOIL_MOIST_ADR  = [0x36, 0x37, 0x39]

#############################################################################
##                               Helpers                                   ##
#############################################################################
#######################################
# S0 counter
#######################################
def s0callback(channel):
    global energyUsed
    energyUsed += s0kWhPerPulse
    logger.info("S0 pulse counted, energy used: " + "{:.3f}".format(energyUsed) + " kWh")

#######################################
# Paho connection established
#######################################
def on_connect(client, userdata, flags, rc, properties=None):
    global mqttOK
    logger.info("Connection established")
    mqttc.subscribe(mqttTopicInput, qos=1)
    mqttOK = True

#######################################
# Callback on received message
#######################################
def callback(client, userdata, message):
    global waterRequested, exhaustRequested

    message = str(message.payload.decode("utf-8"))
    logger.info("Message received: " + message)

    # ---------------------------------
    # MQTT Inputs
    # ---------------------------------
    # Watering request
    if message == "waternow":
        waterRequested = True
    elif message == "exhauston":
        exhaustRequested = True
    elif message == "exhaustoff":
        exhaustRequested = False

#######################################
# Subscription successful
#######################################
def on_subscribe(client, userdata, mid, granted_ops, properties=None):
    logger.info("On subscribe called")

#######################################
# Paho setup
#######################################
def pahoSetup():
    global mqttc
    mqttc = mqtt.Client(callback_api_version = mqtt.CallbackAPIVersion.VERSION2, client_id=mqttsecrets.ClientId)
    mqttc.on_message = callback
    mqttc.on_connect = on_connect
    mqttc.on_subscribe = on_subscribe
    mqttc.username_pw_set(mqttsecrets.Username, mqttsecrets.Password)
    mqttc.connect(mqttsecrets.Broker, mqttsecrets.Port)
    # Start the mqtt loop, no intension to ever end
    mqttc.loop_start()

#######################################
# Water temp sensor
#######################################
def ds18b20_read_temp():
    global waterTempSensor
    try:
        with open(waterTempSensor, 'r') as f:
            temp_String = f.read()
        temp_c = float(temp_String) / 1000.0
        return temp_c
    except:
        logger.error("1-Wire reading failed!")

#######################################
# Sensor setup
#######################################
def sensorSetup():
    global lightSensor, airSensor, soilSensors, waterTempSensor
    global allStemmasOK, lightSensorOK, airSensorOK

    # Pin setup
    GPIO.setmode(GPIO.BCM)
    for pin in digitalOutputs:
        GPIO.setup(pin, GPIO.OUT)
    for pin in digitalInputs:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #for pin in pwmOutputs:
    #    GPIO.setup(pin, GPIO.OUT)
    #    #TODO
    
    # S0 counter
    GPIO.add_event_detect(
        S0counter,
        edge = GPIO.FALLING, 
        callback = s0callback,
        bouncetime = 100)

    # I2C Adafruit
    i2c_bus = board.I2C()

    # Stemma soil moisture sensor
    for address in SOIL_MOIST_ADR:
        try:
            ss = Seesaw(i2c_bus, addr=address)
            soilSensors.append(ss)
            logger.info("Stemma soil sensor " + hex(address) + " found!")
        except:
            logger.error("Stemma soil sensor " + hex(address) + " not found!")
            allStemmasOK = False

    # Light sensor
    try:
        lightSensor = adafruit_bh1750.BH1750(i2c_bus)
    except:
        logger.error("Light sensor couldn't be added!")
        lightSensorOK = False

    # Temp / Air hum sensor
    try:
        airSensor = adafruit_ahtx0.AHTx0(i2c_bus)
    except:
        logger.error("Air sensor couldn't be found!")
        airSensorOK = False

    # Water temperature sensor
    base_dir = '/sys/bus/w1/devices/'
    try:
        device_folder = glob.glob(base_dir + '28*')[0]
        waterTempSensor = device_folder + '/temperature'
        logger.info("Found 1-Wire sensor: " + device_folder)
    except:
        logger.error("No 1-Wire device found!")

    # Upload detected sensor states to MQTT
    try:
        # Stemmas
        topic = mqttTopicOutput + "sensorstates/soil"
        infot = mqttc.publish(topic, str(allStemmasOK), qos=mqttQos)
        infot.wait_for_publish()
        # Light
        topic = mqttTopicOutput + "sensorstates/light"
        infot = mqttc.publish(topic, str(lightSensorOK), qos=mqttQos)
        infot.wait_for_publish()
        # Air
        topic = mqttTopicOutput + "sensorstates/air"
        infot = mqttc.publish(topic, str(airSensorOK), qos=mqttQos)
        infot.wait_for_publish()
    except:
        logger.error("Sending sensor states to MQTT didn't work!")

#######################################
# Actual machine code
#######################################
def machineCode():
    # Import global vars
    global lightSensor, airSensor, soilSensors
    global lastAirCirc, runFan, runHeater, runLight, lastWaterOff, lastSensors, lastSlow, soilSensors, topic, payload
    global controlMode, airTempSet, airTempHyst, airHumMax, soilMoistSet, wateringPulseOn, wateringPulseOff, airCircDuration
    global airTemp, airHum, runExhaust
    global airCircTime, lightSet, lightOn
    global allStemmasOK, lightSensorOK, airSensorOK
    global s0kWhPerPulse, energyUsed
    global lastRunLight, energyPath, waterRequested

    # Remember timestamp
    now = time.time()

    # #################################
    # Measure sensors
    # #################################
    if now > lastSensors + sensorInterval:
        lastSensors = now

        # -----------------------------
        # Measure soil humidities and temperatures
        # -----------------------------
        soilMoistAvg = 0
        # Iterate through all connected sensors
        for idx, soilSensor in enumerate(soilSensors):
            # Grab soil inputs
            try:
                soilMoist       = soilSensor.moisture_read() / 10
                soilTemp        = soilSensor.get_temp()
                # TODO what else can the soilSensor do?

                soilMoistAvg    = soilMoistAvg + soilMoist
                logger.info("Bucket " + str(idx) + ": Temperature: " + "{:.2f}".format(soilTemp) + " °C, Moisture: " + "{:.1f}".format(soilMoist) + "%")

                # Send moisture
                topic = mqttTopicOutput + "bucketmoists/" + str(idx)
                infot = mqttc.publish(topic, str(soilMoist), qos=mqttQos)
                infot.wait_for_publish()
                # Send temperature
                topic = mqttTopicOutput + "buckettemps/" + str(idx)
                infot = mqttc.publish(topic, str(soilTemp), qos=mqttQos)
                infot.wait_for_publish()
            except:
                logger.error("Soil sensor " + str(idx) + " reading didn't work!")

        if len(soilSensors) > 0:
            soilMoistAvg = soilMoistAvg / len(soilSensors)

        # -----------------------------
        # Measure water temp
        # -----------------------------
        try:
            waterTemp = ds18b20_read_temp()
            logger.info("Water temperature: " + str(waterTemp))

            topic = mqttTopicOutput + "watertemp"
            infot = mqttc.publish(topic, str(waterTemp), qos=mqttQos)
            infot.wait_for_publish()
        except:
           logger.error("Reading water temperature didn't work!")

        # -----------------------------
        # Measure light brightness
        # -----------------------------
        try:
            logger.info("Light intensity: %.2f Lux" % lightSensor.lux)
            topic = mqttTopicOutput + "brightness"
            infot = mqttc.publish(topic, str(lightSensor.lux), qos=mqttQos) # TODO
            infot.wait_for_publish()
        except:
            logger.error("Reading or sending Light Sensor didn't work!")

        # -----------------------------
        # Measure Air temp and humidity
        # -----------------------------
        try:
            airTemp = airSensor.temperature
            airHum  = airSensor.relative_humidity
            logger.info("Air temperature: %0.1f C" % airTemp)
            logger.info("Air humidity: %0.1f %%" % airHum)

            # Heater
            if airTemp < (airTempSet - airTempHyst):
                runHeater = True
                logger.info("Heater On")
            elif airTemp < (airTempSet + airTempHyst):
                runHeater = False
                logger.info("Heater Off")

            # Send heater state
            topic = mqttTopicOutput + "runheater"
            infot = mqttc.publish(topic, str(runHeater), qos=mqttQos)
            infot.wait_for_publish()
            # Send humidity
            topic = mqttTopicOutput + "airhum"
            infot = mqttc.publish(topic, str(airHum), qos=mqttQos)
            infot.wait_for_publish()
            # Send temperature
            topic = mqttTopicOutput + "airtemp"
            infot = mqttc.publish(topic, str(airTemp), qos=mqttQos)
            infot.wait_for_publish()
        except:
            logger.error("Reading or uploading the air sensor didn't work!")

        # -----------------------------
        # Measure water level in reservoir
        # -----------------------------
        # TODO

        # -----------------------------
        # Energy used
        # -----------------------------
        # Remember in case we die
        with open(energyPath, 'w') as f:
            f.write(str(energyUsed))
        # Upload to MQTT
        try:
            topic = mqttTopicOutput + "energy"
            infot = mqttc.publish(topic, str(energyUsed), qos=mqttQos)
            infot.wait_for_publish()
        except:
            logger.error("Uploading energy to MQTT didn't work!")

        # -----------------------------
        # SOC Temperature
        # -----------------------------
        with open(THERMAL_PATH, 'r') as f:
            socMilliDegrees = float(f.read())
            socTemp         = socMilliDegrees / 1000 
            logger.info("Current SOC temperature: " + "{:.2f}".format(socTemp) + " °C")
        # Upload to MQTT
        try:
            topic = mqttTopicOutput + "telemetry/soctemp"
            infot = mqttc.publish(topic, str(socTemp), qos=mqttQos)
            infot.wait_for_publish()
        except:
            logger.error("Uploading SOC temperature to MQTT didn't work!")

    # #################################
    # Slow interval stuff
    # #################################
    if now > lastSlow + slowInterval:
        lastSlow = now

        # -----------------------------
        # Free disk space in home
        # -----------------------------
        statvfs     = os.statvfs(os.getenv('HOME'))     # / KB   / MB   / GB
        diskSize    = statvfs.f_frsize * statvfs.f_blocks / 1024 / 1024 / 1024 # Size of filesystem in GB
        diskFree    = statvfs.f_frsize * statvfs.f_bavail / 1024 / 1024 / 1024 # Free space in GB
        diskPercent = 100 / diskSize * (diskSize - diskFree)
        logger.info("Filesystem size: " + "{:.3f}".format(diskSize) + "GB")
        logger.info("Filesystem free space: " + "{:.3f}".format(diskFree) + " GB")
        logger.info("Filesystem percent used: " + "{:.0f}".format(diskPercent) + " %")
        # Upload to MQTT
        try:
            topic = mqttTopicOutput + "telemetry/fssize"
            infot = mqttc.publish(topic, "{:.3f}".format(diskSize), qos=mqttQos)
            infot.wait_for_publish()
            topic = mqttTopicOutput + "telemetry/fsfree"
            infot = mqttc.publish(topic, "{:.3f}".format(diskFree), qos=mqttQos)
            infot.wait_for_publish()
            topic = mqttTopicOutput + "telemetry/fspercent"
            infot = mqttc.publish(topic, "{:.0f}".format(diskPercent), qos=mqttQos)
            infot.wait_for_publish()
        except:
            logger.error("Uploading disk usage to MQTT didn't work!")

    # #################################
    # Actuators
    # #################################
    # ---------------------------------
    # Circulation
    # ---------------------------------
    # If time since last circulation exceeded the setpoint:
    if now > lastAirCirc + (airCircTime * 60) and not runFan:
        # Turn fan on
        runFan = True
        logger.info("Turning circulation on")
        # Send circ state
        try:
            topic = mqttTopicOutput + "runfan"
            infot = mqttc.publish(topic, str(runFan), qos=mqttQos)
            infot.wait_for_publish()
        except:
            logger.error("Uploading circulation state to MQTT didn't work!")
    # If time since last circulation exceeded the setpoint + fan duration:
    if now > lastAirCirc + (airCircTime * 60) + airCircDuration and runFan:
        # Turn fan off and remember circulation time
        runFan = False
        lastAirCirc = now
        logger.info("Turning circulation off")
        # Send circ state
        try:
            topic = mqttTopicOutput + "runfan"
            infot = mqttc.publish(topic, str(runFan), qos=mqttQos)
            infot.wait_for_publish()
        except:
            logger.error("Uploading circulation state to MQTT didn't work!")

    # ---------------------------------
    # Exhaust
    # ---------------------------------
    # Currently exhaust is only done manually on MQTT request
    if exhaustRequested != runExhaust:
        # Upload to MQTT
        try:
            topic = mqttTopicOutput + "exhaust"
            infot = mqttc.publish(topic, str(exhaustRequested), qos=mqttQos)
            infot.wait_for_publish()
        except:
            logger.error("Uploading exhaust state to MQTT didn't work!")
        # Log requested state
        if exhaustRequested:
            logger.info("Turning exhaust on")
        else:
            logger.info("Turning exhaust off")
        # Accept requested state
        runExhaust = exhaustRequested

    # ---------------------------------
    # Lighting
    # ---------------------------------
    # Lighting is turned on/off purely based on an on and off timer.
    # Shadow at noon currently unsupported
    currentHour = datetime.datetime.now().hour
    runLight    = currentHour >= lightOnTime and currentHour < lightOffTime
    if runLight != lastRunLight:
        # Upload to MQTT
        try:
            topic = mqttTopicOutput + "runlight"
            infot = mqttc.publish(topic, str(runLight), qos=mqttQos)
            infot.wait_for_publish()
        except:
            logger.error("Sending light state to MQTT didn't work!")
        # Log requested state
        if runLight:
            logger.info("Turning light on!")
        else:
            logger.info("Turning light off!")
        # Accept requested state
        lastRunLight = runLight

    # ---------------------------------
    # Watering
    # ---------------------------------
    # Currently watering is only done manually on MQTT request
    if waterRequested:
        waterRequested = False
        GPIO.output(relayWater, True)
        logger.info("Water pump on")
        time.sleep(wateringPulseOn) # (Blocking so we don't risk keeping water on)
        GPIO.output(relayWater, False)
        logger.info("Water pump off")
        
    # #################################
    # HW Output
    # #################################
    GPIO.output(relayLight,     runLight)
    GPIO.output(relayHeater,    runHeater)
    GPIO.output(relayExhaust,   runExhaust)
    GPIO.output(relayCirc,      runFan or runExhaust)

#############################################################################
##                               main()                                    ##
#############################################################################
def main():
    global mqttOK, energyUsed, energyPath

    # Configure logger
    logging.basicConfig(
        filename    = logPath,
        format      = "%(asctime)s | %(levelname)s | %(message)s",
        datefmt     = "%Y-%m-%d %H:%M:%S",
        encoding    = "utf-8",
        level       = logging.DEBUG
    )
    logger.addHandler(logging.StreamHandler())

    logger.info("---------------------")
    logger.info("---Starting  Grass---")
    logger.info("---------------------")

    # Read out remembered energy if present
    try:
        with open(energyPath, 'r') as f:
            energyUsed = float(f.read())
            logger.info("Read out " + "{:.3f}".format(energyUsed) + " kWh energy used from memory!")
    except:
        logger.warning("No energy memory present. Starting at 0kwh!")

    # Paho setup
    while not mqttOK:
        try:
            pahoSetup()
        except:
            logger.error("MQTT connection failed! Retrying..")
        time.sleep(3)

    # Sensor setup
    sensorSetup()

    # Machine code
    while(1):
        machineCode()
        time.sleep(1)


#############################################################################
##                         main() idiom                                    ##
#############################################################################
if __name__ == "__main__":
    main()
