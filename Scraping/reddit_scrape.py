import praw
import pandas as pd
import requests
import time
import math
import sys
import string

reddit = praw.Reddit(client_id='kQoyoJ9Ag4JxTQ', client_secret='fPR3EGxAsC4ERoPHW4HNfxaMsle5Nw', user_agent='nsscraper')
subreddit_name = 'NationalServiceSG'

def submissions_pushshift_praw(subreddit, start=None, end=None, limit=100, extra_query=""):
    """
    A simple function that returns a list of PRAW submission objects during a particular period from a defined sub.
    This function serves as a replacement for the now deprecated PRAW `submissions()` method.
    
    :param subreddit: A subreddit name to fetch submissions from.
    :param start: A Unix time integer. Posts fetched will be AFTER this time. (default: None)
    :param end: A Unix time integer. Posts fetched will be BEFORE this time. (default: None)
    :param limit: There needs to be a defined limit of results (default: 100), or Pushshift will return only 25.
    :param extra_query: A query string is optional. If an extra_query string is not supplied, 
                        the function will just grab everything from the defined time period. (default: empty string)
    
    Submissions are yielded newest first.
    
    For more information on PRAW, see: https://github.com/praw-dev/praw 
    For more information on Pushshift, see: https://github.com/pushshift/api
    """
    matching_praw_submissions = []
    
    # Default time values if none are defined (credit to u/bboe's PRAW `submissions()` for this section)
    utc_offset = 28800
    now = int(time.time())
    start = max(int(start) + utc_offset if start else 0, 0)
    end = min(int(end) if end else now, now) + utc_offset
    
    # Format our search link properly.
    search_link = ('https://api.pushshift.io/reddit/submission/search/'
                   '?subreddit={}&after={}&before={}&sort_type=score&sort=asc&limit={}&q={}')
    search_link = search_link.format(subreddit, start, end, limit, extra_query)
    
    # Get the data from Pushshift as JSON.
    retrieved_data = requests.get(search_link)
    returned_submissions = retrieved_data.json()['data']
    
    i = 0
    # Iterate over the returned submissions to convert them to PRAW submission objects.
    for submission in returned_submissions:
        
        progress(i, len(returned_submissions), status='Collecting posts')
        # Take the ID, fetch the PRAW submission object, and append to our list
        praw_submission = reddit.submission(id=submission['id'])
        matching_praw_submissions.append(praw_submission)
        i += 1
     
    # Return all PRAW submissions that were obtained.
    return matching_praw_submissions

# Progress bar
def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()  # As suggested by Rom Ruben (see: http://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console/27871113#comment50529068_27871113)

# Get posts beginning from February 1 2021
extracted_posts = submissions_pushshift_praw(subreddit_name, start=1612108800, limit=2000) # Replaced: sub = reddit.subreddit(subreddit_name).new(limit=100)

posts = []
for p in extracted_posts:
    try:
        posts.append([p.title, p.score, p.id, p.subreddit, p.url, p.num_comments, p.selftext, p.link_flair_template_id, p.link_flair_text, p.created])
    except AttributeError:
        posts.append([p.title, p.score, p.id, p.subreddit, p.url, p.num_comments, p.selftext, "None", "None", p.created])

posts = pd.DataFrame(posts, columns=['title', 'score', 'id', 'subreddit', 'url', 'num_comments', 'body', 'flair_id', 'flair', 'created'])
print("Posts:")
print(posts)

# Get all comments per post
all_comments = []
i = 0
for iden in posts['id']:
    progress(i, len(posts.index), status='Collecting comments')
    post = reddit.submission(id=iden)
    post.comments.replace_more(limit=0)
    for c in post.comments.list():
        all_comments.append([c.score, c.id, c.subreddit, c.depth, c.body, c.created, iden])
    i += 1

all_comments = pd.DataFrame(all_comments, columns=['score', 'id', 'subreddit', 'depth', 'body', 'created', 'op_id'])
print("Comments:")
print(all_comments)

# Preprocess data
posts.loc[(posts.body == "[removed]"), "body"] = ""
posts.loc[(posts.body == "[deleted]"), "body"] = ""
all_comments.loc[(all_comments.body == "[removed]"), "body"] = "" 
all_comments = all_comments.filter(items = ["body"]).rename(columns = {"body": "content"})

posts.to_csv('C:/Users/TzeMin/Documents/capstone/BT4103CapstoneProject/ScrapedOutput/nationalservicesg_posts.csv', index=False)
all_comments.to_csv('C:/Users/TzeMin/Documents/capstone/BT4103CapstoneProject/ScrapedOutput/nationalservicesg_comments.csv', index=False)

lastDigit = posts["title"].str.strip().str[-1]
mask = (~lastDigit.isin(list(string.punctuation)))
need_fullstop = posts[mask]
posts.loc[mask, "title"] = need_fullstop["title"] + "."
posts["content"] = posts["title"] + " " + posts["body"]
posts = posts.filter(items = ["content"])

# Combine the two datasets into one
textdata = posts.append(all_comments, ignore_index = True)
textdata.to_csv('C:/Users/TzeMin/Documents/capstone/BT4103CapstoneProject/ScrapedOutput/nationalservicesg_combineddata.csv', index=False)