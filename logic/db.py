import sqlite3

sql_config = sqlite3.connect('logic/comments.db')
sql_con = sql_config.cursor()
sql_temp = sql_config.cursor()

sql_con.execute("CREATE TABLE IF NOT EXISTS 'options' (id INTEGER PRIMARY KEY AUTOINCREMENT, option_name TEXT UNIQUE)")

options = []
tableText = ""
for result in sql_con.execute("SELECT `option_name` FROM `options`"):
    options.append(result[0])
    tableText += f", {result[0]} TEXT DEFAULT 0"

print(f'Current options to check for: \n\t{options}')

sql_con.execute(
    f"CREATE TABLE IF NOT EXISTS 'submissions' (id INTEGER PRIMARY KEY AUTOINCREMENT, submission_id TEXT, bot_comment_id TEXT {tableText}, skip INTEGER DEFAULT 0)")

sql_con.execute(
    "CREATE TABLE IF NOT EXISTS 'users' (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, submission_id TEXT)")


def getBotComments():
    return [result[0] for result in
            sql_con.execute(
                f"SELECT `bot_comment_id` FROM `submissions`")]


def addBotComment(comment_id):
    sql_temp.execute(f"INSERT INTO submissions (comment_id) VALUES ('{comment_id}')")


def addUserToComment(user_id, submission_id):
    sql_temp.execute("INSERT INTO users (user_id, submission_id) VALUES (?,?)", (user_id, submission_id))


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


def getUsersWhoVotedOnSubmission(submission_id):
    return [result[0] for result in sql_con.execute(
        f"SELECT user_id FROM `users` WHERE submission_id IS '{submission_id}'")]


def commit():
    sql_config.commit()
