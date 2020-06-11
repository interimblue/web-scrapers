import requests
import urllib.request
import re
import logging
import json
import os
import datetime as dt
import sys
import time
import signal
from bs4 import BeautifulSoup

#===============================================================================
#                                Setup 
#===============================================================================

### Logging
start = time.time()
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s  %(message)s',
    datefmt='%Y-%m-%d_T_%H:%M:%S',
    filename='8kun_scraper.log',
    level=logging.DEBUG
    )

### Get post Ids from first 10 pages
eightkun_base_url = 'https://8kun.top/' 
page_1_url = 'https://8kun.top/pnd/index.html'
imageBoard = 'pnd'
maxPages = 10
matchingString = 'id="op_'
path = '8kun-data/'

### Lists
divList = []
listOfPostIds = []

### Signal handler used to terminate function when http request hands (due to unresponsive 8kun)
def handler(signum, frame):
    logging.error("Terminating fetch of page due to no respose after 1 minute...")
    raise Exception("* URL Request Terminated *")

### We define a timeout time of 60 seconds. If any requests hang for more than 
### this time they are terminated by the signal handler
timeoutTime = 60 

### Create necessary directory structure - else file writing will throw exception
if os.path.exists(path):
    logging.info("Directory %s exists, using existing directory" % path)
else:
    try:  
        logging.info("Directory %s not found, attepting to create directory" % path)
        os.mkdir(path)
    except OSError:  
        logging.error("Failed to create directory: %s" % path)
    else:  
        logging.info("Successfully created the directory %s. Proceeding to scrape..." % path)

#===============================================================================
#                           Get Ids from pages 
#===============================================================================

# Structure: https://8kun.top/pnd/3.html
# fullUrl = eightkun_base_url + imageBoard + str(pageNumber) + '.html'

### Scrape post Ids
for pageNumber in range(1,10):
    ### Construct url
    if pageNumber == 1:
        url = page_1_url
    else:
        url = eightkun_base_url + imageBoard + '/' + str(pageNumber) + '.html'
    
    ### Connect to the URL
    logging.info("Pinging page {p} at {url}...".format(p=pageNumber, url=url))
    try:
        ### First define a signal alarm, to terminate the function in case the request hangs
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeoutTime)

        response = requests.get(url)
    except Exception as e:
        logging.error("Fatal error when attempting to fetch 8kun data")
        logging.error(e)
    
    soup = BeautifulSoup(response.text, "html.parser")

    ### Find the Ids
    for div in soup.findAll('div'):
        matchObject = re.search(matchingString, str(div))
        if matchObject is not None:
            divList.append(div)

    ### Extract the Ids
    for div in divList:     
        matchObject = re.search("op_", div.get('id'))
        if matchObject is None:
            divList.remove(div)
    
    for div in divList:
        postId = div.get('id')[3:]
        listOfPostIds.append(postId)
   
    ### 8kun will terminate the connection if requests are too frequent (standard DOS protection)
    time.sleep(3)

logging.info("Total posts scraped [%s]" %len(listOfPostIds))
listOfPostIds = list(set(listOfPostIds))
logging.info("Total UNIQUE posts scraped [%s]" %len(listOfPostIds))

#===============================================================================
#                           Download 
#===============================================================================

datetime = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

### Now fetch the main post URL (with all comments) for each Id and save the entire html page
### Example id structure: https://8kun.top/pnd/res/121497.html#121497
logging.info("Preparing to request and save individual Post HTML pages...")
for postId in listOfPostIds:
    
    ### URL and filename construction
    url = eightkun_base_url + imageBoard + '/' + 'res/' + str(postId) + '.html' + '#' + str(postId)
    filename = path + datetime + '_' + imageBoard + '_' + str(postId) + '.html'
    
    ### Connect to the specific post page with all the comments
    logging.info("Getting %s..." %url)
    try:
        ### First define a signal alarm, to terminate the function in case the request hangs
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeoutTime)

        ### Now fetch the URl 
        response = requests.get(url)
    except Exception as e:
        logging.error("Fatal error when attempting to fetch 8kun data")
        logging.error(e)
    soup = BeautifulSoup(response.text, "html.parser")

    ### Write to file
    try:
        logging.info("Writing 8kun HTML response to file...")
        with open(filename, "w") as file:
            file.write(str(soup))
    except Exception as e:
        logging.error("Fatal error when attempting to write HTML from 8kun to file")
        logging.error(e)
    
    ### 8kun will terminate the connection if requests are too frequent (standard DOS protection)
    time.sleep(1)

### Logging: Timing consolidation
end = time.time()
timeElasped = end-start 
logging.info('=============== Time elasped: %s ==============='% timeElasped)


