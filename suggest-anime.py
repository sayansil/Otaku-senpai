import pandas as pd
import difflib
import sys
import random
import itertools
from operator import itemgetter
from utils import split_csv, uprint, csv_to_dataframe_parsing_lists, genres_tuple, load_saved_database

DATA_FILE = "./DATABASE/anime_cleaned.tsv"
USER_DATA_FILE = "./DATABASE/ratings_cleaned.tsv"

ANIME_KEY = 'anime_id'
RATING_KEY = 'rating'

RESULTS_HEADER = '--results='
FILTER_HEADER = '--genres='

class AnimeByGenre(object):
    def __init__(self, data_file):
        self.raw_data = csv_to_dataframe_parsing_lists(data_file)

    def containing_genre(self, genre, as_dataframe = True):
        filtered = list(filter(lambda item: genre < set(map(lambda x: x.lower(), item['genre'])), self.raw_data.to_dict(orient = 'records')))
        if not filtered:
            return None
        elif as_dataframe:
            return pd.DataFrame.from_records(filtered, index = ANIME_KEY).sort_values(by = RATING_KEY, ascending = False)
        else:
            return filtered

    def suggested_anime_by_user(self, user_ids, user_data_file, genres_to_consider, as_dataframe = True):
        genre_id_lookup = dict(enumerate(genres_tuple(self.raw_data)))

        if (not isinstance(genres_to_consider, int)) or (genres_to_consider <= 0 or genres_to_consider >= len(genre_id_lookup)):
            raise ValueError("Genres to consider must be integer in range")

        user_data = load_saved_database(user_data_file).df.set_index('user_id')
        known_user_ids = frozenset(user_data.index.values)

        user_ids = known_user_ids.intersection(frozenset(map(int, user_ids)))

        if not user_ids:
            return None, []

        def user_recommendations(user_id):
            user_genre_rating_info = user_data.loc[[user_id], list(user_data.dtypes.index)[1 : -1]].values.tolist()[0]
            user_anime_info = frozenset(user_data.loc[[user_id], [list(user_data.dtypes.index)[-1]]].values.tolist()[0][0])

            genre_list = []
            rated = 0
            for genre_id, rating in enumerate(user_genre_rating_info):
                if rating > 0.0:
                    rated += 1
                    genre_list.append((genre_id_lookup[genre_id], rating))

            genres = frozenset(list(map(lambda x: x[0].lower(), sorted(genre_list, key = itemgetter(1), reverse = True)))[ : min(genres_to_consider, rated)])
            user_recommendations = self.containing_genre(genres, as_dataframe = False)
            if user_recommendations is None:
                user_recommendations = []
            return genres, filter(lambda item: item[ANIME_KEY] not in user_anime_info, user_recommendations)

        already_recommended_ids = set()
        raw_genres, raw_recommendations = zip(*map(user_recommendations, user_ids))
        new_recommendations = []
        all_genres = set().union(*raw_genres)
        for recommendation in itertools.chain(*raw_recommendations):
            if recommendation[ANIME_KEY] not in already_recommended_ids:
                already_recommended_ids.add(recommendation[ANIME_KEY])
                new_recommendations.append(recommendation)

        if not new_recommendations:
            return None, all_genres
        elif as_dataframe:
            return pd.DataFrame.from_records(new_recommendations, index = ANIME_KEY).sort_values(by = RATING_KEY, ascending = False), all_genres
        else:
            return new_recommendations, all_genres

    def find_by_user(self, user_ids, user_data_file = USER_DATA_FILE, genres_to_consider = 2, results_to_display = -1, output_file = sys.stdout):
        user_ids = split_csv(user_ids) if ',' in user_ids else [user_ids]
        results, genres = self.suggested_anime_by_user(user_ids, user_data_file, genres_to_consider)
        results_exist = not (results is None or results.empty)
        if results_exist and (0 <= results_to_display < len(results.index)):
            results = results.head(results_to_display)
        print("Genres considered: {}".format(str(genres)))
        print("New anime recommendations based on users with IDs {}:".format(str(user_ids)))
        uprint(results.to_csv() if results_exist else "No new anime recommendations possible for user.", file = output_file)

    def find_by_genre(self, genre, results_to_display = -1, output_file = sys.stdout):
        genres = genres_tuple(self.raw_data)
        normalized_genres = list(map(lambda x: x.strip().lower(), genres))

        genre = genre.strip().lower()
        genre = frozenset(split_csv(genre) if ',' in genre else [genre])
        genre_options = list(map(lambda item: (item, difflib.get_close_matches(item, normalized_genres)), genre))

        entry_error, gross_error = False, False
        for specific_genre, specific_options in genre_options:
            if specific_genre not in specific_options:
                if len(specific_options) > 0:
                    print("You might have wanted any of the following:\n", file = output_file)
                    for specific_option in specific_options:
                        print(specific_option, file = output_file)
                else:
                    print("Genre not found\n\n", file = output_file)
                    gross_error = True
                entry_error = True

        if gross_error:
            print("Complete List of All Genres", file = output_file)
            for specific_genre in genres:
                print(specific_genre, file = output_file)

        if not entry_error:
            results = self.containing_genre(genre)
            results_exist = not (results is None or results.empty)
            if results_exist and (0 <= results_to_display < len(results.index)):
                results = results.head(results_to_display)
            uprint(results.to_csv() if results_exist else "No anime found matching all genres provided.", file = output_file)

def main(argv):
    results = -1
    if len(argv) > 1 and argv[1].startswith(RESULTS_HEADER):
        results = int(argv[1][len(RESULTS_HEADER): ])
        del argv[1]
    suggestor = AnimeByGenre(DATA_FILE)
    if argv[0].lower() == '--genre':
        suggestor.find_by_genre(input("Enter genre(s) to find anime for: ") if len(argv) < 2 else ",".join(argv[1:]), results_to_display = results)
    elif argv[0].lower() == '--user':
        genres = 2
        if len(argv) > 1 and argv[1].startswith(FILTER_HEADER):
            genres = int(argv[1][len(FILTER_HEADER): ])
            del argv[1]
        suggestor.find_by_user(input("Enter user ID to find anime for: ") if len(argv) < 2 else ",".join(argv[1:]), results_to_display = results, genres_to_consider = genres)
    else:
        print("Invalid mode, use either '--genre' to search by genre or '--user' to search by user.")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        main(sys.argv[1:])
    else:
        users = map(str, random.sample(range(69600), random.randint(1, 69600//500)))
        main(["--user", "--results=15", "--genres=4", ",".join(users)])