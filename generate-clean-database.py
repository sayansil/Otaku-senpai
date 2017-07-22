import pandas as pd
import os

DATA_FILE = "./DATABASE/anime.csv"
NEW_DATA_FILE = "./DATABASE/anime_cleaned.tsv"

def clean_by_id(df):
    ids = df.iloc[:,0]
    drops=[]

    for i in range(len(ids)):
        if not str(ids[i]).isdigit():
            drops.append(i)

    df = df.drop( df.index[ drops ] )
    return df

def clean_by_rating(df):
    rates = df.iloc[:,-1]
    drops=[]

    for i in range(len(rates)):
        if not isinstance( rates[i], float ):
            drops.append(i)
        elif rates[i] < 0 or str(rates[i])=="nan":
            drops.append(i)
    df = df.drop( df.index[ drops ] )
    return df

def clean_genres(df):
    genres = df.iloc[:,2]

    drops=[]
    for i in range(len(genres)):
        if str(genres[i]) == "nan" or str(genres[i]) == "NaN":
            drops.append(i)

    df = df.drop( df.index[ drops ] )
    return df

def create_dataframe(datafile):
    df = pd.read_csv(datafile, encoding = 'utf8')
    remove = [3,4,6]
    df.drop( df.columns[remove], axis=1, inplace=True )

    df = clean_by_id(df)
    df = df.reset_index(drop=True)
    df = clean_by_rating(df)
    df = df.reset_index(drop=True)
    df = clean_genres(df)
    df = df.reset_index(drop=True)

    return df

def generate_database(df, datafile):
    df.to_csv(datafile, sep='\t', encoding='utf-8', index=False)
    print("Database created in " + datafile)

generate_database(create_dataframe(DATA_FILE), NEW_DATA_FILE)

