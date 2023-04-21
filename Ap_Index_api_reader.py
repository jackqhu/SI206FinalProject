import sqlite3
import requests
import regex as re
from datetime import date, timedelta
import json

#Global Constants
months = ['January','February','March','April','May','June','July','August','September','October','November','December']

def apple_date_retriever(conn,curr):
    curr.execute("SELECT release_date FROM Apple_Products ORDER BY id")
    db_dates = curr.fetchall()
    dates = []
    for db_date in db_dates:  
        #Year
        year = db_date[0][-4:]

        #Month
        found = re.search('(\w+)\s?(\d+)?,?',db_date[0])
        month = months.index(found.group(1)) + 1
        if month == -1:
            print("month not found")
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

def inflation_retriever(conn,curr,dates,name_of_table):
   
    curr.execute("CREATE TABLE IF NOT EXISTS {} (id INTEGER PRIMARY KEY, date TEXT, inflation_val_1st Number, inflation_val_2nd Number)".format(name_of_table))
    curr.execute("SELECT * FROM {}".format(name_of_table))
    data = curr.fetchall()

    # If all dates already have data then dont pull anymore
    if (len(data) >= len(dates)):
        print("All Data Has Been Collected")
        return
    
    remaining = str(len(dates) - len(data))
    print("Remaining Data: " + remaining)
    perc = str((len(data) * 1.0)/len(dates))
    print('Percent Complete: ' + perc)

    #Find all unqiue years
    years = {}
    for x in dates:
        years[x.year] = years.get(x.year,[])
        years[x.year].append(x)

    #Finds the next 25 values, or until all values are done
    end = 25
    start = 0
    start += len(data)
    end += len(data)
    if end > len(years):
        end = len(years)

    #For each of the 25 request stock data from week ago till that day and add to the db
    for i in range(start,end):
        the_year = list(years.keys())[i]

        #Return type
        headers = {'Content-type': 'application/json'}

        #Average Price
        field = "AP"
        #Adjusted/Unadjusted Seasonal Price
        adjust = "U"
        #U.S. city average
        location = '0000'
        
        request_wo_item = field + adjust + location

        #702111: Bread, white, pan, per lb. (453.6 gm)
        item1 = "702111"
        #718311: Potato chips, per 16 oz.
        item2 = "718311"

        #Data for request
        data = json.dumps({"seriesid": [request_wo_item + item1, request_wo_item + item2],"startyear":the_year, "endyear":the_year})
        the_url = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
        r = requests.request('GET', url=the_url, data=data, headers=headers)
        
        #Verifies Connection Went Through
        if r.status_code != 200:
            print(r.status_code)
            exit(1)
        
        #Collect json->dict
        dic = r.json()

        #Tests if stock can be retrieved
        if dic['status'] == "REQUEST_FAILED":
            print("Request failed: " + str(the_year))
            exit(1)
        #If there is a message (usually says no data available)
        if len(dic['message']) != 0:
            print("Message for " + str(the_year) + ": ")
            for message in dic['message']:
                print("\t- " + str(message))

        #For each date that is this year
        for x in years[the_year]:

            #Get the month
            month_1 = x.strftime('%B')
            month_2 = ""
            if month_1 == "December":
                month_1 = "November"
                month_2 = "December"
            else:
                month_2 = (x + timedelta(days=30)).strftime('%B')

            #Running total for each item
            inflation_val_1st = 1
            inflation_val_2nd = 1
            
            #For item collected
            for item in dic['Results']['series']:
                
                start1 = inflation_val_1st
                start2 = inflation_val_2nd

                #For price of month 1 of that item 
                for i in item['data']:
                    if i['periodName'] == month_1:
                        start1 *= x['value']
                        break
                #For price of month 2 of that item 
                for i in item['data']:
                    if i['periodName'] == month_2:
                        start2 *= i['value']
                        break

                #If month1 doesnt exist, find closest month that isnt current month
                if start1 == inflation_val_1st:
                    approx_month = int(len(item['data']) * ((x.month)/12.0))
                    inflation_val_1st *= item['data'][approx_month]['value']

                if start2 == inflation_val_2nd:
                    approx_month = int(len(item['data']) * ((x.month)/12.0))
                    inflation_val_2nd *= item['data'][approx_month]['value']

            #Puts Inflation rate data into table
            curr.execute('INSERT INTO {} (id, date, inflation_val_1st, inflation_val_2nd)  VALUES (?, ?, ?, ?)'.format(name_of_table), (i, x.strftime("%Y-%m-%d"), inflation_val_1st, inflation_val_2nd))
    conn.commit()

def main():
    conn = sqlite3.connect('Apptendo.db')
    curr = conn.cursor()
    #For Apple 
    apple_dates = apple_date_retriever(conn,curr)
    apple_to_dict = apple_dict(conn,curr,apple_dates)
    unique_apple_dates = list(apple_to_dict.keys())
    inflation_retriever(conn,curr,unique_apple_dates,'Inflation_Apple')

    #For Nintendo
    apple_dates = apple_date_retriever(conn,curr)
    apple_to_dict = apple_dict(conn,curr,apple_dates)
    unique_apple_dates = list(apple_to_dict.keys())
    inflation_retriever(conn,curr,unique_apple_dates,'Inflation_Apple')


if __name__ == "__main__":
    main()