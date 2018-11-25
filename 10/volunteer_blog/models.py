from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from volunteer_blog import db, login_manager ,app
from flask_login import UserMixin






@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(30), nullable=False)
    username = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    telephone = db.Column(db.String(30), nullable=True)
    image_file = db.Column(db.String(30), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    user_created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # ***
    authenticated = db.Column(db.Boolean, default=False)
    email_confirmation_sent_on = db.Column(db.DateTime, nullable=True)
    email_confirmed = db.Column(db.Boolean, nullable=True, default=False)
    email_confirmed_on = db.Column(db.DateTime, nullable=True)
    # ***
    joins = db.relationship('Join', backref='organizer', lazy=True)
    posts = db.relationship('Post', backref='author', lazy=True)

    # ***
    def get_confirm_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'email': self.email}).decode('utf-8')

    @staticmethod
    def verify_confirm_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            email = s.loads(token)['email']
        except:
            return None
        return User.query.filter_by(email=email).first()
    # ***


    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    #just tell python we won't take self as arguments we only take token as arguments
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)


class Post(db.Model):



    id = db.Column(db.Integer, primary_key=True)
    enroll_close_date = db.Column(db.String(30), nullable=True)
    location = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(30),  nullable=False)
    time = db.Column(db.String(30), nullable=False)
    title = db.Column(db.String(30),  nullable=False)
    content = db.Column(db.String(1000),  nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    joins = db.relationship('Join', backref='post', lazy=True)
    def __repr__(self):
        return f"Post('{self.title}','{self.location}','{self.date}')"



class Join(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    volunteering_hrs = db.Column(db.Integer, nullable=True)
    volunteering_pos = db.Column(db.String(30), nullable=True)
    volunteering_comm = db.Column(db.String(100), nullable=True)
    volunteer_contact = db.Column(db.String(30), nullable=False)
    volunteer_username = db.Column(db.String(30), nullable=False)
    volunteer_email = db.Column(db.String(30), nullable=False)
    organizer_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    def __repr__(self):
        return f"Join('{self.user_id}','{self.post_id}')"


