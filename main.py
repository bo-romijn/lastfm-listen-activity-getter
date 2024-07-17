from datetime import datetime as dt
import concurrent.futures
import pandas as pd
import pylast
import config
import time
import json

# Setup (Config file is not included as it contains my personal API key and account data)
API_KEY = config.API_KEY
API_SECRET = config.API_SECRET

username = config.USERNAME
password_hash = pylast.md5(config.PASSWORD)

network = pylast.LastFMNetwork(
    api_key=API_KEY,
    api_secret=API_SECRET,
    username=username,
    password_hash=password_hash,
)

def get_user_tracks(user, network):

    # Initialize start timer
    start_time = time.perf_counter()

    # Gets LastFM user
    user = network.get_user(user)

    # Gets user registry date unix timestamp and date
    date_registered_unix_timestamp = int(user.get_registered())
    date_registered = dt.fromtimestamp(date_registered_unix_timestamp).strftime('%d-%m-%Y')

    print(f"Getting tracks from user {user}...")

    user_tracks = list()

    # Gets artists of all tracks ever listened to by user
    recent_tracks = user.get_recent_tracks(limit=None, cacheable=True)
    for i, track in enumerate(recent_tracks):

        # (Re)initializes a list
        track_list = list()

        # Appends artist name
        track_artist_name = str(track.track.artist.name).encode("utf-8")
        track_list.append(track_artist_name.decode())

        # Appends scrobble date (mm-dd-YYYY)
        track_list.append(int(track.timestamp))

        # Appends track_list to user_tracks as an entry
        user_tracks.append(track_list)
    
    # End time
    end_time = time.perf_counter()

    time_elapsed = end_time - start_time
    print(f"Got {len(user_tracks)} tracks from {user} in {time_elapsed.__round__(3)}s")
    
    return user_tracks

all_tracks = list()
users = {} # LastFM usernames go here

for user in users:
    user_tracks = get_user_tracks(user, network)
    all_tracks.extend(user_tracks)

# Fetching tracks finished
print(f"All tracks fetched from lastfm. Total: {len(all_tracks)}")

# Set for unique dates
days = set()

# Dict for unique artists (used as a template)
template = dict()

# Puts all unique dates and artists in their respective lists
for date in all_tracks:
    template.update({artist_name: 0})
    days.add(date)

masterlist = dict()

# Sort the days so the masterlist comes out in the right order
days = sorted(days)
for day in days:
    # Adds total scrobbles of artists and their respective days to template
    for artist_name, date in all_tracks:

        if day == date:
            template[artist_name] += 1

    # Copies template and updates masterlist with it
    day_dict = template.copy()
    masterlist.update({str(dt.fromtimestamp(day).strftime("%d %m, %Y")): day_dict})

# Converts masterlist to valid JSON and outputs it into an Excel spreadsheet
masterlist = json.dumps(masterlist, indent=4)
dataframe = pd.read_json(masterlist)

with pd.ExcelWriter("bar-chart-race.xlsx",  datetime_format = "DD-MM-YYYY", date_format = "DD-MM-YYYY") as writer:
    dataframe.to_excel(writer)