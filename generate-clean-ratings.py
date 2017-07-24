import sys
import os
import itertools
import time
from utils import split_csv, genres_tuple, csv_to_dataframe_parsing_lists

LOOKUP_FILE = "./DATABASE/anime_cleaned.tsv"
DATA_FILE = "./DATABASE/ratings.csv"

USER_KEY = 'user_id'
INFO_KEY = 'genre_ratings'
COUNT_KEY = 'genre_ratings_count'
ANIME_KEY = 'animes_rated'

class Ratings(object):
    def __init__(self, data_file, id_lookup_file):
        self.data_file = data_file
        self.lines_processed = 0
        self.users_processed = 0
        raw_lookup = csv_to_dataframe_parsing_lists(id_lookup_file)
        self.genres = genres_tuple(raw_lookup)
        genre_index = dict(zip(self.genres, range(len(self.genres))))
        self.id_lookup = dict(zip(raw_lookup.anime_id, map(lambda genres: list(map(lambda genre: genre_index[genre], genres)), raw_lookup.genre)))

    def intialize_user_data(self, key):
        user = {USER_KEY: key}
        user[INFO_KEY] = []
        user[COUNT_KEY] = []
        user[ANIME_KEY] = []
        for genre_id in range(len(self.genres)):
            user[INFO_KEY].append(None)
            user[COUNT_KEY].append(0)
        return user


    def normalize(dataframe, index = USER_KEY):
        return dataframe.set_index(index)

    def finalize_user(user):
        final_user = {USER_KEY: user[USER_KEY], ANIME_KEY: user[ANIME_KEY]}
        final_user[INFO_KEY] = list(map(lambda x: 0.0 if x is None else round(x, 2) , user[INFO_KEY]))
        return final_user

    def stream_data(self):
        with open(self.data_file, 'r') as raw_data:
            for line in raw_data.readlines():
                self.lines_processed += 1
                if self.lines_processed == 1:
                    continue
                else:
                    yield tuple(map(lambda x: int(x), split_csv(line.strip())))

    def remove_unrated_entries(self):
        for datum in self.stream_data():
            # Rating is field# 2
            if datum[2] >= 0:
                yield datum

    def pack_by_user(self):
        return itertools.groupby(self.remove_unrated_entries(), key = lambda x: x[0])

    def process_user_info(self):
        for key, user_info in self.pack_by_user():
            user_data = self.intialize_user_data(key)
            for user_id, anime_id, rating in user_info:
                print("{:d} entries processed".format(self.lines_processed))
                # Avoid edge cases at the boundary between cleaned and raw data
                if anime_id in self.id_lookup:
                    user_data[ANIME_KEY].append(anime_id)
                    genre_ids = self.id_lookup[anime_id]

                    for genre_id in genre_ids:
                        genre_rated_count = user_data[COUNT_KEY][genre_id]
                        # Cumulative Moving Average
                        if user_data[INFO_KEY][genre_id] is None:
                            user_data[INFO_KEY][genre_id] = rating
                        else:
                            user_data[INFO_KEY][genre_id] = (rating + (genre_rated_count * user_data[INFO_KEY][genre_id])) / (genre_rated_count + 1)
                        user_data[COUNT_KEY][genre_id] += 1

            self.users_processed += 1
            print("{:d} users processed".format(self.users_processed))

            yield Ratings.finalize_user(user_data)

    def format_for_csv(prefix, data, suffix):
        return "\t".join(map(str, [prefix] + data + [suffix]))

    def format_user_data_for_csv(user_data):
        return Ratings.format_for_csv(user_data[USER_KEY], user_data[INFO_KEY], user_data[ANIME_KEY])

    def pack_results(self, output_file_path = 'ratings_cleaned.tsv'):
        with open(output_file_path, 'w') as output_file:
            output_file.write(Ratings.format_for_csv(USER_KEY, list(self.genres), ANIME_KEY) + "\n")
            output_file.writelines(map(lambda item: Ratings.format_user_data_for_csv(item) + "\n", self.process_user_info()))
        print("Entries processed = {:d}, Users processed = {:d}".format(self.lines_processed - 1, self.users_processed))

def main(argv):
    start_time = time.time()
    Ratings(DATA_FILE, LOOKUP_FILE).pack_results()
    print("{:d} seconds taken for processing".format(int(time.time() - start_time)))

if __name__ == "__main__":
    main(sys.argv)