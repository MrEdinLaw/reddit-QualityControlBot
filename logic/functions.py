import logic.reddit as reddit
from config import config
from logic import db

# Get already fetched submissions and comments
processedComments = db.getSyncedComments()
trackingSubmissions = db.getSubmissionsWithBotCommentId()
botComments = db.getBotComments()
fetchedSubmissionIds = db.getSubmissions()


def addSyncedComment(comment_id):
    processedComments.append(comment_id)
    db.addSyncedComment(comment_id)


def addBotComment(comment_id):
    botComments.append(comment_id)
    db.addBotComment(comment_id)


def addUserToComment(user_id, comment_id):
    db.addUserToComment(user_id, comment_id)


def skipPost(post_id):
    db.setPostToSkip(post_id)


def addNewSubmission(submission_id, comment_id):
    trackingSubmissions.append([submission_id, comment_id])
    fetchedSubmissionIds.append(submission_id)
    db.addNewSubmission(submission_id, comment_id)


def addNewBotComment(submission):
    newBotComment = submission.reply(config['comment_text'])
    print("\tReply added.")
    newBotComment.mod.distinguish(sticky=True)
    print("\tComment stickied.")
    return newBotComment


def getNewRepliesToComment(submission_id, comment_id):
    result = []
    for reply in reddit.getRepliesOfCommentId(submission_id, comment_id):
        print(reply.body)

    return result
