import os
import sqlalchemy

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import time

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure DB
# db = SQL("sqlite:///createpage.db")
db = SQL(os.environ["DATABASE_URL"])

# colour options
colors = [{"color": "Black", "code": "#000000"}, {"color": "White", "code": "#FFFFFF"}, {"color": "Red", "code": "#FF0000"},
          {"color": "Orange", "code": "#FFA500"}, {"color": "Yellow", "code": "#FFFF00"}, {"color": "Green", "code": "#008000"},
          {"color": "Blue", "code": "#0000FF"}, {"color": "Purple", "code": "#800080"}, {"color": "Maroon", "code": "#800000"},
          {"color": "Olive", "code": "#808000"}, {"color": "Lime", "code": "#00FF00"}, {"color": "Teal", "code": "#008080"},
          {"color": "Aqua", "code": "#00FFFF"}, {"color": "Navy", "code": "#000080"}, {"color": "Fuchsia", "code": "#FF00FF"},
          {"color": "Gray", "code": "#808080"}, {"color": "Silver", "code": "#C0C0C0"}]

# font options
fonts = ["Arial", "Times New Roman", "Courier New", "Verdana", "Georgia", "Palatino", "Garamond", "Bookman", "Tahoma", "Trebuchet MS"]

@app.route("/")
@login_required
def index():
    """Show user a list of their webpages"""
    webpages = db.execute("SELECT webpage_id, webpage_name FROM webpages WHERE user_id=:user_id",
                          user_id=session['user_id'])

    return render_template("index.html", webpages=webpages)


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to home page
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
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # gets all registrant usernames
        rows = db.execute("SELECT username FROM users;")

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure same password again was submitted
        elif  request.form.get("password") != request.form.get("password_again"):
            return apology("correctly type password (again)")

        # generate password hash
        hash = generate_password_hash(request.form.get("password"))

        # check for duplicate username
        for row in rows:
            if row['username'] == request.form.get("username"):
                return apology("username taken", 400)

        # adds login info to table (user_id = Primary_Key)
        user_id = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                                     username=request.form.get("username"), hash=hash)

        # adds navbar info to navbars
        db.execute("INSERT INTO navbars (user_id) VALUES (:user_id)", user_id=user_id)

        # log user in
        session["user_id"] = user_id

        # Redirect user to home page
        return redirect("/")

    # register user (via GET method)
    else:
        return render_template("register.html")


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    """ Change account settings """

    # account change form submission
    if request.method == "POST":

        # check password
        current_password = request.form.get("current_password")
        hash = db.execute("SELECT hash FROM users WHERE user_id = :user_id",
                          user_id=session['user_id'])


        if not check_password_hash(hash[0]["hash"], current_password):
            return apology("INVALID PASSWORD", 400)

        # error conditions
        password = request.form.get("password")
        password2 = request.form.get("password2")

        if password == None:
            return apology("Please type in new password", 400)

        elif password != password2:
            return apology("Correctly re-type password", 400)

        password_hash = generate_password_hash(request.form.get("password"))

        # change password
        db.execute("UPDATE users SET hash = :hash WHERE user_id = :user_id",
                   hash=password_hash, user_id=session['user_id'])

        # redirect
        return redirect("/logout")

    else:
        # get username
        username_list = db.execute("SELECT username FROM users WHERE user_id = :user_id",
                              user_id=session['user_id'])
        username = username_list[0]

        # GET account template
        return render_template("account.html", username=username)


@app.route("/display", methods=["POST"])
@login_required
def display():
    # display user_webpage with their stylings
    webpage_id = request.form.get("webpage_id")

    webpage_stylings_list = db.execute("SELECT webpage_name, navbar, background FROM webpages WHERE webpage_id=:webpage_id", webpage_id=webpage_id)
    webpage_stylings = webpage_stylings_list[0]

    title_stylings_list = db.execute("SELECT title, title_font, title_color, title_size, title_alignment FROM titles WHERE webpage_id=:webpage_id",
                                webpage_id=webpage_id)
    title_stylings = title_stylings_list[0]

    text_stylings = db.execute("SELECT text, text_font, text_color, text_size, text_alignment FROM texts WHERE webpage_id=:webpage_id",
                               webpage_id=webpage_id)

    navbar_stylings_list = db.execute("SELECT navbar_width, navbar_color, navlink_font, navlink_color, navlink_size FROM navbars WHERE user_id=:user_id",
                                      user_id=session['user_id'])
    navbar_stylings = navbar_stylings_list[0]

    navlinks = db.execute("SELECT navlink_text, navlink_link FROM navbar_links WHERE user_id=:user_id",
                                      user_id=session['user_id'])

    # Get display.html
    return render_template("display.html", webpage_stylings=webpage_stylings, title_stylings=title_stylings, text_stylings=text_stylings,
                           navbar_stylings=navbar_stylings, navlinks=navlinks)


# change webpage: create, edit, delete
@app.route("/webpage", methods=["GET"])
@login_required
def webpage():
    # Get user's webpage names
    webpage_names = db.execute("SELECT webpage_name FROM webpages WHERE user_id = :user_id", user_id=session['user_id'])

    # Get webpage template
    return render_template("webpage.html", colors=colors, webpage_names=webpage_names)

@app.route("/create_webpage", methods=["POST"])
@login_required
def create_webpage():
    # error conditions
    webpage_name = request.form.get("webpage_name")

    webpages = db.execute("SELECT webpage_name FROM webpages WHERE user_id = :user_id", user_id=session['user_id'])

    for webpage in webpages:
        if webpage['webpage_name'] == webpage_name:
            return apology("Webpage name already used", 400)

    # add webpage to webpages table
    db.execute("INSERT INTO webpages (user_id, navbar, background, webpage_name) VALUES (:user_id, :navbar, :background, :webpage_name)",
               user_id=session['user_id'], navbar=request.form.get("navbar"), background=request.form.get("background"),
               webpage_name=request.form.get("webpage_name"))

    # creates title row in titles table
    webpage_ids = db.execute("SELECT webpage_id FROM webpages WHERE user_id = :user_id AND webpage_name = :webpage_name",
                            user_id=session['user_id'], webpage_name=request.form.get("webpage_name"))
    webpage_id = webpage_ids[0]

    db.execute("INSERT INTO titles (webpage_id) VALUES (:webpage_id)",
              webpage_id=webpage_id['webpage_id'])

    # redirect to index
    return redirect("/")

@app.route("/change_webpage", methods=["POST"])
@login_required
def change_webpage():
    # webpage settings
    webpages = db.execute("SELECT background, navbar FROM webpages WHERE user_id = :user_id AND webpage_name = :webpage_name",
                         user_id=session['user_id'], webpage_name=request.form.get("webpage_name"))
    webpage = webpages[0]

    # do not change elements
    background = request.form.get("background")
    if request.form.get("background") == "do not change":
        background = webpage['background']

    navbar = request.form.get("navbar")
    if request.form.get('navbar') == "do not change":
        navbar = webpage['navbar']

    # updates webpages table
    db.execute("UPDATE webpages SET navbar = :navbar, background = :background WHERE user_id = :user_id AND webpage_name = :webpage_name",
               navbar=navbar, background=background, user_id=session['user_id'], webpage_name=request.form.get("webpage_name"))

    # redirect to index
    return redirect("/")

@app.route("/delete_webpage", methods=["POST"])
@login_required
def delete_webpage():
     # delete title column
    web = db.execute("SELECT webpage_id FROM webpages WHERE user_id=:user_id AND webpage_name = :webpage_name",
                     user_id=session['user_id'], webpage_name=request.form.get("webpage_name"))

    db.execute("DELETE FROM titles WHERE webpage_id=:webpage_id",
               webpage_id=web[0]['webpage_id'])

    # delete all text for webpage
    db.execute("DELETE FROM texts WHERE webpage_id = :webpage_id", webpage_id=web[0]['webpage_id'])

    # delete all navlinks that lead to webpage
    db.execute("DELETE FROM navbar_links WHERE navlink_link = :webpage_id", webpage_id=web[0]['webpage_id'])

    # Delete row from webpages
    db.execute("DELETE FROM webpages WHERE user_id = :user_id AND webpage_name = :webpage_name",
               user_id=session['user_id'], webpage_name=request.form.get("webpage_name"))

    # redirect to index
    return redirect("/")


# change title: create, edit, delete
@app.route("/title", methods=["GET", "POST"])
@login_required
def title():
    # Get user's webpage names
    webpage_names = db.execute("SELECT webpage_name FROM webpages JOIN titles ON titles.webpage_id = webpages.webpage_id WHERE user_id = :user_id AND title IS NULL",
                               user_id=session['user_id'])

    all_webpage_names = db.execute("SELECT webpage_name FROM webpages JOIN titles ON titles.webpage_id = webpages.webpage_id WHERE user_id = :user_id AND title IS NOT NULL",
                                   user_id=session['user_id'])

    return render_template("title.html", colors=colors, fonts=fonts, webpage_names=webpage_names, all_webpage_names=all_webpage_names)

@app.route("/create_title", methods=["POST"])
@login_required
def create_title():
    # get webpage_id
    webpage_ids = db.execute("SELECT webpage_id FROM webpages WHERE user_id = :user_id AND webpage_name = :webpage_name",
               user_id=session['user_id'], webpage_name=request.form.get("webpage_name"))
    id = webpage_ids[0]['webpage_id']

    db.execute("UPDATE titles SET title=:title, title_font=:font, title_color=:color, title_size=:size, title_alignment=:alignment WHERE webpage_id=:webpage_id",
               webpage_id=id, title=request.form.get('title'), font=request.form.get('title_font'), color=request.form.get('title_color'),
               size=request.form.get('title_size'), alignment=request.form.get('title_alignment'))

    # redirect to index
    return redirect("/")

@app.route("/change_title", methods=["POST"])
@login_required
def change_title():
    # select webpage to change title
    webpage_ids = db.execute("SELECT webpage_id FROM webpages WHERE user_id = :user_id AND webpage_name = :webpage_name",
               user_id=session['user_id'], webpage_name=request.form.get("webpage_name"))
    id = webpage_ids[0]['webpage_id']

    # webpage previous title settings
    titles = db.execute("SELECT title, title_font, title_color, title_size, title_alignment FROM titles WHERE webpage_id = :webpage_id",
                        webpage_id=id)
    title = titles[0]

    # checks if user wants to change title attribute
    for key in title:
        if request.form.get(key) != '' and request.form.get(key) != "do not change":
            title[key] = request.form.get(key)

    # updates titles table
    db.execute("UPDATE titles SET title=:title, title_font=:font, title_color=:color, title_size=:size, title_alignment=:alignment WHERE webpage_id=:webpage_id",
               title=title['title'], font=title['title_font'], color=title['title_color'], size=title['title_size'], alignment=title['title_alignment'],
               webpage_id=id)

    # redirect to index
    return redirect("/")

@app.route("/delete_title", methods=["POST"])
@login_required
def delete_title():
    # select webpage to change title
    webpage_ids = db.execute("SELECT webpage_id FROM webpages WHERE user_id = :user_id AND webpage_name = :webpage_name",
               user_id=session['user_id'], webpage_name=request.form.get("webpage_name"))
    id = webpage_ids[0]['webpage_id']

    db.execute("UPDATE titles SET title=NULL, title_font='Arial', title_color='#000000', title_size=40, title_alignment='right' WHERE webpage_id=:webpage_id",
               webpage_id=id)

    # redirect to index
    return redirect("/")


# change text, create, delete
@app.route("/text", methods=["GET"])
@login_required
def text():
    # Get user's webpage names
    webpage_names = db.execute("SELECT webpage_name FROM webpages WHERE user_id = :user_id", user_id=session['user_id'])

    # Get user's text names
    text_names = db.execute("SELECT text_name FROM texts JOIN webpages ON texts.webpage_id = webpages.webpage_id WHERE user_id=:user_id",
                            user_id=session['user_id'])

    # Get text template
    return render_template("text.html", webpage_names=webpage_names, text_names=text_names, colors=colors, fonts=fonts)

@app.route("/create_text", methods=["POST"])
@login_required
def create_text():
    # Previous text names
    text_names = db.execute("SELECT text_name FROM texts JOIN webpages ON texts.webpage_id = webpages.webpage_id WHERE user_id=:user_id",
                            user_id=session['user_id'])
    for text in text_names:
        if request.form.get("text_name") == text['text_name']:
            return apology("Each text must have a different name!", 400)

    # INSERT into texts
    web_id = db.execute("SELECT webpage_id FROM webpages WHERE user_id=:user_id AND webpage_name=:webpage_name",
                        user_id=session['user_id'], webpage_name=request.form.get("webpage_name"))

    db.execute("INSERT INTO texts (webpage_id, text_name, text, text_font, text_color, text_size, text_alignment) VALUES (:webpage_id,:name,:text,:font,:color,:size,:alignment)",
               webpage_id=web_id[0]['webpage_id'], name=request.form.get("text_name"), text=request.form.get("text"),
               font=request.form.get("text_font"), color=request.form.get("text_color"), size=request.form.get("text_size"),
               alignment=request.form.get("text_alignment"))

    # redirect to index
    return redirect("/")

@app.route("/change_text", methods=["POST"])
@login_required
def change_text():
    # SELECT text to change from texts
    text_id = db.execute("SELECT text_id FROM texts JOIN webpages ON texts.webpage_id = webpages.webpage_id WHERE user_id=:user_id AND text_name = :text_name",
                         user_id=session['user_id'], text_name=request.form.get("text_name"))

    # check for do not change or none statements
    text_info_list = db.execute("SELECT text, text_font, text_color, text_size, text_alignment FROM texts WHERE text_id=:text_id",
                                text_id=text_id[0]['text_id'])
    text_info = text_info_list[0]

    for key in text_info:
        if request.form.get(key) != "" and request.form.get(key) != "do not change":
            text_info[key] = request.form.get(key)

    # change text from texts
    db.execute("UPDATE texts SET text = :text, text_font = :font, text_color = :color, text_size = :size, text_alignment = :alignment WHERE text_id = :text_id",
               text_id=text_id[0]['text_id'], text=text_info['text'], font=text_info['text_font'], color=text_info['text_color'],
               size=text_info['text_size'], alignment=text_info['text_alignment'])

    # redirect to index
    return redirect("/")

@app.route("/delete_text", methods=["POST"])
@login_required
def delete_text():
    db.execute("DELETE FROM texts WHERE text_id IN (SELECT text_id FROM texts JOIN webpages ON texts.webpage_id = webpages.webpage_id WHERE user_id = :user_id AND text_name = :text_name)",
               user_id=session['user_id'], text_name=request.form.get("text_name"))

    return redirect("/")


# navbar functions - change navbar, add navlink, delete navlink
@app.route("/navbar", methods=["GET", "POST"])
@login_required
def navbar():
    # Select navbar values
    navbars_info = db.execute("SELECT navbar_width, navbar_color, navlink_font, navlink_color, navlink_size FROM navbars WHERE user_id=:user_id",
                      user_id=session['user_id'])
    info = navbars_info[0]

    # gets color name
    for color in colors:
        if info['navbar_color'] == color['code']:
            navbar_color = color['color']

        if info['navlink_color'] == color['code']:
            navlink_color = color['color']

    # Select webpages from webpages
    webpages = db.execute("SELECT webpage_id, webpage_name FROM webpages WHERE user_id = :user_id",
                          user_id=session['user_id'])

    # Select navlinks from navbar_links
    navlinks = db.execute("SELECT navlink_id, navlink_name FROM navbar_links WHERE user_id = :user_id",
                          user_id=session['user_id'])

    # Get navbar.html
    return render_template("navbar.html", webpages=webpages, navlinks=navlinks, colors=colors, fonts=fonts, info=info, navbar_color=navbar_color, navlink_color=navlink_color)

@app.route("/change_navbar", methods=["POST"])
@login_required
def change_navbar():
    # upadates navbars
    db.execute("UPDATE navbars SET navbar_width=:width, navbar_color=:nav_color, navlink_font=:font, navlink_color=:link_color, navlink_size=:size WHERE user_id=:id",
               id=session['user_id'], width=request.form.get("navbar_width"), nav_color=request.form.get("navbar_color"),
               font=request.form.get("navlink_font"), link_color=request.form.get("navlink_color"), size=request.form.get("navlink_size"))

    # redirect to index
    return redirect("/")

@app.route("/add_navlink", methods=["POST"])
@login_required
def add_navlink():
    # check navlink name
    navlinks = db.execute("SELECT navlink_name FROM navbar_links WHERE user_id = :user_id",
                               user_id=session['user_id'])

    for navlink in navlinks:
        if navlink['navlink_name'] == request.form.get("navlink_name"):
            return apology("Pick unique navlink name!", 400)

    # add navlink to navbar_links
    db.execute("INSERT INTO navbar_links (user_id, navlink_name, navlink_text, navlink_link) VALUES (:user_id, :name, :text, :link)",
               user_id=session['user_id'], name=request.form.get("navlink_name"), text=request.form.get("navlink_text"),
               link=request.form.get("navlink_link"))

    # redirect to index
    return redirect("/")

@app.route("/delete_navlink", methods=["POST"])
@login_required
def delete_navlink():
    # delete navlink from navbar_links
    db.execute("DELETE FROM navbar_links WHERE navlink_id = :navlink_id", navlink_id=request.form.get("navlink_id"))

    # redirect to index
    return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

