#pip install flask-script
#pip install flask-bootstrap
#pip install flask-moment
from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask.ext.script import Manager
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required, Regexp
from collections import OrderedDict
import datetime
import os
import sys

from peewee import *

db = SqliteDatabase('learn.db')


app = Flask(__name__)

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)

#-------------------------------Models----------------------------------------#
class BaseModel(Model):
	class Meta:
		database = db


class Subject(BaseModel):
	subjectname = TextField(unique=True)
	timestamp = DateTimeField(default=datetime.datetime.now)
	
	
class Test(BaseModel):
	subject = ForeignKeyField(Subject, related_name='tests')
	testname = TextField(unique=True)
	
	
class Question(BaseModel):
	test = ForeignKeyField(Test, related_name='questions')
	question = TextField(unique=True)
	correct_answer = TextField()
	incorrect_answer_list = TextField()

#-------------------------------Forms----------------------------------------#
class SubjectForm(Form):
    subject = StringField('Please enter the subject name', validators=[Required()])
    submit = SubmitField('Submit')
    
class TestForm(Form):
    test = StringField('Please enter the test name', validators=[Required()])
    submit = SubmitField('Submit')

class QuestionForm(Form):
    question = StringField('Please enter the question text', validators=[Required()])
    correct_answer = StringField('Please enter the correct answer', validators=[Required()])
    incorrect_answer_list = StringField('Enter the list of incorrect answers, comma-separated', 
                                        validators=[
                                        Required(),
                                        Regexp(message='list needs to be comma separated',
                                        regex=r'[0-9a-zA-Z]+(,[0-9a-zA-Z]+)*')
                                        ])
    submit = SubmitField('Submit')

    

#-------------------------------Initialization----------------------------------------#
def initialize():
  """Create the database and table if they don't exist"""
  db.connect()
  db.create_tables([Subject, Test, Question], safe=True)


 #-------------------------------ErrorHandling----------------------------------------#
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


#-------------------------------Routing----------------------------------------#    
@app.route('/')
def index():
    return render_template('index.html',
                           current_time=datetime.utcnow())                          


@app.route('/subject')
def subject():
    return render_template('subject.html',
                           current_time=datetime.utcnow())

                           
@app.route('/test')
def test():
    return render_template('test.html',
                           current_time=datetime.utcnow())                           


@app.route('/question')
def question():
    return render_template('question.html',
                           current_time=datetime.utcnow())


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)
    
    
@app.route('/submitsubject', methods=['GET', 'POST'])
def submitsubject():
    form = SubjectForm()
    if form.validate_on_submit():
        session['subject'] = form.subject.data
        #add subject to database
        
        
        form.subject.data = ''
        return redirect(url_for('submitsubject'))
    return render_template('subject.html', form=form, subject=session.get('subject'))

    
#-------------------------------DBMethods----------------------------------------#
def add_subject(subject):
    try:
        Subject.create(subjectname=subject)
        flash("Saved successfully.")
    except IntegrityError:
        flash("Subject already Exists!")
				
				
def add_test(subject, test):
    try:
        Test.create(testname = test, subject = subject)
        flash("Saved successfully.")
    except IntegrityError:
        flash("Test already exists!")
            
            
def add_question(test, question):
    try:
        Test.create(testname = test, subject = subject)
        flash("Saved successfully.")
    except IntegrityError:
        flash("Test already exists!")
  
  
def view_subjects(search_query=None):
  """View previous subjects"""
  subjects = Subject.select().order_by(Subject.timestamp.desc())
  
  if search_query:
    subjects = subjects.where(Subject.subjectname.contains(search_query))
  
  return subjects
	  
	  
def view_tests(subject, search_query=None):
  """View previous tests"""
  tests = Test.select().where(Test.subject == subject).order_by(Test.testname.asc())
  
  if search_query:
    tests = tests.where(Test.testname.contains(search_query))
  
  return tests
  
  
def view_questions(test, search_query=None):
  """View previous tests"""
  tests = Test.select().where(Question.test == test).order_by(Question.question.asc())
  
  if search_query:
    questions = questions.where(question.question.contains(search_query))
  
  return questions
      
  
def delete_subject(subject): #might need to pass in database object here instead of just a phrase, or convert the phrase into db object
    subject.delete_instance()
	
	
def delete_test(test):
    test.delete_instance()
    

def delete_question(question):
    question.delete_instance()    


    
if __name__ == '__main__':
    initialize()
    manager.run()