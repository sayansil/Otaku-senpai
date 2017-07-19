import pandas as pd
import os
from zipfile import ZipFile
import json

ZIP_FILE = "anime-recommendations-database"
DATA_FILE = "rating.csv"
NEW_DATA_FILE = "rating_cleaned.json"
DIR = "DATABASE"


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
    
    for i in range( len(df) ):
        percent = int((i/len(df))*10000)/100
        print(str(percent) + "% done")
        
        r = int(df.loc[i, "rating"])
        u = str(df.loc[i,"user_id"])
        a = str(df.loc[i,"anime_id"])
        
        if r != -1:
            if u not in data:
                data[u] = {}
            data[u][a] = r
            
    print("100% done")
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
