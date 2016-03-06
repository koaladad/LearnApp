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
app.config['SECRET_KEY'] = 'fdasj897342_!??#$JOI#$*~~&&&%%fdsajm'

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)

#-------------------------------Models----------------------------------------#
class BaseModel(Model):
	class Meta:
		database = db


class Subject(BaseModel):
	subjectname = TextField(unique=True)
	timestamp = DateTimeField(default=datetime.datetime.utcnow())
	
	
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
    return render_template('index.html')                          


@app.route('/subject')
def subject():
    session['subject']=None
    session['test']=None
    session['question']=None
    return render_template('subject.html', subjects = view_subjects_default_page())


@app.route('/test')
def test():
    session['subject']=None
    session['test']=None
    session['question']=None
    return render_template('test.html', tests = view_tests_default_page())


@app.route('/question')
def question():
    session['subject']=None
    session['test']=None
    session['question']=None
    return render_template('question.html', questions = view_questions_default_page())


#-------------------------------X by Y----------------------------------------#       
@app.route('/testbysubject/<string:subjectname>')
def testbysubject(subjectname):
    session['subject']=subjectname
    subjects=view_subjects(subjectname)  
    return render_template('test.html', tests=view_tests(subjects))

    
@app.route('/questionbytest/<string:testname>')
def questionbytest(testname):
    session['test']=testname
    tests=view_tests(testname)
    #have testname, just do a select of tests where testname = bleh   

    return render_template('question.html', questions=view_questions(tests, testname))
      
    
    
@app.route('/submitsubject', methods=['GET', 'POST'])
def submitsubject():
    form = SubjectForm()
    if form.validate_on_submit():
        session['subject'] = form.subject.data
        #add subject to database        
        add_subject(form.subject.data)
        
        form.subject.data = ''
        return redirect(url_for('subject'))
        #return session.get('subject')
    return render_template('add_entry.html', form=form)#, subject=session.get('subject'))
    
    
@app.route('/submittest/<string:subjectname>', methods=['GET', 'POST'])
def submittest(subjectname):
    subjects=view_subjects(subjectname)
    tests = view_tests(subjects)
    
    form = TestForm()
    if form.validate_on_submit():
        session['test'] = form.test.data
        #add subject to database        
        add_test(subjects, form.test.data)

        form.test.data = ''
        return redirect(url_for('testbysubject', subjectname=subjectname))
        
    return render_template('add_entry.html', form=form)

    
@app.route('/submitquestion/<string:testname>', methods=['GET', 'POST'])
def submitquestion(testname):
    tests=view_tests(testname)
    questions = view_questions(tests)
    
    form = QuestionForm()
    if form.validate_on_submit():
        session['question'] = form.question.data
        add_question(tests, form.question.data)

        form.question.data = ''
        return redirect(url_for('questionbytest', testname=testname))
        
    return render_template('add_entry.html', form=form)    

#-------------------------------Routing Removals----------------------------------------#
@app.route('/deletesubject/<string:subjectname>', methods=['GET'])
def deletesubject(subjectname):
    #delete all subjects, tests, and questions
    subjects = view_subjects(subjectname)
    tests  = view_tests(subjects)
    questions = view_questions(tests)
    
    #delete all questions if questions is not None
    if questions is not None:
        for question in questions:
            delete_subject(question)
            
    if tests is not None:
        for test in tests:
            delete_test(test)                

    if subjects is not None:
        for subject in subjects:
            delete_subject(subject)  

    return redirect(url_for('subject'))
    
    
@app.route('/deletetest/<string:testname>', methods=['GET'])
def deletetest(testname):
    subjectname = session['subject']  
    subjects = view_subjects(subjectname)
    tests  = view_tests(subjects, testname)
    questions = view_questions(tests)
    
    #delete all questions if questions is not None
    if questions is not None:
        for question in questions:
            delete_subject(question)
            
    if tests is not None:
        for test in tests:
            delete_test(test)                 

    #return redirect(url_for('subject'))
    return redirect(url_for('testbysubject', subjectname=subjectname))
    
   
    
#-------------------------------DB Add Methods----------------------------------------#
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
        Test.create(testname = test, subject = subject) #This is creating issues
        flash("Saved successfully.")
    except IntegrityError:
        flash("Test already exists!")
  

#-------------------------------DB View Methods----------------------------------------#         
def view_subjects(search_query=None):
  """View previous subjects"""
  if search_query is not None:
    subjects = Subject.select().where(Subject.subjectname == search_query).order_by(Subject.subjectname.asc())  
    subjects = subjects.where(Subject.subjectname.contains(search_query))
  else:
    subjects = Subject.select().order_by(Subject.subjectname.asc())
  
  return subjects

  
#need to modify so it uses subjectname instead of subject
#todo, modified Test.subject to Test.subject.subjectname	  
def view_tests(subject, search_query=None):
  """View previous tests""" 
  #tests = Test.select().where(Test.subject == subject).order_by(Test.testname.asc())
  #if search_query:
    #tests = tests.where(Test.testname.contains(search_query))
  if search_query is not None:
    tests = Test.select().where(Test.testname == search_query).order_by(Test.testname.asc())  
    tests = tests.where(Test.testname.contains(search_query))
  else:
    tests = Test.select().order_by(Test.testname.asc())    
  
  return tests
  
  
def view_questions(test, search_query=None):
  """View previous tests"""
  #questions = Question.select().where(Question.test == test).order_by(Question.question.asc())
  #if search_query:
    #questions = questions.where(question.question.contains(search_query))
  if search_query is not None:
    questions = Question.select().where(Question.question == search_query).order_by(Question.question.asc())  
    questions = questions.where(Question.question.contains(search_query))
  else:
    questions = Question.select().order_by(Question.question.asc())    
    
  
  return questions
      
      
def view_subjects_default_page():
    """View all tests, for default test page"""
    subjects = Subject.select()
    return subjects
      

def view_tests_default_page():
    """View all tests, for default test page"""
    tests = Test.select()
    return tests


def view_questions_default_page():
    """View all tests, for default test page"""
    questions = Question.select()
    return questions

    
#-------------------------------DB Remove Methods----------------------------------------#         
def delete_subject(subject): #might need to pass in database object here instead of just a phrase, or convert the phrase into db object
    subject.delete_instance()
	
	
def delete_test(test):
    test.delete_instance()
    

def delete_question(question):
    question.delete_instance()    


#-------------------------------Initialization----------------------------------------#            
if __name__ == '__main__':
    initialize()
    manager.run()