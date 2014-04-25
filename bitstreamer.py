import serial

# ========================================================
#	
# bitstreamer.py
#
# This module provides a low level serial translator 
# which is highly customizable for simple serial
# communications applications.
#
# =========================================================

import time
from datetime import datetime
import sys
import csv
import yaml
import os

from CSVIterator import CSVIterator
from struct import *
from threading import Thread 
from datetime import datetime

class BitStreamer(Thread):
	
	# ==========================================================
	# Public Interface
	# ==========================================================

	# -------------------------------------------------------
	# Constructor
	# -------------------------------------------------------
	def __init__(self, debug_mode=False, options={}, baud_rate=9600, serial_port='/dev/ttyS6', sample_period_s='0.025'):
		Thread.__init__(self)

		self.__readyFlag = False

		self.verbose = False			
		self.echo = False				

		self.sensor_values = {}
		self.options = options
		self.serial_port = serial_port
		self.values_index = self.getValuesIndex()
		self.unpack_schema = self.__genUnpackSchema()
		self.sample_period_s = 0.025

		self.__verbose_print("Expected packet size: " + str(self.getPacketSize(self.unpack_schema)))

		self.last_sample_time = self.getSeconds();

		formatted_time = datetime.now().strftime('%Y%m%d-%H-%M-%S')

		## Setting debug mode disables the input
		## and generates an internal signal
		self.debug_mode = debug_mode

		if self.debug_mode == True:
			self.__verbose_print("Warning: Debug Mode Enabled.")
		else:
			self.__init_serial(baud_rate, serial_port)
	
	# Returns if the driver is ready or not.
	def isReady(self,):
		return self.__readyFlag



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
			data_raw = self.__readLine()
			self.verbose_print("RECV: New line!")
			if self.echo:
				print data_raw,

			if('$' in data_raw):
				self.sensor_values = self.__decode(data_raw)
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

	def run(self):
		"""
		Our threaded operation. Use object.start() to run this.
		"""
		if self.debug_mode:
			if( self.isFlagTrue("debug_profile")):
				self.poll_debug_csv(self.OPTIONS['debug_profile'])
			else:
				self.poll_debug_csv()
		else:
			self.poll()
				
				
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

	def __verbose_print(self, string):
		"""
		A small verbose print wrapper.
		"""
		if self.verbose:
			print string

	def __genUnpackSchema(self):
		"""
		Generate the unpack schema we're going to be using.
		"""
		s = "<"
		for element in self.values_index:
			s = s + self.packet_key[element]
		self.__verbose_print(s)
		return s

	def __init_serial(self, BAUD_RATE, SERIAL_PORT):
		"""
		Initialize the serial connection
		"""
		self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE);

	# Read in from serial (with a line delimiter)
	def __readLine(self):
		return self.ser.readline()

	# Read a character from serial
	def __readChar(self):
		return self.ser.read()

	# poll debug using csv
	def __poll_debug_csv(self, debug_file='debug_profile.csv'):
		csv_reader = CSVIterator(debug_file)
		while True:
			self.sensor_values = csv_reader.get_data()
			self.__readyFlag = True

			time.sleep(self.sample_period_s)
			self.setSampleTime()

	def __decode(self, data_raw):
		values = self.__unpack(data_raw)
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

	def __unpack(self, data_raw):
		self.__verbose_print("unpacking...")
		self.__verbose_print("raw data length:" + str(len(data_raw)))
		output = unpack(self.unpack_schema, data_raw)
		return list(output);
