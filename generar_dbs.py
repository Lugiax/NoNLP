from utils import *
import spacy

nlp = spacy.load('es_core_news_lg')
df = cargar_datos()

funcs = {
    'conteo_palabras':{
        'f':contar_palabras,
        'args':{'tipo':'lemma'},
        'path':'historicos/palabras.pkl'            
    },
    'conteo_medios':{
        'f':contar_medios,
        'args':{'nlp':nlp, 'umbral':0.7},
        'path':'historicos/medios.pkl'
    }
}

if __name__=='__main__':
    generar_historico(df, funcs, nlp, guardar=True)