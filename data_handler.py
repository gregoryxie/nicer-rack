"""
Creates SQLite3 server that stores (timestamp,title,length,link,filepath,thumbnail).
Allows for lookup, insertion, deletion, clearing.
Should not store songs longer than MAX_LENGTH
"""

import os
import sqlite3
import datetime

info_db = 'file_info.db'
MAX_LENGTH = 10 # maximum supported video length in minutes

def dto(dt_str):
    return datetime.datetime.strptime(dt_str,'%Y-%m-%d %H:%M:%S.%f')

# Necessary when accessing db, as current working directory changes between scripts
def get_db_path(db_file):
    wd = os.path.abspath(os.getcwd())
    path = wd.split("/nicer-rack",1)[0] + "/nicer-rack/nicer_rack_web/server/" + str(db_file)
    return path

# return true if put in database/already in database, false if cannot
# title string, length int (sec), link string, filepath string, thumbnail string
def insert_data(title, length, link, filepath, thumbnail=""):
    if length > 60 * MAX_LENGTH:
        return False
    if not retrieve_data(link):
        timestamp = datetime.datetime.now()
        with sqlite3.connect(get_db_path(info_db)) as c:
            c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text, thumbnail text);""")
            c.execute('''INSERT into info_db VALUES (?,?,?,?,?,?);''',(timestamp,title,length,link, filepath, thumbnail,))
    return True

# given link: return row data as tuple if exists, else None
def retrieve_data(link):
    with sqlite3.connect(get_db_path(info_db)) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text, thumnbnail text);""")
        current = c.execute('''SELECT * FROM info_db WHERE link=?;''',(link,)).fetchone()
    return current

# given text: return row data if matches artist/song, else None
def retrieve_songs(text):
    with sqlite3.connect(get_db_path(info_db)) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text, thumnbnail text);""")
        current = c.execute('''SELECT * FROM info_db WHERE title LIKE '%' || ? || '%';''',(text,)).fetchall()
    return current

# returns tuples of all rows in db
def retrieve_all_data():
    with sqlite3.connect(get_db_path(info_db)) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text, thumnbnail text);""")
        current = c.execute('''SELECT * FROM info_db;''').fetchall()
    return current

# given link: deletes row data, if exists. returns TUPLE of mp3 filepath of deleted entry.
def delete_data(link):
    with sqlite3.connect(get_db_path(info_db)) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text, thumnbnail text);""")
        out = c.execute('''SELECT filepath FROM info_db WHERE link=?;''',(link,)).fetchone()
        c.execute('''DELETE FROM info_db WHERE link=?;''',(link,))
        return out

# clear data entries older than timestamp given, if exists. returns TUPLE of mp3 filepaths of deleted entries.
def remove_old_data(timestamp):
    with sqlite3.connect(get_db_path(info_db)) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text, thumnbnail text);""")
        out = c.execute('''SELECT filepath FROM info_db WHERE time_<=?;''',(timestamp,)).fetchall()
        c.execute('''DELETE FROM info_db WHERE time_<=?;''',(timestamp,))
        return [x[0] for x in out]

# returns size of table as int
def check_size():
    with sqlite3.connect(get_db_path(info_db)) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text, thumnbnail text);""")
        return c.execute('''SELECT COUNT(*) FROM info_db;''').fetchone()[0]

# should this function even exist? feels dangerous
def clear_db():
    with sqlite3.connect(get_db_path(info_db)) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS info_db (time_ timestamp, title text, length real, link text, filepath text, thumnbnail text);""")
        c.execute('''DELETE FROM info_db;''')


if __name__ == "__main__":
    # TESTING ONLY
    chicken_attack = ("Chicken Attack", 237, "youtube.com/watch?v=miomuSGoPzI", "/audio_files/miomuSGoPzI", "")
    chicken_attack_remix = ("Chicken Attack Remix [official] (not cluckbait)", 170, "youtube.com/watch?v=h2pe01hEwUg", "/audio_files/h2pe01hEwUg")
    new_rules = ("New Rules", 224, "youtube.com/watch?v=k2qgadSvNyU", "/audio_files/k2qgadSvNyU", "")
    
    # insert, check size, retrieve data, delete data, check size again
    if insert_data(*chicken_attack):
        print("Current size after inserting: ",check_size())
    print(retrieve_data(chicken_attack[2]))
    print(delete_data(chicken_attack[2]))
    print("Size after adding and deleting: ",check_size())

    # insert 3 new entries, check size, insert duplicate, check size, delete entry, retrieve entry, retrieve non-existent entry
    insert_data(*chicken_attack)
    insert_data(*new_rules)
    insert_data(*chicken_attack_remix)
    print("Size after inserting 3 rows: ",check_size())
    insert_data(*chicken_attack)
    print("Size after inserting duplicate: ",check_size())
    print(delete_data(new_rules[2]))
    print(retrieve_data(chicken_attack[2]))
    print(retrieve_data(new_rules[2]))
    print(remove_old_data(datetime.datetime.now()))
    print("Size after removing all previous data: ", check_size())