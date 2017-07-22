import re
import sys
import pandas
import numpy

CSV_SEP = re.compile(",\s*")


def split_csv(csv_str):
    return CSV_SEP.split(csv_str)

def uprint(*objects, sep = ' ', end = '\n', file = sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep = sep, end = end, file = file)
    else:
        def escape(obj):
            str(obj).encode(enc, errors = 'backslashreplace').decode(enc)
        print(*map(escape, objects), sep = sep, end = end, file = file)

def csv_to_dataframe_parsing_lists(csv_file, sep = "\t"):
        raw_lookup = pandas.read_csv(csv_file, encoding = 'utf8', sep = sep)
        raw_lookup.genre = list(map(lambda genres: split_csv(genres), raw_lookup.genre))
        return raw_lookup

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
