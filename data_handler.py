"""
Creates SQLite3 server that stores (timestamp,title,length,link,filepath,thumbnail_filepath).
Allows for lookup, insertion, deletion, clearing.
Should not store songs longer than MAX_LENGTH
"""

import sqlite3
import datetime

info_db = '/data/file_info.db'
now = datetime.datetime.now()

MAX_LENGTH = 10 # maximum supported video length in minutes

def dto(dt_str):
    return datetime.datetime.strptime(dt_str,'%Y-%m-%d %H:%M:%S.%f')

# title string, length int (sec), link string, filepath string, thumbnail string (also filepath?)
def insert_data(title, length, link, filepath, thumbnail):
    if length > 60 * MAX_LENGTH:
        return "Too long to be stored."
    timestamp = datetime.datetime.now()
    with sqlite3.connect(info_db) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text);""")
        c.execute('''INSERT into info_db VALUES (?,?,?,?,?);''',(timestamp,title,length,link, filepath))
    return "Data inserted."

def retrieve_data(link):
    pass

def remove_old_data(timestamp):
    with sqlite3.connect(info_db) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text);""")
        c.execute('''DELETE FROM ht_db WHERE time_>=?;''',(timestamp))
    return "Old data deleted."

# should this function even exist? feels dangerous
def clear_db():
    pass
