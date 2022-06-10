from flask import Flask,render_template,request,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_user,login_required,logout_user,current_user
from datetime import datetime
import random

app = Flask(__name__)
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecretkey'
login_manager = LoginManager()
login_manager.init_app(app)
    
class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    name = db.Column(db.String,unique=True,nullable=False)
    password = db.Column(db.String,unique=True,nullable=False)
    date_created = db.Column(db.String, default=datetime.utcnow())
    deck = db.relationship('Deck',backref='user',lazy=True)
    
class Deck(db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    Deck_name = db.Column(db.String,unique=True,nullable=False)
    score = db.Column(db.Integer, default = 0)
    review_time = db.Column(db.String,default=datetime.utcnow())
    card = db.relationship('Card',backref='deck',lazy=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    
class Card(db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    front = db.Column(db.String,unique=True,nullable=False)
    back = db.Column(db.String,unique=True,nullable=False)
    score = db.Column(db.Integer, default=0)
    review_time = db.Column(db.String,default=datetime.utcnow())
    deck_id = db.Column(db.Integer,db.ForeignKey('deck.id'),nullable=False)
    
db.create_all()

@login_manager.user_loader
def user(user_id):
    return User.query.get(int(user_id))

@app.route('/') 
def index():
   return render_template('index.html')

@app.route('/login',methods=['GET','POST'])
def login():

        if request.method=='POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(name=username).first()
            if user and password == user.password :
                login_user(user)
                return redirect('/dashboard')
            else:
                flash('Invalid Credentials ! Please Try Again')
                return redirect(url_for('login'))
              
        return render_template('login.html')
      
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')




@app.route('/sign_up',methods=['GET','POST'])
def sign_up():
    if request.method=='POST':
        name = request.form['username']
        password = request.form['password']
        user = User(name=name,password=password)
        db.session.add(user)
        db.session.commit()
        return redirect('/')
    return render_template('sign_up.html')

@app.route('/dashboard',methods=['GET','POST'])
@login_required
def dashboard():

        decks = Deck.query.filter_by(user_id = current_user.id).all()
        return render_template('dashboard.html',decks=decks)
 
    


@app.route('/add_deck',methods=['GET','POST'])
@login_required
def add_deck():
    if request.method=='POST':
        deck_name = request.form['deck_name']
        now = datetime.now()
        review_time = now.strftime('%Y-%m-%d %H:%M:%S')
        deck = Deck(Deck_name=deck_name,user_id=current_user.id,review_time=str(review_time))
        db.session.add(deck)
        db.session.commit()
        return redirect('/dashboard')
      
    return render_template('add_deck.html')
    

@app.route('/deck/<int:deck_id>/update',methods=['GET','POST'])
def update_deck(deck_id):
    deck = Deck.query.filter_by(id=deck_id).first()
    if request.method=='POST':
        name = request.form['deck_name']
        Deck.query.filter_by(id=deck_id).update({ Deck.Deck_name : name})
        db.session.commit()
        return redirect('/dashboard')
    return render_template('update_deck.html',deck=deck)

@app.route('/deck/<int:deck_id>/delete')
def delete_deck(deck_id):
     deck = Deck.query.filter_by(id=deck_id).first()
     cards = Card.query.filter_by(deck_id=deck.id).all()
     for card in cards :
         db.session.delete(card)
     db.session.delete(deck)
     db.session.commit()
     return redirect('/dashboard')

@app.route('/deck/<int:deck_id>/add_card',methods=['GET','POST'])
@login_required
def add_card(deck_id):
    deck = Deck.query.filter_by(id=deck_id).first()
    if request.method=='POST':
        front = request.form['front']
        back = request.form['back']
        now = datetime.now()
        review_time = now.strftime('%Y-%m-%d %H:%M:%S')
        card = Card(front=front,back=back,deck_id=deck_id,review_time=str(review_time))
        db.session.add(card)
        db.session.commit()
        return redirect('/deck/'+str(deck_id)+'/show_card')
    return render_template('add_card.html',deck=deck)
    

@app.route('/deck/<int:deck_id>/show_card')
def show_cards(deck_id):
    cards = Card.query.filter_by(deck_id=deck_id).all()
    deck = Deck.query.filter_by(id=deck_id).first()
    return render_template('show_cards.html',cards=cards,deck=deck)

@app.route('/deck/<int:deck_id>/<int:card_id>/delete')
def delete_card(deck_id,card_id):
    card = Card.query.filter_by(id=card_id).first()
    db.session.delete(card)
    db.session.commit()
    return redirect('/deck/'+str(deck_id)+'/show_card')

@app.route('/deck/<int:deck_id>/<int:card_id>/update',methods=['GET','POST'])
def update_card(deck_id,card_id):
    if request.method=='POST':
        front = request.form['front']
        back = request.form['back']
        now = datetime.now()
        review_time = now.strftime('%Y-%m-%d %H:%M:%S')
        Card.query.filter_by(id=card_id).update({Card.front:front,Card.back:back,Card.score:0,Card.review_time:review_time})
        db.session.commit()
        return redirect('/deck/'+str(deck_id)+'/show_card')
    return render_template('update_card.html',card_id=card_id,deck_id=deck_id)
  
@app.route('/deck/<int:deck_id>/review',methods=['GET','POST'])
def review(deck_id):    
    if request.method=='POST':
        if request.form['action'] == 'flip':
            card = Card.query.filter_by(id=request.form['card_no']).first()
            deck = Deck.query.filter_by(id=deck_id).first()
            return render_template('review.html',card=card,deck=deck,value='flip')
        if request.form['action'] == 'next':
            card = Card.query.filter_by(id=request.form['card_no']).first()
            deck = Deck.query.filter_by(id=deck_id).first()
            difficulty_level = request.form['review']
            if difficulty_level == '1':
                score = 1
            elif difficulty_level == '2':
                score = 0.5
            else:
                score = 0        
            Card.query.filter_by(id=card.id).update({Card.score : score + card.score})
            Deck.query.filter_by(id=deck.id).update({Deck.score : Deck.score + score})
            db.session.commit()
    deck = Deck.query.filter_by(id=deck_id).first()
    cards = Card.query.filter_by(deck_id=deck_id).all()
    number = random.randint(0,len(cards)-1)
    card = cards[number]
    score = 0
    now = datetime.now()
    review_time = now.strftime('%Y-%m-%d %H:%M:%S')
    Card.query.filter_by(id=card.id).update({Card.score : score + card.score,Card.review_time:review_time})
    Deck.query.filter_by(id=deck.id).update({Deck.score : Deck.score + score,Deck.review_time:review_time})
    db.session.commit()
    return render_template('review.html',card=card,deck=deck,value='next')
if __name__ == '__main__':
    app.run(debug=True)


# from datetime import datetime
# now = datetime.now()
# review_time = now.strftime('%Y-%m-%d %H:%M:%S')
# print(review_time)