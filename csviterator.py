# A simple python class which iterates through a CSV file
import time
import csv
import pprint

class CSVIterator:
    def __init__(self, filename):
        pass

    def initialize():
        self.data = self.read_csv(filename)
        self.data_iter = 0
        self.data_len = len(self.data)

    def read_csv(self, filename):
        container = []
        with open(filename, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                container.append(row)
        return container

    # return the data and iterate!
    def get_data(self):
        # grab our value
        value = self.data[self.data_iter]

        # iterate and check for a wrap-around
        self.data_iter = (self.data_iter + 1) % (self.data_len-1)
        return value
            
if __name__ == "__main__":
    csv_reader = CSVIterator("debug_profile1.csv")
    while True:
        print csv_reader.get_data()
        time.sleep(0.001)
