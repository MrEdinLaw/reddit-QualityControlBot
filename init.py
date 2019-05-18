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
sql_config = sqlite3.connect('data.db')
sql_con = sql_config.cursor()
sql_temp = sql_config.cursor()
sql_con.execute(
    "CREATE TABLE IF NOT EXISTS 'submissions' (id INTEGER PRIMARY KEY AUTOINCREMENT, submission_id TEXT, comment_id TEXT, popular INTEGER DEFAULT 0, unpopular INTEGER DEFAULT 0, skip INTEGER DEFAULT 0)")

sql_con.execute(
    "CREATE TABLE IF NOT EXISTS 'comments' (id INTEGER PRIMARY KEY AUTOINCREMENT, comment_id TEXT)")

sql_con.execute(
    "CREATE TABLE IF NOT EXISTS 'users' (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, submission_id TEXT)")

# Reddit API Connection
reddit = praw.Reddit(client_id=keys['client_id'],
                     client_secret=keys['client_secret'],
                     user_agent=keys['user_agent'],
                     username=keys['username'],
                     password=keys['password'])

# Get already fetched submissions and comments
syncedPosts = []
syncedComments = []
for result in sql_con.execute(
        "SELECT `comment_id` FROM `comments`"):
    syncedComments.append(result[0])

for result in sql_con.execute(
        "SELECT `submission_id` FROM `submissions`"):
    syncedPosts.append(result[0])


# Functions
def addSyncedComment(commentId):
    syncedComments.append(reply.id)  # Add to synced comments
    sql_temp.execute(  # Add comment to synced comments in database
        "INSERT INTO comments (comment_id) VALUES ('" + str(commentId) + "')")


def addUserToComment(userId, commentId):
    sql_temp.execute(  # Add user to synced users for this submission
        "INSERT INTO users (user_id, submission_id) VALUES (?,?)",
        (reply.author.id,
         dataId[0]))

def skipPost(postId):
    sql_temp.execute(  # Post is removed, change data so it will be skipped from now on
        "UPDATE submissions SET skip = 1 WHERE submission_id = '" + str(skipPost) + "';")


# Subreddit Work
subreddit = reddit.subreddit(config['subreddit'])
for submission in subreddit.stream.submissions(pause_after=-1):
    print("Searching for posts...")
    if submission is not None:  # Check if a post is found
        if submission.id not in syncedPosts:  # Check if submission wasn't synced yet
            print("New Post Found")
            print("\tCommenting: ")
            replyObj = submission.reply(config['comment_text'])
            print("\t\tComment Added.")
            replyObj.mod.distinguish(sticky=True)
            print("\t\tComment Stickied.")
            sql_con.execute(
                "INSERT INTO submissions (submission_id, comment_id) VALUES (?,?)",
                (submission.id,
                 replyObj.id))
            sql_config.commit()
            print("\t\tAdded to database.\n\n")
    else:  # No new posts, do the comment thingy
        print("No new posts found, starting comment processing...")
        print("\tGetting submissions and comment ids from database.")
        dataList = sql_con.execute(
            "SELECT `submission_id`,`comment_id`,`popular`,`unpopular` FROM submissions WHERE skip IS 0")
        for dataId in dataList:  # For every dataId (submission Data)
            popular = dataId[2]
            unpopular = dataId[3]
            alreadyVoted = []
            print("\tGetting reddit post data: ", end="")
            postData = reddit.submission(id=dataId[0])  # Request post Data
            print("Done")
            if postData.banned_by is None:  # Check if post is removed (returns None if it isn't)
                print("\tGetting users who already voted: ", end="")
                for userLoad in sql_temp.execute(  # Get users who already voted on this submission
                        "SELECT `user_id` FROM users WHERE submission_id IS '" + dataId[0] + "'"):
                    alreadyVoted.append(userLoad[0])
                print("Done")

                print("\tComment Data.\n\t\tGetting comment data: ", end="")
                commentData = reddit.comment(id=dataId[1])  # Request comment data.
                print("Done\n\t\tRefreshing Comments: ", end="")
                commentData.refresh()  # Refresh comments (For some reason this is required now)
                print("Done")
                try:
                    print("\t\t\tReply Processing: ")
                    oldVotes = popular + unpopular
                    for reply in commentData.replies:  # Loop thru all replies
                        if reply.id not in syncedComments and reply.author.id not in alreadyVoted and reply.author_flair_css_class is not "f":  # Check if reply is not synced yet, author didn't vote yet, and is not banned from voting with a hidden CSS class
                            addSyncedComment(reply.id)  # Add comment to synced comments
                            if reply.author.id != postData.author.id:  # Check if the reply is not written by the author of the submission
                                if "unpopular" in reply.body.lower():
                                    print("\t\t\t\tUnpopular")
                                    unpopular += 1
                                    addUserToComment(reply.author.id, dataId[0])
                                elif "popular" in reply.body.lower():
                                    popular += 1
                                    print("\t\t\t\tPopular")
                                    addUserToComment(reply.author.id, dataId[0])
                            else:
                                print("\t\t\t\tCommenting on own submission.")
                                reply.mod.remove("You cannot vote on your own submission.")
                                reply.author.message("Comment Removed",
                                                     "Please don't vote on your own submissions.\n\n#**This message is from a bot. Your reply will not be read.**")
                    if oldVotes != (popular + unpopular):  # Data changed
                        # Edit the comment to show new data
                        print("\t\t\tChanging comment body: ", end="")
                        commentData.edit(
                            config[
                                'comment_text'] + f'\n\nCurrent Votes:\n\nPopular|Unpopular\n:--|:--\n{popular}|{unpopular}')
                        sql_temp.execute(  # Update popular/unpopular in the database
                            "UPDATE submissions SET unpopular = " + str(unpopular) +" ,popular = " + str(popular) +
                            " WHERE submission_id = '" + str(dataId[0]) + "';")
                        print("Done")
                    else:
                        print("\t\t\t\tNo new replies.")
                except Exception as e:
                    print(e)

                minutes = (datetime.utcnow() - datetime.fromtimestamp(postData.created_utc)).total_seconds() / 60
                if popular + unpopular >= config['votes'] and minutes > config['minutes']:
                    print("\t\t\tPost fulfils requirements for voting")
                    popularity = round(popular / (popular + unpopular))
                    postData.mod.flair(f"Voted {popularity} Popular")
                    skipPost(dataId[0])

                    if popularity >= 70:
                        postData.report(
                            "BotReport: Opinion has " + str(popular) + " votes against " + str(
                                unpopular) + " votes.")
            else:
                print("Post Removed")
                skipPost(dataId[0])

            print("\n\n")
            sql_config.commit()  # commit database changes
