import re
import sys
import pandas
import numpy

CSV_SEP = re.compile(",\s*")
ANIME_KEY = 'animes_rated'


def split_csv(csv_str):
    return CSV_SEP.split(csv_str.strip())

def uprint(*objects, sep = ' ', end = '\n', file = sys.stdout):
    enc = file.encoding
    if enc.lower() == 'utf-8':
        print(*objects, sep = sep, end = end, file = file)
    else:
        def escape(obj):
            return str(obj).encode(enc, errors = 'backslashreplace').decode(enc)
        print(*map(escape, objects), sep = sep, end = end, file = file)

def csv_to_dataframe(csv_file, sep = "\t", comment = None, keys_to_drop = None):
    data = pandas.read_csv(csv_file, encoding = 'utf8', sep = sep, comment = comment)
    if keys_to_drop:
        return data.drop(keys_to_drop, axis = 1, errors = 'ignore')
    else:
        return data

def csv_to_dataframe_parsing_lists(csv_file, sep = "\t", comment = None, key = 'genre', drop_enclosing = False, keys_to_drop = None):
    raw_lookup = csv_to_dataframe(csv_file, sep = sep, comment = comment, keys_to_drop = keys_to_drop)
    raw_lookup[key] = list(map(lambda item_list: split_csv(item_list[1:-1] if drop_enclosing else item_list), raw_lookup[key]))
    return raw_lookup

def load_saved_database(df, preserve_anime_data = True):
    if preserve_anime_data:
        return csv_to_dataframe_parsing_lists(df, key = ANIME_KEY, drop_enclosing = True)
    else:
        return csv_to_dataframe(df, sep = '\t', keys_to_drop = [ANIME_KEY])

def empty_dataframe_based_on(existing_dataframe):
    columns = existing_dataframe.dtypes.index
    return pandas.DataFrame(data = numpy.zeros((0, len(columns))), columns = columns)

def all_genres(data):
    yielded_genres = set()
    for genres in data.genre:
        for genre in genres:
            if genre not in yielded_genres:
                yielded_genres.add(genre)
                yield genre

def genres_tuple(data):
    return tuple(all_genres(data))