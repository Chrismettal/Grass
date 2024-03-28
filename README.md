# Ottogrow <!-- omit in toc -->

[![PyPI - Version](https://img.shields.io/pypi/v/ottogrow?style=flat-square)](https://pypi.org/project/ottogrow/)
[![Repo Version](https://img.shields.io/github/v/tag/chrismettal/ottogrow?label=RepoVersion&style=flat-square)](https://github.com/Chrismettal/ottogrow)
[![PyPI - License](https://img.shields.io/pypi/l/ottogrow?style=flat-square)](https://pypi.org/project/ottogrow/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ottogrow?style=flat-square)](https://pypi.org/project/ottogrow/)
[![Donations: Coffee](https://img.shields.io/badge/donations-Coffee-brown?style=flat-square)](https://github.com/Chrismettal#donations)

This is a work in progress.

**If you like my work please consider [supporting me](https://github.com/Chrismettal#donations)!**

## Installation

### Prerequisites

- Install [Adafruit Blinka](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi) on your pi

### Pypi

Might be pushed to Pypi later idk.

### Local (for development)

- Clone the repo:

`git clone https://github.com/chrismettal/ottogrow`

- Change directory into said cloned repo:

`cd ottogrow`

- Install in "editable" mode:

`pip install -e .`

- Open up `./ottogrow/ottogrow.py` and modify the global parameters at the top to fit your needs.

- Execute `ottogrow` in to run the software. Potentially configure your OS to autorun at boot.

## Usage

TODO

## GPIO mapping

This code is intended to be run on a [PiPLC](https://github.com/chrismettal/piplc) running regular `PiOS` but theoretically it's possible to be run on a bare Pi with some I/O attached.

| GPIO Name | PiPLC function           | Ottogrow                                          |
| :-------: | :----------------------- | :------------------------------------------------ |
| `GPIO_02` | :blue_square: I²C SDA    | `BH1750` light / `AHT20` temp/hum / Soil moisture |
| `GPIO_03` | :blue_square: I²C SCL    | `BH1750` light / `AHT20` temp/hum / Soil moisture |
| `GPIO_04` | :blue_square: Modbus TX  | :x:                                               |
| `GPIO_05` | :blue_square: Modbus RX  | :x:                                               |
| `GPIO_06` | :blue_square: Modbus RTS | :x:                                               |
| `GPIO_07` | :red_square: Q4          |                                                   |
| `GPIO_08` | :red_square: Q3          | 230 V Exhaust                                     |
| `GPIO_09` | :yellow_square: I5       |                                                   |
| `GPIO_10` | :yellow_square: I4       |                                                   |
| `GPIO_11` | :yellow_square: I6       |                                                   |
| `GPIO_12` | :red_square: Q5          | 24 V Water Pump                                   |
| `GPIO_13` | :yellow_square: I7       |                                                   |
| `GPIO_14` | :blue_square: KNX TX     | :x:                                               |
| `GPIO_15` | :blue_square: KNX RX     | :x:                                               |
| `GPIO_16` | :red_square: Q6          | 24 V Circulation fan  (2 x 12v fans in series)    |
| `GPIO_17` | :yellow_square: I1       |                                                   |
| `GPIO_18` | :orange_square: PWM_0    | Circulation Fan speed                             |
| `GPIO_19` | :orange_square: PWM_1    |                                                   |
| `GPIO_20` | :red_square: Q7          |                                                   |
| `GPIO_21` | :red_square: Q8          |                                                   |
| `GPIO_22` | :yellow_square: I3       |                                                   |
| `GPIO_23` | :blue_square: 1-Wire     | `DS18B20` Soil / Water temp                       |
| `GPIO_24` | :red_square: Q1          | 230 V Light                                       |
| `GPIO_25` | :red_square: Q2          | 230 V Heater                                      |
| `GPIO_26` | :yellow_square: I8       |                                                   |
| `GPIO_27` | :yellow_square: I2       |                                                   |

![Schematic](/doc/PiPLC_Testboard.drawio.svg)

## Roadmap

- [ ] Create roadmap

## Donations

**If you like my work please consider [supporting me](https://github.com/Chrismettal#donations)!**

## License

 <a rel="GPLlicense" href="https://www.gnu.org/licenses/gpl-3.0.html"><img alt="GPLv3" style="border-width:0" src="https://www.gnu.org/graphics/gplv3-or-later.png" /></a><br />This work is licensed under a <a rel="GPLlicense" href="https://www.gnu.org/licenses/gpl-3.0.html">GNU GPLv3 License</a>.
