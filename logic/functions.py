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
    result = []  # Results array for later
    votedUserIds = db.getUsersWhoVotedOnSubmission(submission_id)  # Get user_ids that voted already on this submission
    repliesOfComment = reddit.getRepliesOfCommentId(comment_id)  # Get all replies to the bot comment
    if repliesOfComment is not False:  # Check if replies exist
        for reply in repliesOfComment:  # Loop thru all replies
            if reply.author_fullname[3:] not in votedUserIds:  # Check if author has already voted on submission
                option = getTextOption(reply.body)  # Get option in reply body
                if getTextOption(reply.body):  # Check if a option was found
                    result.append([reply, option])  # Add to results array
                    votedUserIds.append(reply.author_fullname[3:])  # Add user to voted users in current loop
    return result


def textHasOption(text):  # Not used anymore currently
    return any(option.lower() in text.lower() for option in db.options)


def getTextOption(text):
    for option in db.options:
        if option.lower() in text.lower():
            return option
    return False


def updateBotComment(submissionId, botCommentId):
    options = db.getDatabaseOptionCount(submissionId)[0]
    voteString = ""
    #  Options
    for option in db.options:
        voteString += f'{option.title()}|'
    voteString = voteString[:-1] + "\n:--|:--\n"
    #  Count/Results
    for option in options:
        voteString += f"{option}|"
    voteString = voteString[:-1]

    reddit.editComment(botCommentId, voteString)
