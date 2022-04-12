"""
Creates SQLite3 server that stores (timestamp,title,length,link,filepath,thumbnail).
Allows for lookup, insertion, deletion, clearing.
Should not store songs longer than MAX_LENGTH
"""

import sqlite3
import datetime

info_db = 'file_info.db'
MAX_LENGTH = 10 # maximum supported video length in minutes

def dto(dt_str):
    return datetime.datetime.strptime(dt_str,'%Y-%m-%d %H:%M:%S.%f')

# return true if put in database/already in database, false if cannot
# title string, length int (sec), link string, filepath string, thumbnail string
def insert_data(title, length, link, filepath, thumbnail=""):
    if length > 60 * MAX_LENGTH or link[:20]!="youtube.com/watch?v=":
        return False
    if not retrieve_data(link):
        timestamp = datetime.datetime.now()
        with sqlite3.connect(info_db) as c:
            c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text, thumbnail text);""")
            c.execute('''INSERT into info_db VALUES (?,?,?,?,?,?);''',(timestamp,title,length,link, filepath, thumbnail))
    return True

# given link: return row data, if exists
def retrieve_data(link):
    with sqlite3.connect(info_db) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text, thumnbnail text);""")
        current = c.execute('''SELECT * FROM info_db WHERE link=;''',(link)).fetchall()
    return current

# given link: deletes row data, if exists. returns LIST of mp3 filepath of deleted entries.
def delete_data(link):
    with sqlite3.connect(info_db) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text, thumnbnail text);""")
        out = c.execute('''SELECT filepath FROM info_db WHERE link=?;''',(link)).fetchall()
        c.execute('''DELETE * FROM info_db WHERE link=?;''',(link))
        return out

# clear data entries older than timestamp given, if exists. returns LIST of mp3 filepaths of deleted entries.
def remove_old_data(timestamp):
    with sqlite3.connect(info_db) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text, thumnbnail text);""")
        out = c.execute('''SELECT filepath FROM info_db WHERE time_<=?;''',(timestamp)).fetchall()
        c.execute('''DELETE * FROM info_db WHERE time_<=?;''',(timestamp))
        return out

# very silly & inefficient for large tables. returns size of table.
def check_size():
    with sqlite3.connect(info_db) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text, thumnbnail text);""")
        return len(c.execute('''SELECT length FROM info_db;''').fetchall())

# should this function even exist? feels dangerous
def clear_db():
    with sqlite3.connect(info_db) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text, thumnbnail text);""")
        c.execute('''DELETE * FROM info_db;''')
