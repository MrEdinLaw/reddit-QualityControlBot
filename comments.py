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
sql_config = sqlite3.connect('comments.db')
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
botComments = []
for result in sql_con.execute(
        "SELECT `comment_id` FROM `comments`"):
    syncedComments.append(result[0])

for result in sql_con.execute(
        "SELECT `submission_id`,`comment_id` FROM `submissions`"):
    syncedPosts.append(result[0])
    botComments.append(result[1])


# Functions
def addSyncedComment(commentId):
    syncedComments.append(commentId)  # Add to synced comments
    sql_temp.execute(  # Add comment to synced comments in database
        "INSERT INTO comments (comment_id) VALUES ('" + str(commentId) + "')")


def addBotComment(commentId):
    botComments.append(commentId)
    sql_temp.execute(  # Add comment to synced comments in database
        "INSERT INTO submissions (comment_id) VALUES ('" + str(commentId) + "')")


def addUserToComment(userId, commentId):
    sql_temp.execute(  # Add user to synced users for this submission
        "INSERT INTO users (user_id, submission_id) VALUES (?,?)",
        (userId,
         commentId))


def skipPost(postId):
    sql_temp.execute(  # Post is removed, change data so it will be skipped from now on
        "UPDATE submissions SET skip = 1 WHERE submission_id = '" + str(skipPost) + "';")


def submissions_and_comments(sub, **kwargs):
    results = []
    results.extend(sub.new(**kwargs))
    results.extend(sub.comments(**kwargs))
    results.sort(key=lambda post: post.created_utc, reverse=True)
    return results


def isPost(check):
    if hasattr(check, "link_author"):
        return False
    else:
        return True


# Subreddit Work
subreddit = reddit.subreddit(config['subreddit'])
dataStream = praw.models.util.stream_generator(lambda **kwargs: submissions_and_comments(subreddit, **kwargs))

for data in dataStream:
    if isPost(data):
        print("New Post")
        submission = data  # I didn't wanna rewrite it
        if submission.id not in syncedPosts:  # Check if submission wasn't synced yet
            print("\tPost is new!")
            print("\t\tCommenting: ")
            replyObj = submission.reply(config['comment_text'])
            print("\t\t\tComment Added.")
            replyObj.mod.distinguish(sticky=True)
            print("\t\t\tComment Stickied.")
            sql_con.execute(
                "INSERT INTO submissions (submission_id, comment_id) VALUES (?,?)",
                (submission.id,
                 replyObj.id))
            syncedPosts.append(submission.id)
            addBotComment(replyObj.id)
            print("\t\t\tAdded to database.\n\n")
    else:
        comment = data
        print("New Comment")
        if comment.id not in syncedComments:
            print("\tComment is new!")
            addSyncedComment(comment.id)
            if comment.parent_id[3:] in botComments:  # Check if the reply is to a bot comment
                print("\t\tProcessing: ")
                sql_con.execute(
                    "SELECT `popular`,`unpopular` FROM submissions WHERE submission_id IS '"
                    + comment.link_id[3:] + "'")
                dbFetch = sql_con.fetchone()
                popular = dbFetch[0]
                unpopular = dbFetch[1]
                oldVotes = popular + unpopular

                if not comment.is_submitter:  # Not OP
                    print("\t\t\tCommenter is NOT Op")
                    sql_con.execute(  # Get users who already voted on this submission
                        "SELECT * FROM users WHERE submission_id IS '" + comment.link_id[3:] + "' AND user_id IS '"
                        + comment.author_fullname[3:] + "'")
                    if sql_con.fetchone() is None:  # User didn't vote
                        voted = False
                        if "unpopular" in comment.body.lower():
                            unpopular += 1
                            voted = True
                            print("\t\t\tVoted: Unpopular")
                        elif "popular" in comment.body.lower():
                            popular += 1
                            voted = True
                            print("\t\t\tVoted: Popular")

                        if voted:
                            addUserToComment(comment.author_fullname[3:], comment.link_id[3:])
                            print("\t\t\tEditing bot comment to show new data: ", end="")
                            botCommentData = reddit.comment(id=comment.parent_id[3:])
                            botCommentData.edit(
                                config[
                                    'comment_text'] + f'\n\nCurrent Votes:\n\nPopular|Unpopular\n:--|:--\n{popular}|{unpopular}')
                            print("Done")
                            sql_temp.execute(  # Update popular/unpopular in the database
                                "UPDATE submissions SET unpopular = " + str(unpopular) + " ,popular = " + str(popular) +
                                " WHERE submission_id = '" + str(comment.link_id[3:]) + "';")
                            print("\t\t\tAdded to database")

                            postData = reddit.submission(id=comment.link_id[3:])  # Request post Data
                            minutes = (datetime.utcnow() - datetime.fromtimestamp(
                                postData.created_utc)).total_seconds() / 60
                            if popular + unpopular >= config['votes'] and minutes > config['minutes']:
                                print("\t\t\tPost fulfils requirements.")
                                popularity = round(popular / (popular + unpopular))
                                postData.mod.flair(f"Voted {popularity} Popular")
                                skipPost(comment.link_id)

                                if popularity >= 70:
                                    print("\t\t\tPost is popular opinion.\n\t\t\tReporting: ", end="")
                                    postData.report(
                                        "BotReport: Opinion has " + str(popular) + " votes against " + str(unpopular) + " votes.")
                                    print("Done")

                    else:  # User voted already
                        print("\t\t\tUser Voted Already")
                else:  # Remove comment and tell OP not to vote to own posts
                    print("\t\t\tCommenter IS OP. Processing: ")
                    comment.mod.remove("You cannot vote on your own submission.")
                    print("\t\t\tComment Removed.")
                    comment.author.message("Comment Removed",
                                           "Please don't vote on your own submissions.\n\n#**This message is from a bot. Your reply will not be read.**")
                    print("\t\t\tOP Notified")
                    addUserToComment(comment.author_fullname[3:], comment.link_id[3:])
            else:
                print("\t\tComment is not a reply to the bot.")

    sql_config.commit()  # commit database changes
    print("Changes committed\n")
