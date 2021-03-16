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
import string
import nltk;

from nltk.tokenize import word_tokenize, sent_tokenize;

url = "http://www.mysmu.edu/faculty/jacklee/singlish_";
alphabets = string.ascii_lowercase

final_content = []

for i in range(0, 26):
	myurl = url + alphabets[i] + ".htm"
	print(myurl);
	chrome = webdriver.Chrome()
	driver = chrome
	driver.get(myurl)

	delay = 3# seconds
	try:
		myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '/html/body')))
		print("Page is ready!")
	except TimeoutException:
		print("Loading took too much time!")


	content = driver.find_elements_by_tag_name("p")
	for definition in content:
		#print(definition.text, "\n\n\n")		
		final_content.append(definition.text);
	time.sleep(5)
	driver.quit()

qq = pd.DataFrame(final_content)

qq.to_csv("singlish.csv")







"""

time.sleep(3)

singlish_content = []

i = 1;
#while i != 0:

content = driver.find_elements_by_class_name("entry-content");

while i != 0:
	try:
		check_more = driver.find_element_by_class_name("nav-previous")
		for j in content:
		#print(j.text, "\n")
			singlish_content.append(j.text);

		time.sleep(5)
		check_more.click();
		
		myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'main')))
	except:
		i = 0;
		print("Reached end of pages")

	


#time.sleep(4)
#driver.quit()

fin_content = []

for i in singlish_content:
	sentences = nltk.sent_tokenize(i);
	#print(sentences)
	for j in range(0, 1):
		words = nltk.word_tokenize(sentences[j]);
		#print(words)
		fin_content.append(list(words))
		#print(words, "\n\n\n")

print("Final words = ", len(fin_content))

"""

