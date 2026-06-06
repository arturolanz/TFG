import pygame
import chess

# --- Configuración General ---
ANCHO_TABLERO = 512
ANCHO_PANEL = 180
ANCHO = ANCHO_TABLERO + ANCHO_PANEL  # 692 píxeles en total
ALTO = 512
TAM_CASILLA = ALTO // 8
MAX_FPS = 15
DIMENSION = 8
PIEZAS = {}              # Diccionario para guardar las imágenes cargadas en memoria
COLOR_HOVER = (0, 150, 255, 80)      # Azul cian semitransparente
COLOR_ULTIMO_MOV = (255, 255, 0, 80)   # Amarillo semitransparente
COLOR_JAQUE = (255, 0, 0, 150)         # Rojo intenso translúcido

# Añade también esta variable global de estado para el cartel de mate
ocultar_cartel_final = False


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

def dibujar_barra_estado(pantalla, texto, es_final=False):
    """
    Dibuja una franja informativa. Si es_final es True, adopta un tono 
    dorado elegante para mostrar el resultado permanente.
    """
    import pygame
    
    # Dorado apagado (184, 134, 11) para el final, Gris oscuro durante la partida
    color_fondo = (184, 134, 11) if es_final else pygame.Color("darkslategray")
    pygame.draw.rect(pantalla, color_fondo, pygame.Rect(0, ALTO, ANCHO, 40))
    
    pygame.font.init()
    fuente = pygame.font.SysFont("Arial", 15, bold=True)
    
    # Formateamos el texto dependiendo del estado de la partida
    texto_mostrar = texto if es_final else f"Teoría: {texto}"
    
    superficie_texto = fuente.render(texto_mostrar, True, pygame.Color("white"))
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

def dibujar_efectos_visuales(pantalla, tablero, tamano_casilla, color_humano):
    """
    Dibuja los resaltados dinámicos (último movimiento, jaque y hover del ratón).
    Recibe una copia estática del tablero (tablero_visual) para evitar el ruido del hilo de la IA.
    """
    import pygame
    import chess
    
    # 1. Resaltar el último movimiento realizado (Origen y Destino)
    if tablero.move_stack:
        ultimo_mov = tablero.peek()
        
        for cas in [ultimo_mov.from_square, ultimo_mov.to_square]:
            col_math = chess.square_file(cas)
            fila_math = chess.square_rank(cas)
            
            if color_humano == chess.WHITE:
                fila_pantalla = 7 - fila_math
                col_pantalla = col_math
            else:
                fila_pantalla = fila_math
                col_pantalla = 7 - col_math
            
            superficie_mov = pygame.Surface((tamano_casilla, tamano_casilla), pygame.SRCALPHA)
            superficie_mov.fill(COLOR_ULTIMO_MOV) 
            pantalla.blit(superficie_mov, (col_pantalla * tamano_casilla, fila_pantalla * tamano_casilla))

    # 2. Iluminar en rojo al Rey si está en Jaque (Efecto Resplandor)
    if tablero.is_check():
        rey_sq = tablero.king(tablero.turn)
        if rey_sq is not None:
            col_math = chess.square_file(rey_sq)
            fila_math = chess.square_rank(rey_sq)
            
            if color_humano == chess.WHITE:
                fila_pantalla = 7 - fila_math
                col_pantalla = col_math
            else:
                fila_pantalla = fila_math
                col_pantalla = 7 - col_math
                
            superficie_jaque = pygame.Surface((tamano_casilla, tamano_casilla), pygame.SRCALPHA)
            centro = (tamano_casilla // 2, tamano_casilla // 2)
            radio_max = (tamano_casilla // 2) - 2 
            
            for radio in range(radio_max, 0, -2):
                alfa = int(200 * (1 - (radio / radio_max)))
                pygame.draw.circle(superficie_jaque, (255, 0, 0, alfa), centro, radio)
                
            pantalla.blit(superficie_jaque, (col_pantalla * tamano_casilla, fila_pantalla * tamano_casilla))

    # 3. Hover del ratón sobre el tablero
    x_raton, y_raton = pygame.mouse.get_pos()
    if 0 <= x_raton < 8 * tamano_casilla and 0 <= y_raton < 8 * tamano_casilla:
        col_hover = x_raton // tamano_casilla
        fila_hover = y_raton // tamano_casilla
        
        superficie_hover = pygame.Surface((tamano_casilla, tamano_casilla), pygame.SRCALPHA)
        superficie_hover.fill(COLOR_HOVER) 
        pantalla.blit(superficie_hover, (col_hover * tamano_casilla, fila_hover * tamano_casilla))

def dibujar_foco_teatral(pantalla, tablero, tamano_casilla, color_humano):
    """
    Oscurece el tablero suavemente y aplica un resplandor radial (foco de luz)
    exclusivamente sobre el rey que recibe el mate y las piezas atacantes.
    """
    import pygame
    import chess

    if not tablero.is_checkmate():
        return

    # 1. Aplicar sombra global suave a todo el tablero
    # Usamos opacidad 80 en lugar de 150 para que el resto del tablero se siga viendo bien
    sombra_global = pygame.Surface((8 * tamano_casilla, 8 * tamano_casilla), pygame.SRCALPHA)
    sombra_global.fill((0, 0, 0, 80)) 
    pantalla.blit(sombra_global, (0, 0))

    # Obtenemos las casillas protagonistas
    rey_sq = tablero.king(tablero.turn)
    atacantes = tablero.checkers()
    protagonistas = [rey_sq] + list(atacantes)

    # 2. Iluminar y redibujar a los protagonistas
    for cas in protagonistas:
        col_math = chess.square_file(cas)
        fila_math = chess.square_rank(cas)

        # Adaptamos la perspectiva
        if color_humano == chess.WHITE:
            fila_pantalla = 7 - fila_math
            col_pantalla = col_math
        else:
            fila_pantalla = fila_math
            col_pantalla = 7 - col_math

        coord_x = col_pantalla * tamano_casilla
        coord_y = fila_pantalla * tamano_casilla

        # A. Crear el resplandor radial (Foco de luz)
        superficie_luz = pygame.Surface((tamano_casilla, tamano_casilla), pygame.SRCALPHA)
        centro = (tamano_casilla // 2, tamano_casilla // 2)
        radio_max = tamano_casilla // 2

        # Dibujamos anillos concéntricos hacia adentro para crear el difuminado
        for radio in range(radio_max, 0, -2):
            # El centro es muy luminoso (alfa 150), los bordes desaparecen (alfa 0)
            alfa = int(150 * (1 - (radio / radio_max))) 
            # width=2 evita que los círculos se superpongan y saturen el canal alfa
            pygame.draw.circle(superficie_luz, (255, 255, 255, alfa), centro, radio, 2)
        
        pantalla.blit(superficie_luz, (coord_x, coord_y))

        # B. Redibujar la pieza original encima de la luz
        # Como está en interfaz.py, podemos acceder al diccionario PIEZAS directamente
        pieza = tablero.piece_at(cas)
        if pieza:
            nombre_pieza = f"{'w' if pieza.color == chess.WHITE else 'b'}{pieza.symbol().lower()}"
            offset = (tamano_casilla - PIEZAS[nombre_pieza].get_width()) // 2
            pantalla.blit(PIEZAS[nombre_pieza], (coord_x + offset, coord_y + offset))

def dibujar_panel_lateral(pantalla, tablero, color_humano):
    """
    Dibuja el panel derecho con el recuento de material agrupado en la parte superior.
    """
    import pygame
    import chess
    
    # 1. Fondo TOTAL del panel. ¡Esto borra la basura visual del frame anterior!
    rect_panel = pygame.Rect(ANCHO_TABLERO, 0, ANCHO_PANEL, ALTO)
    pygame.draw.rect(pantalla, (38, 36, 33), rect_panel) # Tono gris/marrón estilo chess.com
    pygame.draw.line(pantalla, (60, 60, 60), (ANCHO_TABLERO, 0), (ANCHO_TABLERO, ALTO), 2)
    
    # 2. Configuración de conteo
    piezas_iniciales = {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2, chess.ROOK: 2, chess.QUEEN: 1}
    valores = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
    
    capturadas_por_blancas, capturadas_por_negras = [], []
    puntos_blancas, puntos_negras = 0, 0

    for tipo, cantidad_inicial in piezas_iniciales.items():
        blancas_vivas = len(tablero.pieces(tipo, chess.WHITE))
        negras_vivas = len(tablero.pieces(tipo, chess.BLACK))
        
        puntos_blancas += blancas_vivas * valores[tipo]
        puntos_negras += negras_vivas * valores[tipo]
        
        capturadas_por_blancas.extend(['b' + chess.piece_symbol(tipo)] * (cantidad_inicial - negras_vivas))
        capturadas_por_negras.extend(['w' + chess.piece_symbol(tipo).upper()] * (cantidad_inicial - blancas_vivas))

    orden_valor = {'q': 5, 'r': 4, 'b': 3, 'n': 2, 'p': 1}
    capturadas_por_blancas.sort(key=lambda x: orden_valor.get(x[1].lower(), 0), reverse=True)
    capturadas_por_negras.sort(key=lambda x: orden_valor.get(x[1].lower(), 0), reverse=True)

    ventaja_blancas = puntos_blancas - puntos_negras
    
    if color_humano == chess.WHITE:
        piezas_top, piezas_bot = capturadas_por_negras, capturadas_por_blancas
        texto_ventaja_top = f"+{abs(ventaja_blancas)}" if ventaja_blancas < 0 else ""
        texto_ventaja_bot = f"+{ventaja_blancas}" if ventaja_blancas > 0 else ""
    else:
        piezas_top, piezas_bot = capturadas_por_blancas, capturadas_por_negras
        texto_ventaja_top = f"+{ventaja_blancas}" if ventaja_blancas > 0 else ""
        texto_ventaja_bot = f"+{abs(ventaja_blancas)}" if ventaja_blancas < 0 else ""

    pygame.font.init()
    fuente = pygame.font.SysFont("Helvetica", 14, bold=True)
    
    def renderizar_bloque(piezas_array, texto_ventaja, y_inicio):
        x_actual = ANCHO_TABLERO + 15
        if texto_ventaja:
            sup_texto = fuente.render(texto_ventaja, True, (160, 160, 160))
            pantalla.blit(sup_texto, (x_actual, y_inicio + 4))
            x_actual += 30 
            
        for miniatura in piezas_array:
            if x_actual > ANCHO - 25: 
                x_actual = ANCHO_TABLERO + 45 # Sangría si hay doble línea
                y_inicio += 20
            
            clave = miniatura[0].lower() + miniatura[1].lower()
            if clave in PIEZAS:
                # Aumentamos de (20, 20) a (26, 26)
                img_mini = pygame.transform.smoothscale(PIEZAS[clave], (26, 26))
                pantalla.blit(img_mini, (x_actual, y_inicio - 3))
            
            # Aumentamos el espaciado para que respiren más
            x_actual += 10

    # ¡Ambas barras juntas en la zona superior!
    renderizar_bloque(piezas_top, texto_ventaja_top, y_inicio=20)
    renderizar_bloque(piezas_bot, texto_ventaja_bot, y_inicio=60)

def dibujar_historial_movimientos(pantalla, tablero, indice_scroll, y_inicio=110):
    """
    Dibuja un historial tabular estilo chess.com en la zona inferior derecha,
    resaltando en verde la última jugada realizada.
    """
    import pygame
    import chess

    pygame.font.init()
    fuente_texto = pygame.font.SysFont("Helvetica", 14, bold=True)
    fuente_num = pygame.font.SysFont("Helvetica", 14)

    x_base = ANCHO_TABLERO
    
    # 1. Fondo exclusivo del historial
    pygame.draw.rect(pantalla, (30, 28, 25), (x_base, y_inicio, ANCHO_PANEL, ALTO - y_inicio))
    pygame.draw.line(pantalla, (50, 50, 50), (x_base, y_inicio), (ANCHO, y_inicio), 2)

    # 2. Traducción a SAN (Notación Algebraica Estándar) en Español
    tablero_fantasma = chess.Board()
    movimientos_san = []
    for mov in tablero.move_stack:
        movimientos_san.append(tablero_fantasma.san(mov))
        tablero_fantasma.push(mov)

    traduccion_es = str.maketrans("KQRBN", "RDTAC")

    textos_historial = []
    for i in range(0, len(movimientos_san), 2):
        turno_num = (i // 2) + 1
        mov_b = movimientos_san[i].translate(traduccion_es)
        mov_n = movimientos_san[i+1].translate(traduccion_es) if i + 1 < len(movimientos_san) else ""
        textos_historial.append((turno_num, mov_b, mov_n))

    # 3. Matemáticas de la ventana visible
    max_lineas = 6 
    total_turnos = len(textos_historial)
    indice_scroll = max(0, min(indice_scroll, total_turnos - max_lineas))
    lineas_visibles = textos_historial[indice_scroll : indice_scroll + max_lineas]

    # 4. Renderizado en Columnas con Resalte Verde
    y_actual = y_inicio
    alto_fila = 26
    
    # Identificadores para pintar la casilla verde
    ultimo_idx_absoluto = len(textos_historial) - 1
    es_turno_blancas_ultimo = (len(movimientos_san) % 2 != 0)

    for i, (turno, mov_b, mov_n) in enumerate(lineas_visibles):
        # Índice real del turno en la partida completa
        idx_real = indice_scroll + i
        
        # Efecto "Cebra" para las filas
        color_fila = (40, 38, 35) if i % 2 == 0 else (34, 32, 29)
        pygame.draw.rect(pantalla, color_fila, (x_base, y_actual, ANCHO_PANEL, alto_fila))

        # ---> NUEVO: Pintar recuadro verde si es la última jugada <---
        if idx_real == ultimo_idx_absoluto and len(movimientos_san) > 0:
            color_resalte = (86, 126, 58) # Verde sutil estilo ajedrez
            if es_turno_blancas_ultimo:
                # Resaltar la columna de las blancas
                pygame.draw.rect(pantalla, color_resalte, (x_base + 45, y_actual + 2, 60, 22), border_radius=4)
            else:
                # Resaltar la columna de las negras
                pygame.draw.rect(pantalla, color_resalte, (x_base + 110, y_actual + 2, 60, 22), border_radius=4)

        # Textos de la tabla
        pantalla.blit(fuente_num.render(f"{turno}.", True, (130, 130, 130)), (x_base + 10, y_actual + 5))
        pantalla.blit(fuente_texto.render(mov_b, True, (240, 240, 240)), (x_base + 50, y_actual + 5))
        if mov_n:
            pantalla.blit(fuente_texto.render(mov_n, True, (240, 240, 240)), (x_base + 115, y_actual + 5))

        y_actual += alto_fila

    # 5. Botones de navegación interactivos
    y_botones = ALTO - 45
    rect_izq = pygame.Rect(x_base + 25, y_botones, 55, 30)
    rect_der = pygame.Rect(x_base + 100, y_botones, 55, 30)

    color_btn_izq = (60, 60, 60) if indice_scroll > 0 else (40, 40, 40)
    color_btn_der = (60, 60, 60) if indice_scroll < total_turnos - max_lineas else (40, 40, 40)

    pygame.draw.rect(pantalla, color_btn_izq, rect_izq, border_radius=5)
    pygame.draw.rect(pantalla, color_btn_der, rect_der, border_radius=5)

    fuente_flechas = pygame.font.SysFont("Helvetica", 16, bold=True)
    pantalla.blit(fuente_flechas.render("<", True, (200, 200, 200)), (rect_izq.centerx - 5, rect_izq.centery - 8))
    pantalla.blit(fuente_flechas.render(">", True, (200, 200, 200)), (rect_der.centerx - 5, rect_der.centery - 8))

    return indice_scroll, rect_izq, rect_der