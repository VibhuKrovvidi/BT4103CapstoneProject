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

	#review_df = pd.DataFrame()
	#review_df['Reviewer'] = reviewers
	#review_df['Stars'] = stars
	#review_df['Age'] = age
	#review_df['Content'] = content

	#print(review_df)
	#print("Total Reviews Scraped = ", review_df.shape[0])

	time.sleep(4)
	driver.quit()

	return stars,age,content


#myurl1 = "https://www.google.com/maps/place/Tembusu+College/@1.3058932,103.7716691,17z/data=!4m7!3m6!1s0x31da1af50a2f1ebf:0x8aea55fe34ee4a51!8m2!3d1.3058932!4d103.7738578!9m1!1b1"

if __name__ == '__main__':
	s = []
	age = []
	content = []
	myurl1 = "https://www.google.com/maps/place/Healthway+Medical+(Novena+Medical+Centre)/@1.3226432,103.8409845,17z/data=!3m1!5s0x31da19e7738a38fd:0xcc5efc5c9c1bdbf4!4m10!1m2!2m1!1snovena+medical+centre!3m6!1s0x31da19e7834e8185:0x27cfb1274af1bdf2!8m2!3d1.320281!4d103.844022!9m1!1b1"
	myurl2 = "https://www.google.com/maps/place/SATA+CommHealth+Potong+Pasir+Medical+Centre/@1.3290387,103.86781,17z/data=!4m7!3m6!1s0x31da1781b3eafc99:0x9bc33e405fceb63a!8m2!3d1.3290387!4d103.8699987!9m1!1b1"
	myurl3 = 'https://www.google.com/maps/place/Thomson+Wellth+(Medical+and+Aesthetic+Clinic)/@1.3039131,103.8336003,17z/data=!4m7!3m6!1s0x31da19e767ebaba1:0x71b5291cda0d41c4!8m2!3d1.3039131!4d103.835789!9m1!1b1'
	mcs = [myurl1, myurl2, myurl3]
	for a in mcs:
		x,y,z = scrape(a)
		s.extend(x)
		age.extend(y)
		content.extend(z)
	#mydf = scrape(myurl1)

	df = pd.DataFrame(list(zip(s,age,content)), columns = ['Stars','Age','Content'])
	df.to_csv('medical centre review.csv')
