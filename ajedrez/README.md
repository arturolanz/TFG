# Motor de Ajedrez con IA clásica

Este repositorio contiene el código fuente de un Trabajo Fin de Grado basado en el desarrollo de un motor de ajedrez propio en Python. El proyecto combina una interfaz gráfica jugable con un sistema de toma de decisiones basado en técnicas clásicas de Inteligencia Artificial.

El objetivo principal no es competir con motores profesionales como Stockfish, sino construir un sistema funcional, comprensible y ampliable que permita jugar contra una IA propia, reconocer aperturas y analizar el comportamiento del motor durante la partida.

## Funcionalidades principales

* Interfaz gráfica desarrollada con Pygame.
* Movimiento de piezas mediante ratón.
* Validación de movimientos legales mediante `python-chess`.
* Posibilidad de jugar con blancas o negras.
* Motor de decisión propio basado en Minimax.
* Optimización mediante poda Alfa-Beta.
* Evaluación heurística basada en material, posición y otros criterios estratégicos.
* Búsqueda de quiescencia para reducir el efecto horizonte.
* Evaluación específica para finales.
* Reconocimiento de aperturas mediante archivo JSON.
* Uso de libro de aperturas en formato Polyglot.
* Registro de partidas en formato PGN.
* Herramientas de depuración para analizar las decisiones de la IA.
* Interfaz con resaltado de movimientos, jaques, último movimiento y mensajes de final de partida.

## Estructura del proyecto

.
├── data/
│   ├── aperturas.bin
│   └── aperturas.json
├── docs/
│   ├── logs_partidas/
│   └── partidas_descargadas/
├── src/
│   ├── images/
│   ├── config.py
│   ├── engine.py
│   ├── interfaz.py
│   └── main.py
├── .gitignore
├── README.md
└── requirements.txt

## Descripción de los archivos y carpetas principales

### `src/`

Carpeta principal del código fuente de la aplicación. Contiene los módulos encargados de la lógica del juego, la interfaz gráfica, la configuración y el punto de entrada del programa.

### `src/main.py`

Archivo principal del proyecto. Gestiona el bucle de ejecución, los eventos del usuario, los turnos, la comunicación entre la interfaz y el motor, el reinicio de partidas y la coordinación de la IA en segundo plano.

### `src/engine.py`

Contiene el núcleo lógico del motor. Incluye la gestión del tablero, la validación de movimientos, el sistema de aperturas, Minimax, poda Alfa-Beta, evaluación heurística, búsqueda de quiescencia y guardado de partidas en PGN.

### `src/interfaz.py`

Contiene las funciones relacionadas con la parte visual. Se encarga de dibujar el tablero, cargar las piezas, mostrar resaltados, mensajes de estado, panel lateral, historial de movimientos y elementos gráficos de apoyo.

### `src/config.py`

Centraliza constantes y parámetros del proyecto, como rutas de archivos, tamaño del tablero, valores de piezas y tablas de evaluación posicional.

### `src/images/`

Carpeta que contiene las imágenes de las piezas utilizadas por la interfaz gráfica.

### `data/`

Carpeta que contiene los datos externos utilizados por el motor:

* `aperturas.json`: catálogo de aperturas y variantes reconocidas por el sistema.
* `aperturas.bin`: libro de aperturas en formato Polyglot.

### `docs/`

Carpeta destinada a almacenar registros y partidas generadas por la aplicación:

* `logs_partidas/`: registros de partidas.
* `partidas_descargadas/`: partidas exportadas en formato PGN.

### `requirements.txt`

Archivo que recoge las dependencias necesarias para ejecutar el proyecto.

### `.gitignore`

Archivo de configuración de Git que evita subir al repositorio archivos temporales, entornos virtuales, cachés y partidas generadas.


## Instalación

Se recomienda utilizar un entorno virtual para instalar las dependencias del proyecto.

### 1. Clonar el repositorio

git clone URL_DEL_REPOSITORIO
cd NOMBRE_DEL_REPOSITORIO

### 2. Crear un entorno virtual

En Windows:

python -m venv venv
venv\Scripts\activate

En Linux o macOS:

python3 -m venv venv
source venv/bin/activate

### 3. Instalar dependencias

pip install -r requirements.txt

## Ejecución

Para iniciar la aplicación, ejecutar:

## Ejecución

Para iniciar la aplicación, ejecutar el archivo principal situado dentro de la carpeta `src`:

python src/main.py

En algunos sistemas puede ser necesario utilizar:

python3 src/main.py

Al iniciar el programa se muestra una pantalla de selección donde el usuario puede elegir el color de las piezas y comenzar la partida.


## Uso básico

1. Ejecutar `main.py`.
2. Seleccionar si se desea jugar con blancas o negras.
3. Hacer clic sobre una pieza propia.
4. Hacer clic sobre una casilla de destino legal.
5. Esperar la respuesta de la IA.
6. Continuar la partida hasta jaque mate, tablas o reinicio.

Durante la partida, la interfaz muestra información adicional como movimientos legales, último movimiento, estado de jaque, apertura reconocida e historial de movimientos.

## Registro de partidas

El sistema permite guardar partidas en formato PGN. Estos archivos pueden utilizarse posteriormente para analizar las partidas en herramientas externas como Lichess o Chess.com.

## Sistema de aperturas

El proyecto utiliza dos mecanismos relacionados con aperturas:

* Un archivo JSON para reconocer líneas y mostrar el nombre de la apertura.
* Un libro Polyglot para seleccionar jugadas teóricas durante la fase inicial de la partida.

Esta separación permite ampliar el catálogo de aperturas sin modificar directamente la lógica principal del motor.

## Notas sobre el desarrollo

El proyecto ha sido desarrollado con un enfoque incremental. Primero se construyó una versión jugable básica, después se incorporó una IA sencilla y posteriormente se añadieron técnicas más avanzadas como Minimax, poda Alfa-Beta, evaluación heurística, búsqueda de quiescencia, reconocimiento de aperturas, multithreading y herramientas de depuración.

## Limitaciones

El motor no pretende alcanzar el nivel de un motor profesional. Su fuerza de juego está limitada por la profundidad de búsqueda, el coste computacional de Python y la ausencia de algunas optimizaciones avanzadas, como tablas de transposición.

Aun así, el sistema cumple su objetivo principal: ofrecer una aplicación funcional, jugable y comprensible que permita estudiar el funcionamiento interno de un motor de ajedrez clásico.

## Autor

Proyecto desarrollado como Trabajo Fin de Grado.

Autor: Arturo Lanzarote Rivas

Universidad: Universidad de Córdoba
