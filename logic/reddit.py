import praw

from config import config
from keys import keys

reddit = praw.Reddit(client_id=keys['client_id'],
                     client_secret=keys['client_secret'],
                     user_agent=keys['user_agent'],
                     username=keys['username'],
                     password=keys['password'])

subreddit = reddit.subreddit(config['subreddit'])


def getSubmissions():
    return [result for result in
            reddit.subreddit(config['subreddit']).new(limit=1000)]


def getRepliesOfCommentId(comment_id):
    comment = reddit.comment(id=comment_id)
    #  comment.reply_sort = 'new'
    comment = comment.refresh()
    replies = comment.replies
    return replies
