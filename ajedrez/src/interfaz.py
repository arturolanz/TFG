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

def dibujar_piezas(pantalla, board, color_humano=chess.WHITE):
    """ Dibuja las piezas orientadas según el color del jugador. """
    for casilla in chess.SQUARES:
        pieza = board.piece_at(casilla)
        if pieza is not None:
            nombre_pieza = f"{'w' if pieza.color == chess.WHITE else 'b'}{pieza.symbol().lower()}"
            
            # MATEMÁTICA DE ESPEJO: Si jugamos con negras, invertimos filas y columnas
            if color_humano == chess.WHITE:
                fil = 7 - chess.square_rank(casilla)
                col = chess.square_file(casilla)
            else:
                fil = chess.square_rank(casilla)
                col = 7 - chess.square_file(casilla)
                
            offset = (TAM_CASILLA - PIEZAS[nombre_pieza].get_width()) // 2
            pantalla.blit(PIEZAS[nombre_pieza], (col * TAM_CASILLA + offset, fil * TAM_CASILLA + offset))

def resaltar_casillas(pantalla, casilla_seleccionada, movimientos_validos, color_humano=chess.WHITE):
    """ Resalta la casilla seleccionada y los posibles destinos adaptando la perspectiva. """
    superficie = pygame.Surface((TAM_CASILLA, TAM_CASILLA), pygame.SRCALPHA)
    
    if casilla_seleccionada:
        f, c = casilla_seleccionada
        superficie.fill((255, 255, 0, 100)) # Amarillo transparente
        pantalla.blit(superficie, (c * TAM_CASILLA, f * TAM_CASILLA))
        
        superficie.fill((0, 255, 0, 100)) # Verde para movimientos válidos
        for mov in movimientos_validos:
            if color_humano == chess.WHITE:
                f_dest = 7 - chess.square_rank(mov.to_square)
                c_dest = chess.square_file(mov.to_square)
            else:
                f_dest = chess.square_rank(mov.to_square)
                c_dest = 7 - chess.square_file(mov.to_square)
            pantalla.blit(superficie, (c_dest * TAM_CASILLA, f_dest * TAM_CASILLA))

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

def resaltar_guia_teorica(pantalla, movimiento_guia, color_humano=chess.WHITE):
    """ Dibuja la guía azul invertida si somos las negras. """
    if movimiento_guia is not None:
        casilla_origen = movimiento_guia.from_square
        casilla_destino = movimiento_guia.to_square
        
        for casilla, color in [(casilla_origen, (0, 191, 255)), (casilla_destino, (30, 144, 255))]:
            if color_humano == chess.WHITE:
                fil = 7 - (casilla // 8)
                columna = casilla % 8
            else:
                fil = (casilla // 8)
                columna = 7 - (casilla % 8)
                
            rectangulo = pygame.Rect(columna * TAM_CASILLA, fil * TAM_CASILLA, TAM_CASILLA, TAM_CASILLA)
            pygame.draw.rect(pantalla, color, rectangulo, 4)

def pantalla_seleccion_color(pantalla, reloj, ancho, alto):
    """
    Dibuja un menú de selección de bando antes de iniciar el bucle principal.
    Devuelve chess.WHITE o chess.BLACK según el botón pulsado.
    """
    fuente = pygame.font.SysFont("Helvetica", 32, bold=True)
    esperando = True
    color_elegido = None

    while esperando:
        pantalla.fill((40, 40, 40)) # Fondo gris oscuro elegante
        
        # Coordenadas y dimensiones de los botones
        rect_blancas = pygame.Rect(ancho//2 - 150, alto//2 - 80, 300, 60)
        rect_negras  = pygame.Rect(ancho//2 - 150, alto//2 + 20, 300, 60)
        
        # Dibujamos los botones
        pygame.draw.rect(pantalla, (240, 240, 240), rect_blancas, border_radius=10)
        pygame.draw.rect(pantalla, (30, 30, 30), rect_negras, border_radius=10)
        pygame.draw.rect(pantalla, (200, 200, 200), rect_negras, 2, border_radius=10) # Borde
        
        texto_b = fuente.render("Jugar con Blancas", True, (20, 20, 20))
        texto_n = fuente.render("Jugar con Negras", True, (240, 240, 240))
        
        pantalla.blit(texto_b, texto_b.get_rect(center=rect_blancas.center))
        pantalla.blit(texto_n, texto_n.get_rect(center=rect_negras.center))
        
        pygame.display.flip()
        
        # Escuchamos los clics
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if rect_blancas.collidepoint(evento.pos):
                    color_elegido = chess.WHITE
                    esperando = False
                elif rect_negras.collidepoint(evento.pos):
                    color_elegido = chess.BLACK
                    esperando = False
                    
        reloj.tick(15)
        
    return color_elegido


def dibujar_coordenadas(pantalla, color_humano):
    """
    Dibuja los indicadores de fila (1-8) y columna (a-h) en los bordes del tablero.
    La perspectiva se invierte automáticamente si el jugador humano lleva las negras.
    """
    # Usamos una fuente pequeña y legible
    fuente = pygame.font.SysFont("Helvetica", 14, bold=True)
    
    # 1. Definimos el orden lógico según la perspectiva del jugador
    if color_humano == chess.WHITE:
        filas = ['8', '7', '6', '5', '4', '3', '2', '1']
        columnas = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    else:
        filas = ['1', '2', '3', '4', '5', '6', '7', '8']
        columnas = ['h', 'g', 'f', 'e', 'd', 'c', 'b', 'a']
        
    for i in range(8):
        # Para que el texto se lea bien, puedes ajustar este color (ej. un gris oscuro o claro)
        # según la paleta de colores que estés usando para tus casillas.
        color_texto = (40, 40, 40) 
        
        # Dibujar NÚMEROS (Eje Y)
        # Se pintan en el margen izquierdo (columna 0) de cada fila
        texto_fila = fuente.render(filas[i], True, color_texto)
        # X=5 para un pequeño margen, Y depende de la iteración
        pantalla.blit(texto_fila, (5, i * TAM_CASILLA + 5))
        
        # Dibujar LETRAS (Eje X)
        # Se pintan en el margen inferior (fila 7) de cada columna
        texto_col = fuente.render(columnas[i], True, color_texto)
        # X depende de la iteración (casi al final de la casilla), Y pegado al fondo
        pantalla.blit(texto_col, (i * TAM_CASILLA + TAM_CASILLA - 15, 8 * TAM_CASILLA - 20))