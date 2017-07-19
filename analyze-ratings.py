import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from time import strftime as stime
import os
from sklearn.cluster.bicluster import SpectralCoclustering


RATINGS_FILE = "rating_cleaned.json"
ANIME_FILE = "anime_cleaned.csv"
DIR = "DATABASE"
DATA_FILE = "ratings_database.csv"



def cocluster_data(users, n_clusters=5):
    matrix = users.iloc[:, 1:]
    corr_list = pd.DataFrame.corr( matrix )
    
    clustered_model = SpectralCoclustering(n_clusters = n_clusters, random_state=0)
    clustered_model.fit(corr_list)
    
    feed = clustered_model.row_labels_
    
    users = matrix.transpose()
    
    users["Group"] = pd.Series(feed, index=users.index)
    users = users.iloc[np.argsort( feed )]
    users = users.reset_index(drop=True)

    matrix = users.iloc[:, :-1].transpose()
    matrix.columns = all_genres(pd.read_csv(DIR+"\\"+ANIME_FILE, encoding="utf8"))
    corr_list = pd.DataFrame.corr( matrix ) 
    
    
    return corr_list


def plot_correlation(corr_list, name):
    labelsY = corr_list.index
    labelsX = []
    for label in labelsY:
        labelsX.append(label[0:6])
    
    fig, ax = plt.subplots()
    fig.set_figheight(14)
    fig.set_figwidth(18)
    
    im = ax.pcolor(corr_list)
    fig.colorbar(im)
    
    ax.tick_params(labelsize=10)

    ax.xaxis.set(ticks=np.arange(0.5, len(labelsX)), ticklabels=labelsX)
    ax.yaxis.set(ticks=np.arange(0.5, len(labelsY)), ticklabels=labelsY)
    
    plt.xticks(rotation=45)
    plt.axis("tight")

    plt.title("Correlation in anime genres", fontsize=30)
    
    if not os.path.exists("ANALYSIS"):
        os.makedirs("ANALYSIS")
    plt.savefig("ANALYSIS\\"+ name + stime("%d-%m-%Y_%H-%M-%S") + ".pdf")
    plt.show()
    

def correlate_data(df):
    matrix = df.iloc[:, 1:]
    corr_list = pd.DataFrame.corr( matrix )
    return corr_list
    

def create_dataframe(j_file, a_data):
    all_g = all_genres(a_data)
    cols = ["user"] + all_g
    df = pd.DataFrame(0, index=range( len(j_file) ), columns=cols)
    k=0
    for user in j_file:
        l = len(j_file)
        print( k , " out of " , l )
        df.loc[k,"user"] = int(user)
        
        times = dict( zip(all_g, [0]*len(all_g) ))
        
        for anime in j_file[user]:   
            genres = get_genre(a_data, anime)
            rating = j_file[user][anime]
            
            for genre in genres:
                times[genre] += 1
                df.loc[k, genre] += rating
        
        for genre in all_g:
            if(times[genre] != 0):
                val = df.loc[k,genre] / times[genre]
                df.loc[k,genre] = int(val*100)/100       
        k += 1
        
    return df
                

def get_genre(df, a_id):
    a_id=str(a_id)
    temp = (df.query("anime_id == "+a_id).genre)
    if len(temp) == 0:
        return []
    
    gs = df.loc[(temp.index[0]),"genre"].split(",")
    gs = list( map( lambda x:x.strip(), gs ) )
    return gs


def all_genres(df):
    gs = df.iloc[:, 2]
    genres = []
    
    for gl in gs:
        gl = gl.split(",")
        for i in range(len(gl)):
            gl[i] = gl[i].strip()
        genres = set( list(genres) + gl)
    return list(genres)


def create_database(afile, rfile, new_rfile, dirc):
    afile = dirc + "\\" + afile
    rfile = dirc + "\\" + rfile
    
    a_data = pd.read_csv(afile, encoding = 'utf8')
    print("anime data loaded.")
    with open(rfile) as data_file:    
        r_data = json.load(data_file)
        
    print("ratings data loaded.")

    r_data = create_dataframe(r_data, a_data)
    save_database(r_data, new_rfile, dirc)    
    
    
def save_database(df, datafile, dirc):
    if not os.path.exists(dirc):
        os.makedirs(dirc)
        
    datafile = dirc + "\\" + datafile
    
    df.to_csv(datafile, encoding='utf-8', index=False)
    print("Database created in " + datafile)

    
def load_saved_database(datafile, dirc):
    datafile = dirc + "\\" + datafile
    df = pd.read_csv(datafile, encoding="utf8")
    return df
    
    
def analyse_saved_data(df):
    c1 = correlate_data(df)
    plot_correlation(c1,"correlated-genres")
    c2 = cocluster_data(df, n_clusters=2)
    plot_correlation(c2,"coclustered-genres")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    