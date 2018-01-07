import pandas as pd
import difflib
import sys
#import random
import itertools
from operator import itemgetter
from utils import split_csv, uprint, csv_to_dataframe_parsing_lists, genres_tuple, load_saved_database

DATA_FILE = "DATABASE/anime_cleaned.tsv"
USER_DATA_FILE = "DATABASE/ratings_cleaned.tsv"

ANIME_KEY = 'anime_id'
RATING_KEY = 'rating'
GENRE_KEY = 'genre'
NAME_KEY = 'name'

#RESULTS_HEADER = '--results='
#FILTER_HEADER = '--genres='
#RECOMMENDATION_HEADER = '--all'

class AnimeByGenre(object):
    def __init__(self, data_file, user_data_file):
        self.raw_data = csv_to_dataframe_parsing_lists(data_file)
        self.user_data = load_saved_database(user_data_file).set_index('user_id')
        self.known_user_ids = frozenset(self.user_data.index.values)
        self.genres = self.user_data.dtypes.index[1:-1]
        self.anime_data_indexed = self.raw_data.set_index(ANIME_KEY)
        self.all_animes = [x[0] for x in self.anime_data_indexed.loc[:, [NAME_KEY]].values.tolist()]

    def get_genres(self, anime_id):
        return set(self.anime_data_indexed.loc[[int(anime_id)], [GENRE_KEY]].values[0][0])

    def get_name(self, anime_id):
        return self.anime_data_indexed.loc[[int(anime_id)], [NAME_KEY]].values[0][0]

    def get_rating(self, anime_id):
        return self.anime_data_indexed.loc[[int(anime_id)], [RATING_KEY]].values[0][0]

    def get_id(self, anime_name):
        return self.anime_data_indexed[self.anime_data_indexed[NAME_KEY] == anime_name].index[0]

    def prepare_result(self, filtered, as_dataframe):
        if not filtered:
            return None
        elif as_dataframe:
            return pd.DataFrame.from_records(filtered, index=ANIME_KEY)
        else:
            return filtered

    def containing_genre(self, genre, as_dataframe=True):
        genre = frozenset(map(str.lower, genre))
        records = self.raw_data.to_dict(orient='records')
        grouped = sorted([(item, len(genre.intersection(map(str.lower, item[GENRE_KEY])))) for item in records], key=itemgetter(1), reverse=True)
        filtered = [item for item, matches in grouped if matches > 0]
        return self.prepare_result(filtered, as_dataframe)

    def suggested_anime_by_anime(self, anime_ids, as_dataframe=True):
        anime_ids = list(map(int, anime_ids))
        all_genres = set().union(*map(self.get_genres, anime_ids))
        data = self.containing_genre(all_genres, as_dataframe=False)
        filtered = [item for item in data if item[ANIME_KEY] not in anime_ids]
        return self.prepare_result(filtered, as_dataframe), all_genres

    def find_by_anime(self, anime_names, results_to_display=-1, output_file=sys.stdout):
        anime_options = [(item, difflib.get_close_matches(item, self.all_animes)) for item in anime_names]
        anime_names = (item for item, options in anime_options if item in options)
        for anime, options in anime_options:
            if anime not in options:
                if len(options) > 0:
                    print("You might have wanted any of the following:\n", file = output_file)
                    for option in options:
                        print(option, file = output_file)
                else:
                    print("Anime of name '{}' not found!\n\n".format(anime))
        results, genres = self.suggested_anime_by_anime(map(self.get_id, anime_names))
        print("Genres considered: {}".format(str(genres)), file=output_file)
        results_exist, results = self.crop_results(results, results_to_display)
        uprint(self.format_results(results) if results_exist else "No anime found matching all genres provided.", file=output_file)

    def user_watched_anime_ids(self, user_id):
        return set(self.user_data.loc[[user_id], [self.user_data.dtypes.index[-1]]].values[0][0])

    def animes_watched_by_user(self, user_ids):
        return dict(((user_id, self.anime_data_indexed.loc[list(map(int, self.user_watched_anime_ids(user_id)))]) for user_id in user_ids))

    def suggested_anime_by_user(self, user_ids, genres_to_consider, filter_seen=True, as_dataframe=True):
        genre_id_lookup = dict(enumerate(genres_tuple(self.raw_data)))

        if genres_to_consider <= 0 or genres_to_consider > len(genre_id_lookup):
            raise ValueError("Genres to consider must be integer in range 1 to {}".format(len(genre_id_lookup)))

        user_ids = self.known_user_ids & user_ids

        if not user_ids:
            return None, []

        def user_recommendations(user_id):
            user_genre_rating_info = self.user_data.loc[[user_id], self.genres].values[0]
            user_anime_info = self.user_watched_anime_ids(user_id)
            genre_list = []
            rated = 0
            for genre_id, rating in enumerate(user_genre_rating_info):
                if rating > 0.0:
                    rated += 1
                    genre_list.append((genre_id_lookup[genre_id], rating))

            user_watched_anime_genres = list(map(self.get_genres, user_anime_info))

            def similarity(anime_id):
                specific_genres = self.get_genres(anime_id)
                return sum([len(specific_genres & known) for known in user_watched_anime_genres])

            def already_seen(anime_id):
                return str(anime_id) in user_anime_info

            genres = frozenset([x[0].lower() for x in sorted(genre_list, key=itemgetter(1), reverse=True)][:min(genres_to_consider, rated)])
            user_recommendations = self.containing_genre(genres, as_dataframe=False)
            if user_recommendations is None:
                user_recommendations = []
            user_recommendations.sort(key=lambda item: similarity(item[ANIME_KEY]) , reverse=True)
            return genres, [item for item in user_recommendations if not (filter_seen and already_seen(item[ANIME_KEY]))]

        already_recommended_ids = set()
        raw_genres, raw_recommendations = zip(*map(user_recommendations, user_ids))
        new_recommendations = []
        all_genres = set().union(*raw_genres)
        for recommendation in itertools.chain(*raw_recommendations):
            if recommendation[ANIME_KEY] not in already_recommended_ids:
                already_recommended_ids.add(recommendation[ANIME_KEY])
                new_recommendations.append(recommendation)

        return (self.prepare_result(new_recommendations, as_dataframe), all_genres)

    def format_anime(self, anime_df):
        return map(lambda anime: (self.get_name(anime), self.get_rating(anime), self.get_genres(anime)), anime_df.index.values)

    def format_results(self, anime_df):
        return  NAME_KEY+", "+RATING_KEY+", "+GENRE_KEY+":\n" + "\n".join(("{}, {}, {}".format(name, rating, genre) for name, rating, genre in self.format_anime(anime_df)))

    def crop_results(self, results, results_to_display):
        results_exist = not (results is None or len(results) == 0 or (isinstance(results, pd.DataFrame) and results.empty))
        if results_exist and (0 <= results_to_display < len(results.index)):
            return results_exist, results.head(results_to_display)
        else:
            return results_exist, results

    def find_by_user(self, user_ids, genres_to_consider = 2, filter_seen = True, results_to_display = -1, output_file = sys.stdout):
        user_ids = frozenset(map(int, (split_csv(user_ids) if ',' in user_ids else [user_ids]) if isinstance(user_ids, str) else user_ids))
        results, genres = self.suggested_anime_by_user(user_ids, genres_to_consider, filter_seen = filter_seen)
        results_exist = not (results is None or results.empty)
        if results_exist and (0 <= results_to_display < len(results.index)):
            results = results.head(results_to_display)
        print("Genres considered: {}".format(str(genres)))
        print("New anime recommendations based on users with IDs {}:".format(str(list(user_ids))))
        uprint(self.format_results(results) if results_exist else "No new anime recommendations possible for user.", file=output_file)

    def find_by_genre(self, genre, results_to_display = -1, output_file = sys.stdout):
        genres = genres_tuple(self.raw_data)
        normalized_genres = list(map(lambda x: x.strip().lower(), genres))

        genre = frozenset((x.strip().lower() for x in ((split_csv(genre) if ',' in genre else [genre]) if isinstance(genre, str) else genre)))
        genre_options = [(item, difflib.get_close_matches(item, normalized_genres)) for item in genre]

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
            results_exist, results = self.crop_results(self.containing_genre(genre), results_to_display)
            uprint(self.format_results(results) if results_exist else "No anime found matching all genres provided.", file=output_file)

suggestor = AnimeByGenre(DATA_FILE, USER_DATA_FILE)

# Remove script code below as it has become too complicated - use in interactive mode via `suggestor`

#def main(argv):
#    results = -1
#    if len(argv) > 1 and argv[1].startswith(RESULTS_HEADER):
#        results = int(argv[1][len(RESULTS_HEADER): ])
#        del argv[1]
#    suggestor = AnimeByGenre(DATA_FILE)
#    if argv[0].lower() == '--genre':
#        suggestor.find_by_genre(input("Enter genre(s) to find anime for: ") if len(argv) < 2 else ",".join(argv[1:]), results_to_display = results)
#    elif argv[0].lower() == '--user':
#        genres = 2
#        filter_seen = True
#        if RECOMMENDATION_HEADER in argv:
#            filter_seen = False
#            argv.remove(RECOMMENDATION_HEADER)
#        if len(argv) > 1 and argv[1].startswith(FILTER_HEADER):
#            genres = int(argv[1][len(FILTER_HEADER): ])
#            del argv[1]
#        suggestor.find_by_user(input("Enter user ID to find anime for: ") if len(argv) < 2 else ",".join(argv[1:]), results_to_display = results, genres_to_consider = genres, filter_seen = filter_seen)
#    else:
#        print("Invalid mode, use either '--genre' to search by genre or '--user' to search by user.")
#
#if __name__ == "__main__":
#    if len(sys.argv) > 2:
#        main(sys.argv[1:])
#    else:
#        # Note: The limits on the random numbers mean:
#        # 69600 - the number of users in the database,
#        # 500 - to keep the query a manageable size
#        users = map(str, random.sample(range(69600), random.randint(1, 69600//500)))
#        # Note: The order is important! (I should probably be using argparse here, but I'm lazy)
#        main(["--user", "--results=5", "--genres=4", "1"])#",".join(users)])