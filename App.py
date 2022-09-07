from flask import Flask, render_template, redirect, url_for,flash,request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_marshmallow import Marshmallow
from marshmallow import Schema,fields,ValidationError,validates,validate
import  logging
from flask_paginate import Pagination


app = Flask(__name__)
app.secret_key = "secret key"
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@localhost/groceries'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db=SQLAlchemy(app)
ma=Marshmallow(app)
login=LoginManager()
login.init_app(app)
login.login_view = 'login'

bootstrap = Bootstrap(app)
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s:%(levelname)s: %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class User(UserMixin,db.Model):
    userid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    username=db.Column(db.String(80),unique=True,nullable=False)
    password=db.Column(db.String(30),nullable=False)
    useremail=db.Column(db.String(50),unique=True,nullable=False)
    groceries = db.relationship("Grocery",backref='user')
    def __init__(self,username,password,useremail):
        self.username=username
        self.password=password
        self.useremail=useremail

    def get_id(self):
        return (self.userid)

class Grocery(db.Model):

    id = db.Column(db.Integer,primary_key=True , autoincrement=True)
    name = db.Column(db.String(80),nullable=False)
    price = db.Column(db.String(80),nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.userid"))


    def __int__(self,name,price,user_id):
        self.name=name
        self.price=price
        self.user_id=user_id






class GrocerySchema(ma.Schema):
    name=fields.String(validate=validate.Regexp(regex="^[A-Za-z]+$"))
    price=fields.Integer()

grocery_schema=GrocerySchema()
groceries_schema = GrocerySchema(many=True)

class UserSchema(ma.Schema):
    username=fields.String(validate=validate.Regexp(regex="^[A-Za-z]+$"))
    password=fields.String()
    useremail=fields.Email()

user_schema=UserSchema()
users_schema=UserSchema(many=True)


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return render_template('index.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:

        username = request.form['username']
        password = request.form['password']

        account = User.query.filter_by(username=username).first()
        if account and account.password == password:
            try:
            # Create session data, we can access this data in other routes
                login_user(account)
                logger.debug('user logged in succesfully')
                msg = 'logged in successfully'
                user_id=current_user.userid
                item = Grocery.query.filter_by(user_id=user_id).paginate(page=1, per_page=3, error_out=True)
                return render_template('home.html',item=item, msg=msg)
            except Exception as e:
                return e

        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
            return render_template('login.html', msg=msg)
            # Show the login form with message (if any)
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        my_account=User(username=username,password=password,useremail=email)
        db.session.add(my_account)
        try:
            result = UserSchema().load({"username": username, "password": password, "useremail": email})
            try:

                db.session.commit()
                flash("registered")
                logging.info(f'user registered succesfully:{username}')

                return render_template('index.html')
            except Exception as e:
                return (e)
        except ValidationError as error:
            return (error.messages)



    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
        logging.warning('please fill out the form')
    # Show registration form with message (if any)
    return render_template('signup.html', msg=msg)




@app.route('/logout')
def logout():
    msg='logout successfully'
    logout_user()
    logging.info('user log out successfully')
    return redirect(url_for('login'))




@app.route('/groceries/<int:page>')
def user1(page):
    user_id = current_user.userid
    item = Grocery.query.filter_by(user_id=user_id).paginate(page=page,per_page=3,error_out=True)
    return render_template("home.html",item=item,user=user_id)
@app.route("/add", methods=["GET", "POST"])
def grocery():
    if request.form:
        _name = request.form['inputName']

        price = request.form['inputPrice']
        try:
            result=GrocerySchema().load({"name":_name,"price":price})
            my_data = Grocery(name=_name, price=price,user_id=current_user.userid)
            db.session.add(my_data)

            db.session.commit()
            logging.info(f'grocery added successfully:{_name}')
            flash('grocery added successfully')
            return redirect(url_for('user1'))
        except ValidationError as error:
            logging.critical(error.messages)
            return (error.messages)











@app.route("/update",methods=["GET","POST"])
def update():
    try:
        oldname=request.form['oldname']


        newname = request.form['newname']

        newprice = request.form['newprice']
        try:
            result=GrocerySchema().load({"name":newname,"price":newprice})
            my_data = Grocery.query.filter_by(name=oldname).first()
            my_data.name = newname
            my_data.price = newprice
            db.session.commit()
            logging.info('grocery added successfully')
            flash('grocery updated successfully')
            return redirect(url_for('user1'))
        except ValidationError as error:
            logging.warning(error.messages)
            return(error.messages)
    except Exception as e:
        logging.critical(e)
        print(e)








@app.route("/delete",methods=["GET","POST"])
def delete():
    try:
        id = request.form.get("id")
        grocery = Grocery.query.filter_by(id=id).first()
        db.session.delete(grocery)
        db.session.commit()
        logging.info(f'grocery deleted successfully : {grocery}')
        return redirect(url_for('user1'))
    except Exception as e:
        logging.critical(e)
        print(e)







if __name__=='__main__':
    app.run(debug=True)