from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import requests
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
import time

def scrape(myurl1):
	chrome = webdriver.Chrome()
	driver = chrome
	driver.get(myurl1)

	delay = 3# seconds
	try:
		myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'content-container')))
		print("Page is ready!")
	except TimeoutException:
		print("Loading took too much time!")


	time.sleep(10)




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








	# Get all content boxes
	reviewers = []
	stars = []
	age = []
	content = []

	boxes = driver.find_elements_by_class_name('section-review-content')
	for i in boxes:
		temp_rev = i.find_elements_by_class_name('section-review-title')
		for j in temp_rev:
			reviewers.append(j.text);

	temp_str = driver.find_elements_by_class_name('section-review-stars')
	stars = [q.get_attribute("aria-label") for q in temp_str]

	temp_age = driver.find_elements_by_class_name('section-review-publish-date')
	age = [t.text for t in temp_age]

	temp_content = driver.find_elements_by_class_name('section-review-review-content')
	content = [c.text for c in temp_content]

		
	#print(reviewers, len(reviewers), '\n\n')
	#print(stars, len(stars), '\n\n')
	#print(age, len(age), '\n\n')
	#print(content, len(content), '\n\n')

	review_df = pd.DataFrame()
	review_df['Reviewer'] = reviewers
	review_df['Stars'] = stars
	review_df['Age'] = age
	review_df['Content'] = content

	print(review_df)
	print("Total Reviews Scraped = ", review_df.shape[0])

	time.sleep(4)
	driver.quit()

	return review_df


#myurl1 = "https://www.google.com/maps/place/Tembusu+College/@1.3058932,103.7716691,17z/data=!4m7!3m6!1s0x31da1af50a2f1ebf:0x8aea55fe34ee4a51!8m2!3d1.3058932!4d103.7738578!9m1!1b1"

if __name__ == '__main__':
	myurl1 = "https://www.google.com/maps/place/Cinnamon+College/@1.3067015,103.7713382,17z/data=!4m7!3m6!1s0x31da1af5169c1e05:0xbf1136a704621ca3!8m2!3d1.3067015!4d103.7735269!9m1!1b1"
	myurl2 = "https://www.google.com/maps/place/CMPB/@1.280195,103.815126,17z/data=!4m7!3m6!1s0x31da1bd0af54732f:0x9c274decbab4e599!8m2!3d1.280195!4d103.815126!9m1!1b1"
	scrape(myurl2);




