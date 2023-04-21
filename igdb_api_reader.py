import sqlite3
import requests
import json
import config
import datetime

client_id = config.client_id
client_secret = config.client_secret

def authenticate_igdb():
    #Personal Info
    token_url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }

    #Retrieve access token
    r = requests.post(url=token_url, data=params)
    access_token = r.json()['access_token']
    return access_token

def get_mario_games(curr, access_token):
    #Get user info
    base_url = 'https://api.igdb.com/v4/games'
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }

    #Select all retrieved games
    curr.execute("SELECT * FROM Mario_Games")
    #Index into their list of games relative to games we have retrieved
    offset = len(curr.fetchall())
    #Sets requests
    body = f'fields name, first_release_date, franchises; where name = *"Mario"* & category = 0; sort first_release_date asc; limit 25; offset {offset};'
    
    #Sends POST request to IGDB API
    r = requests.post(url=base_url, headers=headers, data=body)
    mario_games = r.json()
    return mario_games

def save_to_JSON(mario_games, file_name='mario_games.json'):
    with open(file_name, 'w') as json_file:
        json.dump(mario_games, json_file, indent=4)

def process_JSON(curr, conn, mario_games):
    #When done exit
    curr.execute('SELECT * FROM Mario_Games')    
    if len(curr.fetchall()) == 235:
        print("Mario Database: Completed")
        return
    
    #For every game in request
    for game in mario_games:
        #Convert Unix time to YEAR-MONTH-DAY
        date = datetime.datetime.utcfromtimestamp(game['first_release_date']).strftime('%Y-%m-%d')
        
        #If not franchise set to -1
        if game.get('franchises',[]) == []:
            game['franchises'] = -1
        else:
            #Either pick first franchise or Mario's franchise (845)
            if 845 in game['franchises']:
                game['franchises'] = 845
            else:
                game['franchises'] = game['franchises'][0]
        
        #Insert entry into table
        curr.execute('INSERT INTO Mario_Games (name, release_date, franchise) VALUES (?, ?, ?)', (game['name'], date, game['franchises']))
    conn.commit()

def main():
    #Connect to DB
    conn = sqlite3.connect('Apptendo.db')
    curr = conn.cursor()

    #Create Table
    curr.execute('CREATE TABLE IF NOT EXISTS Mario_Games (id INTEGER PRIMARY KEY, name TEXT, release_date DATE, franchise INT)')
    
    #Pull request of mario games
    mario_games = get_mario_games(curr, authenticate_igdb())

    # Save retrieved data into a JSON file
    save_to_JSON(mario_games)
    
    #Insert request into Table
    process_JSON(curr, conn, mario_games)

    conn.close()

if __name__ == "__main__":
    main()
