import serial

# ========================================================
#	
# SerialManager.py
#
# This class abstracts the base communications layer in 
# desktop application, so that we can easily inject debug
# functionality later on.
#
# =========================================================

import time
from datetime import datetime
import sys
import csv
import yaml
import os

from CSVIterator import CSVIterator
from SerialDeviceLogger import SerialDeviceLogger
from struct import *
from threading import Thread 
from datetime import datetime

class bitstreamer(Thread):
	
	# ==========================================================
	# Public Interface
	# ==========================================================

	# -------------------------------------------------------
	# Constructor
	# -------------------------------------------------------
	def __init__(self, debug_mode=False, hardware_mode='clip', OPTIONS={}, BAUD_RATE=9600, SERIAL_PORT='/dev/ttyS6'):
		Thread.__init__(self);
		self.__readyFlag = False

		# Our reference index for the packet
		self.verbose = False			# Flag - Say what we're doing 
		self.echo = False				# Flag - Echo the input back

		# Check if we've already initialized the csv logger
		self.init_log_flag  = False

		self.sensor_values = {}
		self.OPTIONS = OPTIONS
		self.SERIAL_PORT = SERIAL_PORT
		self.hardware_mode = hardware_mode
		self.verbose_print("our hardware mode is: " + str(hardware_mode))
		self.values_index = self.getValuesIndex()
		self.unpack_schema = self.__genUnpackSchema()
		self.sample_period_s = 0.025

		self.verbose_print("Expected packet size: " + str(self.getPacketSize(self.unpack_schema)))

		self.last_sample_time = self.getSeconds();

		formatted_time = datetime.now().strftime('%Y%m%d-%H-%M-%S')
		
		self.device_logger = SerialDeviceLogger("device_logs", {'test_metadata': 'sucks'})

		## Setting debug mode disables the input
		## and generates an internal signal
		self.debug_mode = debug_mode

		if self.debug_mode == True:
			print "Warning: Debug Mode Enabled."
		else:
			self.init_serial(BAUD_RATE, SERIAL_PORT)

	# Returns if the driver is ready or not.
	def getReady(self,):
		return self.__readyFlag

	# Print with a flag (useful for debugging)
	def verbose_print(self, string):
		if self.verbose:
			print string

	# Generate the unpack format we're going to be using
	def __genUnpackSchema(self):
		s = "<"
		for element in self.values_index:
			s = s + self.packet_key[element]
		self.verbose_print(s)
		return s

	# Parses an unpack schema and spits out the size.
	def getPacketSize(self, unpack_schema):
		size = 0
		self.verbose_print("Get packet size for " + str(unpack_schema))
		for x in unpack_schema:
			if x is 'c':
				size += 1
			elif x is 'h':
				size += 2
			elif x is 'f':
				size += 4
		return size


	# Grab the index of the packet from a yaml file.
	def getValuesIndex(self):
		self.packet_key = {}
		try:
			file_name = "packet_key.yaml"
			config_file = open(file_name, 'r')
			self.packet_key = yaml.load(config_file)
		except(Exception):
			print "CONFIG ERROR: no packet key detected."

			values_index = ['packet_header','data_1', 'data_2', 'checksum', 'packet_ender']
		return values_index

	# ----------------------------------------------------	
	#
	# Returns how many seconds its been since the last sample.
	#
	# ----------------------------------------------------	
	def secondsSinceLastSample(self):
		return( self.getSeconds() - self.last_sample_time).seconds

	# ----------------------------------------------------	
	#
	# Constantly poll for data in a while loop.
	#
	# ----------------------------------------------------
	def poll(self):
		while True:
			data_raw = self.readLine()
			self.verbose_print("RECV: New line!")
			if self.echo:
				print data_raw,

			if('$' in data_raw):
				self.sensor_values = self.decode(data_raw)
				self.setSampleTime();
				self.__readyFlag = True

				self.device_logger.setKeys(self.sensor_values.keys())
				if('csv_logging' in self.OPTIONS):
					if(self.OPTIONS['csv_logging']):
						self.device_logger.writeLog(self.sensor_values)

	# returns if a option flag is true or not 
	def isFlagTrue(self, option_flag):
		if( option_flag in self.OPTIONS):
			if(self.OPTIONS[option_flag]):
				return True
			else:
				return False
		else:
			return False
				
				

	# Our threaded operation. Use object.start() to start this
	def run(self):
		if self.debug_mode:
			# NOTE: We no longer need poll_debug, since 
			# we have profiles to read off of now.
			# self.poll_debug()
			if( self.isFlagTrue("debug_profile")):
				self.poll_debug_csv(self.OPTIONS['debug_profile'])
			else:
				self.poll_debug_csv()
				

		else:
			try:
				self.poll()
			except Exception as ex:
				# Hide the errors for now...
				# TODO: Figure out how to report these in a better manner.
				# (perhaps logging it somewhere?)
				print ex
				self.run();
				

	# ==========================================================
	# Semi-public interface
	#
	# These functions are not meant to normally be called
	# since the class handles threading. But can be called 
	# IF really needed, or for debug purposes. 
	# ==========================================================

	# ----------------------------------------------------	
	#
	# Constantly poll in debug mode. 
	#
	# All this currently does is waste cycles in the background
	# and fetch some dummy values. Updates the global
	# sensor_values class variable.
	#
	#
	# ----------------------------------------------------
	def poll_debug(self):
		print "Warning: We're in debug mode!"
		# Set our debug values()
		while True:
			self.sensor_values = self.getFinalDummyValues()

			self.__readyFlag = True
			self.setSampleTime();
			time.sleep(1)

	# Returns a dictionary of our current sensor values
	def getValues(self):
		return self.sensor_values

	# Gets the current time
	def getSeconds(self):
		return datetime.now()

	# Sets the sample timer flag
	def setSampleTime(self):
		self.last_sample_time = self.getSeconds();

	# ==========================================================
	# Private Interface (Not for use outside this class!!)
	# ==========================================================

	# Initialize the serial connection
	def init_serial(self, BAUD_RATE, SERIAL_PORT):
		# Initialize our serial port with the correct control flags (for our breadboarded arduino)
		self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE);

		# NOTE: This option was previously added for serial communcation to barebones
		# breadboared arduino running at 8Mhz
		# self.ser.setRTS(False);

	# Read in from serial (with a line delimiter)
	def readLine(self):
		return self.ser.readline()

	# Read a character from serial
	def readChar(self):
		return self.ser.read()

	# Returns our dummy dictonary 
	def getFinalDummyValues(self):
		final_values_dict = {}
		for value in self.values_index:
			# print value
			final_values_dict[value] = -21
		return final_values_dict

	# Poll debug using csv
	def poll_debug_csv(self, debug_file='debug_profile.csv'):
		csv_reader = CSVIterator(debug_file)
		while True:
			self.sensor_values = csv_reader.get_data()
			self.__readyFlag = True


			time.sleep(self.sample_period_s)
			self.setSampleTime()

	def write_csv(self):
		write_values = []
		print "writing csv"
		with open('debug_values.csv', 'wb') as csvfile:
			writer = csv.writer(csvfile, delimiter=',')

	def write(self, string):
		self.ser.writeLog(string)

	def decode(self, data_raw):
			values = self.unpack(data_raw)
			

			final_values = {}

			for i in range(len(self.values_index)):
				final_values[self.values_index[i]] = values[i]

			# Remove items from the dictionary we don't need
			del final_values['checksum']
			del final_values['packet_header']
			del final_values['packet_ender']
			del final_values['packet_id']

			if self.verbose:
				 print final_values

			return final_values

	def unpack(self, data_raw):
		self.verbose_print("unpacking")
		self.verbose_print("raw data length:" + str(len(data_raw)))
		output = unpack(self.unpack_schema, data_raw)
		return list(output);
