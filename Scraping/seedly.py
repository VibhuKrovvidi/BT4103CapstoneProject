from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException
from bs4 import BeautifulSoup
import requests


l = []
d = []
p = []
r = []

def for_each_page(driver,l,d,p,r):
    #expand all reviews, get list of reviews, loop through list of review
    #for each indiv review, if it is in the list, skip
    #print('expanding reviews')
    #expand all reviews:
    attempt = 1
    while attempt < 3:
        try:
            i = 0
            while True:
                #locate all 'show more' botton
                show_more = driver.find_elements_by_xpath("//a[@class= 'sc-1rz2iis-2 jazfqp']")
                if len(show_more) > i:
                    try:
                        show_more[i].click()
                    except ElementClickInterceptedException:
                        driver.execute_script("arguments[0].click();", show_more[i])
                        #driver.implicitly_wait(5)
                        #show_more[i].click()
                    i += 1
                    time.sleep(0.5)
                    continue
                break
            break
        except StaleElementReferenceException:
            if attempt == 3:
                raise
            attempt += 1
    #print('done expanding')
    #print('getting all reviews')
    #get list of reviews
    list_of_reviews = driver.find_elements_by_xpath('//div[@class = "sc-1x4gszy-0 ktoiFN"]')
    num_of_reviews = len(list_of_reviews)
    test = ['customer', 'friendly', 'service','agents','person']
    #print('done getting')
    #loop through list of review
    for re in list_of_reviews:
        #print('loop')
        review = re.find_element_by_xpath(".//div[contains(@class, 'sc-1rz2iis-1 enauUK')]").text
        review = review.split('\n')
        keep = []
        for para in review:
            #print('printing split')
            #print(para)
            if any(ele in para.lower() for ele in test):
                print(True)
                keep.append(para)
        keep = " ".join(keep)    
        #filter the review
        #check if review exists
        if review in r:
            #print('oh no')
            #if a review is matching, it means those that comes after are alrd in the database
            break
        else:
            #print('new review')
            level = re.find_element_by_xpath(".//a[contains(@class, 'sc-1dzlw9z-0 mQXuB')]").text
            date = re.find_element_by_xpath(".//div[contains(@class, 'sc-1le1lzz-12 gcZjTF')]").text
            try:
                purchased = re.find_element_by_xpath(".//p[contains(@class, 'sc-1le1lzz-5 kQzcBP')]").text
            except:
                purchased = 'None'
            l.append(level)
            d.append(date)
            p.append(purchased)
            r.append(keep)
            #print('added')

#load the website
brands = ['circles-life', 'myrepublic-mobile','giga', 'gomo', 'redone', 'tpg-mobile', 'grid-mobile', 'm1', 'starhub','vivifi']
#brands = ['vivifi']
driver = webdriver.Chrome()
for b in brands:
    #print(b)
    driver.get('https://seedly.sg/reviews/sim-only-mobile-plans/' + b)
    time.sleep(2)

    #for cust service filter
    #cust_filter = driver.find_element_by_xpath(".//p[@class= 'u2q3h3-14 bAGVyn']")
    #try:
    #    cust_filter.click()
    #except ElementClickInterceptedException:
    #    driver.execute_script("arguments[0].click();", cust_filter)
    #time.sleep(2)

    #get total number of pages
    pages = driver.find_elements_by_xpath("//a[@class='page-link']")
    total_pages = int(pages[-1].text)
    #print('total = ' + str(total_pages))

    #save page 1 first
    for_each_page(driver,l,d,p,r)

    #for each page, get the list of page number, only click if page number = page_now + 1
    #loop through all pages
    page_now = 1
    while page_now < total_pages:
        #print('page now = ' + str(page_now))
        page_list = driver.find_elements_by_xpath("//a[@class='page-link']")
        counter = 0
        for number in page_list:
            #print(number.text)
            if int(number.text) == page_now + 1:
                try: 
                    page_list[counter].click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", page_list[counter])
                    #driver.implicitly_wait(5)
                    #page_list[counter].click()
                page_now += 1
                time.sleep(1)
                for_each_page(driver,l,d,p,r)
                break
            else:
                counter += 1
    continue

driver.close()

data = pd.DataFrame(list(zip(l,d,p,r)), columns = ['level','date','purchased','review'])
#print(data)
data.to_csv('vivifi.csv', index = False)

