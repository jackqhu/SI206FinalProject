import matplotlib.pyplot as plt
import sqlite3
from datetime import date, timedelta
import re
import csv
import os

months = ['January','February','March','April','May','June','July','August','September','October','November','December']
calculated_data = []

"""
Returns a date in YYYY-MM-DD format, 
when given the result of a query into the db in the terms of (Date, ...)

Inputs: 
 - Tuple where first index is a improperly formated date
Outputs:
 - Date object using the datetime class

"""
def get_date(i):

        #Year
        year = i[0][-4:]

        #Month
        found = re.search('(\w+)\s?(\d+)?,?',i[0])
        month = months.index(found.group(1)) + 1
        if month == -1:
            print("month not found")
            exit(1)
        month = str(month)
        
        #Day
        day = 1
        found = re.search('\d*?,',i[0])
        if found:
            if found.group(0) != ",":
                day = found.group(0)[:-1]


        #Return this newly create object
        return date(int(year),int(month),int(day))


"""
Creates a Scatter plot comparing inflation rates to rate of release of Apple Products

Inputs: 
 - SQLite3: Conn,Curr
Outputs:
 - None

"""
def apple_graph1(conn,curr):
    #Retrieves relevant data from DB
    curr.execute("SELECT Inflation_Apple.date, Inflation_Apple.inflation_val_1st, Inflation_Apple.inflation_val_2nd, Apple_Products.name FROM Inflation_Apple JOIN Apple_Products ON Apple_Products.id - 1 = Inflation_Apple.id")
    apple_data = curr.fetchall()

    for i in apple_data:
        # Name of Product , Release Date Reformated, Calculated Inflation rate
        calculated_data.append([i[3],i[0],abs(i[1] - i[2])])


    x = []
    x_ticks = []
    y = []
    #Puts the queried data from the DB into proper X and Y
    for counter in range(0,len(apple_data),10):
        i = apple_data[counter]
        time = date(int(i[0][0:4]),int(i[0][5:7]),int(i[0][8:10]))
        x.append(time)
        x_ticks.append(i[0])
        
        inflation1 = i[1]
        inflation2 = i[2]
        y.append(abs(inflation1 - inflation2)) 

    fig = plt.figure(figsize=(10, 3))

    #Formats graph
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)

    plt.title('Inflation vs Apple Release Dates')
    plt.xlabel('Releases of Every 10th Apple Product')
    plt.ylabel('Inflation Rate')

    plt.scatter(x, y)
    plt.xticks(x_ticks,rotation=90, fontsize=8)
    plt.tight_layout()
    plt.savefig('graph1.png')
    plt.show()


"""
Creates a Scatter plot comparing inflation rates to rate of release of Mario Games

Inputs: 
 - SQLite3: Conn,Curr
Outputs:
 - None

"""
def nintendo_graph1(conn,curr):
    #Retrieves relevant data from DB
    curr.execute("SELECT Inflation_Nintendo.date, Inflation_Nintendo.inflation_val_1st, Inflation_Nintendo.inflation_val_2nd, Mario_Games.name FROM Inflation_Nintendo JOIN Mario_Games ON Mario_Games.id - 1 = Inflation_Nintendo.id")
    mario_data = curr.fetchall()


    for i in mario_data:
        # Name of Product , Release Date Reformated, Calculated Inflation rate
        calculated_data.append([i[3],i[0],abs(i[1] - i[2])])

    x = []
    x_ticks = []
    y = []
    #Puts the queried data from the DB into proper X and Y
    for counter in range(0,len(mario_data),10):
        i = mario_data[counter]
        time = date(int(i[0][0:4]),int(i[0][5:7]),int(i[0][8:10]))
        x.append(time)
        x_ticks.append(i[0])
        
        inflation1 = i[1]
        inflation2 = i[2]
        y.append(abs(inflation1 - inflation2)) 
    
    plt.scatter(x, y)

    #Formats graph
    plt.xticks(x_ticks,rotation=90, fontsize=8)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)
    

    plt.xlabel('Releases of Every 10th Mario Game')
    plt.ylabel('Inflation Rate')
    plt.title('Inflation vs Mario Release Dates')
    plt.tight_layout()
    plt.savefig('graph2.png')
    plt.show()


"""
Creates a Scatter plot graphing multiple types of Apple products 
to understand the frequency these types of products were released 

Inputs: 
 - SQLite3: Conn,Curr
Outputs:
 - None

"""
def apple_graph2(conn,curr):
    # Retrieves relevant data from DB, joining the Product type with the Product ID
    curr.execute("SELECT release_date, Apple_Categories.category FROM Apple_Products JOIN Apple_Categories ON Apple_Products.category = Apple_Categories.id")
    apple_data = curr.fetchall()
    
    # X is a dictionary
    # Keys - Apple Product Types
    # Values - List of years product was released in
    x = {}
    
    # Y is a dictionary 
    # Keys - Apple Product Types
    # Values - Frequency of this type of Apple product released for each year associated above
    y = {}

    #Formats the X dictionary    
    for counter in range(len(apple_data)):
        i = apple_data[counter]
        temp_date = get_date(i)
        x[i[1]] = x.get(i[1],[])
        if temp_date.year not in x[i[1]]:
            x[i[1]].append(temp_date.year)

    #Creates all of the lists for the y dictionary with intial values of 0
    for item in list(x.keys()):
        y[item] = [0] * len(x[item])
    
    #Increments the values in the y dictionary so they match the intended frequency per year 
    for counter in range(len(apple_data)):
        i = apple_data[counter]
        temp_date = get_date(i).year
        index_of_x = x[i[1]].index(temp_date)
        y[i[1]][index_of_x] += 1

    #Graphs each Type of Apple Product one at a time    
    fig,ax = plt.subplots()
    for item_type in list(y.keys()):
        ax.scatter(x[item_type],y[item_type],label=item_type)
    ax.legend()
    

    #Format graph
    ax.set_xticks(range(1976, 2024, 1), minor=True)
    ax.set_yticks(range(0,26,1), minor=True)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    

    plt.xlabel('Years')
    plt.ylabel('Frequency of Apple-Product Type')
    plt.title('Types of Apple Product Releases vs Time')
    plt.tight_layout()
    plt.savefig('graph3.png')
    plt.show()


"""
Opens database and then calls each function to make Graphs 

Inputs:
None

Outputs:
None
"""
def make_graphs():
    conn = sqlite3.connect('Apptendo.db')
    curr = conn.cursor()
    apple_graph1(conn, curr)
    nintendo_graph1(conn,curr)
    apple_graph2(conn,curr)

    if os.path.exists('Apptendo.csv') == False:
        with open('Apptendo.csv', 'w', newline='') as file:
            # create a CSV writer object
            writer = csv.writer(file)

            writer.writerow(['Name of Product/Game', 'Release Date', 'Inflation from that month'])

            # write each row of the data to the CSV file
            for row in calculated_data:
                writer.writerow(row)
    

if __name__ == "__main__":
    make_graphs()
