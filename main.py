import random
import uuid
import hashlib

from flask import Flask, request, make_response, render_template, redirect, url_for
from models import db, User

app = Flask(__name__)
db.create_all()


@app.route("/", methods=["GET"])
def index():
    session_token = request.cookies.get("session_token")
    if session_token:
        usuario = db.query(User).filter_by(session_token=session_token).first()
    else:
        usuario = None
    return render_template("index.html", user=usuario)


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("user-name")
    email = request.form.get("user-email")
    password = request.form.get("user-password")

    user = db.query(User).filter_by(email=email).first()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    if user is None:
        secret_number = random.randint(1, 30)

        user = User(name=name, email=email, secret_number=secret_number, password= hashed_password)

        db.add(user)
        db.commit()
    if hashed_password != user.password:
        return "WRONG PASSWORD! Go back and try again."
    else:
        session_token = str(uuid.uuid4())

        user.session_token = session_token
        db.add(user)
        db.commit()

        response = make_response(redirect(url_for("index")))
        response.set_cookie("session_token", session_token, httponly=True, samesite='Strict')

        return response


@app.route("/result", methods=["POST"])
def result():
    session_token = request.cookies.get("session_token")
    guess = int(request.form.get("guess"))

    user = db.query(User).filter_by(session_token=session_token).first()

    if user.secret_number == guess:
        new_secret = random.randint(1, 30)
        user.secret_number = new_secret

        db.add(user)
        db.commit()

        return render_template("success.html", secret_number=guess)
    else:
        return render_template("failure.html", secret_number=user.secret_number, guess=guess)


@app.route("/profile", methods=["GET"])
def profile():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()

    if user:
        return render_template("profile.html", user=user)
    else:
        return redirect(url_for("index"))


@app.route("/profile/edit", methods=["GET", "POST"])
def profile_edit():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()

    if request.method == "GET":
        if user:
            return render_template("profile_edit.html", user=user)
        else:
            return redirect(url_for("index"))
    elif request.method == "POST":
        if user:
            user_name = request.form.get("user-name")
            user_email = request.form.get("user-email")

            user.name = user_name
            user.email = user_email

            db.add(user)
            db.commit()
            return redirect(url_for("profile"))
        else:
            return redirect(url_for("index"))


@app.route("/profile/delete", methods=["GET", "POST"])
def profile_delete():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()

    if request.method == "GET":
        if user:
            return render_template("profile_delete.html", user=user)
        else:
            return redirect(url_for("index"))
    elif request.method == "POST":
        if user:
            user.deleted = True
            db.delete(user)
            db.commit()
            response = make_response(redirect(url_for("index")))
            response.set_cookie("session_token", user=user)
            return response
        else:
            return redirect(url_for("index"))


@app.route("/users", methods=["GET"])
def list_users():
    users = db.query(User).all()
    return render_template("users.html", users=users)


@app.route("/user/<int:user_id>", methods=["GET"])
def user_details(user_id):
    user = db.query(User).get(user_id)
    return render_template("user_details.html", user=user)


@app.route("/new/password", methods=["GET", "POST"])
def new_password():
    if request.method == "GET":
        session_token = request.cookies.get("session_token")
        user = db.query(User).filter_by(session_token=session_token).first()
        if user:
            return render_template("new_password.html")
        else:
            return redirect(url_for("index"))

    elif request.method == "POST":
        old_password = request.form.get("old-password")
        new_password = request.form.get("new-password")
        session_token = request.cookies.get("session_token")

        hashed_old_password = hashlib.sha256(old_password.encode()).hexdigest()
        user = db.query(User).filter_by(password=hashed_old_password, session_token=session_token).first()

        if user and new_password:
            hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()
            user.password = hashed_new_password
            db.add(user)
            db.commit()
            return redirect(url_for("profile"))
        else:
            return "Error authenticating user."


if __name__ == '__main__':
    app.run()
