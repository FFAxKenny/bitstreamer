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

from csviterator import CSVIterator
from struct import *
from threading import Thread 
from datetime import datetime

class BitStreamer(Thread):
    # ==========================================================
    # Public Interface
    # ==========================================================

    # -------------------------------------------------------
    # Pesudo-constructor
    # -------------------------------------------------------
    def __init__(self):
        Thread.__init__(self)


    # - 
    # Full constructor
    # -
    def initialize(self, debug_mode=False, options={}, baud_rate=9600, serial_port='/dev/ttyS6', sample_period_s='0.025'):
        self.__readyFlag = False

        self.__verbose = False          
        self.__echo = False             

        # Corrupted packets - don't match our packet length, but have the correct header
        # Incorrect packets - don't match anything at all.
        self.corrupted_packets = 0;
        self.incorrect_packets = 0;
        self.total_packets = 0;

        self.sensor_values = {}
        self.options = options
        self.serial_port = serial_port
        self.values_index = self.getValuesIndex()
        self.unpack_schema = self.__genUnpackSchema()

        self.packet_config = self.loadPacketConfig()

        self.last_sample_time = self.getSeconds();

        formatted_time = datetime.now().strftime('%Y%m%d-%H-%M-%S')

        ## Setting debug mode disables the serial input and generates an internal signal
        self.debug_mode = debug_mode
        if self.debug_mode == True:
            self.__verbose_print("Warning: Debug Mode Enabled.")
        else:
            self.__init_serial(baud_rate, serial_port)
    
    # Returns if the driver is ready or not.
    def isReady(self,):
        return self.__readyFlag

    # Parses an unpack schema and spits out the size.
    def parsePacketSize(self, unpack_schema):
        size = 0
        # self.verbose_print("Get packet size for " + str(unpack_schema))
        for x in unpack_schema:
            if x is 'c':
                size += 1
            elif x is 'h':
                size += 2
            elif x is 'f':
                size += 4
            else:
                # Do nothing
                pass
        return size

    def loadPacketConfig(self):
        self.packet_config = {}
        with open('packet_kay.yaml') as config_file:
            self.packet_config = yaml.load(config_file)

    def getPacketIndex(self):
        """ 
        Sets the packet index (useful for later), when we're 
        iterating through things.
        """
        pass

        """
        OLD CODE
        self.packet_key = {}
        try:
            file_name = "packet_key.yaml"
            config_file = open(file_name, 'r')
            self.packet_key = yaml.load(config_file)
        except(Exception):
            print "CONFIG ERROR: no packet key detected."
        values_index = ['packet_header','data_1', 'data_2', 'checksum', 'packet_ender']
        return values_index
        """

    def secondsSinceLastSample(self):
        """
        Returns how long it's been since the last sample.
        """
        return( self.getSeconds() - self.last_sample_time).seconds

    def poll(self):
        """ 
        Continuously poll for new data.
        """
        while True:
            data_raw = self.__readLine()
            self.__verbose_print("RECV: New line!")
            self.total_packets += 1

            if('$' in data_raw):
                # If our packet header matches, decode it
                try:
                    self.sensor_values = self.__decode(data_raw)
                    self.setSampleTime();
                    self.__readyFlag = True
                except:
                    # TODO: Log to a file
                    self.corrupted_packets += 1
                finally:
                    pass
            else:
                # Else do nothing
                self.incorrect_packets += 1
                pass

    # Poll using a csv file.
    def poll_debug_csv(self, debug_file='debug_profile.csv'):
        csv_reader = CSVIterator(debug_file)
        while True:
            self.sensor_values = csv_reader.get_data()
            self.__readyFlag = True

            time.sleep(self.sample_period_s)
            self.setSampleTime()

    def checkCSV(self):
        """ 
        Checks the csv file to see if it matches our packet descriptor
        """
        pass

    def isFlagTrue(self, option_flag):
        """ 
        Returns true if an option exists in the options dictionary, 
        as well if it is actually 'True' itself.
        """
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

    def __init_serial(self, baud_rate, serial_port):
        """
        Initialize the serial connection
        """
        self.ser = serial.Serial(serial_port, baud_rate);

    # Read in from serial (with a line delimiter)
    def __readLine(self):
        return self.ser.readline()

    # Read a character from serial
    def __readChar(self):
        return self.ser.read()

    def __decode(self, data_raw):
        values = self.__unpack(data_raw)
        final_values = {}

        for i in range(len(self.values_index)):
            final_values[self.values_index[i]] = values[i]

        # Remove the descriptors, and print only the data
        for key in self.packet_config['packet']['descriptors']:
            del final_values[key]
            
        if self.verbose:
             print final_values

        return final_values

    def __unpack(self, data_raw):
        self.__verbose_print("unpacking...")
        self.__verbose_print("raw data length:" + str(len(data_raw)))
        output = unpack(self.unpack_schema, data_raw)
        return list(output);
