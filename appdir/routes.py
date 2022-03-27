from flask import render_template, flash, redirect, url_for, session, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from appdir import app, db
from appdir.forms import RegisterForm, LoginForm, QuestionForm, AnswerForm
from appdir.models import User, Question, Answer, Viewpoint, Comment, Follow, Invite
from datetime import datetime


@app.route('/', methods=['GET', 'POST'])
def root():
    question_form = QuestionForm()
    if question_form.validate_on_submit():
        return validate_question(question_form)
    return render_template('index.html', question_form=question_form, username=session.get('USERNAME'))


def validate_question(question_form):
    now_time = datetime.now()
    new_question = Question(title=question_form.title.data, description=question_form.description.data,
                            user_id=session.get('USERID'), datetime=now_time)
    db.session.add(new_question)
    db.session.commit()
    flash('You have posted your question successfully!', 'success')
    return redirect(url_for('questions', type='new'))


@app.route('/index', methods=['GET', 'POST'])
def index():
    question_form = QuestionForm()
    session.clear()
    flash('You have logged out!', 'success')
    if question_form.validate_on_submit():
        return validate_question(question_form)
    return render_template('index.html', username=session.get('USERNAME'), question_form=question_form)


@app.route('/question<question_id>', methods=['GET', 'POST'])
def question(question_id):
    current_question = Question.query.filter(Question.id == question_id).first()
    question_form = QuestionForm()
    if question_form.validate_on_submit():
        return validate_question(question_form)
    answer_form = AnswerForm()
    if answer_form.validate_on_submit():
        return validate_answer(answer_form=answer_form, question_id=question_id)

    users_in_db = User.query.all()
    answers_in_db = Answer.query.filter(Answer.question_id == question_id)
    answer_ids = []
    for answer in answers_in_db:
        answer_ids.append(answer.id)
    answers = get_answers(answer_ids=answer_ids)

    return render_template('question.html', username=session.get('USERNAME'), question_form=question_form,
                           question=current_question, answer_form=answer_form, answers=answers,
                           user_id=session.get('USERID'), users=users_in_db)


@app.route('/favorites')
def favorites():
    question_form = QuestionForm()
    if question_form.validate_on_submit():
        return validate_question(question_form)
    viewpoints_in_db = Viewpoint.query.filter(Viewpoint.like == True, Viewpoint.user_id == session.get('USERID'))
    answer_ids = []
    for viewpoint in viewpoints_in_db:
        answer_ids.append(viewpoint.answer_id)
    answers = get_answers(answer_ids)
    return render_template('favorites.html', username=session.get('USERNAME'), question_form=question_form,
                           answers=answers,
                           user_id=session.get('USERID'))


def get_answers(answer_ids):
    answers = []
    answers_in_db = Answer.query.all()
    for answer in answers_in_db:
        user = User.query.filter(User.id == answer.user_id).first()
        time_str = answer.datetime.strftime("%Y-%m-%d %H:%M:%S")
        viewpoints_in_db = Viewpoint.query.filter(Viewpoint.answer_id == answer.id)
        agree = 0
        disagree = 0
        like = False
        for viewpoint in viewpoints_in_db:
            if viewpoint.agree:
                agree += 1
            if viewpoint.disagree:
                disagree += 1
            if viewpoint.user_id == session.get('USERID'):
                like = viewpoint.like
        followed = False
        follow_in_db = Follow.query.filter(Follow.user_id == session.get('USERID'),
                                           Follow.followed_id == user.id).first()
        if follow_in_db:
            followed = True
        comments_in_db = Comment.query.filter(Comment.answer_id == answer.id)
        comments = []
        for comment in comments_in_db:
            comment_user = User.query.filter(User.id == comment.user_id).first()
            new_comment = {
                'username': comment_user.username,
                'content': comment.content
            }
            comments.append(new_comment)
        answer_info = {
            'id': answer.id,
            'username': user.username,
            'content': answer.content,
            'time': time_str,
            'agree': agree,
            'disagree': disagree,
            'like': like,
            'comments': comments,
            'question_id': answer.question_id,
            'followed': followed
        }
        if answer.id in answer_ids:
            answers.append(answer_info)
    return answers


def validate_answer(answer_form, question_id):
    content = answer_form.content.data
    now_time = datetime.now()
    user_id = session.get('USERID')
    answer = Answer(content=content, datetime=now_time, user_id=user_id, question_id=question_id)
    db.session.add(answer)
    db.session.commit()
    flash('You have posted your answer successfully!', 'success')
    return redirect(url_for('question', question_id=question_id))


@app.route('/api/agree', methods=['GET', 'POST'])
def api_agree():
    user_id = request.form['user_id']
    answer_id = request.form['answer_id']
    viewpoint = Viewpoint.query.filter(Viewpoint.user_id == user_id, Viewpoint.answer_id == answer_id).first()
    if not viewpoint:
        new_viewpoint = Viewpoint(agree=True, disagree=False, user_id=user_id, answer_id=answer_id,
                                  like=False)
        db.session.add(new_viewpoint)
    else:
        if viewpoint.agree:
            viewpoint.agree = False
        else:
            viewpoint.agree = True
            viewpoint.disagree = False
    db.session.commit()
    return jsonify({'returnValue': 0})


@app.route('/api/disagree', methods=['GET', 'POST'])
def api_disagree():
    user_id = request.form['user_id']
    answer_id = request.form['answer_id']
    viewpoint = Viewpoint.query.filter(Viewpoint.user_id == user_id, Viewpoint.answer_id == answer_id).first()
    if not viewpoint:
        new_viewpoint = Viewpoint(agree=False, disagree=True, user_id=user_id, answer_id=answer_id,
                                  like=False)
        db.session.add(new_viewpoint)
    else:
        if viewpoint.disagree:
            viewpoint.disagree = False
        else:
            viewpoint.disagree = True
            viewpoint.agree = False
    db.session.commit()
    return jsonify({'returnValue': 0})


@app.route('/api/heart', methods=['GET', 'POST'])
def api_heart():
    user_id = request.form['user_id']
    answer_id = request.form['answer_id']
    viewpoint = Viewpoint.query.filter(Viewpoint.user_id == user_id, Viewpoint.answer_id == answer_id).first()
    if not viewpoint:
        new_viewpoint = Viewpoint(agree=False, disagree=False, user_id=user_id, answer_id=answer_id,
                                  like=True)
        db.session.add(new_viewpoint)
    else:
        if viewpoint.like:
            viewpoint.like = False
        else:
            viewpoint.like = True
    db.session.commit()
    return jsonify({'returnValue': 0})


@app.route('/api/comment', methods=['GET', 'POST'])
def api_comment():
    user_id = request.form['user_id']
    answer_id = request.form['answer_id']
    comment = request.form['comment']
    new_comment = Comment(content=comment, user_id=user_id, answer_id=answer_id)
    db.session.add(new_comment)
    db.session.commit()
    flash('Comment posted successfully!', 'success')
    return jsonify({'returnValue': 0})


@app.route('/api/follow', methods=['GET', 'POST'])
def api_follow():
    user_id = request.form['user_id']
    followed_name = request.form['followed_name']
    user_in_db = User.query.filter(User.username == followed_name).first()
    followed_id = user_in_db.id
    follow_in_db = Follow.query.filter(Follow.user_id == user_id, Follow.followed_id == followed_id).first()
    if not follow_in_db:
        new_follow = Follow(user_id=user_id, followed_id=followed_id)
        db.session.add(new_follow)
    else:
        db.session.delete(follow_in_db)
    db.session.commit()
    return jsonify({'returnValue': 0})


@app.route('/api/invite', methods=['GET', 'POST'])
def api_invite():
    inviter_id = request.form['inviter_id']
    invitee_name = request.form['invitee_name']
    question_id = request.form['question_id']
    print(invitee_name)
    user_in_db = User.query.filter(User.username == invitee_name).first()
    invitee_id = user_in_db.id
    invite_in_db = Invite.query.filter(Invite.inviter_id == inviter_id, Invite.invitee_id == invitee_id,
                                       Invite.question_id == question_id).first()
    if not invite_in_db:
        invite = Invite(inviter_id=inviter_id, invitee_id=invitee_id, question_id=question_id)
        db.session.add(invite)
        db.session.commit()
    flash('You have invited the user to answer the question!', 'success')
    return jsonify({'returnValue': 0})


@app.route('/questions/<type>', methods=['GET', 'POST'])
def questions(type):
    question_form = QuestionForm()
    invites_in_db = Invite.query.filter(Invite.invitee_id == session.get('USERID'))
    invite_question_ids = []
    for invite in invites_in_db:
        invite_question_ids.append(invite.question_id)
    questions_in_db = Question.query.all()
    my_questions = []
    for question in questions_in_db:
        user = User.query.filter(User.id == question.user_id).first()
        answers_in_db = Answer.query.filter(Answer.question_id == question.id)
        new_question = {
            'id': question.id,
            'username': user.username,
            'title': question.title,
            'description': question.description,
            'answers': answers_in_db.count(),
            'time': question.datetime.strftime("%Y-%m-%d %H:%M:%S")
        }
        if type == 'invitation':
            if question.id in invite_question_ids:
                my_questions.append(new_question)
        else:
            my_questions.append(new_question)
    if question_form.validate_on_submit():
        return validate_question(question_form)
    if type == 'hot':
        my_questions = sorted(my_questions, key=lambda keys: keys['answers'])
        my_questions.reverse()
        return render_template('hot.html', username=session.get('USERNAME'), question_form=question_form,
                               questions=my_questions)
    if type == 'new':
        my_questions = sorted(my_questions, key=lambda keys: keys['time'])
        my_questions.reverse()
        return render_template('new.html', username=session.get('USERNAME'), question_form=question_form,
                               questions=my_questions)
    if type == 'invitation':
        my_questions.reverse()
        return render_template('invitation.html', username=session.get('USERNAME'), question_form=question_form,
                               questions=my_questions)


@app.route('/follow')
def follow():
    question_form = QuestionForm()
    if question_form.validate_on_submit():
        return validate_question(question_form)

    answer_ids = []
    follows_in_db = Follow.query.filter(Follow.user_id == session.get('USERID'))
    follow_ids = []
    for follow_item in follows_in_db:
        follow_ids.append(follow_item.followed_id)
    answers_in_db = Answer.query.all()
    for answer in answers_in_db:
        if answer.user_id in follow_ids:
            answer_ids.append(answer.id)

    answers = get_answers(answer_ids=answer_ids)
    return render_template('follow.html', username=session.get('USERNAME'), question_form=question_form,
                           answers=answers,
                           user_id=session.get('USERID'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    question_form = QuestionForm()
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        return validate_register(register_form)
    return render_template('register.html', form=register_form)


def validate_register(form):
    if form.password.data != form.repassword.data:
        flash('Passwords do not match!', 'error')
        return redirect(url_for('register'))
    if User.query.filter(User.username == form.username.data).first():
        flash('The username has been used!', 'error')
        return redirect(url_for('register'))
    if User.query.filter(User.email == form.email.data).first():
        flash('The email has been used by other users!', 'error')
        return redirect(url_for('register'))
    password_hash = generate_password_hash(form.password.data)
    user = User(username=form.username.data, email=form.email.data, password_hash=password_hash)
    db.session.add(user)
    db.session.commit()
    flash('User registered with username: {}'.format(form.username.data), 'success')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    question_form = QuestionForm()
    login_form = LoginForm()
    if login_form.validate_on_submit():
        return validate_login(login_form)
    return render_template('login.html', form=login_form)


def validate_login(form):
    user_in_db = User.query.filter(User.username == form.username.data).first()
    if not user_in_db:
        flash('No user found with username: {}'.format(form.username.data), 'error')
        return redirect(url_for('login'))
    if check_password_hash(user_in_db.password_hash, form.password.data):
        flash('Login successfully!', 'success')
        session["USERNAME"] = user_in_db.username
        session["USERID"] = user_in_db.id
        return redirect(url_for('root'))
    flash('Incorrect Password', 'error')
    return redirect(url_for('login'))
