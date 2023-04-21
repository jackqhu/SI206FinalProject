import sqlite3
import requests
import json
import config
import datetime

client_id = config.client_id
client_secret = config.client_secret

def authenticate_igdb():
    token_url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    r = requests.post(url=token_url, data=params)

    access_token = r.json()['access_token']
    return access_token

def get_mario_games(curr, access_token):
    base_url = 'https://api.igdb.com/v4/games'
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    curr.execute("SELECT * FROM Mario_Games")
    offset = len(curr.fetchall())
    body = f'fields name, first_release_date; where name = *"Mario"* & category = 0; sort first_release_date asc; limit 25; offset {offset};'
    r = requests.post(url=base_url, headers=headers, data=body)
    mario_games = r.json()
    return mario_games

def process_JSON(curr, conn, mario_games):
    for game in mario_games:
        date = datetime.datetime.utcfromtimestamp(game['first_release_date']).strftime('%Y-%m-%d')
        curr.execute('SELECT * FROM Mario_Games WHERE name = ?', (game['name'],))
        if len(curr.fetchall()):
            continue
        curr.execute('INSERT INTO Mario_Games (name, release_date) VALUES (?, ?)', (game['name'], date))
    conn.commit()

def main():
    conn = sqlite3.connect('Apptendo.db')
    curr = conn.cursor()

    curr.execute('CREATE TABLE IF NOT EXISTS Mario_Games (id INTEGER PRIMARY KEY, name TEXT, release_date DATE)')
    mario_games = get_mario_games(curr, authenticate_igdb())
    process_JSON(curr, conn, mario_games)

    conn.close()

if __name__ == "__main__":
    main()