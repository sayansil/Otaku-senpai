import pandas as pd
import os
from zipfile import ZipFile
import json
import re

ZIP_FILE = "anime-recommendations-database"
DATA_FILE = "rating.csv"
ANIME_FILE = "anime_cleaned.csv"
NEW_DATA_FILE = "rating_cleaned2.json"
DIR = "DATABASE"
CSV_SPLITTER = re.compile(",\s*")


def open_zip(zipfile, datafile):
    zipfile = '{0}.zip'.format(zipfile)
    print("Extracting " + zipfile)
    with ZipFile(zipfile, 'r') as myzip:
        myzip.extract(datafile)

def create_rated_database(datafile):
    df = pd.read_csv(datafile, encoding = 'utf8')
    
    df = clean_database(df)
    return df


def clean_database(df):
    
    data = {}
    
    af=pd.read_csv(DIR+"/"+ANIME_FILE, encoding="utf8")
    
    a_to_g = dict( zip( af.anime_id , af.genre ) )
    percentizer, index = 100/len(df), 0
    
    for r, u, a in zip( df.rating, df.user_id, df.anime_id ):        
        if a not in a_to_g:
            print(str(a) + " not in known")
            continue
        g = a_to_g[a]
        
        u = str(u)
        r = int(r)
        
        if r != -1:
            if u not in data:
                data[u] = {}
            aKey = str(a)
            data[u][aKey] = {}
            data[u][aKey]["genre"] = CSV_SPLITTER.split(g.strip())
            data[u][aKey]["rating"] = r
            
        percent = index*percentizer
        index += 1
        print("{:05.2f}% done".format(percent))    
    
    return data

def generate_rated_database(df, datafile, dirc):
    if not os.path.exists(dirc):
        os.makedirs(dirc)
        
    datafile = dirc + "\\" + datafile
    
    fp= open(datafile, "w")
    json.dump(df, fp, indent=4)
    fp.close()
    print("Database created in " + datafile)

def clean_traces(datafiles):
    for datafile in datafiles:
        os.remove(datafile, dir_fd=None)


open_zip(ZIP_FILE, DATA_FILE)
df = create_rated_database(DATA_FILE)
generate_rated_database(df, NEW_DATA_FILE, DIR)
clean_traces([DATA_FILE])
