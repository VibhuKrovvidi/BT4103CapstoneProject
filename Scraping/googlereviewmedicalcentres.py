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




	#reviewCount = len(driver.find_elements_by_xpath("//div[@class='section-review ripple-container']"))

	#totalReviews = driver.find_elements_by_xpath('//*[@id="pane"]/div/div[1]/div/div/div[3]/div[2]/div/div[2]/div[2]');
	#totalReviews = [i for i in totalReviews][0].text
	#totalReviews = int(totalReviews.split()[0])
	#print(str(totalReviews) + " reviews found")

	# loading a minimum of 50 reviews
	#while reviewCount < totalReviews: #<=== change this number based on your requirement
		#print("Scrolling to review number :", reviewCount)
		# load the reviews
	#	driver.find_element_by_xpath("//div[contains(@class,'section-loading-spinner')]").location_once_scrolled_into_view 
		# wait for loading the reviews
	#	WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,"//div[@class='section-loading-overlay-spinner'][@style='display:none']")))
		# get the reviewsCount
	#	reviewCount = len(driver.find_elements_by_class_name("section-review-content"))

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
	dbmedical = "https://www.google.com/maps/place/DB+Medical:+Women's+%26+Men's+Health+Clinic,+STD+Testing+services+Singapore/@1.3039054,103.8333876,17z/data=!4m7!3m6!1s0x31da19eb657259e1:0xde7f4bdac3092fba!8m2!3d1.3039054!4d103.8355763!9m1!1b1"
	lifescanpara = "https://www.google.com/maps/place/Lifescan+Medical+Centre+(Paragon)+by+SMG/@1.3223051,103.8319112,13z/data=!4m8!1m2!2m1!1slifescan+medical!3m4!1s0x31da19032c9c1695:0x935841c916165058!8m2!3d1.3039054!4d103.8355763"
	lifescannov = 'https://www.google.com/maps/place/Lifescan+Medical+Centre+(Novena)+by+SMG/@1.3223051,103.8319112,13z/data=!4m10!1m2!2m1!1slifescan+medical!3m6!1s0x31da1961131fe769:0xc0550554970c97ad!8m2!3d1.3206513!4d103.8443689!9m1!1b1'
	nuffield = 'https://www.google.com/maps/place/Nuffield+Medical+Siglap/@1.312145,103.9222273,17z/data=!4m7!3m6!1s0x31da22a49fbaa45f:0x2b02dee2b1767262!8m2!3d1.312145!4d103.924416!9m1!1b1'
	fullerton = 'https://www.google.com/maps/place/Fullerton+Health+Screening+Centre+(NAC26)+@+Ngee+Ann+City/@1.3027623,103.8321014,17z/data=!4m7!3m6!1s0x31da1991f188a28f:0x6cbe025ff6b9503c!8m2!3d1.3027623!4d103.8342901!9m1!1b1'
	trucare = 'https://www.google.com/maps/place/Trucare+Medical+Clinic+And+Surgery+(Hougang+Central)/@1.3223051,103.8319112,13z/data=!4m10!1m2!2m1!1strucare+medical!3m6!1s0x31da1636e6dd9c55:0xbd8dfa74aeb4b64a!8m2!3d1.3704607!4d103.8952681!9m1!1b1'
	mediway = 'https://www.google.com/maps/place/Mediway+Medical+Centre/@1.301357,103.8471493,17z/data=!4m7!3m6!1s0x31da19bc43a8cf6d:0x315ecf597092bba7!8m2!3d1.301357!4d103.849338!9m1!1b1'
	precious = 'https://www.google.com/maps/place/Precious+Medical+Centre/@1.3042346,103.8339929,17z/data=!4m7!3m6!1s0x31da199231016065:0x217a90b58a789ed2!8m2!3d1.3042346!4d103.8361816!9m1!1b1'
	wl = 'https://www.google.com/maps/place/WL%26H+Medical/@1.3063434,103.8296719,17z/data=!4m7!3m6!1s0x31da198a28390f8d:0x4074d8da19f62d15!8m2!3d1.3063434!4d103.8318606!9m1!1b1'
	thomsonmedical = 'https://www.google.com/maps/place/Thomson+Medical+Centre/@1.3253292,103.8393125,17z/data=!4m7!3m6!1s0x31da19e1c9e43fe7:0x2be5ea31a650bf02!8m2!3d1.3253292!4d103.8415012!9m1!1b1'
	mounte = 'https://www.google.com/maps/place/Executive+Health+Screeners+-+Mount+Elizabeth+Hospital/@1.3223051,103.8319112,13z/data=!4m10!1m2!2m1!1smount+elizabeth+hospital+health+screening!3m6!1s0x31da1992febf3501:0x66b112a4ba300661!8m2!3d1.3042908!4d103.8351673!9m1!1b1'
	raffles = 'https://www.google.com/maps/place/Raffles+Health+Screeners/@1.3012602,103.8549811,17z/data=!4m7!3m6!1s0x31da19b091e666c5:0x2e2f1a9d2bc1fae2!8m2!3d1.3012586!4d103.8571714!9m1!1b1'
	mcs = [dbmedical,lifescanpara, lifescannov,nuffield,fullerton,trucare,mediway,precious,wl,thomsonmedical, mounte, raffles]
	for a in mcs:
		print('doing ' + a)
		x,y,z = scrape(a)
		s.extend(x)
		age.extend(y)
		content.extend(z)
		print('done ' + a)
		continue
	#mydf = scrape(myurl1)

	df = pd.DataFrame(list(zip(s,age,content)), columns = ['Stars','Age','Content'])
	df.to_csv('medical centre review.csv')
