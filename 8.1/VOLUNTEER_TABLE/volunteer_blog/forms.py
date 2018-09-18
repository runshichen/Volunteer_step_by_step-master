from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField,  SubmitField, PasswordField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from volunteer_blog.models import User



class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    telephone = StringField('Telephone')
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    category = SelectField('Category', choices=[('organization', 'Organization'), ('volunteer', 'Volunteer')])
    submit = SubmitField('Sign Up')


    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')



class PostForm(FlaskForm):
    enroll_close_date = StringField('Enroll Close Date', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    date = StringField('Date for event', validators=[DataRequired()])
    time = StringField('Time for event', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Mission', validators=[DataRequired()])
    submit = SubmitField('Post')


class PostJoinForm(FlaskForm):
    user_id = IntegerField('User Id', validators=[DataRequired()])
    volunteer_contact = StringField('Contact', validators=[DataRequired()])
    volunteer_username = StringField('Name', validators=[DataRequired()])
    volunteer_email = StringField('Email', validators=[DataRequired()])
    organizer_id = IntegerField('Organizer Id', validators=[DataRequired()])
    submit = SubmitField('Register')


class UpdateAccountForm(FlaskForm):
    picture = FileField('Update Your Profile Picture',validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')