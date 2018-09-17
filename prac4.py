#!/usr/bin/python
 
import spidev
import time
import os
import RPi.GPIO as GPIO  # Import the RPi Library for GPIO pin control

GPIO.setmode(GPIO.BOARD) # the physical pin number scheme

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000

# intuitive names to pins using board numbering
resetBtn=8
frequencyBtn=10
stopBtn=16
displayBtn=18

# Setting up
GPIO.setup(resetBtn,GPIO.IN,pull_up_down=GPIO.PUD_UP)           # Button 1 is an input, and activate pulldown resistor
GPIO.setup(frequencyBtn,GPIO.IN,pull_up_down=GPIO.PUD_UP)       # Button 2 is an input, and activate pullup resistor
GPIO.setup(stopBtn,GPIO.IN,pull_up_down=GPIO.PUD_UP)            # Button 3 is an input, and activate pullup resistor
GPIO.setup(displayBtn,GPIO.IN,pull_up_down=GPIO.PUD_UP)         # Button 4 is an input, and activate pullup resistor

time_stamp = time.time()					# to keep track of the time

stp=False       # start/stop flag

# Define sensor channels
light_channel = 0
temp_channel  = 1
pot_channel = 2
 
# Function to read SPI data from MCP3008 chip
# Channel must be an integer 0-7
def ReadChannel(channel):
  adc = spi.xfer2([1,(8+channel)<<4,0])
  data = ((adc[1]&3) << 8) + adc[2]
  return data
 
# Function to convert data to voltage level,
# rounded to specified number of decimal places.
def ConvertVolts(data,places):
  volts = (data * 3.3) / float(1023)
  volts = round(volts,places)
  return volts
 
# Function to calculate temperature from
# number of decimal places.
def ConvertTemp(data,places):
	# all values from MCP9700 spec sheet
	ADC_VREF = 5.0
	ADC_V_PER_COUNT = ADC_VREF/1023.0
	T_COEF = 100.0
	Offset = 0.5

	temp_volt = data * ADC_V_PER_COUNT
  	temp 	  = (temp_volt - Offset)*T_COEF
	temp	  = round(temp, places)
  	return temp
 
# Define sensor channels
light_channel = 0
temp_channel  = 1
 
# Define delay between readings
delay = 1 #1 second
 
while True:
 
  # Read the light sensor data
  light_level = ReadChannel(light_channel)
  light_volts = ConvertVolts(light_level,2)
 
  # Read the temperature sensor data
  temp_level = ReadChannel(temp_channel)
  temp_volts = ConvertVolts(temp_level,2)
  temp       = ConvertTemp(temp_level,2)
 
  # Print out results
  print "--------------------------------------------"
  print("Light: {} ({}V)".format(light_level,light_volts))
  print("Temp : {} ({}V) {} deg C".format(temp_level,temp_volts,temp))
 
  # Wait before repeating loop
  time.sleep(delay)
