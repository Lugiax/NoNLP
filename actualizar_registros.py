from utils import abrir
import time
import pandas as pd
import requests
import regex as re

carpeta_registros = 'registros/'
db_filename = 'actualizado.pkl'
n_pag = 0
pag_inicio = 0
max_pags = 10

try:#Intenta leer el dataframe o crea uno nuevo
    df = pd.read_pickle(db_filename)
except:
    df = None

while True and n_pag<max_pags:
    print(F'REVISIÓN DE LA PÁGINA {n_pag+pag_inicio+1}')
    r = requests.get(f'https://www.gob.mx/presidencia/es/archivo/articulos?idiom=es&order=DESC&page={n_pag+pag_inicio+1}')
    links = ['https://www.gob.mx'+s for s in
                re.findall(r'(\/presidencia\/es\/articulos\/version-estenografica-[a-z 0-9 -]+)\?idiom=es', r.text)
            ]
    time.sleep(0.2)
    for l in links:
        if df is not None and l in df.url.tolist():
            continue
        nombre_conferencia = l.split("/")[-1]
        datos = abrir(nombre_conferencia, carpeta_registros)
        time.sleep(0.2)

        if datos is None:
            continue
        _new_df = pd.DataFrame.from_records(datos, index=[0])
        if df is None:
            df = _new_df
        else:
            df = df.append(_new_df, ignore_index=True)
    n_pag+=1
    df.to_pickle(db_filename)
print(df.info())
print(df.head())
