# Copyright (C) 2020 Edin Demic @MrEdinLaw - All Rights Reserved
# You may use, and modify this code but not distribute

# TODO
# When no new comments for # of scans start skipping post

# Imports
import logic.functions as logic

# New System
while True:
    print("\n\t\tNEW RUN\n")
    # Scan for new posts
    for submission in logic.reddit.getSubmissions():
        if submission.id not in logic.submissionsWithBotComment:
            print("New Post Found")
            newBotComment = logic.addNewBotComment(submission)
            logic.addNewSubmission(submission.id, newBotComment.id)
            print("\tPost processing done.")
            logic.db.commit()

    # Scan for new replies to comments
    for tracked_submission in logic.trackedSubmissions:  # Loop thru all submission that we track
        for new_reply in logic.getNewRepliesToComment(tracked_submission[0], tracked_submission[1]):  # Loop thru new replies of users
            logic.db.addUserToComment(new_reply[0].author_fullname[3:], tracked_submission[0])  # The reply was processed, add it to the database
            logic.db.addVoteToSubmission(tracked_submission[0], new_reply[1])

        # Update the table
        logic.updateBotComment(tracked_submission[0], tracked_submission[1])
    logic.db.commit()

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
                                "BotReport: Opinion has " + str(popular) + " votes against " + str(
                                    unpopular) + " votes.")
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
