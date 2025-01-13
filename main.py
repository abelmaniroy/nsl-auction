import os
import random
from email.policy import default
from enum import unique

import pandas as pd
from flask import Flask, redirect, url_for, request, flash
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey

from sqlalchemy.orm import backref
from werkzeug.utils import secure_filename

from constants import team_names, pending, unsold

app = Flask(__name__)

app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_PATH'] = 'static/images'
app.secret_key = "nsl"
db = SQLAlchemy(app)
session = db.session



# class Pool(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     players = db.relationship("Player", backref='belongs_to_pool')
#
#     def __repr__(self):
#         return "Pool no:" + str(self.id)


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
    # pos = db.Column(db.String)
    # ach = db.Column(db.String)
    # pool = db.Column(ForeignKey(Pool.id), nullable=False)
    team = db.Column(ForeignKey(Team.id), nullable=False)
    img = db.Column(db.String,default=os.path.join('static/images', "0"))
    amount = db.Column(db.Float, default=0)
    # status = db.Column(db.Enum(Status), nullable=False, default=Status.pending)

    def __repr__(self):
        return "Player " + self.name


# def get_pool_data(pool_id):
#     pool = Pool.query.get(pool_id)
#     return pool


# def get_all_pools():
#     pool_ids = [pool.id for pool in Pool.query.all()]
#     return pool_ids

# def get_pool_data(pool_id):
#     pool = Pool.query.get(pool_id)
#     return pool

def get_player_list():
    players = Player.query.all()
    return players

def get_next_player():
    players = Player.query.filter_by(team=pending).all()
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
            image = request.files.get('image')

            player = Player(name=name, team=pending)
            if image and image.filename != '':

                filename = secure_filename(image.filename)
                app.logger.warning(image.filename)
                image_path = os.path.join(app.config['UPLOAD_PATH'], filename)
                image.save(image_path)
                player.img = filename

            session.add(player)
            session.commit()
            return redirect(url_for('player_list'))

        except Exception as e:
            session.rollback()  # Rollback in case of error
            print(f"An error occurred: {e}")  # Log the error for debugging
            return "An error occurred while creating players.", 500
    return render_template("create_player.html", pouch=get_pouch())

@app.route("/player/edit/<int:player_id>", methods=['GET', 'POST'])
def edit_player(player_id):
    player = session.query(Player).get(player_id)

    if request.method == "POST":
        try:
            name = request.form.get('name')
            image = request.files.get('image')
            team_id = request.form.get('team')
            # Update the player's name if provided
            if name:
                player.name = name

            if team_id:
                player.team = team_id

            # Update the player's image if provided
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                app.logger.warning(image.filename)
                image_path = os.path.join(app.config['UPLOAD_PATH'], filename)
                image.save(image_path)
                player.img = filename

            session.commit()
            return redirect(url_for('player_list'))

        except Exception as e:
            session.rollback()  # Rollback in case of error
            print(f"An error occurred: {e}")  # Log the error for debugging
            return "An error occurred while editing the player.", 500

    return render_template("edit_player.html", player=player, pouch=get_pouch(), teams=get_team_list())


# @app.route("/pool/<pool_id>", methods=["POST", "GET"])
# def pool_view(pool_id):
#     if request.method == "POST":
#         try:
#             new_pool = Pool()
#             session.add(new_pool)
#             session.commit()
#             return redirect(url_for('pool_view', pool_id=new_pool.id))
#
#         except Exception as e:
#             session.rollback()  # Rollback in case of error
#             print(f"An error occurred: {e}")  # Log the error for debugging
#             return "An error occurred while creating pool.", 500
#     return render_template('pool_view.html', data=get_pool_data(pool_id), pools=get_all_pools(), pouch=get_pouch())

@app.route("/player_list", methods=["POST","GET"])
def player_list():
    players = get_player_list()
    return render_template("player_list.html", data=players, pouch=get_pouch())

@app.route("/player/<player_id>", methods=["POST", "GET"])
def player_card(player_id):
    player = Player.query.get(player_id)
    if request.method == "POST":
        try:
            team_id = request.form.get('team')

            # team = Team.query.filter_by(name=)
            amount = request.form.get('amount')

            player.team = int(team_id)
            if player.team != unsold:
                player.amount = float(amount)
                team = player.sold_to
                team.pouch -= float(amount)
            app.logger.warning(player.sold_to.name + "   " + str(player.sold_to.pouch))
            session.commit()
            flash(f"Player transfer Complete",category="success")

        except Exception as e:
            session.rollback()  # Rollback in case of error
            print(f"An error occurred: {e}")  # Log the error for debugging
            return "An error occurred while resetting players.", 500
    return render_template('player.html', player=player, teams=get_team_list(), pouch=get_pouch())


@app.route('/auction')
def auction():
    next = get_next_player()
    if next:
        return redirect(url_for('player_card', player_id=next.id))
    else:
        return redirect(url_for('player_list'))


@app.route('/reset_all', methods=["POST"])
def reset_all():
    try:
        session.query(Player).update({Player.team: pending})
        session.query(Team).update({Team.pouch: 100})
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
    return redirect(url_for('player_list'))

def export_players_to_excel(file_path):
    try:
        # Query to get all players along with their team name and sold amount
        players = (
            session.query(Player.name, Team.name.label("team"), Player.amount)
            .join(Team, Player.team == Team.id)
            .all()
        )

        # Convert query results to a DataFrame
        data = pd.DataFrame(players, columns=["Player Name", "Team", "Sold Amount"])

        # Write to Excel, grouped by team
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            for team_name, group in data.groupby("Team"):
                group.to_excel(writer, sheet_name=team_name, index=False)

        print(f"Player data successfully written to {file_path}.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        session.close()

@app.route('/export')
def export():
    try:
        file_path = "exports/players_by_team.xlsx"
        # Export players to Excel
        export_players_to_excel(file_path)
        print("written to ", file_path)
        flash(f"Player data successfully exported to {file_path}.", "success")
    except Exception as e:
        flash(f"An error occurred during export: {e}", "danger")
    return redirect(url_for('home'))
