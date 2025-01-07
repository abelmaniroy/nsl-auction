import random


from flask import Flask, redirect, url_for, request
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey

from sqlalchemy.orm import backref

from constants import Status

app = Flask(__name__)

# @app.route("/")
# def hello_world():
#     return "<p>Hello, World!</p>"
from flask import Flask
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
session = db.session

class Pool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    players = db.relationship("Player",backref='belongs_to')
    def __repr__(self):
        return "Pool no:"+str(self.id)

class Player(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     name = db.Column(db.String, nullable=False, unique=True)
     pos = db.Column(db.String)
     ach = db.Column(db.String)
     pool = db.Column(ForeignKey(Pool.id))
     status = db.Column(db.Enum(Status), nullable=False, default=Status.pending)
     def __repr__(self):
         return "Player "+self.name

def get_pool_data(pool_id):
    pool = Pool.query.get(pool_id)
    return pool
def get_all_pools():
    pool_ids = [pool.id for pool in Pool.query.all()]
    return pool_ids
def get_next_player(pool_id):
    players = Player.query.filter_by(pool=pool_id, status=Status.pending).all()
    return random.choice(players) if players else None

@app.route("/pool/<pool_id>")
def pool_view(pool_id):
    return render_template('pool_view.html',data=get_pool_data(pool_id), pools = get_all_pools())

@app.route("/player/<player_id>",methods=["POST","GET"])
def player_card(player_id):
    player = Player.query.get(player_id)
    if request.method == "POST":
        try:
            player.status=Status.team1
            session.commit()
        except Exception as e:
            session.rollback()  # Rollback in case of error
            print(f"An error occurred: {e}")  # Log the error for debugging
            return "An error occurred while resetting players.", 500
    return render_template('player.html', player=player)

@app.route('/auction/<pool_id>')
def auction(pool_id):
    next = get_next_player(pool_id)
    if next:
        return redirect(url_for('player_card',player_id=next.id))
    else:
        return redirect(url_for('pool_view',pool_id=pool_id))

@app.route('/reset_all',methods=["POST"])
def reset_all():
    try:
        session.query(Player).update({Player.status:Status.pending})
        session.commit()
        return redirect(url_for('home'))
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        print(f"An error occurred: {e}")  # Log the error for debugging
        return "An error occurred while resetting players.", 500
@app.route('/')
def home():
    return render_template('home.html')