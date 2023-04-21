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
        #Inflation data does not go back further than this date
        if date(1980,12,12) < temp_date:
            dates.append(temp_date)
    return dates

def apple_dict(conn,curr,dates):

    curr.execute("SELECT name FROM Apple_Products ORDER BY id")
    db_names = curr.fetchall()
    dic = {}
    num_dates = len(dates)

    #443 is the TOTAL number of Apple products
    start_dates = 443 - num_dates
    for i in range(num_dates):
        dic[dates[i]] = dic.get(dates[i],[])
        dic[dates[i]].append(db_names[i + start_dates][0])

    return dic

def inflation_retriever(conn,curr,dates,name_of_table):
   
    curr.execute("CREATE TABLE IF NOT EXISTS {} (id INTEGER PRIMARY KEY, date TEXT, inflation_val_1st FLOAT, inflation_val_2nd FLOAT)".format(name_of_table))
    curr.execute("SELECT date FROM {}".format(name_of_table))
    table_info = curr.fetchall()

    # If all dates already have data then dont pull anymore
    if (len(table_info) >= len(dates)):
        print("All Data Has Been Collected")
        return

    #Find all unique years
    years = {}
    for x in dates:
        years[x.year] = years.get(x.year,[])
        years[x.year].append(x)
    
    remaining = str(len(dates) - len(table_info))
    print("Remaining Data: " + remaining)
    perc = str((len(table_info) * 1.0)/len(dates))
    print('Percent Complete: ' + perc)



    counter = 0
    id = len(table_info)
    while True:
        #Updates list of content
        curr.execute("SELECT date FROM {}".format(name_of_table))
        table_info = curr.fetchall()
        same_year_again = False
        #If no dates in the db choose the first year elem 
        if len(table_info) == 0:
            the_year = list(years.keys())[0]
        #If the last date of that year was NOT the last element added to the db start at that year
        elif table_info[-1][0] == years[int(table_info[-1][0][:4])][-1]:
            the_year = table_info[-1][0][:4]
            same_year_again = True
        #If the last date of that year WAS the last element, start at the next year
        else:
            if list(years.keys()).index(int(table_info[-1][0][:4]))+1 == len(list(years.keys())):
                print("All Data Collected for " + name_of_table)
                return
            the_year = list(years.keys())[list(years.keys()).index(int(table_info[-1][0][:4]))+1]
         
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
                if "Request could not be serviced" in message:
                    return

        
        #For each date that is this year
        if same_year_again:
            last_date = table_info[-1][0]
            date_start = years[the_year].index(last_date) + 1
        else:
            date_start = 0
        for x in range(date_start,len(years[the_year])):
            list_of_this_year = years[the_year]
            if counter == 25:
                print("25 Submissions added")
                return 
            #Get the month
            month_1 = list_of_this_year[x].strftime('%B')
            month_2 = ""
            if month_1 == "December":
                month_1 = "November"
                month_2 = "December"
            else:
                month_2 = (list_of_this_year[x] + timedelta(days=31)).strftime('%B')

            #Running total for each item
            inflation_val_1st = 1.0
            inflation_val_2nd = 1.0
            
            
            #For item collected
            for item in dic['Results']['series']:  
                start1 = inflation_val_1st
                start2 = inflation_val_2nd

                #For price of month 1 of that item 
                for elem in item['data']:
                    if elem['periodName'] == month_1:
                        inflation_val_1st *= float(elem['value'])
                        break
                #For price of month 2 of that item 
                for elem in item['data']:
                    if elem['periodName'] == month_2:
                        inflation_val_2nd *= float(elem['value'])
                        break

                #If month1 doesnt exist, find closest month that isnt current month
                if start1 == inflation_val_1st:
                    approx_month = int(len(item['data']) * ((list_of_this_year[x].month)/12.0))
                    inflation_val_1st *= float(item['data'][approx_month]['value'])

                if start2 == inflation_val_2nd:
                    approx_month = int(len(item['data']) * ((list_of_this_year[x].month)/12.0))
                    inflation_val_2nd *= float(item['data'][approx_month]['value'])

            curr.execute('INSERT OR IGNORE INTO {} (id, date, inflation_val_1st, inflation_val_2nd)  VALUES (?, ?, ?, ?)'.format(name_of_table), (id + counter, list_of_this_year[x].strftime("%Y-%m-%d"), inflation_val_1st, inflation_val_2nd))
            conn.commit()
            counter += 1

def nintendo_date_retriever(conn,curr):
    curr.execute("SELECT release_date FROM Mario_Games ORDER BY id")
    raw_dates = curr.fetchall()
    dates = []
    for x in raw_dates:
        dates.append(date(year=int(x[0][0:4]),month=int(x[0][5:7]),day=int(x[0][8:10])))
    return dates

def nintendo_dict(conn,curr,dates):
    curr.execute("SELECT name FROM Mario_Games ORDER BY id")
    db_names = curr.fetchall()
    dic = {}
    num_dates = len(dates)

    #235 is the TOTAL number of Mario Games
    start_dates = 235 - num_dates
    for i in range(num_dates):
        dic[dates[i]] = dic.get(dates[i],[])
        dic[dates[i]].append(db_names[i + start_dates][0])
    return dic
def main():
    conn = sqlite3.connect('Apptendo.db')
    curr = conn.cursor()
    #For Apple 
    apple_dates = apple_date_retriever(conn,curr)
    apple_to_dict = apple_dict(conn,curr,apple_dates)
    unique_apple_dates = list(apple_to_dict.keys())
    inflation_retriever(conn,curr,unique_apple_dates,'Inflation_Apple')

    #For Nintendo
    nintendo_dates = nintendo_date_retriever(conn,curr)
    nintendo_to_dict = nintendo_dict(conn,curr,nintendo_dates)
    unique_nintendo_dates = list(nintendo_to_dict.keys())
    inflation_retriever(conn,curr,unique_nintendo_dates,'Inflation_Nintendo')


if __name__ == "__main__":
    main()