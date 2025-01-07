import random


from flask import Flask, redirect, url_for, request
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey

from sqlalchemy.orm import backref

from constants import team_names, pending

app = Flask(__name__)

app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
session = db.session


class Pool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    players = db.relationship("Player", backref='belongs_to_pool')

    def __repr__(self):
        return "Pool no:" + str(self.id)


class Team(db.Model):
    # id = db.Column(db.Enum(Status), nullable=False, primary_key=True)
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    pouch = db.Column(db.Float, default=100)
    name = db.Column(db.String)
    players = db.relationship("Player", backref="sold_to")

    def __repr__(self):
        return self.name


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    pos = db.Column(db.String)
    ach = db.Column(db.String)
    pool = db.Column(ForeignKey(Pool.id), nullable=False)
    team = db.Column(ForeignKey(Team.id), nullable=False)

    # status = db.Column(db.Enum(Status), nullable=False, default=Status.pending)

    def __repr__(self):
        return "Player " + self.name


def get_pool_data(pool_id):
    pool = Pool.query.get(pool_id)
    return pool


def get_all_pools():
    pool_ids = [pool.id for pool in Pool.query.all()]
    return pool_ids


def get_next_player(pool_id):
    players = Player.query.filter_by(pool=pool_id, team=pending).all()
    return random.choice(players) if players else None


def get_team_list():
    # teams = []
    # # enums = [j for j in Status][1:]
    # for i in enums:
    #     team = Team.query.get(i)
    #     teams.append(team)
    teams = Team.query.all()[2:]
    return teams


def get_pouch():
    try:
        pouch = [i for i in Team.query.all()[2:]]
        return pouch
    except Exception as e:
        print(f"An error occurred: {e}")
        return "An error occurred while fetching pouch."


def create_team():
    for i in team_names:
        team = Team(id=i[1], name=i[0])
        db.session.add(team)
        db.session.commit()


@app.route("/player/create", methods=['GET', 'POST'])
def create_player():
    if request.method == "POST":
        try:
            name = request.form.get('name')
            pos = request.form.get('pos')
            ach = request.form.get('ach')
            pool = request.form.get('pool')
            player = Player(name=name, pos=pos, ach=ach, pool=pool, team=pending)
            session.add(player)
            session.commit()
            return redirect(url_for('pool_view', pool_id=pool))

        except Exception as e:
            session.rollback()  # Rollback in case of error
            print(f"An error occurred: {e}")  # Log the error for debugging
            return "An error occurred while creating players.", 500
    return render_template("create_player.html", pools=get_all_pools(), pouch=get_pouch())


@app.route("/pool/<pool_id>", methods=["POST", "GET"])
def pool_view(pool_id):
    if request.method == "POST":
        try:
            new_pool = Pool()
            session.add(new_pool)
            session.commit()
            return redirect(url_for('pool_view', pool_id=new_pool.id))

        except Exception as e:
            session.rollback()  # Rollback in case of error
            print(f"An error occurred: {e}")  # Log the error for debugging
            return "An error occurred while creating pool.", 500
    return render_template('pool_view.html', data=get_pool_data(pool_id), pools=get_all_pools(), pouch=get_pouch())


@app.route("/player/<player_id>", methods=["POST", "GET"])
def player_card(player_id):
    player = Player.query.get(player_id)
    if request.method == "POST":
        try:
            team_id = request.form.get('team')
            # team = Team.query.filter_by(name=)
            amount = request.form.get('amount')

            player.team = int(team_id)
            team = player.sold_to
            team.pouch -= float(amount)
            app.logger.warning(player.sold_to.name + "   " + str(player.sold_to.pouch))
            session.commit()

        except Exception as e:
            session.rollback()  # Rollback in case of error
            print(f"An error occurred: {e}")  # Log the error for debugging
            return "An error occurred while resetting players.", 500
    return render_template('player.html', player=player, teams=get_team_list(), pouch=get_pouch())


@app.route('/auction/<pool_id>')
def auction(pool_id):
    next = get_next_player(pool_id)
    if next:
        return redirect(url_for('player_card', player_id=next.id))
    else:
        return redirect(url_for('pool_view', pool_id=pool_id))


@app.route('/reset_all', methods=["POST"])
def reset_all():
    try:
        session.query(Player).update({Player.team: pending})
        session.commit()
        return redirect(url_for('home'))
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        print(f"An error occurred: {e}")  # Log the error for debugging
        return "An error occurred while resetting players.", 500

@app.route('/reset-pouch/',methods=["GET","POST"])
def reset_pouch():
    if request.method=="POST":


        try:
            for i in get_pouch():
                i.pouch = request.form.get(str(i.id))
            session.commit()
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            print(f"An error occurred: {e}")  # Log the error for debugging
            return "An error occurred while resetting pouch.", 500

    return render_template('reset_pouch.html', pouch=get_pouch())

@app.route('/')
def home():
    return render_template('home.html', pouch=get_pouch())
