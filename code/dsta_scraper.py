from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.remote_connection import RemoteConnection
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

# Import standard tools
import time
import pandas as pd
import praw
import requests
import math
import sys
import string

# Imports the Google Cloud client library
from google.auth import compute_engine
from google.cloud import datastore

class DSTA_Scraper:
	def __init__(self):
		

		"""
		webdriver.Remote(
			command_executor='http://selenium-hub:4444/wd/hub',
			desired_capabilities=getattr(DesiredCapabilities, "FIREFOX")
		)
		RemoteConnection.set_timeout(36000)
		"""


	def initializeGDS(self):
		global credentials
		global client
		print("Setup Database Connection")
		credentials = compute_engine.Credentials()
		# service account
		self.client = datastore.Client.from_service_account_json('sa.json')

	def get_google_reviews(self, url, location = "CMPB"):
		driver = webdriver.Chrome()
		driver.get(url);

		delay = 3# seconds
		try:
			myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'content-container')))
			print("Page is ready!")
		except TimeoutException:
			print("Loading took too much time!")

		time.sleep(3)
		reviewCount = len(driver.find_elements_by_xpath("//div[@class='section-review ripple-container']"))

		totalReviews = driver.find_elements_by_xpath('//*[@id="pane"]/div/div[1]/div/div/div[3]/div[2]/div/div[2]/div[2]');
		totalReviews = [i for i in totalReviews][0].text
		totalReviews = int(totalReviews.split()[0])
		print(str(totalReviews) + " reviews found")

		# loading a minimum of 50 reviews
		while reviewCount < totalReviews: #<=== change this number based on your requirement
			#print("Scrolling to review number :", reviewCount)
			# load the reviews
			driver.find_element_by_xpath("//div[contains(@class,'section-loading-spinner')]").location_once_scrolled_into_view 
			# wait for loading the reviews
			WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,"//div[@class='section-loading-overlay-spinner'][@style='display:none']")))
			# get the reviewsCount
			reviewCount = len(driver.find_elements_by_class_name("section-review-content"))

		content = []
		temp_content = driver.find_elements_by_class_name('section-review-review-content')
		content = [c.text for c in temp_content]

		time.sleep(2)
		driver.quit()
		
		kind = "google_reviews"

		for c in range(0, len(content)):
			name = location + "_reviewnumber_" + str(c+1)
			task_key = self.client.key(kind, name)
			task = datastore.Entity(key=task_key)
			task['content'] = content[c]
			self.client.put(task)
			#break; # To be removed in deployment

			print('Saved {}: {}'.format(task.key.name, task['content']))
		print("Google Review for " + location + " have been scraped and stored");


	def get_harwarezone(self):
		pass;

	def submissions_pushshift_praw(self, subreddit, reddit, start=None, end=None, limit=100, extra_query=""):
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
	        
	        self.progress(i, len(returned_submissions), status='Collecting posts')
	        # Take the ID, fetch the PRAW submission object, and append to our list
	        praw_submission = reddit.submission(id=submission['id'])
	        matching_praw_submissions.append(praw_submission)
	        i += 1
	     
	    # Return all PRAW submissions that were obtained.
	    return matching_praw_submissions

	# Progress bar
	def progress(self, count, total, status=''):
	    bar_len = 60
	    filled_len = int(round(bar_len * count / float(total)))
	    percents = round(100.0 * count / float(total), 1)
	    bar = '=' * filled_len + '-' * (bar_len - filled_len)
	    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
	    sys.stdout.flush()  # As suggested by Rom Ruben (see: http://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console/27871113#comment50529068_27871113)


	def get_reddit(self, subreddit_name = "NationalServiceSG"):
		reddit = praw.Reddit(client_id='kQoyoJ9Ag4JxTQ', client_secret='fPR3EGxAsC4ERoPHW4HNfxaMsle5Nw', user_agent='nsscraper')
		
		# Get posts beginning from February 1 2021
		extracted_posts = self.submissions_pushshift_praw(subreddit = subreddit_name, start=1612108800, limit=2000, reddit = reddit)

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
		    self.progress(i, len(posts.index), status='Collecting comments')
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

		posts = posts['body'].tolist()
		comments = all_comments['content'].tolist()

		kind = "reddit_posts"

		#print(posts)
		
		for c in range(0, len(posts)):
			if posts[c] == "":
				continue;
			else:
				name = subreddit_name + "_postnumber_" + str(c+1)
				task_key = self.client.key(kind, name)
				task = datastore.Entity(key=task_key)
				task['content'] = posts[c]
				self.client.put(task)
				print('Saved {}: {}'.format(task.key.name, task['content']))
				break; # To be removed in deployment

		kind = "reddit_comments"
		for c in range(0, len(comments)):
			if comments[c] == "":
				continue;
			else:
				name = subreddit_name + "_commentnumber_" + str(c+1)
				task_key = self.client.key(kind, name)
				task = datastore.Entity(key=task_key)
				task['content'] = comments[c]
				self.client.put(task)
				print('Saved {}: {}'.format(task.key.name, task['content']))
				break; # To be removed in deployment
		
			
		print("Reddit Data for " + subreddit_name + " have been scraped and stored");



	def get_seedly(self):
		pass;

#########################################





def main():
	print("Starting DSTA Web Scraper")
	scraper = DSTA_Scraper()
	scraper.initializeGDS()


	# Test greview
	#scraper.get_google_reviews("https://www.google.com/maps/place/CMPB/@1.280195,103.815126,17z/data=!4m7!3m6!1s0x31da1bd0af54732f:0x9c274decbab4e599!8m2!3d1.280195!4d103.815126!9m1!1b1", "CMPB")

	# Test harewarezone

	# Test reddit
	scraper.get_reddit();
	"""
	# Initialise list of greview_urls
	greview_urls = [] # Store a tupple. Eg: ("google.com", "CMPB")
	hzone_urls = []
	reddit_urls = []
	seedly_urls = []

	for i in greview_urls:
		get_google_reviews(i[0], i[1]);
	"""

if __name__ == '__main__':
	main()

# Initialise remote driver


#driver.get(url)

