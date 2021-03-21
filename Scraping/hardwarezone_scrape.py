from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoSuchElementException

post_title = []
post_username = []
post_message = []
reply_to = []

driver = webdriver.Chrome()
#for each page:
#load the forum
driver.get('https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/saf-ippt-ipt-rt-questions-4220677-380.html')
time.sleep(3)

#title of forum
forum_title = driver.find_element_by_class_name('header-gray').text
print('forum title = ' + forum_title)

next_text = "Next ›"
flag = True
next_button = driver.find_element_by_class_name("prevnext")
buttons = driver.find_elements_by_class_name("prevnext")
for b in buttons:
    if b.text == next_text:
        next_button = b



while flag:
    #get list of all posts
    print('getting posts')
    posts = driver.find_elements_by_class_name('alt1')

    #drop last 2, then drop every alternate
    posts.pop()
    posts.pop()
    del posts[1::2]
    print('done getting posts')

    names = driver.find_elements_by_class_name('bigusername')
    for n in names:
        post_username.append(n.text)

    #message (whole box) = post_message, message being replied to = quote
    #for every post, check if there is quote.
    for p in posts:
        #get the full message, including prev if present
        full = p.find_element_by_class_name('post_message').text
        #check if there is reply
        try:
            reply = p.find_element_by_class_name('quote').text
            reply = reply.split('\n')
            full = full.split('\n')[1:]
            #wtv that is in the full message, but not in the quote is the reply for that user
            new = [i for i in full if i not in reply]
            new = " ".join(new) #join to one string
            reply = " ".join(reply)
            post_message.append(new) #adding the actual message to a list
            reply_to.append(reply) #adding the reply to a list if there is
            post_title.append(forum_title) #adding title
        except NoSuchElementException:
            full = full.split('\n')
            full = " ".join(full)
            post_message.append(full)
            reply_to.append('NIL') #no replies
            post_title.append(forum_title)

    if next_button.text == next_text:
        print('clicking next')
        next_button.click()
    else:
        flag = False

    buttons_list = []
    buttons = driver.find_elements_by_class_name("prevnext")
    for b in buttons:
        buttons_list.append(b.text)

    for b in buttons:
        if b.text == next_text:
            next_button = b
            
    if next_text not in buttons_list:
        next_button = driver.find_element_by_class_name("prevnext")
    
data = pd.DataFrame(list(zip(post_title,post_username,post_message,reply_to)), columns = ['post_title','post_username', 'post', 'reply to'])
data.to_csv("hwz_Post_title_output.csv")
driver.close()









