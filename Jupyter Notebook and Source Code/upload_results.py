import csv
import pymysql
import os
import scrape
import json


class CSVManager:
    def __init__(self, **kwargs):
        self.path = kwargs.get('path')
        self.sources = kwargs.get('sources')
        if not self.get_csvs():
            raise NotADirectoryError("There is no scan scan data in directory '%s" % self.path)
        self.csvs = self.get_csvs()

    def get_csvs(self):
        # get all the csv from the results directory
        csvs = []
        for file in os.listdir(self.path):
            if file[:file.find(" ")] in self.sources:
                csvs.append(self.path + "/" + file)
        return csvs

    def write_csvs(self, db):
        # writes data from every csv
        for path in self.csvs:
            self.write_data(path, db)

    @staticmethod
    def write_data(path, db):
        def check_valid(data):
            # checks to see if price is valid and that there is no item with the same url in the db
            if data[1] is not "Invalid" and data[6] == '0':
                if db.check_primary(db.save_table, "address", data[2]) == 0:
                    return True
                else:
                    return False

        # writes all the data
        with open(path) as f:
            reader = csv.reader(f)
            for row in reader:
                if check_valid(row) is True:
                    db.write_scan([row[0].replace("'", "").encode('ascii', 'replace').decode(),
                                   int(row[1][:row[1].find('.')]), row[2], row[7][:row[7].find(' ')],
                                   row[4], row[3], row[7], "1"])

    def move_scans(self):
        # puts all the csv files from the results directory to the old subdirectory
        # which contains a folder for each source
        for path in self.csvs:
            filename = self.__after_nth_substring(path, '/', 6)
            source = filename[:filename.index(' ')]
            subdirectory = path[:path.index(filename)] + "old/" + source + "/"
            if not os.path.exists(subdirectory):
                os.makedirs(subdirectory)
            new_path = subdirectory + filename
            os.rename(path, new_path)

    @staticmethod
    def __after_nth_substring(string, substring, n):
        # return the string after nth occurrence of the substring
        string_trim = string
        for i in range(0, n):
            string_trim = string_trim[string_trim.find(substring) + 1:]
        return string_trim


if __name__ == "__main__":
    # writes all the valid items from the scan csvs to the server
    with open('config.json', 'r') as f:
        config = json.load(f)
    results_db = scrape.ScanDBManager(config["LOCAL"], config["BASIC"])
    scan_sources = results_db.get_sources()
    manager = CSVManager(path=config["BASIC"]["result_path"],
                         sources=scan_sources)
    manager.write_csvs(results_db)
    manager.move_scans()
