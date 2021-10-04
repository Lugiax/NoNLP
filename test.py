import requests
from bs4 import BeautifulSoup
import regex as re
import string
import spacy
from spacy.lang.es import Spanish
from spacy.tokenizer import Tokenizer
from collections import Counter
import os
import pandas as pd
from glob import glob
import numpy as np

from utils import *
from listas import *
from objs import *


"""
Referencias
https://relopezbriega.github.io/blog/2017/09/23/procesamiento-del-lenguaje-natural-con-python/
https://www.aprendemachinelearning.com/ejercicio-nlp-cuentos-de-hernan-casciari-python-espanol/
https://likegeeks.com/es/tutorial-de-nlp-con-python-nltk/
https://docs.python.org/3/library/string.html
https://blog.ekbana.com/nlp-for-beninners-using-spacy-6161cf48a229
"""

#nlp = spacy.load('es_core_news_lg')
#tokenizer = Tokenizer(spacy.load('es_core_news_sm').vocab)

#Se cargan los datos de todas las mañaneras disponibles
#df = cargar_datos().iloc[:5]

hist_pal = cargar_datos('historicos/medios.pkl')
frecs = hist_pal.sum()
print(frecs)
generar_nube_de_palabras({k:frecs[k].tolist() for k in frecs.index.tolist()})
#vals.to_json('historico_palabras_interes.json', date_format='iso')



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