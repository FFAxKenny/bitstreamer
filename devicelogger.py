# A class for logging serial devices
import os
import time
import csv
import yaml
import datetime

class DeviceLogger():
	# Constructor
	def __init__(self, log_dir, metadata):
		print "Init"
		self.log_dir = log_dir
		self.metadata = metadata
		self.file_path = self.getFilePath()
		self.metadata_path = self.getMetadataFilePath()
		self.datestamp = self.getDateStamp()

		# We haven't written to the log yet. 
		# So set the flag to false
		self.init_flag  = False

		self.checkPath()
		self.writeMetadata()

	# Destructor
	def __del__(self):
		print "Closing"
	
	def getFilePath(self):
		path = os.path.join(self.log_dir, self.getDateStamp(), str(self.getDateStamp()) + ".csv")
		path = str(path)
		return path

	def getMetadataFilePath(self):
		path = os.path.join(self.log_dir, self.getDateStamp(), str(self.getDateStamp()) + ".yaml")
		str(path)
		return path

	# returns a formatted date stamp for our filenames
	def getDateStamp(self):
		# Check if the metadata contains a specific datestamp format
		if 'datestamp' in self.metadata:
			return self.metadata['datestamp']
		else:
			return datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

	def setKeys(self, keys):
		self.keys = keys

	def checkPath(self):
		# Check if the device logger directory exists
		# if not, create it.
		if not os.path.exists(self.log_dir):
			os.mkdir(self.log_dir)
		os.mkdir(os.path.join(self.log_dir, self.getDateStamp()))

	def writeMetadata(self):
		with open(self.metadata_path, 'wb') as outfile:
		    outfile.write( yaml.dump(self.metadata, default_flow_style=False) )

	def writeLog(self, data):
		with open(self.file_path, 'ab+') as f:  # Just use 'w' mode in 3.x
			w = csv.DictWriter(f, self.keys)
			if not self.init_flag:
				w.writeheader()
				self.init_flag = True
			w.writerow(data)

if __name__ == "__main__":
	device_logger = DeviceLogger("test_log/", {'cool_config': True})
	test_data = {'data1': 1.00390625, 'data2': 0.049804688, 'data3': -0.001953125, 'data4': -35, 'data5': -59, 'data6': -78}
	# test_data = {'test': '-1'}
	device_logger.setKeys(test_data.keys())
	while True:
		print "writing log"
		device_logger.writeLog(test_data)
		time.sleep(1)
