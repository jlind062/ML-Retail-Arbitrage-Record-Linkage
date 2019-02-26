# ML-Retail-Arbitrage-Record-Linkage

The following is an attempt to use sklearns implementation machine learning algorithms to provide data record linkage between different web scraped databases of market data. All the relevant data, code, results, and methadology is included in the jupyter notebook. This includes a tutorial on how to use Scrapy to make a web crawler to extract the product data from various websites, the source code, images, and results used in the Jupyter notebook.

The results were ultimately extremely ineffective when compared to the current implementation of using levenshtein distance to match data across different sources. ML in this content is slower, more complex, and less accurate. However, there is still much value to some of the methadology and scripts using in this investigation. 

The included files are:
Machine_Learning_Arbitrage_Record_Linkage.ipynb: The jupyter notebook containing code, methadology, and results.
Jupyter Notebook and Source Code/
	Amazon Source HTML.htm: HTML source code used to develop Amazon scraper
	config.json: configuration file with information for SQL server and scrapers
	images: images used in Machine_Learning_Arbitrage_Record_Linkage.ipynb
	results: local csv results of scrapers
	scrape.py: script to manage and run all scrapers
	scrapers/
		scraper_amazon.py: scraper to collect product data from Amazon
		scraper_kijiji.py: scraper to collect product data from Kijiji
		scraper_craigslist.py: scraper to collect product data from Craigslist
	upload_results.py: script to upload results to SQL server