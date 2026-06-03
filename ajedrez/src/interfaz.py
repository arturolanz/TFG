import pygame
import chess

# --- Configuración General ---
ANCHO = ALTO = 512       # Tamaño de la ventana (8 casillas por 64 pixeles)
DIMENSION = 8            # Un tablero de ajedrez tiene 8x8 casillas
TAM_CASILLA = ALTO // DIMENSION
MAX_FPS = 15             # No necesitamos muchos FPS para el ajedrez
PIEZAS = {}              # Diccionario para guardar las imágenes cargadas en memoria

def cargar_imagenes():
    """Carga las imágenes de las piezas desde la carpeta 'images' a un diccionario."""
    piezas = ['wp', 'wr', 'wn', 'wb', 'wq', 'wk', 'bp', 'br', 'bn', 'bb', 'bq', 'bk']
    escala = 0.95 # Para que la pieza ocupe el 95% de la casilla y no se vea apretada
    tam_pieza = int(TAM_CASILLA * escala)
    
    for pieza in piezas:
        # Cargamos la imagen y la escalamos para que encaje perfectamente
        imagen = pygame.image.load("images/" + pieza + ".png")
        PIEZAS[pieza] = pygame.transform.scale(imagen, (tam_pieza, tam_pieza))

def dibujar_tablero(pantalla):
    """Dibuja el patrón cuadriculado del tablero (blanco y gris)."""
    colores = [pygame.Color("white"), pygame.Color("gray")]
    for f in range(DIMENSION):
        for c in range(DIMENSION):
            color = colores[((f + c) % 2)]
            pygame.draw.rect(pantalla, color, pygame.Rect(c*TAM_CASILLA, f*TAM_CASILLA, TAM_CASILLA, TAM_CASILLA))

def dibujar_piezas(pantalla, board):
    """
    Dibuja las piezas sobre el tablero basándose en el estado del motor (board).
    """
    # Calculamos cuánto espacio sobra para centrar la pieza en su casilla
    offset = (TAM_CASILLA - PIEZAS['wp'].get_width()) // 2
    
    for f in range(DIMENSION):
        for c in range(DIMENSION):
            # IMPORTANTE: python-chess cuenta desde abajo (fila 0 = abajo), 
            # pero pygame dibuja desde arriba (fila 0 = arriba).
            # Por eso invertimos la fila restando: 7 - f
            casilla = chess.square(c, 7 - f)
            pieza = board.piece_at(casilla) 
            
            if pieza is not None:
                # Determinamos el nombre del archivo (ej: 'w' + 'p' = 'wp' para peón blanco)
                color = 'w' if pieza.color == chess.WHITE else 'b'
                tipo = pieza.symbol().lower()
                nombre_pieza = color + tipo
                
                # Dibujamos la pieza sumando el offset en X e Y para centrarla
                pantalla.blit(PIEZAS[nombre_pieza], (c*TAM_CASILLA + offset, f*TAM_CASILLA + offset))

def resaltar_casillas(pantalla, casilla_sel, movimientos_validos):
    """Resalta la casilla clickeada, los movimientos posibles (puntos) y el ratón (hover)."""
    
    # 1. Resaltar casilla seleccionada (Cuadrado amarillo transparente)
    if casilla_sel:
        f, c = casilla_sel
        s = pygame.Surface((TAM_CASILLA, TAM_CASILLA))
        s.set_alpha(100) # 100 de transparencia
        s.fill(pygame.Color("yellow"))
        pantalla.blit(s, (c * TAM_CASILLA, f * TAM_CASILLA))

        # 2. Resaltar movimientos posibles para esa pieza (Círculos azules)
        for mov in movimientos_validos:
            destino = mov.to_square
            col_dest = chess.square_file(destino)
            fil_dest = 7 - chess.square_rank(destino) # Invertimos para pygame
            
            # Dibujamos el círculo justo en el centro de la casilla destino
            centro_x = col_dest * TAM_CASILLA + TAM_CASILLA//2
            centro_y = fil_dest * TAM_CASILLA + TAM_CASILLA//2
            pygame.draw.circle(pantalla, pygame.Color("blue"), (centro_x, centro_y), 8)

    # 3. Iluminar casilla bajo el ratón (Hover en azul suave)
    x, y = pygame.mouse.get_pos()
    c, f = x // TAM_CASILLA, y // TAM_CASILLA
    # Solo iluminamos si el ratón está dentro de los límites lógicos del tablero
    if 0 <= c < 8 and 0 <= f < 8:
        s = pygame.Surface((TAM_CASILLA, TAM_CASILLA))
        s.set_alpha(50)
        s.fill(pygame.Color("blue"))
        pantalla.blit(s, (c * TAM_CASILLA, f * TAM_CASILLA))

def mostrar_mensaje_final(pantalla, texto):
    """
    Dibuja un cartel rectangular semi-transparente con el resultado
    y las instrucciones para reiniciar.
    """
    # 1. Hacemos el banner un poco más alto (120px) para que quepan dos líneas
    banner = pygame.Surface((ANCHO, 120))
    banner.set_alpha(200) 
    banner.fill(pygame.Color("black"))
    pantalla.blit(banner, (0, ALTO // 2 - 60))

    pygame.font.init()
    
    # 2. Texto principal (El resultado)
    fuente_principal = pygame.font.SysFont("Arial", 28, bold=True)
    superficie_texto = fuente_principal.render(texto, True, pygame.Color("white"))
    texto_rect = superficie_texto.get_rect(center=(ANCHO // 2, ALTO // 2 - 15))
    pantalla.blit(superficie_texto, texto_rect)

    # 3. Texto secundario (Instrucciones de reinicio)
    fuente_secundaria = pygame.font.SysFont("Arial", 18)
    superficie_reinicio = fuente_secundaria.render("Pulsa 'R' para reiniciar", True, pygame.Color("lightgray"))
    reinicio_rect = superficie_reinicio.get_rect(center=(ANCHO // 2, ALTO // 2 + 25))
    pantalla.blit(superficie_reinicio, reinicio_rect)

def dibujar_barra_estado(pantalla, texto_apertura):
    """
    Dibuja una franja informativa en la parte inferior de la ventana
    para renderizar la apertura o fase de juego actual.
    """
    # Pintamos un rectángulo de fondo gris oscuro justo debajo del tablero (en la coordenada Y = 512)
    pygame.draw.rect(pantalla, pygame.Color("darkslategray"), pygame.Rect(0, ALTO, ANCHO, 40))
    
    pygame.font.init()
    fuente = pygame.font.SysFont("Arial", 15, bold=True)
    
    # Renderizamos el texto informativo en color blanco
    superficie_texto = fuente.render(f"Teoría: {texto_apertura}", True, pygame.Color("white"))
    texto_rect = superficie_texto.get_rect(center=(ANCHO // 2, ALTO + 20))
    
    pantalla.blit(superficie_texto, texto_rect)

def resaltar_guia_teorica(pantalla, movimiento_guia):
    """
    Dibuja un indicador visual azul en el tablero para sugerirle al 
    usuario el siguiente movimiento para completar la apertura elegida.
    """
    if movimiento_guia is not None:
        # Extraemos las casillas de origen y destino del movimiento chess.Move
        casilla_origen = movimiento_guia.from_square
        casilla_destino = movimiento_guia.to_square
        
        # Convertimos las casillas de la librería (0-63) a coordenadas X, Y de la pantalla
        # python-chess cuenta desde abajo a la izquierda, Pygame desde arriba a la izquierda
        for casilla, color in [(casilla_origen, (0, 191, 255)), (casilla_destino, (30, 144, 255))]:
            fila = 7 - (casilla // 8)
            columna = casilla % 8
            
            # Dibujamos un rectángulo con un borde grueso (4px) alrededor de las casillas sugeridas
            rectangulo = pygame.Rect(columna * TAM_CASILLA, fila * TAM_CASILLA, TAM_CASILLA, TAM_CASILLA)
            pygame.draw.rect(pantalla, color, rectangulo, 4)