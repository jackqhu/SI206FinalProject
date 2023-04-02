import matplotlib.pyplot as plt
import sqlite3

"""
Retrieves a the information of the Apple Products

Inputs: 
None

Outputs: y, labels
y - Heights of each product
labels - Name of each product
"""
def retrieve_apple():
    y = range(100)
    labels = range(100)
    return y, labels
    


"""
Creates a Bar-graph the comparison of Apple Products

Inputs: y, labels
y - Heights of each product
labels - Name of each product

Outputs:
None
"""
def apple_graph(y,labels):
    x = range(len(y))
    plt.bar(x, y, width = 0.4)
    plt.xticks(labels,rotation=90, fontsize=8)
    plt.tight_layout()
    plt.show()



"""
Retrieves Data from database and then calls each function to make Graphs and 

Inputs:
None

Outputs:
None
"""
def make_graphs():
    apple_graph()

if __name__ == "__main__":
    make_graphs()
