from collections import Counter, OrderedDict
import json
import os

    
class GeneradorScriptGraficas():
    def __init__(self, filename=None):
        self.fname = filename
        self.script=''
        self._last=None
        self.graficas=OrderedDict()
    
    def agregar_grafica(self, name=None, **layout):
        """
        Debe recibir un diccionario con toda la información del
        layout de la gráfica siguiendo el formato descrito en
        https://plotly.com/javascript/reference/layout/
        """
        layout_base = {
            'title' : "'Gráfico 1'",
            'showlegend': 'true',
        }
        layout_base.update(layout)

        if name is None:
            name = len(self.graficas.keys())
        
        self.graficas[name] = {'layout': layout_base,
                               'datos':[]}
        self._last = name
    
    def agregar_datos(self, datos, name=None, **kwargs):
        """
        Recibe un diccionario con los datos y su configuración
        para graficar y se agregan al diccionario de "name"· Los
        datos son representados por un diccionario como:
        {
            'x': [lista de datos en x],
            'y': [lista de datos en y],
            'type': str  'scatter'
            'name': str Nombre de la serie de datos,
            ...
        }
        según las referencias https://plotly.com/javascript/reference/.

        Los parámetros se pueden extender según los que se agreguen
        en **kwargs
        """
        if name is None:
            name = self._last
        datos_base = {
            'name': f"data_{len(self.graficas[self._last]['datos'])}"
        }
        datos_base.update(datos)
        datos_base.update(kwargs)
        self.graficas[name]['datos'].append(datos_base)
    
    def agregar_datos_de_lista(self, datos_lista, name=None, **kwargs):
        """
        Procesa un conjunto de datos en un diccionario. Cada entrada 
        es un conjunto de datos independiente. 
        """
        for d in datos_lista:
            self.agregar_datos(d, name, **kwargs)
    
    def generar_script(self, filename=None):
        """
        Genera el texto de JavaScript que genera las gráficas
        guardadas.
        """
        if filename is None:
            filename = self.fname
        for k in self.graficas:
            sections=[]
            names = []
            for d in self.graficas[k]['datos']:
                var_name = ''.join(d['name'].split(' ')).lower()
                trace_str = """
var %VARNAME% = {
    x: [%DATAX%],
    y: [%DATAY%],
    type: 'scatter',
    name: '%NAME%',
    %OTHERS%
}; 
                    """
                trace_str = trace_str.replace('%VARNAME%', var_name)\
                    .replace('%NAME%', d['name'])\
                    .replace('%DATAY%', ','.join(d['y']))\
                    .replace('%DATAX%', ','.join(d['x']))\
                    .replace('%OTHERS%',',\n'.join([f'{k}:{v}' for k,v in d.items()
                                                    if k not in ['name','y','x']]))
                sections.append(trace_str)
                names.append(var_name)

            self.script += '\n'.join(sections)
            self.script += """
var layout_%NAME% = {%LAYOUT%};"""\
                    .replace('%NAME%', k)\
                    .replace('%LAYOUT%', ',\n\t'.join([f'{k} : {v}' for k,v in self.graficas[k]['layout'].items()]))
            self.script += f"""
var data_{k} = [{', '.join(names)}];
Plotly.newPlot('{k}_graph', data_{k}, layout_{k});
                    """ +\
                    """
function cambiar_grafica(){
    let boton = document.getElementById('boton_graph');
    if (boton.innerText==='Cambiar a medios'){
        boton.innerText = 'Cambiar a palabras';
        Plotly.newPlot('graph', data_medios, layout_palabras);
    }
    else{
        boton.innerText = 'Cambiar a medios';
        Plotly.newPlot('graph', data_palabras, layour_medios);
    }
    
} 
                    """
            
        if filename is not None:
            folder = os.path.split(filename)[0]
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with open(filename, 'w') as f:
                f.write(self.script)
            print(f'Script guardado en {filename}')
        return self.script

if __name__=='__main__':
    gen = GeneradorScriptGraficas()
    gen.agregar_grafica('mazmorra', **{'nada': "'ok'"})
    gen.agregar_datos({'x': ['10'], 'y':['20']})
    gen.agregar_datos({'x': ['1'], 'y':['2']})

    gen.agregar_grafica('mazmorra2', **{'nada': "'ok2'"})
    gen.agregar_datos({'x': ['100'], 'y':['20000'], 'name':'holi'})
    gen.agregar_datos({'x': ['1000'], 'y':['2000']})
    script = gen.generar_script('BORRAR.js')
    print(script)



    
    
