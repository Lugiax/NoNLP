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
import numpy as np
from textdistance import damerau_levenshtein, levenshtein

from spacy.lang.es import Spanish
import spacy
from stop_words import get_stop_words
from listas import *

S_WORDS = get_stop_words('es')

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

def contar_medios(doc, nlp=None, umbral=0.7):
    if nlp is None:
        nlp = spacy.load('es_core_news_md')
    medios = [nlp(m) for m in LISTA_MEDIOS]

    medios_encontrados=[]
    for ent in doc.ents:
        if ent.label_ in ['ORG']:
            scores = [1-levenshtein.normalized_distance(ent.text.strip(), m.text) for m in medios]
            #if sum(scores):
            #    idx = np.argmax(scores)
            #else:
                #scores = [ent.similarity(m) for m in medios]
            idx = np.argmax(scores)
            #print(f'Similitud entre {ent.text} y {medios[idx]} = {scores[idx]}')
            #print(list(zip(medios, scores)))
            if scores[idx]>umbral:
                print(f'Similitud entre {ent.text} y {medios[idx]} = {scores[idx]}')
                print(f'Se encontró:{medios[idx]}, {scores[idx]}')
                medios_encontrados.append(medios[idx].text)
    
    return Counter(medios_encontrados)

def contar_palabras(doc, tipo='lemma', interes=[], exclusion=None):
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

def convertir_fecha(fecha):
    """
    Convierte fechas entre el formato string y datetime
    """
    pass


def df_a_lista(df):
    """
    Función para preparar la información de un DataFrame y 
    poder pasarlo al generador de scripts.
    El df debe contener fechas tipo datetime como índice,
    nombres en las columnas y solo valores numéricos.
    En este momento solo se pueden hacer gŕaficos scatter
    """
    fechas = ["'"+s.strftime('%Y-%m-%d')+"'" for s in df.index.tolist()]
    cols = df.columns.tolist()
    datos = []
    for c in cols:
        datos.append({
            'x': fechas,
            'y': [str(i) for i in df[c].tolist()],
            'name' : f'{c}',
        })
    return datos
        

def extractor_de_conversaciones(texto):
    """
    Las conversaciones comienzan con una pregunta y terminan con otra
    pregunta o con el final de la conferencia
    """
    separados = texto.split('PREGUNTA')[1:]
    return(['PREGUNTA'+s for s in separados])


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



def generar_historico(df, funcs, nlp=None, guardar=False, entradas_max=None):
    """
    Genera un histórico de elementos definidos por las funciones func, donde:
        funcs : dict {'NOMBRE_HISTORICO':{'f'   : func,
                                          'args': args,
                                          'path': path}}
    y func es una función que toma como argumento un doc y devuelve un Counter(),
    args son los argumentos que se le pasarán y path es el directorio del archivo.

    Al final la función devuelve un diccionario con un dataframe por cada función
    """
    print('Generando palabras')
    hists = {}
    for h in funcs:
        db_filename = funcs[h].get('path', '')
        if db_filename!='' and os.path.isfile(db_filename):
            hists[h] = pd.read_pickle(db_filename)
            print(f'Archivo {db_filename} leido...')
        else:
            hists[h] = None
            print(f'Historico "{h}" creado')
    if nlp is None:
        nlp = spacy.load('es_core_news_lg')

    n_entradas = df.shape[0] if entradas_max is None else entradas_max
    steps = np.ceil(n_entradas/100)
    #print(f'Procesando palabras de {db_filename}... ')
    for i in range(n_entradas):
        #if i%steps==0:
        #    print(f'\r Avance: {int(i/n_entradas*100)}%', end='')
        serie = df.iloc[i]
        for h, func in funcs.items(): 
            if hists[h] is not None and serie.fecha in hists[h].index:
                continue
            mas_limpio = re.sub(r'[\.,\-0-9¡!¿?\n]+', ' ', serie.limpio)
            doc = nlp(mas_limpio)
            res = func['f'](doc, **func['args'])
            #cuenta = contar_palabras(doc, tipo='lemma')
            _new_df = pd.DataFrame.from_records(res, index=[serie.fecha])
            if hists[h] is None:
                hists[h] = _new_df
            else:
                hists[h] = hists[h].append(_new_df)
    
    #print('\r Avance: 100% --- Terminado :D')
    
    for h in hists.values():
        h.fillna(0, inplace=True)
        h.sort_index(ascending=False, inplace=True)
    if guardar: 
        for h in funcs:
            db_filename = funcs[h].get('path', '')
            if db_filename!='':
                folder = os.path.split(db_filename)[0]
                if not os.path.isdir(folder):
                    os.makedirs(folder)
                print(f'Guardando en {db_filename}')
                hists[h].to_pickle(db_filename)
    return(hists)



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

def generar_plot_script(df, selector_id='grafico', save_path=None):
    script = """
    %TRACES%

    var data = [%TRACELIST%];

    Plotly.newPlot('%SELECTOR_ID%', data);
    """
    fechas = ["'"+s.strftime('%Y-%m-%d')+"'" for s in df.index.tolist()]
    cols = df.columns.tolist()
    
    trace_list=[]
    for n in cols:
        trace_str = """
        var %TRACENAME% = {
            x: [%DATAX%],
            y: [%DATAY%],
            type: 'scatter',
            name: '%TRACENAME%'
        }; 
        """
        trace_str = trace_str.replace('%TRACENAME%', n)\
                    .replace('%DATAY%', ','.join([str(i) for i in df[n].tolist()]))\
                    .replace('%DATAX%', ','.join(fechas))

        trace_list.append(trace_str)
    
    script = script.replace('%TRACES%', '\n'.join(trace_list))\
             .replace('%TRACELIST%', ','.join(cols))\
             .replace('%SELECTOR_ID%', selector_id)
    
    if save_path is not None:
        with open(save_path, 'w') as f:
            f.write(script)

    return script

def limpiar(texto):
    t = re.sub(r'([Nn]one)', '', texto)#re.sub(r'(\n)?([Nn]one)?(\n)?', '', texto)
    t = re.sub(r'[\(\)-]', ' ', t)
    return t

def medio_valido(t, ventana = 1):
    medio = [v.replace('-', ' ') for v  in lista_de_medios if t.text.lower() in v and t.pos_ in ['NOUN', 'PROPN']]
    if len(medio) and medio[0] in doc[t.i-ventana:t.i+ventana+1].text.lower():
        return medio[0]
    else:
        return None

    
def separador_de_conversacion(conv):
    """
    Separa los diálogos de cada personaje identificado por
    "MAYÚSCULAS, MAYÚSCULAS:" y los agrupa en un diccionario.
    Cada clave es el nombre de un personaje, donde INTERLOCUTOR
    es el/la reportero/a 
    """
    patt = re.compile(r'((\p{Lu}[ ,]*)+\p{Lu}{2,}):')
    speach_spans = [(e.span(), e.group()) for e in re.finditer(patt, conv)]
    if not len(speach_spans):
        return { }
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


def tokenizar(texto):
    return spacy.load('es_core_news_sm')(texto)