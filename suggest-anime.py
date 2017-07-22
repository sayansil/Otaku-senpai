import pandas as pd
import difflib
import re
import sys

DATA_FILE = "./DATABASE/anime_cleaned.csv"
CSV_SEP = re.compile(",\s*")

def split_csv(csv_str):
    return CSV_SEP.split(csv_str)

def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)

class AnimeByGenre(object):
    def __init__(self, data_file):
        self.raw_data = pd.read_csv(data_file, encoding = 'utf8', sep = '~')
        self.raw_data.genre = list(map(lambda genres: split_csv(genres), self.raw_data.genre))

    def all_genres(self):
        yielded_genres = set()
        for genres in self.raw_data.genre:
            for genre in genres:
                if genre not in yielded_genres:
                    yielded_genres.add(genre)
                    yield genre


    def containing_genre(self, genre):
        genre_set = set(genre)
        filtered = list(filter(lambda item: genre_set < set(map(lambda x: x.lower(), item['genre'])), self.raw_data.to_dict(orient = 'records')))
        return pd.DataFrame.from_records(filtered, index='anime_id').sort_values(by = 'rating', ascending = False)


    def data(self):
        return self.raw_data.set_index('anime_id')


    def find_by_genre(self, genre, output_file = sys.stdout):
        genres = self.all_genres()
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
            uprint(self.containing_genre(genre).to_csv(), file = output_file)

def main(argv):
    AnimeByGenre(DATA_FILE).find_by_genre(input("Enter genre(s) to find anime for: ") if len(argv) < 2 else ",".join(argv[1:]))

if __name__ == "__main__":
    main(sys.argv)