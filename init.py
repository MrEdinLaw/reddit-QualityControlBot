# Copyright (C) 2018 Edin Demic @MrEdinLaw - All Rights Reserved
# You may use, and modify this code but not distribute

import praw
from time import sleep
from datetime import datetime
import sqlite3

from keys import keys

sql_config = sqlite3.connect('data.db')
sql_con = sql_config.cursor()
sql_temp = sql_config.cursor()
sql_con.execute(
    "CREATE TABLE IF NOT EXISTS 'submissions' (id INTEGER PRIMARY KEY AUTOINCREMENT, submission_id TEXT, comment_id TEXT, popular INTEGER DEFAULT 0, unpopular INTEGER DEFAULT 0, skip INTEGER DEFAULT 0)")

sql_con.execute(
    "CREATE TABLE IF NOT EXISTS 'comments' (id INTEGER PRIMARY KEY AUTOINCREMENT, comment_id TEXT)")

sql_con.execute(
    "CREATE TABLE IF NOT EXISTS 'users' (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, submission_id TEXT)")

clientId = keys['client_id']
clientSecret = keys['client_secret']
userAgent = keys['user_agent']
username = keys['username']
password = keys['password']

# REST API connection
reddit = praw.Reddit(client_id=clientId,
                     client_secret=clientSecret,
                     user_agent=userAgent,
                     username=username,
                     password=password)

BODY_TEXT = "Is this a **Popular** or **Unpopular** opinion? Please reply to this comment with either *'popular'* or *'unpopular'*\n\n#**Please do not vote on your own submissions.**"
syncedPosts = []
syncedComments = []
SUBREDDIT = "unpopularopinion"

# Get already fetched submissions and comments
for result in sql_con.execute(
        "SELECT `comment_id` FROM `comments`"):
    syncedComments.append(result[0])

for result in sql_con.execute(
        "SELECT `submission_id` FROM `submissions`"):
    syncedPosts.append(result[0])

subreddit = reddit.subreddit(SUBREDDIT)
for submission in subreddit.stream.submissions(pause_after=0):
    if submission is not None:  # Check if a post is found
        if submission.id not in syncedPosts:  # Check if submission wasn't synced yet
            replyObj = submission.reply(BODY_TEXT)
            replyObj.mod.distinguish(sticky=True)
            sql_con.execute(
                "INSERT INTO submissions (submission_id, comment_id) VALUES (?,?)",
                (submission.id,
                 replyObj.id))
            sql_config.commit()
            print("New Post")
    else:  # No new posts, do the comment thingy
        dataList = sql_con.execute(
            "SELECT `submission_id`,`comment_id`,`popular`,`unpopular` FROM submissions WHERE skip IS 0")
        for dataId in dataList:  # For every dataId (submission Data)
            popular = dataId[2]
            unpopular = dataId[3]
            alreadyVoted = []
            postData = reddit.submission(id=dataId[0])
            print(dataId)
            if postData.banned_by is None:  # Check if post is removed (returns None if it isn't)

                for userLoad in sql_temp.execute(  # Get users who already voted on this submission
                        "SELECT `user_id` FROM users WHERE submission_id IS '" + dataId[0] + "'"):
                    alreadyVoted.append(userLoad[0])

                commentData = reddit.comment(id=dataId[1])  # Get comment object from the comment ID
                commentData.refresh()  # Refresh comments (For some reason this is required nowdays)

                for reply in commentData.replies:  # Loop thru all replies
                    try:
                        if reply.id not in syncedComments and reply.author.id not in alreadyVoted and reply.author_flair_css_class is not "f":  # Check if reply is not synced yet, author didn't vote yet, and is not banned from voting with a hidden CSS class
                            syncedComments.append(reply.id)  # Add to synced comments
                            sql_temp.execute(  # Add comment to synced comments in database
                                "INSERT INTO comments (comment_id) VALUES ('" + str(reply.id) + "')")
                            if reply.author.id != postData.author.id:  # Check if the reply is not written by the author of the submission
                                print("Start Reply Processing")

                                voted = False
                                if "unpopular" in reply.body.lower():
                                    print("UnPopular")
                                    unpopular += 1
                                    voted = True
                                elif "popular" in reply.body.lower():
                                    popular += 1
                                    print("Popular")
                                    voted = True

                                if voted:
                                    sql_temp.execute(  # Add user to synced users for this submission
                                        "INSERT INTO users (user_id, submission_id) VALUES (?,?)",
                                        (reply.author.id,
                                         dataId[0]))

                                    commentData.edit(
                                        BODY_TEXT + f'\n\nCurrent Votes:\n\nPopular|Unpopular\n:--|:--\n{popular}|{unpopular}')
                                            # Edit the comment body to show the current popular/unpopular stats
                            else:
                                syncedComments.append(reply.id)  # Add to synced comments
                                sql_temp.execute(  # Add comment to synced comments in database
                                    "INSERT INTO comments (comment_id) VALUES ('" + str(reply.id) + "')")
                                print("Commenting on own submission.")
                                reply.mod.remove("You cannot vote on your own submission.")
                                reply.author.message("Comment Removed", "Please don't vote on your own submissions.\n\n#**This message is from a bot. Your reply will not be read.**")

                    except Exception as e:
                        print(type(e))

                minutes = (datetime.utcnow() - datetime.fromtimestamp(postData.created_utc)).total_seconds() / 60
                if popular + unpopular >= 0 and minutes > 0:
                    if popular >= unpopular:
                        postData.mod.flair("Popular Opinion")
                        postData.report(
                            "BotReport: Opinion has " + str(popular) + " votes against " + str(
                                unpopular) + " votes.")
                    else:
                        postData.mod.flair("Actual unpopular opinion")

                sql_temp.execute(  # Update popular/unpopular in the database
                    "UPDATE submissions SET unpopular = " + str(unpopular) +
                    " ,popular = " + str(popular) +
                    " WHERE submission_id = '" + str(dataId[0]) + "';")
            else:
                print("Post Removed")
                sql_temp.execute(  # Post is removed, change data so it will be skipped from now on
                    "UPDATE submissions SET skip = 1 WHERE submission_id = '" + str(dataId[0]) + "';")

            sql_config.commit()  # commit database changes
