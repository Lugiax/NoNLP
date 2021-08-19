from wordcloud import WordCloud
import matplotlib.pyplot as plt
import regex as re
import datetime
from glob import glob
import os
from bs4 import BeautifulSoup
import requests
from collections import Counter
import pandas as pd

from spacy.lang.es import Spanish
import spacy
from stop_words import get_stop_words
from listas import *

S_WORDS = get_stop_words('es')

def limpiar(texto):
    t = re.sub(r'([Nn]one)', '', texto)#re.sub(r'(\n)?([Nn]one)?(\n)?', '', texto)
    t = re.sub(r'[\(\)-]', ' ', t)
    return t

def tokenizar(texto):
    return spacy.load('es_core_news_sm')(texto)

def contar_palabras(doc, tipo='texto', interes=[], exclusion=None):
    """
    Devuelve un contador con las palabras en el texto que cumplan
    las condiciones estbalecidas. Se puede seleccionar en devolver
    el lemma o el texto, seleccionando de ["lemma", "texto"]
    Se puede pasar una lista de palabras de interés o de exclusión
    """
    if exclusion is None: exclusion = S_WORDS + LISTA_NO_DESEADAS
    _c = {'texto': 'text', 'lemma': 'lemma_'}
    lista = [getattr(token, _c[tipo]).lower() for token in doc if token.text.lower() not in exclusion
                                                                and not (token.is_punct or
                                                                        token.is_space or
                                                                        token.is_stop or
                                                                        token.pos_=='VERB' or
                                                                        token.is_digit)]
    if len(interes)>0:
        lista = [i for i in lista if i in interes]
    return Counter(lista)


def medio_valido(t, ventana = 1):
    medio = [v.replace('-', ' ') for v  in lista_de_medios if t.text.lower() in v and t.pos_ in ['NOUN', 'PROPN']]
    if len(medio) and medio[0] in doc[t.i-ventana:t.i+ventana+1].text.lower():
        return medio[0]
    else:
        return None

def extractor_de_conversaciones(texto):
    """
    Las conversaciones comienzan con una pregunta y terminan con otra
    pregunta o con el final de la conferencia
    """
    separados = texto.split('PREGUNTA')[1:]
    return(['PREGUNTA'+s for s in separados])

def separador_de_conversacion(conv):
    """
    Separa los diálogos de cada personaje identificado por
    "MAYÚSCULAS, MAYÚSCULAS:" y los agrupa en un diccionario.
    Cada clave es el nombre de un personaje, donde INTERLOCUTOR
    es el/la reportero/a 
    """
    patt = re.compile(r'((\p{Lu}[ ,]*)+\p{Lu}{2,}):')
    speach_spans = [(e.span(), e.group()) for e in re.finditer(patt, conv)]
    #Se calculan los intervalos de cada diálogo
    speach_inter = [(speach_spans[i][0][1],speach_spans[i+1][0][0])\
                     for i in range(len(speach_spans)-1)]\
                     + [(speach_spans[-1][0][-1], -1)]
    dialogos = {}
    for span, speachs in zip(speach_inter, speach_spans):
        inicio, final = span
        personaje = speachs[1][:-1].split(', ')[0]
        personaje = 'INTERLOCUTOR' if personaje in ('PREGUNTA','INTERLOCUTORA') else personaje
        dialogo = conv[inicio:final]
        dialogo = re.sub(r'\n|\n\s', ' ', dialogo) #Quitar saltos de línea y espacios de más
        dialogos.update({personaje: dialogos.get(personaje, '') + dialogo})
    
    return dialogos



def generar_nube_de_palabras(contador, **params):
    parametros = {'width':500,
                  'height':500,
                  'background_color':"#d7edfe",
                  'color_func': lambda *args, **kwargs: "#f07167"
                }
    parametros.update(**params)

    nube = WordCloud(**parametros)\
            .generate_from_frequencies(contador)
    
    plt.imshow(nube)
    plt.axis('off')
    plt.show()


def extraer_fecha(nombre):
    if nombre.endswith('.txt'):
        nombre = nombre[:-4]
    meses='enero,febrero,marzo,abril,'\
          'mayo,junio,julio,agosto,septiembre,'\
          'octubre,noviembre,diciembre'.split(',')
    mes_a_numero = {m:i+1 for i,m in enumerate(meses)}
    fecha_texto = nombre.split('_')[-1].split('-')
    fecha = datetime.date(int(fecha_texto[2]),
                          mes_a_numero[fecha_texto[1]],
                          int(fecha_texto[0]))
    return fecha


def abrir(nombre, bd='registros', solo_conferencias=True):
    if solo_conferencias and 'conferencia-de-prensa' not in nombre:
        return None
    
    url = 'https://www.gob.mx/presidencia/es/articulos/'+nombre
    disponibles = glob(os.path.join(bd, '*.txt'))
    indice_registro = [i for i, disp in enumerate(disponibles) if nombre == disp.split('/')[1].split('_')[0]]
    print(f'Nombre: {nombre}')
    if len(indice_registro)>0:
        #print(f'{disponibles[indice_registro[0]]}')
        #print(f'Leyendo el archivo {nombre}... ', end='')
        fname = disponibles[indice_registro[0]]
        with open(fname, 'r') as f:
            limpio = f.read()
        print('\tLeido :D')
    else:
        texto = requests.get(url).text
        soup = BeautifulSoup(texto, 'html.parser')
        discurso = '\n'.join([str(s.string) for s in soup.select('.article-body p')])
        titulo = soup.select('h1')
        subtitulo = soup.select('h2')
        titulo = str(titulo[0].string) if len(titulo)!=0 else 'TITULO FALTANTE'
        subtitulo = str(subtitulo[0].string) if len(subtitulo)!=0 else 'SUBTITULO FALTANTE'
        cuadro_fecha = soup.find_all('section' , 'border-box')[0].text
        fecha_txt = re.findall(re.compile('\d{1,2}\sde\s\w+\sde\s\d{4}'), cuadro_fecha)[0].replace(' de ', '-')

        #print(f'Analizando: {titulo} - {subtitulo} - {fecha_txt}\n{url}')
        limpio = '\n'.join([titulo, subtitulo, limpiar(discurso)])
        fname = f'{nombre}_{fecha_txt}'
        with open(os.path.join(bd, f'{fname}.txt'), 'w') as f:
            f.write(limpio)
        print('\tDescargado y guardado')

    return {'url': url,
            'fname': fname,
            'fecha': extraer_fecha(fname),
            'limpio': limpio}

def cargar_datos(db='actualizado.pkl'):
    return pd.read_pickle(db)

"""
indice_registro = [i for i, reg in enumerate(registros) if nombre_conferencia in reg]
#Se busca el archivo descargad o se descarga en su defecto
if len(indice_registro)>0:
    ruta = registros[indice_registro[0]]
    _nombre_archivo = os.path.basename(ruta)[:-4]
    print(f'Leyendo el archivo {ruta}')
    with open(ruta, 'r') as f:
        limpio = f.read()
else:
    print(f'Descargando de {l}...')
    texto = requests.get(l).text
    soup = BeautifulSoup(texto, 'html.parser')
    discurso = '\n'.join([str(s.string) for s in soup.select('.article-body p')])
    titulo = str(soup.select('h1')[0].string)
    subtitulo = str(soup.select('h2')[0].string)
    cuadro_fecha = soup.find_all('section' , 'border-box')[0].text
    fecha = re.findall(re.compile('\d{1,2}\sde\s\w+\sde\s\d{4}'), cuadro_fecha)[0].replace(' de ', '-')

    print(f'Analizando: {titulo} - {subtitulo} - {fecha}\n{l}')
    limpio = '\n'.join([titulo, subtitulo, limpiar(discurso)])
    _nombre_archivo = f'{nombre_conferencia}_{fecha}'
    with open(os.path.join(carpeta_registros, f'{_nombre_archivo}.txt'), 'w') as f:
        f.write(limpio)
    print('\tDescargado y guardado')
"""
