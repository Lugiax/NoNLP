from utils import *
from listas import *
from objs import *

hist_pal = cargar_datos('historicos/palabras.pkl').sort_index(ascending=False)
hist_med = cargar_datos('historicos/medios.pkl').sort_index(ascending=False)

#Trabajando solo con las palabras de interés
cols_pal = set(hist_pal.columns.tolist())
val_pal = cols_pal.intersection(set(LISTA_INTERES))
hist_pal = hist_pal[list(val_pal)]

generador = GeneradorScriptGraficas('scripts/graficas.js')
generador.agregar_grafica('palabras')
generador.agregar_datos_de_lista(df_a_lista(hist_pal), **{'visible':"'legendonly'"})
#generador.generar_script()

#generador = GeneradorScriptGraficas('scripts/grafica_medios.js')
generador.agregar_grafica('medios')
generador.agregar_datos_de_lista(df_a_lista(hist_med))
generador.generar_script()