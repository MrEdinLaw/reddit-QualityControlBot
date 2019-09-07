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


def getRepliesOfCommentId(submission_id, comment_id):
    submission = reddit.submission(id=submission_id)
    submission.comments.replace_more(limit=None)
    comment_queue = submission.comments[:]  # Seed with top-level

    botCommentReplies = False
    scanId = 0
    while botCommentReplies is False:
        if comment_queue[scanId] == comment_id:
            if len(comment_queue[scanId].replies) > 0:
                botCommentReplies = comment_queue[scanId].replies
        scanId += 1

    return botCommentReplies


def refresh():
    subreddit._fetch()
