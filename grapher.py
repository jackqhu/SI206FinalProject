import matplotlib.pyplot as plt
import sqlite3
from datetime import date, timedelta
import re

months = ['January','February','March','April','May','June','July','August','September','October','November','December']


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

        return date(int(year),int(month),int(day))


"""
Creates a Bar-graph the comparison of Apple Products

Inputs: y, labels
y - Heights of each product
labels - Name of each product

Outputs:
None
"""
def apple_graph1(conn,curr):
    curr.execute("SELECT date, inflation_val_1st, inflation_val_2nd FROM Inflation_Apple")
    apple_data = curr.fetchall()

    x = []
    x_ticks = []
    y = []
    for counter in range(0,len(apple_data),10):
        i = apple_data[counter]
        time = date(int(i[0][0:4]),int(i[0][5:7]),int(i[0][8:10]))
        x.append(time)
        x_ticks.append(i[0])
        
        inflation1 = i[1]
        inflation2 = i[2]
        y.append(abs(inflation1 - inflation2)) 

    plt.scatter(x, y)
    plt.xticks(x_ticks,rotation=90, fontsize=8)
    plt.tight_layout()
    plt.savefig('graph1.png')
    plt.show()

def nintendo_graph1(conn,curr):
    curr.execute("SELECT date, inflation_val_1st, inflation_val_2nd FROM Inflation_Nintendo")
    mario_data = curr.fetchall()

    x = []
    x_ticks = []
    y = []
    for counter in range(0,len(mario_data),10):
        i = mario_data[counter]
        time = date(int(i[0][0:4]),int(i[0][5:7]),int(i[0][8:10]))
        x.append(time)
        x_ticks.append(i[0])
        
        inflation1 = i[1]
        inflation2 = i[2]
        y.append(abs(inflation1 - inflation2)) 

    plt.scatter(x, y)
    plt.xticks(x_ticks,rotation=90, fontsize=8)
    plt.tight_layout()
    plt.savefig('graph2.png')
    plt.show()

def apple_graph2(conn,curr):
    #

    curr.execute("SELECT release_date, Apple_Categories.category FROM Apple_Products JOIN Apple_Categories ON Apple_Products.category = Apple_Categories.id")
    apple_data = curr.fetchall()
    
    x = {}
    y = {}
    for counter in range(len(apple_data)):
        i = apple_data[counter]
        temp_date = get_date(i)
        x[i[1]] = x.get(i[1],[])
        if temp_date.year not in x[i[1]]:
            x[i[1]].append(temp_date.year)

    for item in list(x.keys()):
        y[item] = [0] * len(x[item])
    
    for counter in range(len(apple_data)):
        i = apple_data[counter]
        temp_date = get_date(i).year
        index_of_x = x[i[1]].index(temp_date)
        print(i[1])
        print(temp_date)
        print(index_of_x)
        y[i[1]][index_of_x] += 1 
    fig,ax = plt.subplots()
    for item_type in list(y.keys()):
        ax.scatter(x[item_type],y[item_type],label=item_type)
    ax.legend()
    plt.tight_layout()
    plt.savefig('graph3.png')
    plt.show()


"""
Retrieves Data from database and then calls each function to make Graphs and 

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

if __name__ == "__main__":
    make_graphs()
