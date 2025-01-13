import os

from constants import pending
from main import db, Player, app

# Path to the folder containing images
image_folder = 'static/images'


def create_players_from_images(folder_path):
    """
    Reads images from a folder and creates Player objects in the database.
    """
    # Ensure the folder exists
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist.")
        return

    # Get all image files in the folder
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

    if not image_files:
        print(f"No image files found in folder '{folder_path}'.")
        return

    # Iterate over files and create Player objects
    for image_file in image_files:
        # Extract name (without extension) from filename
        name = os.path.splitext(image_file)[0]

        # Create Player object
        player = Player(name=name, img=image_file, team=pending)

        # Add to the session
        db.session.add(player)

    # Commit all changes to the database
    try:
        db.session.commit()
        print(f"Successfully added {len(image_files)} players to the database.")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding players to the database: {e}")


# Run the script
if __name__ == '__main__':
    with app.app_context():
        create_players_from_images(image_folder)
