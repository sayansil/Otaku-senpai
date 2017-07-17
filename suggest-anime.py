import pandas as pd
import difflib

DATA_FILE = "anime_cleaned.csv"


def all_genres():
    gs = df.iloc[:, 2]
    genres = []
    
    for gl in gs:
        gl = gl.split(",")
        for i in range(len(gl)):
            gl[i] = gl[i].strip()
        genres = set( list(genres) + gl)
    return list(genres)





def fb_genre(genre, strict):
    columns = list(df)
    df_ = pd.DataFrame(columns=columns)
    k = 0

    for i in range( len(df) ):
        gs = df.loc[i, "genre"]
        gs = str(gs).split(",")
        
        g_found = False
        o_g_found = False
        for g in gs:
            if str.lower(g.strip()) == str.lower(genre.strip()):
                g_found = True
                if not strict:
                    break
            else:
                o_g_found = True
                
        if (not strict and g_found) or (strict and g_found and not o_g_found):
            df_.loc[k] = list(df.loc[i,:])
            k += 1
            
    return df_



def find_by_genre(genre, strict=False):
    genres = all_genres()
    genres = list(map( lambda x: str.lower(x).strip(), genres ))
    
    
    genre = str.lower(genre).strip()
    close = difflib.get_close_matches(genre, genres)

    
    if str.lower(genre).strip() in close:
        print( fb_genre( genre, strict ) )
    elif len(close) > 0:
        print("You might have wanted:\n")
        print(close)
        for g in close:
            print(g)
    else:
        print("Genre not found\n\n")
        print("Complete list of all genres:")
        for g in genres:
            print(g)




df = pd.read_csv(DATA_FILE, encoding = 'utf8')