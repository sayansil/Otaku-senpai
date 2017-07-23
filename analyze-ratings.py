import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from sklearn.cluster.bicluster import SpectralCoclustering
from utils import genres_tuple, csv_to_dataframe_parsing_lists, load_saved_database

RATINGS_FILE = "./DATABASE/ratings_cleaned.tsv"
ANIME_FILE = "./DATABASE/anime_cleaned.tsv"
OUTPUT_DIR = "./ANALYSIS"


def cocluster_data(data, n_clusters = 5):
    users = data.df
    matrix = users.iloc[:, 1:]

    clustered_model = SpectralCoclustering(n_clusters = n_clusters, random_state = 0)
    clustered_model.fit(pd.DataFrame.corr(matrix))

    feed = clustered_model.row_labels_

    users = matrix.transpose()

    users.Group = pd.Series(feed, index = users.index)
    users = users.iloc[np.argsort(feed)]
    users = users.reset_index(drop = True)

    matrix = users.iloc[:, :-1].transpose()
    genres = genres_tuple(csv_to_dataframe_parsing_lists(ANIME_FILE))
    matrix.columns = genres

    return pd.DataFrame.corr(matrix)


def plot_correlation(corr_list, name, output_dir = OUTPUT_DIR):
    labelsY = corr_list.index
    labelsX = labelsY[:]

    fig, ax = plt.subplots()
    fig.set_figheight(14)
    fig.set_figwidth(18)

    im = ax.pcolor(corr_list)
    fig.colorbar(im)

    ax.tick_params(labelsize = 10)

    ax.xaxis.set(ticks = np.arange(0.5, len(labelsX)), ticklabels = labelsX)
    ax.yaxis.set(ticks = np.arange(0.5, len(labelsY)), ticklabels = labelsY)

    plt.xticks(rotation = 90)
    plt.axis("tight")

    plt.title("Correlation in anime genres: {}".format(name), fontsize = 30)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    plt.savefig("{}/{}.pdf".format(output_dir, name))

def correlate_data(data):
    return pd.DataFrame.corr(data.df.iloc[:, 1:])

def analyse_saved_data(df_file):
    df = load_saved_database(df_file, preserve_anime_data = False)
    c1 = correlate_data(df)
    plot_correlation(c1,"correlated-genres")
    c2 = cocluster_data(df, n_clusters=2)
    plot_correlation(c2,"coclustered-genres")

analyse_saved_data(RATINGS_FILE)