import selenium
from selenium import webdriver
import pandas as pd
import openpyxl

PATH = r"C:\Users\Kai\Desktop\BA Mods Materials\AY 2021 Sem 2\BT4103\chromedriver.exe"
webdriver = webdriver.Chrome(PATH)

webdriver.get("https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/pes-d-dilemma-3709993.html")

usernames = []
post_titles = []
posts = []
date = []


names = webdriver.find_elements_by_class_name('bigusername')
for n in names:
    usernames.append(n.text)
#print(len(usernames))
    
titles = webdriver.find_elements_by_class_name('header-gray')
for n in names:
    post_titles.append(titles[0].text)
#print(len(post_titles))

post_message = webdriver.find_elements_by_class_name('post_message')
for m in post_message:
    posts.append(m.text)
#print(len(posts))



review_df = pd.DataFrame()
review_df['usernames'] = usernames
review_df['post_titles'] = post_titles
review_df['posts'] = posts

review_df.to_excel("output.xlsx") 

webdriver.close()

