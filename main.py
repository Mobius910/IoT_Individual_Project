import wiringpi as wp
from bmp280 import BMP280
from smbus2 import SMBus, i2c_msg
import paho.mqtt.client as mqtt
import time

# MQTT & ThingsSpeak Credentials
MQTT_BROKER = "mqtt3.thingspeak.com"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

MQTT_TOPIC = "channels/2897217/publish"
MQTT_CLIENT_ID = "GzMJIDk3FxwMJQ8rFAMNJSw"
MQTT_USER = "GzMJIDk3FxwMJQ8rFAMNJSw"
MQTT_PASSWORD = "zDvosrwnvPoTnMlCpM5v/6RR"

# MQTT connection & messaging callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected OK with result code {str(rc)}")
    else:
        print(f"Failed connection with result code {str(rc)}")
        
def on_disconnect(client, userdata, flags, rc):
    print(f"Disconnected with resulting code {str(rc)}")

def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic}; message: {msg.payload}")

# Reading BH1750 Lux values
def bh1750_values(bus, addr):
    # 1 lux high resolution measurement & 120ms measure time (see datasheet)
    write = i2c_msg.write(addr, [0x10]) 
    # 2 bytes size read request (see datasheet)
    read = i2c_msg.read(addr, 2) 
    bus.i2c_rdwr(write, read)
    bytes_read = list(read)
    # Byte to lux conversion (see datasheet)
    return (((bytes_read[0] & 3) << 8) + bytes_read[1]) / 1.2

# Adjust PWM brightness
def adjustPWM(lux, baselineLux, brightness):
    lux_difference = baselineLux - lux

    # if current lux is within 5 lux of baseline, stay same
    if abs(lux_difference) < 5:
        print("Lux is within the range...\n")
    else:
        # if current lux is not within range, auto control brightness
        if baselineLux > lux:
            brightness += 5  # Increase brightness
            print("Increasing light brightness...\n")
        else:
            brightness -= 5  # Decrease brightness
            print("Decreasing light brightness or turning off light...\n")
    # Ensure brightness is within 0-100% and convert to int
    brightness = int(max(0, min(100, brightness)))                
    print(f"PWM brightness : {brightness}%\n")
    return brightness

# Control LED with SoftPWM
def controlPWM(sig, cnt, wait):
    wp.softPwmWrite(sig, cnt)
    time.sleep(wait)

def main():
    # I2C Setup BMP280
    bmp280_bus = SMBus(0)
    bmp280_bus_address = 0x77

    # I2C Setup BH1750
    bh1750_bus = SMBus(0)
    bh1750_bus_address = 0x23

    # BMP280 Setup
    bmp280 = BMP280(i2c_addr= bmp280_bus_address, i2c_dev=bmp280_bus)

    # WiringPi Initializing
    wp.wiringPiSetup()

    # Initialize variables
    brightness = 0
    pwm = 2
    wait = 0.02
    baselineLux = 0
    relayPin = 3

    # Input baseline lux & temperature
    baselineLux = float(input("What is the baseline lux? : "))
    baselineTemp = float(input("What is the baseline temperature? : "))
    
    # Set SoftPWM pin & Start PWM
    wp.softPwmCreate(pwm, 0, 100)
    wp.softPwmWrite(pwm, 0)

    # Set Relay to OUTPUT
    wp.pinMode(relayPin, 1)

    # Setup MQTT Client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, MQTT_CLIENT_ID)
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # Connection initiation to MQTT Broker
    print(f"Initiating connection to {MQTT_BROKER}")
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start() # Holds MQTT connection until manually disconnected

    while True:
        print("------------------------\n")
        
        # Measure temperature from BMP280
        bmp280_temp = bmp280.get_temperature()
        print(f"Current Temperature : {bmp280_temp:.2f}\n")
        print(f"Baseline Temperature : {baselineTemp}\n")
        
        # Convert temperature data into JSON format
        mqtt_bmp280_data = f"field1={str(bmp280_temp)}&status=MQTTPUBLISH"
        mqtt_bmp280_baseline = f"field4={str(baselineTemp)}&status=MQTTPUBLISH"
        
        # Control warmth & auto adjust using temperature measurement data
        if baselineTemp < bmp280_temp:
            wp.digitalWrite(relayPin, wp.HIGH) # HIGH | 1 | Deactivate | No 5V | No Light
            print(f"Heater OFF...\n") 
        else:
            wp.digitalWrite(relayPin, wp.LOW) # LOW | 0 | Activate | 5V | Light on
            print(f"Heater ON...\n")
            
        # Measure lux from BH1750
        lux = bh1750_values(bh1750_bus, bh1750_bus_address)
        
        print("---\n")
        print(f"Current Lux : {lux:.2f}\n")
        print(f"Baseline Lux : {baselineLux}\n")
        
        # Convert lux data into JSON format
        mqtt_bh1750_data = f"field2={str(lux)}&status=MQTTPUBLISH"
        mqtt_bh1750_baseline = f"field3={str(baselineLux)}&status=MQTTPUBLISH"
        
        # Control PWM & auto adjust using light measurement data
        brightness = adjustPWM(lux, baselineLux, brightness)
        controlPWM(pwm, brightness, wait)
        
        # Publish data to ThingsSpeak
        try:
            client.publish(topic=MQTT_TOPIC, payload=mqtt_bmp280_data + "&" + 
                           mqtt_bmp280_baseline + "&" + mqtt_bh1750_data + "&"
                           + mqtt_bh1750_baseline, qos=0, retain=False,
                           properties=None)
            # 10 second interval per data upload
            time.sleep(10)
        except OSError:
            client.reconnect()

if __name__ == "__main__":
    main()
# SDA (SDI) (data) (yellow cable) : wPi 0
# SCL (SCK) (time) (green cable) : wPi 1
# LED PWM : wPi 2 (yellow cable to led)
# Relay : wPi 3 (physical 8) (yellow cable to relay)