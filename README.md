# BT4103CapstoneProject

## Service Delivery Analytics | Group 10 | AY20-21, Semester 2

------

### What Is This Project?

This project is a tool to extract, process and present insights from publicly available data sources regarding client sentiment towards service delivery for NS Services. In order to run this tool, you will need:

- A working internet connection
- An introductory understanding of GitHub and Python
- Access accounts for Firebase and DSTA login credentials



### How Do I Start The App?

First, you should **clone** this repository locally. Then, use your terminal to naviagte to the folder housing the code.

Then, go to **BT4103CapstoneProject > flaskapp **

Once there, we will need to install all dependencies. To do this, enter this command:

```
pip install -r requirements.txt
```

Once all requirements have been installed, you can run the web app by entering this command:

```
python main.py
```

After a few seconds, you should see the Flask app running with a link such as :

```
Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

On your browser, go to this link. It hosts the local web application. To start, **enter your DSTA issued credentials**.



### How Do I Use This App?

On initial login, a very expensive (ie time-consuming) process will occur in the backend. You will probably need to wait for a few seconds (roughly 10s) before you can view the dashboard. The dashboard contains three key pieces of insight aimed at answering the question **"What is good? What is bad?"**

- Entities by frequency = How frequently do users refer to an entity in the extracted code?
- WordCloud of Features = What are specific features commonly mentioned
- Average sentiment of each entity = the average sentiment for all entities as collected by our data



Now that you have the *What*, let's move to the *Why*.



On the menu bar click the hamburger icon to view the options. There you should see a new tab for posts breakdown. Click on it. Again, a very expensive operation takes place in the backend so give it a few seconds.



The posts breakdown consists of two separate pieces of insight.

- Entity Tagged Posts = A tool to inspect each entity in greater detail
  - At the top, you will see a dropdown. Choose an entity or all entities for further inspection
  - To the left, you will see a line chart of how the average sentiment for that entity has been changing over time. 
  - To the right, you will see all posts filtered by the selected entity
  - The purpose of this is to connect the average sentiment numbers to the actual feedback, allowing you to better understand what causes positive or negative sentiments
- By clicking `Switch View`, you can access the Sentence-Level Sentiment
  - We understand that looking at sentences in isolation may take away from your ability to draw context from the reviews. For this reason we have included this tab to give you complete reviews broken down by sentence and allocated a sentiment score.
  - A traffic light scheme is provided, giving positive, neutral and negative scores to sentences to better identify aspects of a sentence that need attention.



The dashboard's ability to give meaningful insight is only as good as the data it uses. Thus, we encourage regular scheduling to run the scripts. Alternatively, you can manually run the scripts by clicking the option from the hamburger menu bar.



#### Something is Broken! What should I do?

- Most often, just restarting the server (ie going to you terminal and pressing Ctrl + C and then re-running the steps) will work. 
- If you have been using the dashboard for a long period of time you might find it less responsive. This is because we have used caching to ensure a seamless experience. This caching expires after 10 minutes which may cause the sluggish behaviour you are experiencing.
- If you get `Internal Server Error`, it means the code is broken. You must approach an administrator or a provider to help debug the code. However, as of publishing, the code has been extensively tested with the version of dependencies found in `requirements.txt`. **Please ensure that you have not updated any dependencies!**

