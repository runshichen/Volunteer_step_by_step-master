import os
import secrets
from datetime import datetime
from PIL import Image
from flask import render_template, url_for, redirect, request, flash, abort, send_file
from sqlalchemy.exc import IntegrityError
from volunteer_blog import app, db ,bcrypt, mail
from volunteer_blog.forms import RegistrationForm , LoginForm, PostForm ,PostJoinForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm
from volunteer_blog.models import User, Post, Join
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import xlsxwriter


@app.route("/")
@app.route("/home", methods=['GET', 'POST'])
def home():
    page = request.args.get('page',1 ,type=int)
    posts = Post.query.order_by(Post.post_created_time.desc()).paginate(page=page, per_page=5)
    posts_list = Post.query.all()
    organization_list = []
    # Delete Duplicated Element
    for organization in posts_list:
        if not organization.author.username in organization_list:
            organization_list.append(organization.author.username)
    return render_template('home.html', posts=posts, organization_list=organization_list)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
           login_user(user)
           next_page = request.args.get('next')
           return redirect(next_page) if next_page else redirect(url_for('account'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(10)
    f_name , f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125,125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@app.route('/account', methods=['GET','POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit:
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
            flash('Updated Successfully', 'success')
        db.session.commit()
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    #current_user = organizer
    posts = Post.query.filter_by(user_id=current_user.id).all()

    or_joins = Join.query.filter_by(organizer_id=current_user.id).all()

    #current_user = volunteer
    vo_joins = Join.query.filter_by(user_id=current_user.id).all()

    return render_template('account.html',title='Account', image_file=image_file, form=form,vo_joins=vo_joins,
                           or_joins=or_joins,posts=posts)


@app.route('/vlist/<int:post_id>', methods=['GET','POST'])
@login_required
def vlist(post_id):
    post_title = Post.query.filter_by(id=post_id).first().title
    or_joins = Join.query.filter_by(organizer_id=current_user.id).all()
    return render_template('vlist.html', title='vlist', or_joins=or_joins, post_id=post_id, post_title=post_title)


@app.route('/return_file/<int:post_id>', methods=['GET','POST'])
@login_required
def return_file(post_id):
    workbook = xlsxwriter.Workbook('vlist.xlsx',{'in_memory': True})
    worksheet = workbook.add_worksheet()
    worksheet.write('A1', 'Name')
    worksheet.write('B1', 'Email')
    worksheet.write('C1', 'Contact')

    row=1
    col=0
    or_joins = Join.query.filter_by(organizer_id=current_user.id).all()
    for join in or_joins:
        if join.post_id == post_id:
            worksheet.write(row,col, join.volunteer_username)
            worksheet.write(row,col+1, join.volunteer_email)
            worksheet.write(row,col+2, join.volunteer_contact)
            row += 1
    workbook.close()

    return send_file('/Users/lixudong/Desktop/github/Volunteer 3/vlist.xlsx', as_attachment=True)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(enroll_close_date=form.enroll_close_date.data, location=form.location.data, date=form.date.data,
                    time=form.time.data, title=form.title.data, content=form.content.data, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('new_post.html', form=form, title='Enroll Volunteer', legend='Enroll Volunteer')


@app.route('/post/<int:post_id>', methods=['GET','POST'])
@login_required
def post(post_id):
    post = Post.query.get_or_404(post_id)
    form = PostJoinForm()
    join = Join.query.filter(Join.user_id == current_user.id, Join.post_id == post_id).all()
    if Join.query.filter(Join.user_id == current_user.id, Join.post_id == post_id).all():
        flash('You already registered this event ! For your registration details, please go to your account', 'info')
    if form.validate_on_submit and form.volunteer_contact.data:
        join = Join(user_id=current_user.id, post_id=post_id, volunteer_contact=form.volunteer_contact.data,
                    volunteer_username=current_user.username, volunteer_email=current_user.email,
                    organizer_id=post.author.id)
        db.session.add(join)
        db.session.commit()
        flash('Thank you for registration !', 'success')
        return redirect(url_for('home'))
    return render_template('post.html', post=post, form=form,join=join)


@app.route('/post/<int:post_id>/update', methods=['GET','POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.enroll_close_date = form.enroll_close_date.data
        post.date = form.date.data
        post.time = form.time.data
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash(f'Your post has been updated !''success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.enroll_close_date.data = post.enroll_close_date
        form.location.data = post.location
        form.date.data = post.date
        form.time.data = post.time
        form.title.data = post.title
        form.content.data = post.content
    return render_template('update_post.html', title='Update Post', form=form, legend='Update Post')

@app.route('/post/<int:post_id>/delete', methods=['GET','POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    joins = Join.query.filter_by(post_id=post_id).all()
    if post.author != current_user:
        abort(403)
    for join in joins:
        db.session.delete(join)
        db.session.commit()
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted','success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>", methods=['GET', 'POST'])
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user) \
        .order_by(Post.post_created_time.desc()) \
        .paginate(page=page, per_page=3)

    return render_template('user_posts.html', posts=posts, user=user)



def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='github1840@gmail.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


#reset the password with token active
@app.route("/reset_password/<token>", methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user.password = hashed_password
            db.session.commit()
            flash('Your password has been updated! Now you can login ','success')
            return redirect(url_for('login'))
    return render_template('reset_token.html',title='Reset Password',form = form)



def send_confirm_email(user):
    token = user.get_confirm_token()
    msg = Message('Please confirm your email',
                  sender='github1840@gmail.com',
                  recipients=[user.email])
    msg.body = f'''To verify you email, visit the following link:
{url_for('confirm_email', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                user = User(category=form.category.data, username=form.username.data, email=form.email.data,
                                 password=hashed_password)
                db.session.add(user)
                db.session.commit()

                send_confirm_email(user)
                flash('Thanks for registering!  Please check your email to confirm your email address.', 'success')
                return redirect(url_for('recipes'))
            except IntegrityError:
                db.session.rollback()
                flash('ERROR! Email ({}) already exists.'.format(form.email.data), 'error')
    return render_template('register.html', title='Register', form=form)


@app.route('/confirm/<token>')
def confirm_email(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_confirm_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('register'))
    if user.email_confirmed:
        flash('Account already confirmed. Please login.', 'info')

    else:
        user.email_confirmed = True
        user.email_confirmed_on = datetime.now()
        db.session.add(user)
        db.session.commit()
        flash('Thank you for confirming your email ','success')
        return redirect(url_for('login'))
    return redirect(url_for('login'))


@app.route("/recipes", methods=['GET', 'POST'])
def recipes():
    return render_template('recipes.html')