import pygame
import chess

# Configuración
ANCHO = ALTO = 512 # 8 casillas por 64 pixeles
DIMENSION = 8
TAM_CASILLA = ALTO // DIMENSION
MAX_FPS = 15
PIEZAS = {}

def cargar_imagenes():
    """Carga las imágenes de las piezas en un diccionario."""
    piezas = ['wp', 'wr', 'wn', 'wb', 'wq', 'wk', 'bp', 'br', 'bn', 'bb', 'bq', 'bk']
    escala = 0.95 # Para que la pieza ocupe el 95% de la casilla
    tam_pieza = int(TAM_CASILLA * escala)
    for pieza in piezas:
        # Cargamos la imagen desde tu carpeta 'images'
        imagen = pygame.image.load("images/" + pieza + ".png")
        # La escalamos para que encaje perfectamente en la casilla
        PIEZAS[pieza] = pygame.transform.scale(imagen, (tam_pieza, tam_pieza))

def dibujar_tablero(pantalla):
    """Dibuja los cuadros del tablero."""
    colores = [pygame.Color("white"), pygame.Color("gray")]
    for f in range(DIMENSION):
        for c in range(DIMENSION):
            color = colores[((f + c) % 2)]
            pygame.draw.rect(pantalla, color, pygame.Rect(c*TAM_CASILLA, f*TAM_CASILLA, TAM_CASILLA, TAM_CASILLA))

def dibujar_piezas(pantalla, tablero):
    """Dibuja las piezas sobre el tablero basándose en el estado de python-chess."""
    # Calculamos cuánto espacio sobra para centrar la pieza
    # Si la casilla mide 64 y la pieza 58, sobran 6px. El centro es moverla 3px.
    offset = (TAM_CASILLA - PIEZAS['wp'].get_width()) // 2
    
    for f in range(DIMENSION):
        for c in range(DIMENSION):
            # IMPORTANTE: python-chess cuenta desde abajo, pygame desde arriba
            # Usamos chess.square(columna, fila)
            casilla = chess.square(c, 7 - f)
            pieza = tablero.piece_at(casilla)
            
            if pieza is not None:
                # Determinamos el nombre del archivo (ej: 'wp', 'bn')
                color = 'w' if pieza.color == chess.WHITE else 'b'
                tipo = pieza.symbol().lower()
                nombre_pieza = color + tipo
                
                #Dibujamos sumando el offset en X e Y
                pantalla.blit(PIEZAS[nombre_pieza], 
                              (c*TAM_CASILLA + offset, f*TAM_CASILLA + offset))

def resaltar_casillas(pantalla, tablero, casilla_sel, movimientos_validos):
    """Resalta la selección, los movimientos posibles y el hover del ratón."""
    # 1. Resaltar casilla seleccionada (Amarillo suave)
    if casilla_sel:
        f, c = casilla_sel
        s = pygame.Surface((TAM_CASILLA, TAM_CASILLA))
        s.set_alpha(100) # Transparencia
        s.fill(pygame.Color("yellow"))
        pantalla.blit(s, (c * TAM_CASILLA, f * TAM_CASILLA))

        # 2. Resaltar movimientos posibles (Puntos o círculos verdes)
        for mov in movimientos_validos:
            # Convertimos el destino del movimiento a coordenadas (f, c)
            destino = mov.to_square
            col_dest = chess.square_file(destino)
            fil_dest = 7 - chess.square_rank(destino)
                
            pygame.draw.circle(pantalla, pygame.Color("blue"), 
                            (col_dest * TAM_CASILLA + TAM_CASILLA//2, 
                                fil_dest * TAM_CASILLA + TAM_CASILLA//2), 8)

    # 3. Iluminar casilla bajo el ratón (Hover)
    x, y = pygame.mouse.get_pos()
    c, f = x // TAM_CASILLA, y // TAM_CASILLA
    # Solo iluminamos si es una casilla lógica del tablero
    if 0 <= c < 8 and 0 <= f < 8:
        s = pygame.Surface((TAM_CASILLA, TAM_CASILLA))
        s.set_alpha(50)
        s.fill(pygame.Color("blue"))
        pantalla.blit(s, (c * TAM_CASILLA, f * TAM_CASILLA))


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Mi Motor de Ajedrez - TFG")
    reloj = pygame.time.Clock()
    
    # Inicializamos el tablero de la lógica y cargamos las fotos
    tablero = chess.Board()
    cargar_imagenes()
    
    corriendo = True
    casilla_seleccionada = () # Guarda el último click del usuario (fila, col)
    clics_jugador = [] # Guarda dos clicks: [(origen), (destino)]
    movimientos_validos = [] # Nueva lista para los puntos verdes
    while corriendo:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                corriendo = False
            
            elif e.type == pygame.MOUSEBUTTONDOWN:
                ubicacion = pygame.mouse.get_pos()
                col = ubicacion[0] // TAM_CASILLA
                fil = ubicacion[1] // TAM_CASILLA

                #LÓGICA DE SELECCIÓN INTELIGENTE
                casilla_sq = chess.square(col, 7-fil)
                pieza = tablero.piece_at(casilla_sq)

                #Si ya hay una selección y hacemos clic en otra pieza del MISMO COLOR

                if pieza and pieza.color == tablero.turn:
                    casilla_seleccionada = (fil, col)
                    clics_jugador = [casilla_seleccionada]
                    # Actualizamos movimientos posibles para esta nueva pieza
                    movimientos_validos = [m for m in tablero.legal_moves if m.from_square == casilla_sq]
                
                # Si es el segundo clic (posible movimiento)
                elif len(clics_jugador) == 1:
                    origen = chess.square(clics_jugador[0][1], 7 - clics_jugador[0][0])
                    destino = chess.square(col, 7 - fil)
                    movimiento = chess.Move(origen, destino)
                    
                    if movimiento in tablero.legal_moves:
                        tablero.push(movimiento)
                        casilla_seleccionada = ()
                        clics_jugador = []
                        movimientos_validos = []
                    else:
                        # Si no es legal y no es pieza propia, limpiamos
                        casilla_seleccionada = ()
                        clics_jugador = []
                        movimientos_validos = []
                else:
                    # Primer clic en vacío o pieza enemiga (no hace nada)
                    pass

                # #Si el usuario hace click dos veces en la misma casilla, deseleccionamos

                # if casilla_seleccionada == (fil,col):
                #     casilla_seleccionada = ()
                #     clics_jugador = []

                # else:
                #     casilla_seleccionada = (fil, col)
                #     clics_jugador.append(casilla_seleccionada)
                
                # #Cuando tenemos dos clicks, intentamos el movimiento
                # if len(clics_jugador) == 2:
                #     # Convertimos coordenadas de Pygame a formato ajedrez (0-63)
                #     origen = chess.square(clics_jugador[0][1], 7 - clics_jugador[0][0])
                #     destino = chess.square(clics_jugador[1][1], 7 - clics_jugador[1][0])

                #     movimiento = chess.Move(origen, destino)

                #     # Verificamos si es un movimiento legal
                #     if movimiento in tablero.legal_moves:
                #         tablero.push(movimiento)
                #         print(f"Movimiento realizado: {movimiento}")
                #     else:
                #         print("Movimiento ilegal")

                #     # Limpiamos para la siguiente jugada
                #     casilla_seleccionada = ()
                #     clics_jugador = []

        # 1. Dibujamos el fondo (cuadros)
        dibujar_tablero(pantalla)
        
        #LLAMADA IMPORTANTE: Resaltar antes de las piezas para que quedan debajo
        resaltar_casillas(pantalla,tablero,casilla_seleccionada,movimientos_validos)
        
        # 2. Dibujamos las piezas encima
        dibujar_piezas(pantalla, tablero)
        
        pygame.display.flip()
        reloj.tick(MAX_FPS)

    pygame.quit()

if __name__ == "__main__":
    main()