# Copyright (C) 2019 Edin Demic @MrEdinLaw - All Rights Reserved
# You may use, and modify this code but not distribute

# Importsa
import praw
from time import sleep
from datetime import datetime
import sqlite3

# Keys and Config
from keys import keys
from config import config

# Database Connection and Table Creation
sql_config = sqlite3.connect('votes.db')
sql_con = sql_config.cursor()
sql_temp = sql_config.cursor()
sql_con.execute(
    "CREATE TABLE IF NOT EXISTS 'submissions' (id INTEGER PRIMARY KEY AUTOINCREMENT, submission_id TEXT, bot_comment_id TEXT, skip INTEGER DEFAULT 0)")

# Reddit API Connection
reddit = praw.Reddit(client_id=keys['client_id'],
                     client_secret=keys['client_secret'],
                     user_agent=keys['user_agent'],
                     username=keys['username'],
                     password=keys['password'])

# Get already fetched submissions and comments
syncedPosts = []
botComments = []
for result in sql_con.execute(
        "SELECT `submission_id`,`bot_comment_id` FROM `submissions` WHERE skip IS 0"):
    syncedPosts.append(result[0])
    botComments.append(result[1])


def addBotComment(commentId):
    botComments.append(commentId)
    sql_temp.execute(  # Add comment to synced comments in database
        "INSERT INTO submissions (bot_comment_id) VALUES ('" + str(commentId) + "')")


def skipPost(postId):
    sql_temp.execute(  # Post is removed, change data so it will be skipped from now on
        "UPDATE submissions SET skip = 1 WHERE submission_id = '" + str(skipPost) + "';")


# Subreddit Work
subreddit = reddit.subreddit(config['subreddit'])
for submission in subreddit.stream.submissions(pause_after=0):
    if submission is not None:  # Check if a post is found
        print("New Post")
        if submission.id not in syncedPosts:  # Check if submission wasn't synced yet
            print("\tPost is new!")
            print("\t\tCommenting: ")
            replyObj = submission.reply(config['comment_text'])
            print("\t\t\tComment Added.")
            replyObj.mod.distinguish(sticky=True)
            print("\t\t\tComment Stickied.")
            sql_con.execute(
                "INSERT INTO submissions (submission_id, bot_comment_id) VALUES (?,?)",
                (submission.id,
                 replyObj.id))
            syncedPosts.append(submission.id)
            addBotComment(replyObj.id)
            print("\t\t\tAdded to database.\n\n")
            sql_config.commit()  # commit database changes
            print("\t\t\tChanges committed\n")
    else:  # Check comments
        print("Checking Comments")
        for comment_id in botComments:
            comment = reddit.comment(id=comment_id)
            print(f"\tComment has a score of {comment.score}")
            minutes = (datetime.utcnow() - datetime.fromtimestamp(
                comment.created_utc)).total_seconds() / 60
            if minutes > config['minutes']:
                print(f"\tComment is {minutes} old. Skipping from now on.")
                post = reddit.submission(id=comment.link_id[3:])
                skipPost(post.id)
                sql_config.commit()  # commit database changes
                botComments.remove(comment_id)
                if comment.score < config['score']:
                    print(vars(comment))
                    post.mod.remove("Post was voted not suitable for subreddit.")
                    print("\t\tPost has been removed.")
