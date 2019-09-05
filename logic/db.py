import sqlite3

sql_config = sqlite3.connect('logic/comments.db')
sql_con = sql_config.cursor()
sql_temp = sql_config.cursor()
sql_con.execute(
    "CREATE TABLE IF NOT EXISTS 'submissions' (id INTEGER PRIMARY KEY AUTOINCREMENT, submission_id TEXT, bot_comment_id TEXT, popular_count INTEGER DEFAULT 0, unpopular_count INTEGER DEFAULT 0, skip INTEGER DEFAULT 0)")

sql_con.execute(
    "CREATE TABLE IF NOT EXISTS 'comments' (id INTEGER PRIMARY KEY AUTOINCREMENT, comment_id TEXT)")

sql_con.execute(
    "CREATE TABLE IF NOT EXISTS 'users' (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, submission_id TEXT)")


def getSyncedComments():
    return [result[0] for result in
            sql_con.execute(
                f"SELECT comment_id FROM `comments`")]


def getBotComments():
    return [result[0] for result in
            sql_con.execute(
                f"SELECT `bot_comment_id` FROM `submissions`")]


def addSyncedComment(comment_id):
    sql_temp.execute(f"INSERT INTO comments (comment_id) VALUES ('{comment_id}')")


def addBotComment(comment_id):
    sql_temp.execute(f"INSERT INTO submissions (comment_id) VALUES ('{comment_id}')")


def addUserToComment(user_id, comment_id):
    sql_temp.execute("INSERT INTO users (user_id, submission_id) VALUES (?,?)", (user_id, comment_id))


def setPostToSkip(post_id):
    sql_temp.execute(f"UPDATE submissions SET skip = 1 WHERE submission_id = '{post_id}';")


def addNewSubmission(submission_id, comment_id):
    sql_con.execute(
        "INSERT INTO submissions (submission_id, bot_comment_id) VALUES (?,?)", (submission_id, comment_id))


def getSubmissionsWithBotCommentId():
    return [result for result in sql_con.execute(
        "SELECT submission_id,bot_comment_id FROM `submissions` WHERE skip IS 0")]


def getSubmissions():
    return [result[0] for result in sql_con.execute(
        "SELECT submission_id FROM `submissions` WHERE skip IS 0")]


def commit():
    sql_config.commit()
