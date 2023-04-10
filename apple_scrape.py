from bs4 import BeautifulSoup
import requests
import os
import json

'''
Scrapes the Apple product release data from wikipedia at the following link:
https://en.wikipedia.org/wiki/Timeline_of_Apple_Inc._products

Author: Taylor Snyder
'''

def load_JSON(filename):
    '''
    Loads in a JSON file with the given name if it exists.
    INPUTS: filename (string)
    RETURNS: Dictionary with loaded data (or empty dictionary)
    '''
    
    try:
        # Open file
        source_dir = os.path.dirname(__file__)
        full_path = os.path.join(source_dir, filename)
        infile = open(full_path, 'r')

        data = json.load(infile)
        print("Loaded in JSON file successfully.")
        return data
        
    except:
        print("Could not open JSON file, beginning process with empty dictionary.")
        return dict()

def write_JSON(filename, data):
    '''
    Writes data as a JSON to the given filename.
    INPUTS: filename (string), data (dictionary)
    RETURNS: None
    '''
    
    with open(filename, 'w') as outfile:
        json.dump(data, outfile, indent=2)

def color_code_lookup(color_code):
    '''
    Returns the item category based on the row's background color.
    INPUT: Table Row Background Color Code (String)
    RETURNS: Item Category (String)
    '''
    
    if color_code == '#FFFF79' or color_code == 'FFFF79':
        return "Apple 1/2/2GS/3"
    elif color_code == '#81D666' or color_code == '81D666':
        return "Lisa"
    elif color_code == '#95CEFE' or color_code == '95CEFE':
        return "Macintosh"
    elif color_code == '#8BFFA3' or color_code == '8BFFA3':
        return "Network Server"
    elif color_code == '#CCFF99' or color_code == 'CCFF99' or color_code == '#CF9':
        return "Phones/Tablets/PDAs"
    elif color_code == '#FFE5E5' or color_code == 'FFE5E5':
        return "iPod/Consumer Products"
    elif color_code == '#D8D8F2' or color_code == 'D8D8F2':
        return "Computer Peripherals"
    else:
        return "N/A"

def add_25_entries(soup, data):
    '''
    Adds up to 25 entries from the provided soup into the data dictionary (if they do not exist already).
    INPUTS: soup (BS4 soup object), data (dictionary)
    RETURNS: number of entries added (integer)
    '''
    
    table_list = soup.find_all('tr', bgcolor=True)
    
    # Placeholders for rowspans in table, entries counter
    rowspan = 0
    rowspan_date = ""
    entries_added = 0
    
    for row in table_list:
        
        row_data = row.find('td')
        row_name = row.find('a')
        
        # Lookup category with bg color code
        row_category = color_code_lookup(row['bgcolor'].rstrip().upper())
        
        
        if row_data:
            # First, check to see if the row has a row span
            if row_data.has_attr('rowspan'):
                rowspan = int(row_data['rowspan'])
                rowspan_date = row_data.text.rstrip()
            
            # If we have rowspan, decrement and use rowspan date until rowspan is done
            if rowspan != 0:
                entry_name = row_name.text.rstrip()
                entry_details = {
                                "release date" : rowspan_date,
                                "category"     : row_category
                                }
                rowspan -= 1
                
                if data.get(entry_name) is None:
                    data[entry_name] = entry_details
                    entries_added += 1
                
            else:
                entry_name = row_name.text.rstrip()
                entry_details = {
                                "release date" : row_data.text.rstrip(),
                                "category"     : row_category
                                }
                
                if data.get(entry_name) is None:
                    data[entry_name] = entry_details
                    entries_added += 1
                
        
        # Check that we do not add more than 25 things per run
        if entries_added >= 25:
            break        
    
    return entries_added
    
def add_entries_to_JSON():
    '''
    Loads JSON data, sends a request to the wikipedia URL, creates the soup object, adds entries, and writes to updated JSON.
    INPUTS: None
    RETURNS: None
    '''
    
    data = load_JSON("apple_data.json")
    
    r = requests.get('https://en.wikipedia.org/wiki/Timeline_of_Apple_Inc._products')
    
    if not r.ok:
        print("Error, unable to connect to url.")
        
    soup = BeautifulSoup(r.content, 'html.parser')
    
    num_entries_added = add_25_entries(soup, data)
    
    write_JSON("apple_data.json", data)
    
    print(f"Added {num_entries_added} entries to the database and JSON.")

# TODO: Make sure we create a foreign key lookup for category (gives me a chance to use JOIN)
def update_SQL_Database():
    pass

def main():
    '''
    Driver function which ensures that each time the program is run, the JSON is updated with <= 25 new entries, and that the SQL database is then also updated.
    INPUTS: None
    RETURNS: None
    '''
    add_entries_to_JSON()
    
if __name__ == '__main__':
    main()