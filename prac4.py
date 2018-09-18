#!/usr/bin/python
 
import spidev
import time
import os
import RPi.GPIO as GPIO  # Import the RPi Library for GPIO pin control
import datetime

GPIO.setmode(GPIO.BOARD) # the physical pin number scheme

# Open SPI bus
spi = None
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000

# intuitive names to pins using board numbering
resetBtn=8
frequencyBtn=10
stopBtn=16
displayBtn=18

# Global variables
flag = True
minute = 0
prev_time = 0
real_time = []
sec = []
light_array = []
temp_array = []
volt_array = []

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

# Define delay between readings
delay = 0.5 	# 500ms by default
 
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

count=0

# function callback 1 for the frequency change
def callback1(channel):
        global delay
        global count
        if GPIO.input(frequencyBtn)==0:
                print "frequency button pressed"
                count += 1
                if count==1:
                        print "changing frequency to 1s"
                        delay = 1
                if count==2:
                        print "changing frequency to 2s"
                        delay = 2
                if count>2:
                        print "changing frequency to default"
                        delay=0.5
                        count=0
# function for reset
def callback2(channel):
        global time_stamp
	global prev_time
	global minute
	
        time_stamp = time.time()
        clearing = os.system("clear") # command for cleaning the console
        if clearing==0:
                print "console cleaned succesfully."
        else:
                print "oops something went wrong."
        convertTimer = time.time()-time_stamp
        timer = time.strftime("%H:%M:%S", time.localtime(convertTimer))
        print("Timer: {}".format(timer))
	prev_time = 0
	minute = 0
	
# function for stop
def stopCallback(channel):
	global spi
	global flag
	if flag:
		spi.close()
		flag = False
	else:
		flag = True
		spi = spidev.SpiDev()
		spi.open(0, 0)
		spi.max_speed_hz = 100000

# function for display 
def displayCallback(channel):
	global minute
	global prev_time
	
	si = len(volt_array)
	print("Time      Timer       Pot      Tem      Light")
	for j in range(si-5, si):
		s = str(sec[j])
		index = s.find(".")
		length = len(s)
		
		if sec[j] < 1:
			print("{}  0{}:00:0{}    {} V  {} C  {}%".format(real_time[j], minute, s[index+1:length], volt_array[j], temp_array[j], light_array[j]))
		
		elif sec[j] >= 1 and sec[j] <= 9:
			if int(s[index+1:length]) < 10:
				print("{}  0{}:0{}:0{}    {} V  {} C  {}%".format(real_time[j], minute, int(sec[j]), int(s[index+1:length]), volt_array[j], temp_array[j], light_array[j]))
				
			else:
				print("{}  0{}:0{}:{}    {} V  {} C  {}%".format(real_time[j], minute, int(sec[j]), int(s[index+1:length]), volt_array[j], temp_array[j], light_array[j]))

		elif sec[j] >= 10 and sec[j] <= 59:
			if int(s[index+1:length]) < 10:
				print("{}  0{}:{}:0{}    {} V  {} C  {}%".format(real_time[j], minute,  int(sec[j]), int(s[index+1:length]), volt_array[j], temp_array[j], light_array[j]))
			
			else:
				print("{}  0{}:{}:{}    {} V  {} C  {}%".format(real_time[j], minute,  int(sec[j]), int(s[index+1:length]), volt_array[j], temp_array[j], light_array[j]))
				
		elif sec[j] >= 60:
			minute += 1
			prev_time = 0
			

# function for monitoring	
def analogMonitor():
	global prev_time
	global delay
        start_time = time.time()
        
	# Read the light sensor data
        light_level = ReadChannel(light_channel)
        light_volts = ConvertVolts(light_level,2)
	light_array.append(light_volts)
 
        # Read the temperature sensor data
        temp_level = ReadChannel(temp_channel)
        temp_volts = ConvertVolts(temp_level,2)
        temp       = ConvertTemp(temp_level,2)
	temp_array.append(temp)
        
	# Read the voltage sensor data
	volt_level = ReadChannel(pot_channel)
        volt = ConvertVolts(volt_level,2)
	volt_array.append(round(volt,2))

        time.sleep(delay)

        now = datetime.datetime.now()
        real_time.append(now.strftime("%H:%M:%S"))

        end_time = time.time()
        elasped_time = (end_time - start_time)
        prev_time = prev_time + elasped_time 
        sec.append(round(prev_time,2))

GPIO.add_event_detect(frequencyBtn, GPIO.FALLING, callback=callback1, bouncetime=200)
GPIO.add_event_detect(resetBtn, GPIO.FALLING, callback=callback2, bouncetime=200)
GPIO.add_event_detect(stopBtn, GPIO.FALLING, callback=stopCallback, bouncetime=200)
GPIO.add_event_detect(displayBtn, GPIO.FALLING, callback=displayCallBack, bouncetime=200)

try:
	while True:
		if flag == False:
			continue
		
		else:
			analogMonitor()

except KeyboardInterrupt:
	spi.close()
	GPIO.cleanup()
 
"""# Read the light sensor data
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
time.sleep(delay)"""
