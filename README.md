# Web Scrapers

## Reddit Scraper v0.2

__Note: This is an unfinished script under development__

This is a simple Reddit scraper that utilises the Reddit API via the Python PRAW wrapper and outputs a json file with the filtered response.

Documentation for PRAW and its usage can be found here: https://praw.readthedocs.io/en/latest/

### TODO

1. Enable access to quarantined subreddits - PRAW has a method for this but it does not work, possibly a bug
2. Increase thread count per scrape

### Usage 

The repository contains one scraper file:
* `scraper_reddit.py`

You must setup the `config.ini` file:
* Create a config.ini file (use the .template file provided) with your `client_id`, `client_secret` and `user_agent` information. This will be used to authenticate with Reddit.
* Add the desired subreddits to the .ini file subreddit list. The name must match the name in the Reddit URL after the /r/ tag

This script will output 1 file per subreddit and will *update* this file with each subsequent scrape. 

__Note: Reddit does not provide a mechanism to download ALL submissions from a subreddit. Therefore, we are only able to collect the top X amount of submissions (API caps at around 1000). This is configurable at your discretion, we chose to scrape 20 posts per 5 minutes, including all comments contained in those posts__

### Scheduling and Logging 

This script is intended to be run with a scheduler, such as cron. Therefore, to aid debugging in case something goes wrong, the script logs each scrape. 

Logging is logged to `scraper_reddit.py.log` 

## 4chan Scraper v0.2

__Note: This is an unfinished script under development__

This is a simple 4chan scraper that utilises the 4chan API and outputs a json file with the filtered response.

Documentation for the API and its usage can be found here: https://github.com/4chan/4chan-API/

### TODO

1. Multiple board support
2. Option to store responses in 1 large file 
3. Support to extract non-recent replies from each thread

### Usage 

The repository contains two files
* `4chan_catalog_scraper_simple.py`
* `4chan_catalog_scraper_custom.py`

#### Simple

The simple file is the most basic implementation needed to generate a response from the 4chan API. Run this script from the command-line to generate a JSON file containing the unfiltered response output. 

#### Custom

The custom file is intended to filter out unnecessary clutter from the response (e.g. image dimensions) and to for use by a scheduler (e.g. a cron job). 

This script will generate a new file each time is run, batching the files into a separate folder per day. The result will be a file under `4chan-data/YYYY-MM/YYYY-MM-DD_HH-MM-SS_board.json`

__Note: Although 4chan provides a list of thread objects, the relpies to each thread stored in the 'last_replies' JSON array are not exhaustive. Therefore, frequent scraping is required to ensure replies to threads are gathered as they are posted.__

### Scheduling and Logging 

Logging is logged to `4chan_catalog_scraper_custom.log` 

To aid scheduling, the script will store each scrape `.json` file with a timestamp under a folder named with the year and month.

## 8kun Scraper v0.1

The 8kun scraper uses no APIs or libraries and scrapes simply from the raw HTML returned by 8kun.top

The scraper does the following:
1. Iterates through pages 1 and 10 gathering post ids (it is often the case that not all comments are visible in the paginated mode hence we scrape comments in step 2)
2. Iterates through the post ids gathered, downloading and storing the entire HTML document returned, which is the unique page for that post containing all comments. E.g. https://8kun.top/pnd/res/701.html#701

The filenames and logging are the same as above.

Note: I included a timeout method in the 8kun scraper (using signal.alarm) since 8kun sometimes randomly hangs or blocks the connection. This results in the scraper hanging on trying to download one specific post. After 60 seconds of waiting, that post html page will be abandoned and the next will be attempted. This is a rare occurrence and I have included a wait method between each request to reduce the risk of being blocked but it does still periodically occur.
