import os
from enum import Enum
from pprint import pprint
from itertools import product

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from sklearn.cluster.bicluster import SpectralCoclustering

from utils import load_saved_database

RATINGS_FILE = "./DATABASE/ratings_cleaned.tsv"
ANIME_FILE = "./DATABASE/anime_cleaned.tsv"
OUTPUT_DIR = "./ANALYSIS"

USER_KEY = 'user_id'
MAX_RATING = 10.0

def cluster_data(users, n_clusters, use_probability_correlation=False):
    training_data = probability_map(users)[1] if use_probability_correlation else correlate_data(users)
    clustered_model = SpectralCoclustering(n_clusters = n_clusters, random_state = 0)
    clustered_model.fit(training_data)
    feed = clustered_model.row_labels_

    genres = training_data.transpose()
    genres["Group"] = pd.Series(feed, index=genres.index)
    genres = genres.iloc[np.argsort(feed)]

    return genres

def cluster_output(data, n_clusters=2, use_probability_correlation=False):
    correlation_type = "Probability" if use_probability_correlation else "Standard"
    clustered_data = cluster_data(data, n_clusters=n_clusters, use_probability_correlation=use_probability_correlation)

    cluster_plot = correlate_data(clustered_data.iloc[:,:-1].transpose())
    plot_data(cluster_plot, "Coclustered Genres, {}  Correlation".format(correlation_type))

    cluster_to_genre = {group: list(clustered_data.loc[clustered_data.Group == group].index) for group in set(clustered_data.Group)}

    with open("{}/genre_clusters_{}.txt".format(OUTPUT_DIR, correlation_type.lower()), 'w') as genre_relations_output_file:
        pprint(cluster_to_genre, indent=4, stream=genre_relations_output_file)

def plot_data(corr_list, name, output_dir=OUTPUT_DIR, ticks=10):
    labelsY = list(corr_list)
    labelsX = labelsY[:]

    fig, ax = plt.subplots()
    fig.set_figheight(14)
    fig.set_figwidth(18)

    im = ax.pcolormesh(corr_list, cmap=None)
    minval, maxval = min(*corr_list.min(axis=1)), max(*corr_list.max(axis=1))
    print(minval, maxval)
    ticklabels = list(map(lambda x: round(x, ndigits=2), np.linspace(minval, maxval, num=ticks)))
    colorbar = fig.colorbar(im, ticks=ticklabels)

    ax.tick_params(labelsize = 10)

    ax.xaxis.set(ticks = np.arange(0.5, len(labelsX)), ticklabels = labelsX)
    ax.yaxis.set(ticks = np.arange(0.5, len(labelsY)), ticklabels = labelsY)

    plt.xticks(rotation = 90)
    plt.axis("tight")

    plt.title(name, fontsize = 30)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    plt.savefig("{}/{}.pdf".format(output_dir, name))

def correlate_data(data):
    return pd.DataFrame.corr(data.iloc[:, 1:])

class Baseline(Enum):
    MODE = 1
    MEDIAN = 2
    MEAN = 3
    HALF = 4

def probability_map(data, baseline=Baseline.MODE, weight=0.5, count_dislikes=False, complement=False):
    """
        Calculates a 2-dimensional probability distribution of the form:
        Given that users liked genre 'x', what is the probability they will like genre 'y'?

        Criterion for a user having liked a genre is whether the user has rated it more than some baseline value.

        We use the definition of conditional probability to quantify this:
        P(L_y|L_x) = P(L_y intersection L_x) / P(L_x) = n(L_y intersection L_x) / n(L_x),
        where 'n(A)' is the size of the set 'A'

        Parameters
        __________
        data : Pandas Dataframe
        baseline : A member of the Baseline enum
        weight : A real value between 0 and 1 determining the relative priority of rating to total users who rated a genre in grouping

        Returns
        _______
        A Pandas Dataframe holding a correlation matrix sorted in order of popularity
    """
    if not (0.0 <= weight <= 1.0):
        raise ValueError("'weight' should be between 0 and 1")
    df = data.set_index('user_id')
    genres = list(df)
    genre_count = len(genres)

    def users_who_liked_or_disliked(a, b, dislikes):
        items = df[a][df[a] < genre_info[b][0]].index if dislikes else df[a][df[a] >= genre_info[b][0]].index 
        return frozenset(items)

    def users_who_rated(a):
        return len(df[a][df[a] > 0.0])

    baselines = {
        Baseline.MODE: lambda genre: df[genre][df[genre] > 0.0].mode()[0],
        Baseline.MEAN: lambda genre: df[genre].mean(),
        Baseline.MEDIAN: lambda genre: df[genre].median(),
        Baseline.HALF: lambda ignored: MAX_RATING / 2
    }

    def calc_baseline(genre):
        return baselines[baseline](genre), users_who_rated(genre)

    genre_info = {genre: calc_baseline(genre) for genre in genres}

    matrix_dimensions = (genre_count, genre_count)

    correlation_matrix = np.zeros(matrix_dimensions)
    complementation_matrix = np.ones(matrix_dimensions)

    def score_genre(genre):
        return (weight * genre_info[genre][0]) + ((1.0 - weight) * genre_info[genre][1])

    ordered_genres = list(sorted(genres, key=score_genre, reverse=True))
    genres_with_indices = list(enumerate(ordered_genres))

    for i, genre_a in genres_with_indices:
        users_who_liked_a = users_who_liked_or_disliked(genre_a, genre_a, count_dislikes)
        num_users_who_liked_a = len(users_who_liked_a)
        for j, genre_b in genres_with_indices:
            correlation_matrix[i][j] = len(users_who_liked_or_disliked(genre_b, genre_b, count_dislikes) & users_who_liked_a) / num_users_who_liked_a

    final_matrix = complementation_matrix - correlation_matrix if complement else correlation_matrix

    def like_or_dislike(dislike):
        return "Disike" if dislike else "Like"
    label_text = "{} given {}".format(like_or_dislike(complement), like_or_dislike(count_dislikes))

    return (label_text, pd.DataFrame(np.matrix(final_matrix), columns=ordered_genres, index=ordered_genres))

def all_probability_maps(data, baseline=Baseline.MODE, weight=0.5):
    for count_dislikes, complement in product((False, True), repeat=2):
        yield probability_map(data, baseline=baseline, weight=weight, count_dislikes=count_dislikes, complement=complement)

def analyse_saved_data(df_file):
    data = load_saved_database(df_file, preserve_anime_data=False)

    correlation_plot = correlate_data(data)
    plot_data(correlation_plot,"Standard Correlated Genres")
    print("Standard Correlation plot generated")

    for label, probability_plot in all_probability_maps(data):
        plot_data(probability_plot, "Probability Correlated Genres - " + label)
    print("Probability Correlation plots generated")

    cluster_output(data, use_probability_correlation=False)
    cluster_output(data, use_probability_correlation=True)
    print("Coclustering plots generated")

if __name__ == "__main__":
    analyse_saved_data(RATINGS_FILE)