import sqlite3
import requests
import regex as re
from datetime import date, timedelta

def apple_dates(conn,curr):
    curr.execute("SELECT release_date FROM Apple_Products ORDER BY id")
    db_dates = curr.fetchall()
    months = ['January','February','March','April','May','June','July','August','September','October','November','December']
    dates = []
    for db_date in db_dates:
        
        
        #Year
        year = db_date[0][-4:]

        #Month
        found = re.search('(\w+)\s?(\d+)?,?',db_date[0])
        month = months.index(found.group(1)) + 1
        if month == -1:
            exit(1)
        month = str(month)
        
        #Day
        day = 1
        found = re.search('\d*?,',db_date[0])
        if found:
            if found.group(0) != ",":
                day = found.group(0)[:-1]
        temp_date = date(int(year),int(month),int(day))

        #We can only use the Apple products that were released after the company went public
        if temp_date >= date(1980,12,12):
            dates.append(temp_date)
    return dates

def apple_dict(conn,curr,dates):

    curr.execute("SELECT name FROM Apple_Products ORDER BY id")
    db_names = curr.fetchall()
    dic = {}
    num_dates = len(dates)

    #443 is the TOTAL number of Apple products
    #We can only use the Apple products that were released after the company went public
    start_dates = 443 - num_dates
    for i in range(num_dates):
        dic[dates[i]] = dic.get(dates[i],[])
        dic[dates[i]].append(db_names[i + start_dates][0])

    return dic

def pull_stock_apple(conn,curr,dates):
   
    curr.execute("CREATE TABLE IF NOT EXISTS apple_stock (id INTEGER PRIMARY KEY, release_date TEXT, stock_value_of_date INTEGER, stock_value_week_before INTEGER)")
    curr.execute("SELECT * FROM apple_stock")
    data = curr.fetchall()

    #If all dates already have data then dont pull anymore
    if (len(data) >= len(dates)):
        print("Returned")
        return
    
    #Finds the next 25 values, or until all values are done
    cur_limit = 25
    pos = len(data)
    limit = pos+cur_limit
    if pos+cur_limit > len(dates):
        limit = len(dates)

    id = 15 + pos
    #For each of the 25 request stock data from week ago till that day and add to the db
    for i in range(pos,limit):
       
        today = dates[i].strftime('%Y-%m-%d')
        last_week = (dates[i] - timedelta(days=7)).strftime('%Y-%m-%d')

        the_url = "https://api.stockdata.org/v1/data/eod?symbols=AAPL&api_token=4XNRuoTNtnRGGypfWkqudfqrcbNSX8ouOyJXukST&date_from="+last_week+"&date_to="+today+"&format=json"
        r = requests.request('GET', url=the_url, params={"api_token": "4XNRuoTNtnRGGypfWkqudfqrcbNSX8ouOyJXukST", "symbols": "AAPL" ,"date_from": last_week,"date_to": today})
        if r.status_code != 200:
            exit(1)
        
        dic = r.json()

        #Tests if stock can be retrieved
        stock_today = None
        stock_week_ago = None
        if len(dic['data']) > 1:
            stock_today = int(dic['data'][0]['high'])
            stock_week_ago = int(dic['data'][len(dic['data']) - 1]['high'])
        if len(dic['data']) == 1:
            stock_today = int(dic['data'][0]['high'])
            stock_week_ago = 0

        #Puts stock data into table
        curr.execute('INSERT INTO apple_stock (id, release_date, stock_value_of_date, stock_value_week_before) VALUES (?, ?, ?, ?)', (id + i, today, stock_today, stock_week_ago))
    conn.commit()

def main():
    conn = sqlite3.connect('Apptendo.db')
    curr = conn.cursor()
    dates = apple_dates(conn,curr)
    db_to_dict = apple_dict(conn,curr,dates)
    unique_dates = list(db_to_dict.keys())

    #unit testing
    dates = [date(2023,4,1),date(2022,1,5),date(2021,10,16)]
    
    #eventually replace dates with unique_dates
    pull_stock_apple(conn,curr,dates)

if __name__ == "__main__":
    main()