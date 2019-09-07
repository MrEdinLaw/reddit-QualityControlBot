import logic.reddit as reddit
from config import config
from logic import db

# Get already fetched submissions and comments
trackedSubmissions = db.getSubmissionsWithBotCommentId()
botComments = db.getBotComments()
submissionsWithBotComment = db.getSubmissions()


def addBotComment(comment_id):
    botComments.append(comment_id)
    db.addBotComment(comment_id)


def addUserToComment(user_id, submission_id):
    db.addUserToComment(user_id, submission_id)


def skipPost(post_id):
    db.setPostToSkip(post_id)


def addNewSubmission(submission_id, comment_id):
    trackedSubmissions.append([submission_id, comment_id])
    submissionsWithBotComment.append(submission_id)
    db.addNewSubmission(submission_id, comment_id)


def addNewBotComment(submission):
    newBotComment = submission.reply(config['comment_text'])
    print("\tReply added.")
    newBotComment.mod.distinguish(sticky=True)
    print("\tComment stickied.")
    return newBotComment


def getNewRepliesToComment(submission_id, comment_id):
    result = []
    votedUserIds = db.getUsersWhoVotedOnSubmission(submission_id)
    repliesOfComment = reddit.getRepliesOfCommentId(submission_id, comment_id)
    if repliesOfComment is not False:
        for reply in repliesOfComment:
            if reply.author_fullname[3:] not in votedUserIds:
                result.append(reply)
                votedUserIds.append(reply.author_fullname[3:])
                addUserToComment(reply.author_fullname[3:], submission_id)

    return result
