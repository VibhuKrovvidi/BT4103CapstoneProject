import praw
import pandas as pd

reddit = praw.Reddit(client_id='kQoyoJ9Ag4JxTQ', client_secret='fPR3EGxAsC4ERoPHW4HNfxaMsle5Nw', user_agent='nsscraper')
subreddit_name = 'NationalServiceSG'

# get top 10 hot posts
sub = reddit.subreddit(subreddit_name)
posts = []
hot_posts = sub.hot(limit=10)

for post in hot_posts:
    posts.append([post.title, post.score, post.id, post.subreddit, post.url, post.num_comments, post.selftext, post.created])

posts = pd.DataFrame(posts, columns=['title', 'score', 'id', 'subreddit', 'url', 'num_comments', 'body', 'created'])
print(posts)

# get all comments per post
all_comments = []
for iden in posts['id']:
    submission = reddit.submission(id=iden)
    submission.comments.replace_more(limit=0)
    
    for c in submission.comments.list():
        all_comments.append([c.score, c.id, c.subreddit, c.depth, c.body, c.created, iden])

all_comments = pd.DataFrame(all_comments, columns=['score', 'id', 'subreddit', 'depth', 'body', 'created', 'op_id'])
print(all_comments)

#posts.to_csv('C:/Users/TzeMin/Documents/capstone/output/nationalservicesg_posts.csv')
#all_comments.to_csv('C:/Users/TzeMin/Documents/capstone/output/nationalservicesg_comments.csv')