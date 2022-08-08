from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Regexp
from flask_wtf.file import FileRequired, FileAllowed


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()],
                           render_kw={'class': 'form-control'})
    password = PasswordField('Password', validators=[DataRequired()],
                             render_kw={'class': 'form-control'})
    submit = SubmitField('Login', render_kw={'class': 'btn btn-outline-primary', 'id': 'submit'})


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()],
                           render_kw={'class': 'form-control'})
    email = StringField('Email',
                        validators=[DataRequired(), Regexp('^([a-zA-Z]|[0-9])(\w|\-)+@[a-zA-Z0-9]+\.([a-zA-Z]{2,4})$')],
                        render_kw={'placeholder': 'email@example.com', 'class': 'form-control'})
    password = PasswordField('Password', validators=[DataRequired()],
                             render_kw={'class': 'form-control'})
    repassword = PasswordField('Repeat Password', validators=[DataRequired()],
                               render_kw={'class': 'form-control'})
    submit = SubmitField('Register', render_kw={'class': 'btn btn-outline-primary', 'id': 'submit'})


class QuestionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()],
                        render_kw={'class': 'form-control', 'id': 'question-title'})
    description = TextAreaField('Description', validators=[DataRequired()],
                                render_kw={'class': 'form-control', 'id': 'question-des'})
    submit = SubmitField('Post', render_kw={'class': 'btn btn-outline-primary', 'id': 'submit-question'})


class AnswerForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()],
                            render_kw={'class': 'form-control', 'id': 'answer-content'})
    submit = SubmitField('Post', render_kw={'class': 'btn btn-outline-primary', 'id': 'submit-answer'})
