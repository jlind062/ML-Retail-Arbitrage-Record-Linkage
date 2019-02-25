import scrapers.scraper_craigslist as Craigslist
import scrapers.scraper_kijiji as Kijiji
from scrapy.crawler import CrawlerProcess
import pymysql
import datetime
import json


class ScanDBManager:
    def __init__(self, db_set, basic_set):
        try:
            self.db = pymysql.connect(host=db_set['host'],
                                      user=db_set['user'],
                                      passwd=db_set['password'],
                                      db=db_set['database'],
                                      charset="utf8")
        except Exception as e:
            raise ConnectionError("Could not connect to the database because of error: %s \n" % e.__str__())
            return
        self.cursor = self.db.cursor()
        self.set_unicode()
        self.word_filter = basic_set['word_filter']
        self.char_filter = basic_set['char_filter']
        try:
            self.check_tables(db_set['scan_table'], db_set['save_table'])
        except (NotADirectoryError, UserWarning) as e:
            print("Error: %s \n has prevented a proper database connection" % e.__str__())

        self.scan_table = db_set['scan_table']
        self.save_table = db_set['save_table']

    def set_unicode(self):
        self.cursor.execute('SET NAMES utf8;')
        self.cursor.execute('SET CHARACTER SET utf8;')
        self.cursor.execute('SET character_set_connection=utf8;')

    def check_tables(self, scan_table, save_table):
        # check if there is a scan table
        if self.cursor.execute("SHOW TABLES LIKE '%s';" % scan_table) == 0:
            raise NotADirectoryError("There is no scan table called '%s")

        # check if the scan table has any links
        if self.cursor.execute("SELECT * FROM %s;" % scan_table) == 0:
            raise UserWarning("There are entries in table '%s' to scan" % scan_table)

        # check if there is a results table, if not create one
        if self.cursor.execute("SHOW TABLES LIKE '%s';" % save_table) == 0:
            self.create_results_table(save_table)

    def create_results_table(self, table_name):
        # create a table to save the results. This should not be hardcoded
        # but move to a config file before launch
        query = """
                CREATE TABLE %s (
                  name VARCHAR(255) NOT NULL,
                  clean_name VARCHAR(255),
                  price INT NOT NULL,
                  address VARCHAR(255) PRIMARY KEY NOT NULL,
                  date DATE NOT NULL,
                  category_code VARCHAR(255) NOT NULL,
                  category VARCHAR(255),
                  city_code VARCHAR(255),
                  city VARCHAR(255),
                  description TEXT,
                  comment TEXT,
                  uploader VARCHAR(255),
                  duplicate BOOLEAN DEFAULT FALSE,
                  profitable BOOLEAN,
                  last_updated DATETIME,
                  active BOOLEAN
                );
                """"" % table_name
        self.cursor.execute(query)

    def get_to_scan(self):
        # returns a list of all the links to scan
        self.cursor.execute("SELECT * FROM %s;" % self.scan_table)
        to_scan = self.cursor.fetchall()
        return to_scan

    def get_sources(self):
        self.cursor.execute("SELECT DISTINCT source FROM %s;" % self.scan_table)
        sources = []
        for source in self.cursor.fetchall():
            sources.append(source[0])
        return sources

    def write_scan(self, data):
        query = "INSERT INTO scan_results (name, clean_name, price, address, date, " \
        "category_code, city, last_updated, active) VALUES " \
        "('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % (
            data[0], self.clean_name(data[0], self.char_filter, self.word_filter),
            data[1], data[2], data[3], data[4], data[5], data[6], data[7])
        try:
            self.cursor.execute(query)
            self.db.commit()
        except pymysql.Error as e:
            print("Error '%s' as a result of query '%s'" %(e.__str__(), query))

    def clean_name(self, raw_name, char_filter, word_filter):
        # removes any chars from the char filter and removes words from the word filter
        # returns in lower case
        try:
            raw_name = raw_name.lower()
            for c in char_filter:
                raw_name = raw_name.replace(c, " ")
            raw_name = ' '.join(raw_name.split())
            words = raw_name.split(' ')
            clean_words = []
            for word in words:
                if (word not in word_filter) and ('$' not in word) and (len(word) > 1):
                    clean_words.append(word)
            name = " ".join(clean_words)
        except Exception as e:
            print("Error cleaning name %s because of exception: %s" % e.__str__)
            name = raw_name
        return name

    def check_primary(self, table, column, key):
        return self.cursor.execute("SELECT 1 FROM %s WHERE %s = '%s' LIMIT 1" % (table, column, key))

    def close(self):
        self.db.close()


class ScanManager:
    @staticmethod
    def scan(process, to_scan, scan_process):
        for link in to_scan:
            if link[2] in scan_process:
                scan_profile = scan_process.get(link[2])
                spider = scan_profile[1]
                path = scan_profile[0]
                spider.add_crawler(process, path=path,
                                   start_urls=[link[1]], city=link[0])
            else:
                raise UserWarning("There is no scan process for source '%s" % link[2])

    @staticmethod
    def main(settings):
        try:
            db = ScanDBManager(settings["LOCAL"], settings["BASIC"])
        except ConnectionError as e:
            print(e)
        process = CrawlerProcess(settings["CRAWLER"])
        to_scan = db.get_to_scan()
        scan_profiles = ScanManager.generate_profiles(settings["SCAN"])
        ScanManager.scan(process, to_scan, scan_profiles)
        process.start()

    @staticmethod
    def generate_profiles(profiles):
        scan_profiles = {}
        start_time = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
        for profile in profiles:
            data = []
            for param in profiles.get(profile):
                if (param[-3:]) == "csv":
                    data.append(param[:-4] + " " + start_time + ".csv")
                elif param[-6:] == "Main()":
                    try:
                        data.append(eval(param))
                    except NameError:
                        print("The scraper class %s could not be read. Make sure you are importing a scraper "
                              "with the proper name" % param)
                else:
                    raise ValueError("Unknown data type '%s' in profile %s" % (param, profile))
            scan_profiles[profile] = data
        return scan_profiles


if __name__ == '__main__':
    with open('config.json', 'r') as f:
        config = json.load(f)
    ScanManager.main(config)
