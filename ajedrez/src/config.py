# src/config.py
from pathlib import Path
import chess

# --- CONFIGURACIÓN DE RUTAS (Cross-platform usando pathlib) ---
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_LIBRO_APERTURAS = RAIZ_PROYECTO / "data" / "aperturas.bin"
RUTA_JSON_APERTURAS = RAIZ_PROYECTO / "data" / "aperturas.json"

# --- CONFIGURACIÓN DE LA INTERFAZ (GUI) ---
TAM_CASILLA = 64
ANCHO = TAM_CASILLA * 8
ALTO = TAM_CASILLA * 8
ALTO_BARRA_ESTADO = 40
MAX_FPS = 30

# --- VALORES HEURÍSTICOS DEL MOTOR ---
VALORES_PIEZAS = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 90000
}

# --- TABLAS DE PIEZA-CASILLA (PST) ---
PST_PEON = [
     0,  0,  0,  0,  0,  0,  0,  0,
    -5, -5, -5, -5, -5, -5, -5, -5,   # fila 2: penaliza no avanzar
     0,  0,  0,  0,  0,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,   # fila 4: premia centro
    10, 10, 20, 30, 30, 20, 10, 10,   # fila 5: premia avance central
    20, 20, 30, 40, 40, 30, 20, 20,   # fila 6: peón avanzado vale mucho
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0
]


PST_CABALLO = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

PST_ALFIL = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

PST_TORRE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
]

PST_REINA = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

PST_REY = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]