# Grass <!-- omit in toc -->

[![Donations: Coffee](https://img.shields.io/badge/donations-Coffee-brown?style=flat-square)](https://github.com/Chrismettal#donations)

This is a python-cased controller for a growbox using [PiPLC](https://github.com/Chrismettal/PiPLC) hardware. It's meant to be run on a Raspberry Pi mounted to your growbox. 
Most sensors are wired using `I²C` so you don't end up running 50 wires through the box. 

It features:

- Lighting schedule
    - Light dimming
- Exhaust fan (Temp / Humidity based)
    - Exhaust speed control
- Circulation fan schedule
    - Circulation fan speed control
- Heating
- Watering (Soil humidity / schedule based)
    - Water resorvoir level measurement
    - Water resorvoir temperature measurement
- Air Temperature / Humidity measurement
- Soil Temperatur / Humidity measurement for 4 buckets

**If you like my work please consider [supporting me](https://github.com/Chrismettal#donations)!**

## Installation

### Prerequisites

- Either create a Python venv or be prepared to `--break-system-packages`

- Install [Adafruit Blinka](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi) for our sensor dependencies

- As of 2024-04, you'll need to remove the default `RPi.GPIO` library via `sudo apt remove python3-rpi.gpio` before installing a forked version with `pip install rpi-lgpio` (potentially with `--break-system-packages`) since GPIO interrupts won't work in the base library version

### Pypi

Might be pushed to Pypi later idk.

### Local (for development)

- Clone the repo:

`git clone https://github.com/chrismettal/grass`

- Change directory into said cloned repo:

`cd grass`

- Install in "editable" mode:

`pip install -e .`

- Open up `./grass/grass.py` and modify the global parameters at the top to fit your needs.

- Execute `grass` to run the software. Potentially configure your OS to autorun at boot.

## Usage

TODO

## GPIO mapping

This code is intended to be run on a [PiPLC](https://github.com/chrismettal/piplc) running regular `PiOS` but theoretically it's possible to be run on a bare Pi with some I/O attached.

| GPIO Name | PiPLC function           | grass                                             |
| :-------: | :----------------------- | :------------------------------------------------ |
| `GPIO_02` | :blue_square: I²C SDA    | `BH1750` light / `AHT20` temp/hum / Soil moisture |
| `GPIO_03` | :blue_square: I²C SCL    | `BH1750` light / `AHT20` temp/hum / Soil moisture |
| `GPIO_04` | :blue_square: Modbus TX  | :x:                                               |
| `GPIO_05` | :blue_square: Modbus RX  | :x:                                               |
| `GPIO_06` | :blue_square: Modbus RTS | :x:                                               |
| `GPIO_07` | :red_square: Q4          | *230 V spare*                                     |
| `GPIO_08` | :red_square: Q3          | 230 V Exhaust                                     |
| `GPIO_09` | :yellow_square: I5       |                                                   |
| `GPIO_10` | :yellow_square: I4       |                                                   |
| `GPIO_11` | :yellow_square: I6       |                                                   |
| `GPIO_12` | :red_square: Q5          | 24 V Water Pump                                   |
| `GPIO_13` | :yellow_square: I7       |                                                   |
| `GPIO_14` | :blue_square: KNX TX     | :x:                                               |
| `GPIO_15` | :blue_square: KNX RX     | :x:                                               |
| `GPIO_16` | :red_square: Q6          | 24 V Circulation fan  (2 x 12v fans in series)    |
| `GPIO_17` | :yellow_square: I1       | S0 energy meter                                   |
| `GPIO_18` | :orange_square: PWM_0    |                                                   |
| `GPIO_19` | :orange_square: PWM_1    |                                                   |
| `GPIO_20` | :red_square: Q7          | *24 V spare*                                      |
| `GPIO_21` | :red_square: Q8          | *24 V spare*                                      |
| `GPIO_22` | :yellow_square: I3       |                                                   |
| `GPIO_23` | :blue_square: 1-Wire     | `DS18B20` Soil / Water temp                       |
| `GPIO_24` | :red_square: Q1          | 230 V Light                                       |
| `GPIO_25` | :red_square: Q2          | 230 V Heater                                      |
| `GPIO_26` | :yellow_square: I8       |                                                   |
| `GPIO_27` | :yellow_square: I2       |                                                   |

![Schematic](/doc/PiPLC_Testboard.drawio.svg)

## Roadmap

- [x] Create Roadmap
- [x] GPIO working
- [x] Light schedule works
- [ ] All sensors can be read
- [x] Power meter works
    - [x] And saves its memory in the same place every time
- [ ] Circulation logic works
- [ ] Exhaust logic works
- [x] Heater logic works
- [ ] Watering logic works
- [x] Timelapse feature works (Via `motion`)
    - [x] Camera still accessible as webcam stream 
- [ ] All print statements become log statements
- [ ] Autostart on machine boot
- [ ] Oneshot MQTT states get sent cyclically
- [ ] MQTT "last will" invalidate sensor states
- [ ] Sensors that aren't present at machine start get detected without restart
- [ ] Get control parameters through MQTT
- [ ] MQTT output overrides
- [ ] MQTT advertising

## Camera

- `sudo apt install motion`
- Change config file to enable timelapse snapshots
- `Change /lib/systemd/system/motion.service` to start in non-daemon mode 
    - `ExecStart=/usr/bin/motion -n`
- `sudo systemctl enable --now motion`

## Donations

**If you like my work please consider [supporting me](https://github.com/Chrismettal#donations)!**

## License

 <a rel="GPLlicense" href="https://www.gnu.org/licenses/gpl-3.0.html"><img alt="GPLv3" style="border-width:0" src="https://www.gnu.org/graphics/gplv3-or-later.png" /></a><br />This work is licensed under a <a rel="GPLlicense" href="https://www.gnu.org/licenses/gpl-3.0.html">GNU GPLv3 License</a>.
