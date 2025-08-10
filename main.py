from __future__ import annotations
from flask import Flask, render_template, redirect, url_for,request,abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column,relationship
from typing import List
from sqlalchemy import ForeignKey
from sqlalchemy import Integer, String, Text
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, PasswordField
from wtforms.validators import DataRequired, URL, NumberRange
from flask_ckeditor import CKEditor, CKEditorField
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash # helps to create hash
import datetime as dt
from functools import wraps
import bleach
from bleach.css_sanitizer import CSSSanitizer

ALLOWED_TAGS = [
    # Text formatting
    'p', 'br', 'b', 'strong', 'i', 'em', 'u', 's', 'sub', 'sup',

    # Lists
    'ul', 'ol', 'li',

    # Links
    'a',

    # Headings
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',

    # Tables
    'table', 'thead', 'tbody', 'tr', 'th', 'td',

    # Blockquotes
    'blockquote',

    # Horizontal line
    'hr',

    # Images (optional, only if CKEditor allows uploads)
    'img',

    # Code formatting
    'pre', 'code', 'span'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'span': ['style'],  # Needed if CKEditor uses inline styles
    'p': ['style'],
    'td': ['style'],
    'th': ['style'],
}

ALLOWED_STYLES = [

    'text-align',
    'color',
    'background-color',
    'font-weight',
    'font-style',
    'text-decoration',
    'width',
    'height',
    'border',
    'border-collapse',
    'border-spacing',
    'vertical-align',
    'padding',
    'margin'
]

css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_STYLES)

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor= CKEditor(app)
app.config['CKEDITOR_PKG_TYPE'] = 'basic'



# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog_website.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CREATE LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)

# CONFIGURING TABLE for users
class Users(UserMixin,db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(250), nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)

    blogs: Mapped[List["BlogPost"]] = relationship(back_populates="user")

    comments: Mapped[List["Comments"]] = relationship(back_populates="user")
# CONFIGURE TABLE for posts
class BlogPost(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id")) 
    user: Mapped["Users"] = relationship(back_populates="blogs") # used to be author

    comments: Mapped[List["Comments"]] = relationship(back_populates="post")

class Comments(db.Model):
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    text: Mapped[int] = mapped_column(String(5000))
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["Users"] = relationship(back_populates="comments")

    post_id: Mapped[int] = mapped_column(ForeignKey("blog_post.id"))
    post: Mapped["BlogPost"] = relationship(back_populates="comments")

# CREATE ADD-POSTS FORM
class AddPost(FlaskForm):
    title = StringField(label='Blog Post Title',validators=[DataRequired()])
    subtitle = StringField(label='Subtitle',validators=[DataRequired()])

    image = StringField(label='Blog Image URL')
    content = CKEditorField(label='Blog Content')
    submit = SubmitField(label='Submit Post')

# CREATING REGISTRATION FORM
class RegisterForm(FlaskForm):
    name = StringField(label='Name',validators=[DataRequired()])
    age = IntegerField(label='Age',validators=[DataRequired(), NumberRange(min=18)])
    email = StringField(label='Email',validators=[DataRequired()])
    password = PasswordField(label='Password',validators=[DataRequired()])
    submit = SubmitField(label='Register')

class LoginForm(FlaskForm):
    email = StringField(label='Email',validators=[DataRequired()])
    password = PasswordField(label='Password',validators=[DataRequired()])
    submit = SubmitField(label='Login')

# CREATE COMMENTS FORM
class CommentForm(FlaskForm):
    text = CKEditorField(label='Add a Comment:')
    submit = SubmitField(label='Post')

# custom decorator
def protect_route(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        if current_user.id == 1 or current_user.id == 2: 
            return func(*args,**kwargs)
            
        else: 
            return abort(403)
        
    return wrapper

@login_manager.user_loader
def load_user(id):
    user = db.session.execute(db.select(Users).filter_by(id=int(id))).scalar()
    return user

@login_manager.unauthorized_handler
def unauthorized():
    error = "Please login first"
    return redirect(url_for('login',error=error))


with app.app_context():
    db.create_all()

@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        age = form.age.data
        email = form.email.data
        user_emails = db.session.execute(db.select(Users.email).order_by(Users.id)).scalars()
        if email in user_emails: 
            error = 'An account with that email already exists.\nPlease log in.'
        password = form.password.data
        user = Users(
            name=name.capitalize(),
            email=email,
            password=generate_password_hash(password=str(password),method="pbkdf2:sha256",salt_length=10),
            age=age
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("get_all_posts"))
    return render_template('register.html',form=form)

@app.route('/login',methods=['GET','POST'])
def login():
    try: 
        error = request.args.get('error')
    except:
        error = None
    email_exists = False
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        all_users = db.session.execute(db.select(Users).order_by(Users.id)).scalars().all()
        for user in all_users:
            if user.email == email: 
                user_id = user.id
                user_stored_hashed_password = user.password
                user_name = user.name
                email_exists = True
                break

        if not email_exists: 
            error = "There is no account with this email."
        else: 
            for user in all_users:
                if user.email == email:
                    password_hash = user.password
                    break
            if not check_password_hash(password_hash,password):
                error = "Password does not match"
            else: 
                login_user(user)
                print(current_user,type(current_user))

                next = request.args.get('next')
                return redirect(next or url_for('get_all_posts'))


    return render_template('login.html',form=form,error=error)

@app.route('/')
def get_all_posts():
    # TODO: Query the database for all the posts. Convert the data to a python list.
    posts = db.session.execute(db.select(BlogPost).order_by(BlogPost.id)).scalars().all()
    posts = [i for i in posts]

    db.session.commit()

    return render_template("index.html", all_posts=reversed(posts))

# TODO: Add a route so that you can click on individual posts.
@app.route('/post/<post_id>',methods=['GET','POST'])
def show_post(post_id):
    # TODO: Retrieve a BlogPost from the database based on the post_id
    data = db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar()
    requested_post = data
    comments = (db.session.execute(db.select(Comments).filter_by(post_id=post_id)).scalars().all()[::-1]
)

    comment_form = CommentForm()
    print(comment_form.validate_on_submit())
    if comment_form.validate_on_submit():
        text = comment_form.text.data
        clean_text = bleach.clean(
            text,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            css_sanitizer=css_sanitizer,
            strip=True
        )

        user_id = current_user.id

        comment = Comments(
            text = clean_text,
            post_id = post_id,
            user_id = user_id,

        )

        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('show_post',post_id=post_id))



    return render_template("post.html", post=requested_post,comment_form=comment_form,comments=comments)

# TODO: add_new_post() to create a new blog post
@app.route('/new-post',methods=['GET','POST'])
@login_required
@protect_route
def new_post():
    form = AddPost()
    if form.validate_on_submit():
        date_time = dt.datetime.today()
        date_= date_time.strftime("%B %d, %Y")
        if current_user.is_authenticated:
            post = BlogPost(
                title = form.title.data,
                date = date_,
                body = form.content.data,
                img_url = form.image.data,
                subtitle = form.subtitle.data,
                user = current_user

            )
        with app.app_context():
            db.session.add(post)
            db.session.commit()
        return redirect(url_for('get_all_posts'))
    
    return render_template('make-post.html',form=form,id=None)

# TODO: edit_post() to change an existing blog post
@app.route('/edit-post/<post_id>',methods=['GET','POST'])
@login_required
@protect_route
def edit_post(post_id):
    # with app.app_context(): ( NOT NEEDED INSIDE A FLASK ROUTE )
    post = db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar()

    if post.user_id == current_user.id:

        form = AddPost( 
            title = post.title,
            subtitle = post.subtitle,
            user = post.user,
            image = post.img_url,
            content = post.body,
        )


        if form.validate_on_submit():
            with app.app_context():
                post = db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar()
                post.title = form.title.data
                post.body = form.content.data

                post.img_url = form.image.data
                post.subtitle = form.subtitle.data

                db.session.commit()
                
            return redirect(url_for('show_post',post_id=post_id)) # apparently you CAN add routing/path params when using redirect?
        
        return render_template('make-post.html',form=form,id=post_id)

    else: 
        return redirect(url_for('show_post',post_id=post_id))
# TODO: delete_post() to remove a blog post from the database

@app.route('/delete/<post_id>')
@login_required
@protect_route
def delete(post_id):
    with app.app_context():
        post = db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar()
        db.session.delete(post)
        db.session.commit()
    return redirect(url_for('get_all_posts'))
# Below is the code from previous lessons. No changes needed.

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True, port=5003)
