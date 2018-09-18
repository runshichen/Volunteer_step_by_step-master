import os
import secrets
from PIL import Image
from flask import render_template, url_for, redirect, request, flash, abort, make_response
from volunteer_blog import app, db ,bcrypt
from volunteer_blog.forms import RegistrationForm , LoginForm, PostForm ,PostJoinForm, UpdateAccountForm
from volunteer_blog.models import User , Post , Join
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
@app.route("/home", methods=['GET', 'POST'])
def home():
    page = request.args.get('page',1 ,type=int)
    posts = Post.query.order_by(Post.post_created_time.desc()).paginate(page=page, per_page=3)
    return render_template('home.html', posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(category=form.category.data, username=form.username.data, email=form.email.data,
                             password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash('Your Account is created','success')
            return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


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

@app.route('/vlist/<int:post_id>', methods=['GET','POST'])
@login_required
def vlist(post_id):
    post_title = Post.query.filter_by(id=post_id).first().title
    or_joins = Join.query.filter_by(organizer_id=current_user.id).all()
    return render_template('vlist.html', title='vlist', or_joins=or_joins, post_id=post_id, post_title=post_title)

'''@app.route('/export', methods=['GET','POST'])
@login_required
def export_data():
    join = Join.query.filter_by(organizer_id = current_user.id).all()
    column_names = ['id', 'volunteering_hrs','volunteering_pos','volunteering_comm','volunteer_contact',
                    'volunteer_username','volunteer_email','organizer_id', 'user_id', 'post_id']
    return excel.make_response_from_tables( join, column_names, "xls")'''