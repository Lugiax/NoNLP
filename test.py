import requests
from prettyprinter import pprint
from bs4 import BeautifulSoup
import regex as re
import string
import spacy
from spacy.lang.es import Spanish
from collections import Counter
import os
import pandas as pd
from glob import glob
import numpy as np

from utils import *
from listas import *


"""
Referencias
https://relopezbriega.github.io/blog/2017/09/23/procesamiento-del-lenguaje-natural-con-python/
https://www.aprendemachinelearning.com/ejercicio-nlp-cuentos-de-hernan-casciari-python-espanol/
https://likegeeks.com/es/tutorial-de-nlp-con-python-nltk/
https://docs.python.org/3/library/string.html
https://blog.ekbana.com/nlp-for-beninners-using-spacy-6161cf48a229
"""

nlp = spacy.load('es_core_news_sm')

#discursos_crudos={}
#contador = None
#palabras_glob = ''
#discursos_glob = ''
carpeta_registros = 'registros/'
#Se cargan los datos de todas las mañaneras disponibles
df = cargar_datos()

def generar_bd_palabras(df, db_filename='historico_palabras.pkl', guardar=False):
    print('Generando palabras')
    if os.path.isfile(db_filename):
        historico = pd.read_pickle(db_filename)
        print('Archivo leido...')
    else:
        historico = None
        print('Historico creado')
    n_entradas = 10#df.shape[0]
    print(f'Procesando palabras de {db_filename}... ')
    for i in range(n_entradas):
        avance = int(i/n_entradas*100)
        if avance%10==0:
            print(f'\r Avance: {avance}%', end='')
        serie = df.iloc[i]
        if historico is not None and serie.fecha in historico.index:
            continue
        doc = tokenizar(serie.limpio)
        cuenta = contar_palabras(doc, tipo='lemma')
        _new_df = pd.DataFrame.from_records(cuenta, index=[serie.fecha])
        if historico is None:
            historico = _new_df
        else:
            historico = historico.append(_new_df)
    print(' Terminado :D')
    historico.fillna(0, inplace=True)
    historico.sort_index(ascending=False)
    if guardar: 
        print(f'Guardando en {db_filename}')
        historico.to_pickle(db_filename)
    return(historico)



hist = generar_bd_palabras(df)
print(hist.head(10))

"""
registros = glob(carpeta_registros+'*.txt')
historico_palabras= pd.DataFrame()
total_palabras = Counter()
for pag in [182]:
    url = f'https://www.gob.mx/presidencia/es/archivo/articulos?idiom=es&order=DESC&page={pag+1}'
    print('Buscando en %s'%url)
    r = requests.get(url)
    links = ['https://www.gob.mx'+s for s in
                re.findall(r'(\/presidencia\/es\/articulos\/[a-z 0-9 -]+)\?idiom=es', r.text)
            ]
    if len(links)==0:
        break
    for l in links:
        nombre_conferencia = l.split("/")[-1]
        lectura = abrir(nombre_conferencia, carpeta_registros, solo_conferencias=True)
        print(lectura['fecha'])
        if lectura is None:
            continue
        #conversaciones = extractor_de_conversaciones(lectura['limpio'])
        #if len(conversaciones)>0:
        #    dialogos = separador_de_conversacion(conversaciones[0])
        #    for p, d in dialogos.items():
        #        if p=='INTERLOCUTOR':
        #            doc = nlp(d)
        #            #for ent in doc.ents:
        #            #    if ent.label_=='PER': print(ent.text, ent.label_)
        #            print(f'\n {p} : {doc[:100]}')
        doc = tokenizar(lectura['limpio'])
        cuenta = contar_palabras(doc, tipo='lemma')#, interes=LISTA_INTERES)
        #for k,v in cuenta.most_common()[:50]:
        #    print(k,v)
        #generar_nube_de_palabras(cuenta)
        total_palabras.update(cuenta)
        historico_palabras = historico_palabras.append(pd.DataFrame(cuenta, index=[lectura['fecha']]))
        print('vacuna ',cuenta.get('vacuna', 0))
"""
"""
#generar_nube_de_palabras(total_palabras)
historico_palabras.fillna(0, inplace=True)

historico_palabras.to_csv('historico.csv')

palabras_int = ['ine', 'tribunal']

fig, ax = plt.subplots(figsize=(10,5))
etiquetas_fechas = [d.strftime('%d-%m') for d in historico_palabras.index][::-1]
x = list(range(len(etiquetas_fechas)))
print('Total de conferencias: ',len(x))
if len(x)>25:
    sel = np.linspace(0,len(x)-1, num=25, dtype= np.uint)
    etiquetas_fechas = [etiquetas_fechas[i] for i in sel]
    x = [x[i] for i in sel]
for p in palabras_int:
    ax.plot(historico_palabras[p].tolist()[::-1], label=p)
ax.set_xticks(x)
ax.set_xticklabels(etiquetas_fechas, rotation='vertical')
ax.set_xlabel('Fecha')
ax.set_ylabel('Frecuencia')
plt.legend()
plt.show()

"""