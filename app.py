# Note: app.py skeleton code from CS50 Problem Set 9: Finance was used for this project

# Import os, glob to clear files from directory
import os, glob

# Importing packages
from cs50 import SQL
from flask import Flask, flash, redirect, url_for, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Imports for date and time
#import datetime, numpy
#from dateutil.relativedelta import relativedelta

# Import for regular expressions
import re

# Additional import for file uploads
from werkzeug.utils import secure_filename

# Import for the actual email sending function
import smtplib

# Import base64 library
import base64

# Import required email modules
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Import library to randomize recipe assignments
import random

# Get root for uplaod folder 
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# Declare path and restrictions for recipe file uploads
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/documents')
ALLOWED_EXTENSIONS = {'txt', 'doc', 'docx', 'pdf', 'png', 'jpg', 'jpeg', 'jfif', 'gif', 'mhtml'}

# Declare path for email text file
# EMAIL_FOLDER = '/templates'

# Declare path and restrictions for food photo uploads
PHOTO_UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/photos')
PHOTO_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jfif', 'gif'}

# Configure application
app = Flask(__name__)

# Configure folder for recipe documents
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure folder for email text file
#app.config['EMAIL_FOLDER'] = EMAIL_FOLDER

# Configure folder for food photo uploads
app.config['PHOTO_UPLOAD_FOLDER'] = PHOTO_UPLOAD_FOLDER

# Prevent user from uploading unlimited file size due to security reasons and to avoid exhausting server space
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///recipes.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Function to check if an extension is valid from: https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to check if a photo is in valid format:
def allowed_photo(photo_name):
    return '.' in photo_name and \
        photo_name.rsplit('.', 1)[1].lower() in PHOTO_ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
@login_required
def swap():
    """Swap submitted recipes amongst users"""

    # Select user currently logged in
    username_db = db.execute("SELECT username FROM accounts WHERE id = ?", session["user_id"])

    username = username_db[0]["username"]

    # Select coordinator's first name
    coordinator_db = db.execute("SELECT coordinator FROM accounts WHERE username = ?", username)

    coordinator = coordinator_db[0]["coordinator"]

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Select participants in database for user currently logged in
        participants_db = db.execute("SELECT participant FROM participants WHERE username = ?", username)

        # Select emails in database for user currently logged in
        emails_db = db.execute("SELECT email FROM participants WHERE username = ?", username)

        # Initialize list for participants
        participants = []
        # Append all participants from table to list above
        for row in participants_db:
            participants.append(row["participant"])

        # Initialize list for email addresses
        emails = []
        # Append all participants' emails from table to list above
        for row in emails_db:
            emails.append(row["email"])

        # Clear all files from recipe upload folder
        for file in os.scandir(UPLOAD_FOLDER):
            os.remove(file.path)

        # Referenced Flask 2.2 Documentation: https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/
        # Check if each POST request has the file part
        for i in range(len(participants)):
            if ('file' + str(i)) not in request.files:
                flash('No file part')
                return redirect("/")
            file = request.files['file' + str(i)]
            # If user does not select a file, display error message
            if file.filename == '':
                flash('Must select file for each participant.')
                # Remove all files uploaded to documents folder
                for file in os.listdir(app.config['UPLOAD_FOLDER']):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
                return redirect("/")
            # If user uploads valid file, secure file
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Otherwise, display error message
            elif file and not allowed_file(file.filename):
                flash('Allowed file types are -> txt, doc, docx, pdf, png, jpg, jpeg, jfif, gif, mhtml')
                return redirect("/")

        # Define sender's email address and generated app password
        sender = 'recipeswap50@gmail.com'
        sender_pass = 'epnwaanpjvcwczly'

        # Get list of files that were submitted, in order
        submitted_files = []
        for i in range(len(participants)):
            submitted_files.append(request.files['file' + str(i)].filename)
            # Need to substitute all whitespace with underscores since os.listdir does the same thing
            submitted_files[i] = '_'.join(submitted_files[i].split())
            # Remove parentheses from string since os.listdir does the same thing
            submitted_files[i] = re.sub(r"[\(\)]", '', submitted_files[i])

        # Get list of all files stored in the documents folder, in no particular order
        documents = os.listdir(UPLOAD_FOLDER)

        # Initialize list for recipes to be assigned to participants
        recipes = []

        # Initialize list for recipe links/webpages to be assigned to participants
        links = []

        # Get first day of next month (for HE PSED only, otherwise may disregard)
        nextMonth = datetime.date.today().replace(day=1) + relativedelta(months=1)

        # Store first Friday of the next month (for HE PSED only, otherwise may disregard)
        #firstFriday = 'Friday, ' + str(numpy.busday_offset(nextMonth, 0, roll='forward', weekmask='Fri'))

        # Tailor e-mail message to each participant
        for i in range(len(participants)):
            # Shuffle list for each loop iteration to ensure everyone is assigned a different recipe
            random.shuffle(documents)
            # Assign each participant a random recipe/file that was submitted
            for j in range(len(documents)):
                # If recipe from documents is not the same recipe submitted by participant
                # AND the second to last document and participant are selected
                if documents[j] != submitted_files[i] and j == len(documents) - 2 and i == len(participants) - 2:
                    # Check if next participant also would not receive their own recipe (second condition)
                    if documents[j + 1] != submitted_files[i + 1]:
                        # Finally, assign recipe to currently selected participant
                        filename = documents[j]
                        # Remove file from list of documents once it's been assigned
                        documents.remove(filename)
                        break
                # For all other i and j combinations, just check the current iteration before assigning recipe
                elif documents[j] != submitted_files[i] and (j != len(documents) - 2 or i != len(participants) - 2):
                    filename = documents[j]
                    documents.remove(filename)
                    break
            # Iterate through each submitted file to check if it's the same as the file about to be assigned
            for k in range(len(submitted_files)):
                if filename == submitted_files[k]:
                    # Append recipe name to list which matches the file about to be assigned
                    recipes.append(request.form.get("recipe" + str(k)))
                    # Append link/webpage to list which matches the file about to be assigned
                    links.append(request.form.get("link" + str(k)))
                    break

            # Used sequence for attaching file from "https://www.geeksforgeeks.org/send-mail-attachment-gmail-account-using-python/"

            # Read recipe file to be sent
            file = open(f'{UPLOAD_FOLDER}/{filename}', "rb")

            # Instance of MIMEBase, named as 'attachment'
            attachment = MIMEBase('application', 'octet-stream')

            # Change payload into encoded form
            attachment.set_payload((file).read())

            # Encode into base64
            encoders.encode_base64(attachment)

            attachment.add_header('Content-Disposition', "file; filename = %s" % filename)

            # Define receiver's email address
            # receiver = emails[i]
            receiver = 'recipeswap50@gmail.com'

            # Set up message body for HECO account
            #if username == 'heco' and request.files['file' + str(i)]:
                #msg_body = f"""Hi {participants[i]},

#Your assigned recipe is attached ({recipes[i]}). Please cook it by {firstFriday}.
#Feel free to add your own personal touch!

#Thanks,
#{coordinator}"""

            # Set up message body for generic account
            #else:
            if request.files['file' + str(i)]:
                msg_body = f"""Hi {participants[i]},

Your assigned recipe is attached ({recipes[i]}).
Feel free to add your own personal touch!

Thanks,
{coordinator}"""

            # Sets up the MIME
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = receiver
            msg['Subject'] = 'Recipe Swap'

            # Sets the attachment and body of the email
            msg.attach(attachment)
            msg.attach(MIMEText(msg_body, 'plain'))

            # Send email to each person with a random recipe attached
            # Code for try and except statements inspired by:
            # "https://medium.com/analytics-vidhya/i-made-a-contactless-secret-santa-algorithm-with-python-7374d4a79c56"
            try:
                s = smtplib.SMTP('smtp.gmail.com', 587)
                s.connect('smtp.gmail.com', 587)
                s.ehlo()
                s.starttls()
                s.login(sender, sender_pass)
                s.sendmail(sender, receiver, msg.as_string())
                print("Successfully sent email.")
                s.quit()
            except smtplib.SMTPException:
                print("Error: Unable to send email.")

        # Clear out table with previous recipe assignments
        db.execute("DELETE FROM recipes")

        # Insert information for recipes into table
        for i in range(len(participants)):
            db.execute("INSERT INTO recipes (username, participant, email, recipe, link) VALUES (?, ?, ?, ?, ?)", username, participants[i], emails[i], recipes[i], links[i])

        # Clear all files from food photo upload folder
        for file in os.scandir(PHOTO_UPLOAD_FOLDER):
            os.remove(file.path)

        # Display message when recipes are swapped
        flash("Recipes swapped! Please check your email.")

        # Display recipe assignments to user
        return redirect("/index")

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        # Display message and redirect user to 'Add Participants' page if less than 3 participants have been added
        if len(db.execute("SELECT * FROM participants WHERE username = ?", username)) < 3:
            flash("Must add at least three participants before swapping recipes.")
            return redirect(url_for('add'))

        # Display message and redirect user to Assignments page if recipes have already been swapped
        if db.execute("SELECT * FROM recipes WHERE username = ?", username):
            flash("Must clear assignments before swapping recipes.")
            return redirect(url_for('index'))

        # Select participants in database for user currently logged in
        participants = db.execute("SELECT participant FROM participants WHERE username = ?", username)

        # Store keys and values into multiple tuples/pairs
        info = zip(participants)

        return render_template("swap.html", info=info)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add user and their information to database"""

    # Select user currently logged in
    username_db = db.execute("SELECT username FROM accounts WHERE id = ?", session["user_id"])

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Store name input value
        new_name = request.form.get("name")

        # Verify name only contains alphabetical characters
        if not new_name.isalpha():
            return apology("invalid name", 400)

        # Store email input value
        new_email = request.form.get("email")

        # Email validation regex from: https://www.geeksforgeeks.org/check-if-email-address-valid-or-not-in-python/
        valid_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        # Verify email address is in valid format
        if not re.fullmatch(valid_email, new_email):
            return apology("invalid email address", 400)

        # Select participants in database for user currently logged in
        participants_db = db.execute("SELECT participant FROM participants WHERE username = ?", username_db[0]["username"])

        # Select emails in database for user currently logged in
        emails_db = db.execute("SELECT email FROM participants WHERE username = ?", username_db[0]["username"])

        # Check if name or email already exists in database
        for row in zip(participants_db, emails_db):
            if new_name.upper() == row[0]["participant"].upper():
                return apology("name already exists", 400)
            elif new_email.lower() == row[1]["email"].lower():
                return apology("email already exists", 400)

        # Insert values above into participants table
        db.execute("INSERT INTO participants (username, participant, email) VALUES (?, ?, ?)", username_db[0]["username"], new_name, new_email)

        # Display message when participant is added to database
        flash(new_name + " has been added!")

        return render_template("add.html")

    # User reached route via GET (as by clicking a link or via redirect)
    elif request.method == "GET":
        return render_template("add.html")

@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    """Delete participant and their information from database"""

    # Select user currently logged in
    username_db = db.execute("SELECT username FROM accounts WHERE id = ?", session["user_id"])

    # Select participants in database for user currently logged in
    participants_db = db.execute("SELECT participant FROM participants WHERE username = ?", username_db[0]["username"])

    # Store keys and values into tuples/pairs
    participants = zip(participants_db)

    # If no participants to delete, apologize to user
    if not participants_db:
        return apology("need to add at least one participant", 400)

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Store name input value
        participant = request.form.get("participant")

        # Delete requested participant from table
        db.execute("DELETE FROM participants WHERE participant = ?", participant)

        # Display message when participant is added to database
        flash(participant + " has been deleted!")

        return render_template("delete.html", participants=participants)

    # User reached route via GET (as by clicking a link or via redirect)
    elif request.method == "GET":
        return render_template("delete.html", participants=participants)


@app.route("/index", methods=["GET", "POST"])
@login_required
def index():
    """Show participant's outstanding and previous recipes"""

    # Select user currently logged in
    username_db = db.execute("SELECT username FROM accounts WHERE id = ?", session["user_id"])

    username = username_db[0]["username"]

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Store participant names in a list of dict objects
        participants = db.execute("SELECT participant FROM participants WHERE username = ?", username)

        # Store recipe names in a list of dict objects
        recipes = db.execute("SELECT recipe FROM recipes WHERE username = ?", username)

        # Store links to recipes in a list of dict objects
        links = db.execute("SELECT link FROM recipes WHERE username = ?", username)

        # Initialize counter to check how many files are requested, then uploaded
        files_uploaded = 0

        # Initialize counter to check how many commment fields are updated
        comments_updated = 0

        # Check if each POST request has the file part
        # Referenced Flask 2.2 Documentation: https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/
        for i in range(len(participants)):
            # Initialize list to store participant's photo names in order they were uploaded
            photo_names = []
            # If participant already uploaded photo(s), skip iteration
            if (db.execute("SELECT photos FROM recipes WHERE username = ? AND participant = ?", username, participants[i]["participant"]))[0]["photos"]:
                continue
            # Continue with statements below for each participant who uploaded a photo
            if request.files['photo' + str(i)]:
                # Add photo file requests to a list
                photos = request.files.getlist('photo' + str(i))
                # Loop through each submitted file for each participant
                for j in range(len(photos)):
                    # If user does not select a file, browser submits an empty file without a filename
                    if photos[j].filename == '':
                        flash('Must select file.')
                        return redirect(url_for('index'))
                    # If user uploads valid photo(s), secure and save photo(s)
                    if photos[j] and allowed_photo(photos[j].filename):
                        photo_name = secure_filename(photos[j].filename)
                        photos[j].save(os.path.join(app.config['PHOTO_UPLOAD_FOLDER'], photo_name))
                        # Append name of uploaded photo to list
                        photo_names.append(photo_name)
                        # Increment counter
                        files_uploaded += 1
                    # If user uploads photo(s) with invalid extension(s), display error message
                    else:
                        flash('Allowed image types are -> png, jpg, jpeg, jfif, gif')
                        return redirect(url_for('index'))

                # Join names of all photos uploaded, separated by a pipe (|)
                photo_names = "|".join(photo_names)

                # Update photos column for current participant in loop
                db.execute("UPDATE recipes SET photos = ? WHERE username = ? AND participant = ?", photo_names, username, participants[i]["participant"])

        # Store photos for recipes in a list of dict objects
        photos = db.execute("SELECT photos FROM recipes WHERE username = ?", username)

        # Insert comments for recipes into table, if updated
        for i in range(len(participants)):
            # Get form input for comment(s)
            comments = request.form.get("comments" + str(i))
            # Get current participant
            participant = participants[i]["participant"]
            # Get current value of comments input field for participant
            comments_db = (db.execute("SELECT comments FROM recipes WHERE username = ? AND participant = ?", username, participant))
            # Update comments column in recipes table for user if input removed and comments field was populated before
            if not comments and comments_db[0]["comments"] != None:
                db.execute("UPDATE recipes SET comments = ? WHERE username = ? AND participant = ?", comments, username, participant)
                # Increment counter
                comments_updated += 1
            # Update comments column in recipe table if input provided and was comments field was blank before
            elif comments and comments_db[0]["comments"] == None:
                db.execute("UPDATE recipes SET comments = ? WHERE username = ? AND participant = ?", comments, username, participant)
                # Increment counter
                comments_updated += 1
            # Update comments column in recipe table if input provided and different from before
            elif comments and comments != comments_db[0]["comments"]:
                db.execute("UPDATE recipes SET comments = ? WHERE username = ? AND participant = ?", comments, username, participant)
                # Increment counter
                comments_updated += 1

        # Display message dependent on if image(s) posted and/or comments entered
        if files_uploaded > 0 and comments_updated > 0:
            flash('Image(s) successfully uploaded and displayed. Comment(s) updated.')
        elif files_uploaded > 0 and comments_updated == 0:
            flash('Image(s) successfully uploaded and displayed.')
        elif files_uploaded == 0 and comments_updated > 0:
            flash('Comment(s) updated.')
        else:
            flash('Must upload at least one image.')
            return redirect(url_for('index'))

        # Store comments for recipes in a list of dict objects
        comments = db.execute("SELECT comments FROM recipes WHERE username = ?", username)

        # Store keys and values into multiple tuples/pairs
        info = zip(participants, recipes, links, photos, comments)

        return render_template("index.html", info=info)

    # User reached route via GET (as by clicking a link or via redirect)
    elif request.method == "GET":
        # If recipes table is empty, apologize to user
        if not db.execute("SELECT participant FROM recipes WHERE username = ?", username):
            return apology("must swap recipes first", 400)

        # Store participant names in a list of dict objects
        participants = db.execute("SELECT participant FROM participants WHERE username = ?", username)

        # Store recipe names in a list of dict objects
        recipes = db.execute("SELECT recipe FROM recipes WHERE username = ?", username)

        # Store links to recipes in a list of dict objects
        links = db.execute("SELECT link FROM recipes WHERE username = ?", username)

        # Store photos for recipes in a list of dict objects
        photos = db.execute("SELECT photos FROM recipes WHERE username = ?", username)

        # Store comments for recipes in a list of dict objects
        comments = db.execute("SELECT comments FROM recipes WHERE username = ?", username)

        # Store keys and values into multiple tuples/pairs
        info = zip(participants, recipes, links, photos, comments)

        return render_template("index.html", info=info)


@app.route("/clear", methods=["POST"])
@login_required
def clear():
    """Clear recipe assignments for all partcipants"""

    # Select user currently logged in
    username_db = db.execute("SELECT username FROM accounts WHERE id = ?", session["user_id"])

    username = username_db[0]["username"]

    # Clear recipe assignments
    db.execute("DELETE FROM recipes WHERE username = ?", username)

    # Clear all files from recipe document upload folder
    for file in os.scandir(UPLOAD_FOLDER):
        os.remove(file.path)

    # Clear all files from recipe photo upload folder
    for file in os.scandir(PHOTO_UPLOAD_FOLDER):
        os.remove(file.path)

    # Display message if recipe assignments were cleared
    flash('All recipe assignments cleared!')

    return redirect('/')


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM accounts WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page to swap recipes
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Store username input into variable
        username = request.form.get("username")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 400)

        # Store hashed password input into variables
        password = generate_password_hash(request.form.get("password"))

        # Password validation regex from: "https://www.tutorialspoint.com/password-validation-in-python"
        # P/W must have at least one digit, lowercase char, uppercase char, special char, and be 8-32 chars in length
        valid_pass = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,18}$"

        # Verify password is in valid format. If not, display corrective message
        if not re.fullmatch(valid_pass, request.form.get("password")):
            flash("Password must have at least one digit, one lowercase character, one uppercase character, one special character, and be 8-32 characters in length.")
            return redirect(url_for('register'))

        # Ensure both password inputs match
        if not check_password_hash(password, request.form.get("confirmation")):
            return apology("passwords must match", 400)

        # Store coordinator input into variable
        coordinator = request.form.get("coordinator")

        # Ensure username doesn't already exist
        if len(db.execute("SELECT id FROM accounts WHERE username = ?", username)) != 0:
            return apology("username taken", 400)
        # If not, insert username, hashed password, and coordinator's first name into database
        else:
            db.execute("INSERT INTO accounts (username, hash, coordinator) VALUES(?, ?, ?)", username, password, coordinator)

        # Query database for username
        rows = db.execute("SELECT * FROM accounts WHERE username = ?", username)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Display message when redirected to homepage.html
        flash("Registered!")

        # Redirect user to page to add participants
        return redirect(url_for('add'))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/change", methods=["GET", "POST"])
def change():
    """Change user's password"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure all fields were filled out. If not, apologize
        if not request.form.get("oldPassword") or not request.form.get("newPassword") or not request.form.get("confirmation"):
            return apology("must provide old and new passwords", 400)

        # Ensure inputted old password is correct. If not, apologize
        if not check_password_hash((db.execute("SELECT hash FROM accounts WHERE id = ?", session["user_id"]))[0]["hash"], request.form.get("oldPassword")):
            return apology("must provide valid old password", 400)

        # Password validation regex from: "https://www.tutorialspoint.com/password-validation-in-python"
        # P/W must have at least one digit, lowercase char, uppercase char, special char, and be 8-32 chars in length
        valid_pass = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,18}$"

        # Store hashed password input into variables
        newPassword = generate_password_hash(request.form.get("newPassword"))

        # Verify email address is in valid format. If not, display corrective message
        if not re.fullmatch(valid_pass, request.form.get("newPassword")):
            flash("New password must have at least one digit, one lowercase character, one uppercase character, one special character, and be 8-32 characters in length.")
            return redirect(url_for('change'))

        # Ensure both password inputs match. If not, apologize
        if not check_password_hash(newPassword, request.form.get("confirmation")):
            return apology("new passwords must match", 400)
        # Ensure new password is not the same as old password. If not, apologize
        if request.form.get("oldPassword") == request.form.get("newPassword"):
            return apology("new password must be different", 400)

        # Update user's password
        db.execute("UPDATE accounts SET hash = ? WHERE id = ?", newPassword, session["user_id"])

        # Display message if password successfully changed
        flash("Password changed!")

        return render_template("change.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("change.html")
