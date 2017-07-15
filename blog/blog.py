import os
import re
import random
import hashlib
import hmac
from string import letters
import time

import webapp2
import jinja2

from google.appengine.ext import db


#import sys
#print sys.path

#sys.path.insert(0, "/Users/btrani/google-cloud-sdk/platform/google")
#sys.path.remove("/Users/btrani/anaconda/lib/python2.7/site-packages")

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = '23wfzas463gzs'

######## System-wide functions

# Render template

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

# Create cookie values

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

# Check cookie values

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

# Create salt for password

def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

# Make password hash from name, pw and salt

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

# Validate password

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

# Get blog key from db

def blog_key(name = 'default'):
    return db.Key.from_path('Blog', name)

# Get user key from db

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

# Specify username, password and email format

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

def login_required(func):
    """
    A decorator to confirm a user is logged in or redirect as needed.
    """
    def login(self, *args, **kwargs):
        # Redirect to login if user not logged in, else execute func.
        if not self.user:
            self.redirect("/login")
        else:
            func(self, *args, **kwargs)
    return login

######## Main blog handler

class Handler(webapp2.RequestHandler):
    
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    # Cookie processing
    
    # Set cookie

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    # Read cookie
    
    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    # Set cookie on login
    
    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    # Reset cookie on logout
    
    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    # Read user info from cookie on page load
    
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))


######## User functions

class User(db.Model):
    
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()
    
    # Retrieve user by userid

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())
    
    # Retrieve user by name

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u
    
    # Register user with hashed pw

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)
        
    # Log into system with pw check

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


##### Blog functions

# Store submitted blog data to table
class Post(db.Model):
    
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    user = db.ReferenceProperty(User, required=True, collection_name="blogs")

    #Make sure there are line breaks between content pieces

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)

##### Main page

class MainPage(Handler):
    
  def get(self):
      blogs = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC")
      if blogs:
          self.render("blog.html", blogs=blogs)

##### Signup page

class Signup(Handler):
    
    def get(self):
        self.render("signup.html")
        
    # Get fields from user input

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username = self.username,
                      email = self.email)

        # Return error message if username not valid
        
        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True
            
        # Return error message if password not valid

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
            
        # Return error message if passwords don't match
        
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        # On error render page but keep input values
        
        if have_error:
            self.render('signup.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError

##### Registration

class Register(Signup):
    
    def done(self):
        # Make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup.html', error_username = msg)
        # Create user and redirect to welcome page
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/welcome')
            
##### Welcome page

class Welcome(Handler):
    
    def get(self):
        if self.user:
            username = self.request.get('username')
            self.render('welcome.html', username = self.user.name)
        else:
            self.redirect('/login')
            
##### Login page

class Login(Handler):
    
    def get(self):
        self.render('login.html')

    def post(self):
        # Retrieve user info
        username = self.request.get('username')
        password = self.request.get('password')
        u = User.login(username, password)
        
        # If login is successful redirect to welcome page
        if u:
            self.login(u)
            self.redirect('/welcome')
        # If login unsuccessful show error and render login page with 
        # stored info
        else:
            msg = 'Invalid login'
            self.render('login.html', error = msg)
            
##### Logout page
            
class Logout(Handler):
    
    def get(self):
        
        if self.user:
            self.logout()
            self.redirect('/')
        
        else:
            error = "You cannot log out if you're not logged in!"
            self.render('login.html', error=error)

##### Likes

class Like(db.Model):
    post = db.ReferenceProperty(Post, required=True)
    user = db.ReferenceProperty(User, required=True)
    
    @classmethod
    def blog_id(cls, blog_id):
        l = Like.all().filter('post =', blog_id)
        return l.count()
    
    @classmethod
    def num_like(cls, blog_id, user_id):
        cl = Like.all().filter('post =', blog_id).filter('user =', user_id)
        return cl.count()
    
##### Un-Likes

class UnLike(db.Model):
    post = db.ReferenceProperty(Post, required=True)
    user = db.ReferenceProperty(User, required=True)
    
    @classmethod
    def blog_id(cls, blog_id):
        ul = UnLike.all().filter('post =', blog_id)
        return ul.count()
    
    @classmethod
    def num_unlike(cls, blog_id, user_id):
        cul = UnLike.all().filter('post =', blog_id).filter('user =', user_id)
        return cul.count()
    
##### Comments

class Comment(db.Model):
    post = db.ReferenceProperty(Post, required=True)
    user = db.ReferenceProperty(User, required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    comment = db.TextProperty(required=True)
    
    @classmethod
    def num_comments(cls, blog_id):
        cm = Comment.all().filter('post =', blog_id)
        return cm.count()
    
    @classmethod
    def blog_id(cls, blog_id):
        cms = Comment.all().filter('post =', blog_id).order('created')
        return cms

##### New posts

class NewPost(Handler):
    
    def get(self):
        # Redirect to new post page if user is logged in
        if self.user:
            self.render("newpost.html")
        # Send to login page if not logged in
        else:
            self.redirect("/login")

    @login_required
    def post(self):
        # Get data from user input
        subject = self.request.get('subject')
        content = self.request.get('content').replace('\n', '<br>')
        u_id = User.by_name(self.user.name)
        
        # If we have all data write to db and redirect to new post page
        if subject and content:
            p = Post(parent = blog_key(), 
                     subject = subject, 
                     content = content,
                     user = u_id)
            p.put()
            self.redirect('/post/%s' % str(p.key().id()))
        # If required data is missing print error
        else:
            error = "Please include a subject and content."
            self.render("newpost.html", 
                        subject=subject, 
                        content=content, 
                        error=error)


##### Post page

class PostPage(Handler):
    
    def get(self, blog_id):
        # Retrieve post key
        key = db.Key.from_path("Post", int(blog_id), parent=blog_key())
        post = db.get(key)

        # If that post does not exist print 404 error
        if not post:
            self.error(404)
            return
        
        # gather all data for blog post
        likes = Like.blog_id(post)
        unlikes = UnLike.blog_id(post)
        comments = Comment.blog_id(post)
        num_comments = Comment.num_comments(post)
        
        # Render page with data
        self.render("post.html",
                    post=post,
                    likes=likes,
                    unlikes=unlikes,
                    comments=comments,
                    num_comments=num_comments)

    def post(self, blog_id):
        #Retrieve data
        key = db.Key.from_path("Post", int(blog_id), parent=blog_key())
        post = db.get(key)
        if post:
            user_id = User.by_name(self.user.name)
            num_comments = Comment.num_comments(post)
            comments = Comment.blog_id(post)
            likes = Like.blog_id(post)
            unlikes = UnLike.blog_id(post)
            total_likes = Like.num_like(post, user_id)
            total_unlikes = UnLike.num_unlike(post, user_id)

        # Ensure user is logged in
        if self.user:
            # Click on like
            if self.request.get("like"):
                # Make sure the author is not the user liking the post
                if post.user.key().id() != self.user.key().id():
                    if total_likes == 0:
                        l = Like(post=post, user=User.by_name(self.user.name))
                        l.put()
                        time.sleep(0.3)
                        self.redirect('/post/%s' % str(post.key().id()))
                    else:
                        error = "Sorry you have already liked this post"
                        self.render("post.html",
                                post=post,
                                likes=likes,
                                unlikes=unlikes,
                                comments=comments,
                                num_comments=num_comments,
                                error=error)
                # Throw error for liking own post
                else:
                    error = "Sorry you cannot like your own post"
                    self.render("post.html",
                                post=post,
                                likes=likes,
                                unlikes=unlikes,
                                comments=comments,
                                num_comments=num_comments,
                                error=error)
            # Click on unlike
            if self.request.get("unlike"):
                # Make sure the author is not the user liking the post
                if post.user.key().id() != self.user.key().id():
                    if total_unlikes == 0:
                        ul = UnLike(post=post, user=User.by_name(self.user.name))
                        ul.put()
                        time.sleep(0.3)
                        self.redirect('/post/%s' % str(post.key().id()))
                    else:
                        error = "Sorry you have already unliked this post"
                        self.render("post.html",
                                post=post,
                                likes=likes,
                                unlikes=unlikes,
                                comments=comments,
                                num_comments=num_comments,
                                error=error)
                # Throw error for unliking own post
                else:
                    error = "Sorry you cannot unlike your own post"
                    self.render("post.html",
                                post=post,
                                likes=likes,
                                unlikes=unlikes,
                                comments=comments,
                                num_comments=num_comments,
                                error=error)
            # Click on add comment
            if self.request.get("add_comment"):
                comment_text = self.request.get("comment_text")
                # Add comment to DB if field is not empty
                if comment_text:
                    c = Comment(post=post, user=User.by_name(self.user.name),
                                comment=comment_text)
                    c.put()
                    time.sleep(0.3)
                    self.redirect('/post/%s' % str(post.key().id()))
                # Throw error for having an empty text box
                else:
                    error = "Please make sure you enter a comment"
                    self.render("post.html",
                                post=post,
                                likes=likes,
                                unlikes=unlikes,
                                comments=comments,
                                num_comments=num_comments,
                                error=error)
            # Click on edit post
            if self.request.get("edit"):
                # Make sure the author is the same user and redirect to edit page
                if post.user.key().id() == User.by_name(self.user.name)\
                                                        .key().id():
                    self.redirect('/edit/%s' % str(post.key().id()))
                # Throw error for if not author
                else:
                    error = "Sorry you can only edit your own posts"
                    self.render("post.html",
                                post=post,
                                likes=likes,
                                unlikes=unlikes,
                                comments=comments,
                                num_comments=num_comments,
                                error=error)
            # Click on delete post
            if self.request.get("delete"):
                # Make sure the author is the same user
                if post.user.key().id() == User.by_name(self.user.name)\
                                                        .key().id():
                    db.delete(key)
                    time.sleep(0.3)
                    self.redirect('/')
                # Throw error for if not author
                else:
                    error = "Sorry you can only delete your own posts"
                    self.render("post.html",
                                post=post,
                                likes=likes,
                                unlikes=unlikes,
                                comments=comments,
                                num_comments=num_comments,
                                error=error)
        else:
            self.redirect("/login")


##### Edit post

class EditPost(Handler):
    
    def get(self, blog_id):
        # Get blog key
        key = db.Key.from_path('Post', int(blog_id), parent=blog_key())
        post = db.get(key)
    
        if self.user:
            if post.user.key().id() == User.by_name(self.user.name).key().id():
                self.render('editpost.html', post=post)
            else:
                self.response.out.write('''Only the creator of the comment can
                                        edit this.''')
        else:
            self.redirect('/login')
            
    @login_required        
    def post(self, blog_id):
         # Get blog key
        key = db.Key.from_path('Post', int(blog_id), parent=blog_key())
        post = db.get(key)
        
        if post:
            if self.request.get('update'):
                subject = self.request.get('subject')
                content = self.request.get('content')
            
                if post.user.key().id() == User.by_name(self.user.name)\
                                            .key().id():
                    if subject and content:
                        post.subject = subject
                        post.content = content
                        post.put()
                        time.sleep(0.3)
                        self.redirect('/post/%s' % str(post.key().id()))
                    else:
                        error = 'Subject and text are required.'
                        self.render('editpost.html',
                                    subject = subject,
                                    content = content,
                                    error = error)
                    
                else:
                    self.response.out.write('''Only the creator of the 
                                            comment can edit this.''')
                
            elif self.request.get('cancel'):
                self.redirect('/post/%s' % str(post.key().id()))  


##### Edit comment    

class EditComment(Handler):
    
    def get(self, post_id, comment_id):
        # Retrieve post and comment
        comment = Comment.get_by_id(int(comment_id))
        if comment:
        # Check that user created that comment
            if comment.user.name == self.user.name:
                # Allow user to edit comment
                self.render('editcomment.html', comment_text=comment.comment)
            else:
                error = "Only the creator of the comment can edit this."
                self.render('editcomment.html', error = error)
            
    def post(self, post_id, comment_id):
        if self.request.get('update_comment'):
            # Retrieve comment
            comment = Comment.get_by_id(int(comment_id))
            # Check that user created that comment
            if comment.user.name == self.user.name:
            # Update comment data in db
                comment.comment = self.request.get('comment_text')
                if comment.comment:
                    comment.put()
                    time.sleep(0.3)
                    self.redirect('/post/%s' % str(post_id))
                else:
                    error = "Comments cannot be blank"
                    self.render('editcomment.html',
                        comment=comment.comment,
                        error=error)
            else:
                error = "Only the creator of the comment can edit this."
                self.render('editcomment.html',
                            comment=comment.comment,
                            error = error)   
        elif self.request.get("cancel"):
            self.redirect('/post/%s' % str(post_id))
            
##### Delete comment

class DeleteComment(Handler):
    
    def get(self, post_id, comment_id):
        # Retrieve comment
        comment = Comment.get_by_id(int(comment_id))
        if comment:
        # Check that user created that comment
            if comment.user.name == self.user.name:
            # Delete comment from db and send to post page
                db.delete(comment)
                time.sleep(0.3)
                self.redirect('/post/%s' % str(post_id))
            else:
                self.write("Only the creator of the comment can delete this.")



app = webapp2.WSGIApplication([
        ('/', MainPage),
        ('/welcome', Welcome),
        ('/newpost', NewPost),
        ('/post/([0-9]+)', PostPage),
        ('/signup', Register),
        ('/login', Login),
        ('/logout', Logout),
        ('/edit/([0-9]+)', EditPost),
        ('/blog/([0-9]+)/editcomment/([0-9]+)', EditComment),
        ('/blog/([0-9]+)/deletecomment/([0-9]+)', DeleteComment)
        ], debug=True)
