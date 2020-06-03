"""
Created on 03/03/2020
Reddit Scraper 0.2 - Scrapes Posts and comments of given subreddits, outputs a subreddit json
@author: Andrew Ellul
"""

from os.path import isfile
import logging
import praw
import pandas as pd
from time import sleep
import csv
import json
import datetime as dt
import os
import errno
import time
import sys
import configparser

#===============================================================================
#                           Setup
#===============================================================================

### Logging - default set to INFO, use DEBUG level for very detailed information for each request. Use with caution as this bloats the log file 
logFileName = os.path.basename(__file__) + '.log'
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s  %(message)s',
    datefmt='%Y-%m-%d_T_%H:%M:%S',
    filename=logFileName,
    level=logging.INFO
    )

### Timing and logging
start = time.time()
logging.info(dt.datetime.now().strftime("[%m-%d-%Y_%H:%M:%S] ") + 'Reddit scraper starting...')

### Credentials setup - load from an external config.ini file for security
config = configparser.ConfigParser()
config.read('config.ini')
my_client_id = config["auth"]['client_id']
my_client_secret = config["auth"]['client_secret']
my_user_agent = config["auth"]['user_agent']

### Initialise and authenticate
reddit = praw.Reddit(client_id=my_client_id,
                     client_secret=my_client_secret,
                     user_agent=my_user_agent)

### We do not want to interact with reddit. Output should be true
logging.info(dt.datetime.now().strftime("[%m-%d-%Y_%H:%M:%S] ") + 'Authenticated. Read only: %s' % reddit.read_only)

### A separate file we be created and maintained per subreddit, where scraped posts and their comments will be stored
subredditNames = json.loads(config.get("subreddits","subredditsToScrape"))


#===============================================================================
#                           Serializers
#===============================================================================
def extractCommentArray(commentForest):
    commentList = []
    for comment in commentForest:
        commentAsJSON = serializeComment(comment)
        commentList.append(commentAsJSON)
    return commentList

### Manually hand pick the attributes of the PRAW object we want to store, and return a JSON object that is writable to a file
def serializeRedditor(redditor):
    ### It could be possible that the user account was deleted, in which case redditor is None and would throw an exception if called
    if redditor is not None: 
        logging.debug(dt.datetime.now().strftime("[%m-%d-%Y_%H:%M:%S] ") + 'Serializing redditor [%s] to JSON' % redditor.id)
        return {
            'id': redditor.id,
            'name': redditor.name,
            'comment_karma': redditor.comment_karma,
            'created_utc': redditor.created_utc,
            'has_verified_email': redditor.has_verified_email,
            'icon_img': redditor.icon_img,
            'is_employee': redditor.is_employee,
            'is_mod': redditor.is_mod,
            'is_gold': redditor.is_gold
        }
    else:
        return {
            'id': 'deleted'
        }

### Manually hand pick the attributes of the PRAW object we want to store, and return a JSON object that is writable to a file
def serializeComment(comment):
    logging.debug(dt.datetime.now().strftime("[%m-%d-%Y_%H:%M:%S] ") + 'Serializing comment [%s] to JSON' % comment.id)
    return {
        'id': comment.id,
        'body': comment.body,
        'created_utc': comment.created_utc,
        'edited': comment.edited,
        'is_submitter': comment.is_submitter,
        'link_id': comment.link_id,
        'parent_id': comment.parent_id,
        'permalink': comment.permalink,
        'score': comment.score,
        'stickied': comment.stickied,
        'subreddit_id': comment.subreddit_id
    }

### Manually hand pick the attributes of the PRAW object we want to store, and return a JSON object that is writable to a file
def serializeSubmission(submission):
    logging.debug(dt.datetime.now().strftime("[%m-%d-%Y_%H:%M:%S] ") + 'Serializing submission [%s] to JSON' % submission.id)
    redditorAsJSON = serializeRedditor(submission.author)

    ### The comment forest contains a number of MoreComments objects that must be removed or resolved before parsing
    ### See https://praw.readthedocs.io/en/latest/tutorials/comments.html#the-replace-more-method
    submission.comments.replace_more(limit=None)

    commentList = extractCommentArray(submission.comments.list())
    return {
        'id': submission.id,
        'title': submission.title,
        'name': submission.name,
        'author': redditorAsJSON,
        'created_utc': submission.created_utc,
        'edited': submission.edited,    
        'num_comments': submission.num_comments,
        'over_18': submission.over_18,
        'permalink': submission.permalink,
        'score': submission.score,
        'upvote_ratio': submission.upvote_ratio,
        'url': submission.url,
        'comments': commentList
    }

#===============================================================================
#                           File Writer
#===============================================================================

def writeSubmissionToJson(submissionAsJSON, subredditName):
    ### Each subreddit scrape has its own json file of submissions and comments, updated upon each scrape
    filename = 'data/' + subredditName + '.json'

    ### Check if data directory exists, if not, create it, else fileNotFound error 
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    ### Append serialized submission object to the end of the JSON file
    with open(filename, 'a+') as f:
        json.dump(submissionAsJSON, f)
        f.write(",")

#===============================================================================
#                           Scraper
#===============================================================================

### Scrape Posts from a single Subreddit 
def scrapePosts(subredditName):
    ### Get Subreddit object
    subreddit = reddit.subreddit(subredditName)

    logging.info(dt.datetime.now().strftime("[%m-%d-%Y_%H:%M:%S] ") + 'Fetching subreddit %s' % subredditName)

    ### Object containing all new submissions up to the limit stated or less (reddit API has limits imposed on each request)
    responseLimit = 20 # per 10 minutes / 600 seconds

    allNewSubmissions = subreddit.new(limit=responseLimit)
    logging.info(dt.datetime.now().strftime("[%m-%d-%Y_%H:%M:%S] ") + 'Fetching new submissins, [limit: %s]' % responseLimit)


    ### For each submission, we need to serialize it and store it as json 
    for submission in allNewSubmissions:
        submissionAsJSON = serializeSubmission(submission)
        writeSubmissionToJson(submissionAsJSON, subredditName)

#===============================================================================
#                           Main
#===============================================================================

### Scrape each given subreddit
logging.info(dt.datetime.now().strftime("[%m-%d-%Y_%H:%M:%S] ") + 'Beginning Reddit scrape. Target subreddits: %s' % subredditNames)
for subredditName in subredditNames:
    try:
        scrapePosts(subredditName)
    except Exception as e:
            logging.error("Fatal error when scraping subreddit %s" % subredditName)
            logging.error(e)

### Logging: Timing consolidation
end = time.time()
timeElasped = end-start 
logging.info('=============== Time elasped: %s ==============='% timeElasped)
