import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from main import Player, Team, session  # Replace with the actual path to your models

DATABASE_URI = "sqlite:///your_database.db"  # Replace with your database URI
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

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


# File path for the output Excel file
file_path = "exports/players_by_team.xlsx"

# Export players to Excel
export_players_to_excel(file_path)
print("written to ",file_path)