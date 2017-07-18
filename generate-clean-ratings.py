import pandas as pd
from zipfile import ZipFile
import os

ZIP_FILE = "anime-recommendations-database"
DATA_FILE = "rating.csv"
NEW_DATA_FILE = "rating_cleaned.csv"


def clean_unrated(df):
    drops=[]
    
    for i in range( len(df) ):
        percent = int((i/len(df))*10000)/100
        print(str(percent) + "% done")
        if df.loc[i][2] == -1:
            drops.append(i)
    
    print("100% done")
    df = df.drop( df.index[ drops ] )
    return df

def clean_traces(datafiles):
    for datafile in datafiles:
        os.remove(datafile, dir_fd=None)

def open_zip(zipfile, datafile):
    zipfile = '{0}.zip'.format(zipfile)
    print("Extracting " + zipfile)
    with ZipFile(zipfile, 'r') as myzip:
        myzip.extract(datafile)

def generate_rated_database(df, datafile):
    df.to_csv(datafile, encoding='utf-8', index=False)
    print("Database created in " + datafile)

def create_rated_dataframe(datafile):
    df = pd.read_csv(datafile, encoding = 'utf8')
    
    df = clean_unrated(df)
    df = df.reset_index(drop=True)

    return df


open_zip(ZIP_FILE, DATA_FILE)
df = create_rated_dataframe(DATA_FILE)
generate_rated_database(df, NEW_DATA_FILE)
clean_traces([DATA_FILE])