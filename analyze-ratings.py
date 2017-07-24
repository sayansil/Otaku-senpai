import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from sklearn.cluster.bicluster import SpectralCoclustering
from enum import Enum
from utils import load_saved_database

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
    matrix = users.iloc[:, :-1].transpose()
    return pd.DataFrame.corr(matrix)

def plot_correlation(corr_list, name, output_dir = OUTPUT_DIR):
    labelsY = list(corr_list)
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

class Baseline(Enum):
    MODE = 1
    MEDIAN = 2
    MEAN = 3

def manual_correlate(data, baseline=Baseline.MODE):
    df = data.set_index('user_id')
    genres = list(df)[1:]
    genre_count = len(genres)

    def calc_baseline(key):
        if baseline is Baseline.MODE:
            return df[key][df[key] > 0.0].mode()[0]
        elif baseline is Baseline.MEAN:
            return df[key].mean()
        elif baseline is Baseline.MEDIAN:
            return df[key].median()
        else:
            raise ValueError("'baseline' must be one of 'mean', median' or 'mode'")

    genre_info = {genre: calc_baseline(genre) for genre in genres}

    def count_users(a, b):
        return len(df[a][df[a] >= genre_info[b]])

    def rated_users(a):
        return len(df[a][df[a] > 0.0])

    corr_matrix = np.zeros((genre_count, genre_count))

    ordered_genres = list(sorted(genres, key=lambda x: genre_info[x], reverse=True))
    genres_with_indices = list(enumerate(ordered_genres))
    with open('log2.txt', 'w+') as log:
        for i, a in genres_with_indices:
            for j, b in genres_with_indices:
                p_a = count_users(a, a) / rated_users(a)
                p_b_a = count_users(b, a) / rated_users(b)
                # Probability can be maximally 1
                p_b_given_a = min(1.0, p_b_a / p_a)
                print("{}, {} -> {}, {} = {}/{} = {}".format(i, j, a, b, p_b_a, p_a, p_b_given_a), file=log)
                corr_matrix[i][j] = p_b_given_a

    return pd.DataFrame(np.matrix(corr_matrix), columns=ordered_genres)

def analyse_saved_data(df_file):
    df = load_saved_database(df_file, preserve_anime_data=False)
#    c1 = correlate_data(df)
#    plot_correlation(c1,"correlated-genres")
#    c2 = cocluster_data(df, n_clusters=2)
#    plot_correlation(c2,"coclustered-genres")
    c3 = manual_correlate(df)
    c3.to_csv("log.txt",index=False)
    plot_correlation(c3,"manual-correlated-genres")

analyse_saved_data(RATINGS_FILE)