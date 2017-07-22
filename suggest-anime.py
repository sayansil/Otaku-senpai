import pandas as pd
import difflib
import sys
from utils import split_csv, uprint, csv_to_dataframe_parsing_lists, genres_tuple

DATA_FILE = "./DATABASE/anime_cleaned.tsv"

class AnimeByGenre(object):
    def __init__(self, data_file):
        self.raw_data = csv_to_dataframe_parsing_lists(data_file)

    def containing_genre(self, genre):
        genre_set = set(genre)
        filtered = list(filter(lambda item: genre_set < set(map(lambda x: x.lower(), item['genre'])), self.raw_data.to_dict(orient = 'records')))
        if not filtered:
            return None
        else:
            return pd.DataFrame.from_records(filtered, index = 'anime_id').sort_values(by = 'rating', ascending = False)

    def data(self):
        return self.raw_data.set_index('anime_id')

    def find_by_genre(self, genre, output_file = sys.stdout):
        genres = genres_tuple(self.raw_data)
        normalized_genres = list(map(lambda x: x.strip().lower(), genres))

        genre = genre.strip().lower()
        genre = split_csv(genre) if ',' in genre else [genre]
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
            uprint(results.to_csv() if results_exist else "No anime found matching all genres provided.", file = output_file)

def main(argv):
    AnimeByGenre(DATA_FILE).find_by_genre(input("Enter genre(s) to find anime for: ") if len(argv) < 2 else ",".join(argv[1:]))

if __name__ == "__main__":
    main(sys.argv)