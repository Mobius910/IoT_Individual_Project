# IoT Individual Project

This repository contains the script used for the **IoT Essentials Individual Project**, part of the Elektronics-ICT curriculum.

---
## Prerequisite

The following Python libraries are essential for this project’s functionality. 
Ensure they are installed before running the script.

To install the required packages, use the following commands :

```bash
sudo apt install python3-pip
sudo pip3 install bmp280 smbus2 paho.mqtt
```

Additionally, install **WiringOP** and **WiringOP-Python** on your Orange Pi using the links below:

- [WiringOP](https://github.com/orangepi-xunlong/wiringOP)
- [WiringOP-Python](https://github.com/orangepi-xunlong/wiringOP-Python/blob/master/README.rst)

After rebooting the Orange Pi, run the script using:

```bash
sudo python3 main.py
```
