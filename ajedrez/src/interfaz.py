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
    Pantalla inicial sobria para configurar la partida.
    Permite elegir color y escribir o pegar una apertura.
    Devuelve: (color_elegido, nombre_apertura)
    """
    import pygame
    import chess
    import sys

    pygame.font.init()

    # Fuentes normales, sin estilo exagerado
    fuente_titulo = pygame.font.SysFont("Arial", 30, bold=True)
    fuente_subtitulo = pygame.font.SysFont("Arial", 15)
    fuente_btn = pygame.font.SysFont("Arial", 19, bold=True)
    fuente_label = pygame.font.SysFont("Arial", 16)
    fuente_input = pygame.font.SysFont("Arial", 15)
    fuente_ayuda = pygame.font.SysFont("Arial", 12)

    # Paleta parecida a una app de escritorio
    fondo = (34, 34, 31)
    panel = (43, 42, 38)
    panel_borde = (78, 75, 68)

    texto = (235, 232, 224)
    texto_suave = (165, 160, 150)

    claro = (230, 226, 216)
    oscuro = (24, 24, 22)
    verde = (118, 150, 86)

    # Layout más compacto
    panel_rect = pygame.Rect(0, 0, 560, 330)
    panel_rect.center = (ancho // 2, alto // 2)

    margen_x = panel_rect.x + 48

    btn_blancas = pygame.Rect(margen_x, panel_rect.y + 105, 210, 48)
    btn_negras = pygame.Rect(margen_x + 250, panel_rect.y + 105, 210, 48)

    input_rect = pygame.Rect(margen_x, panel_rect.y + 215, 460, 42)

    check_guiada_rect = pygame.Rect(margen_x, input_rect.bottom + 34, 18, 18)

    texto_apertura = ""
    input_activo = False
    apertura_guiada = False

    while True:
        mouse = pygame.mouse.get_pos()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif e.type == pygame.MOUSEBUTTONDOWN:
                input_activo = input_rect.collidepoint(e.pos)

                if check_guiada_rect.collidepoint(e.pos):
                    apertura_guiada = not apertura_guiada

                if btn_blancas.collidepoint(e.pos):
                    return chess.WHITE, texto_apertura.strip(), apertura_guiada

                elif btn_negras.collidepoint(e.pos):
                    return chess.BLACK, texto_apertura.strip(), apertura_guiada

            elif e.type == pygame.KEYDOWN and input_activo:
                mods = pygame.key.get_mods()

                if e.key == pygame.K_RETURN:
                    input_activo = False

                elif e.key == pygame.K_ESCAPE:
                    texto_apertura = ""
                    input_activo = False

                elif e.key == pygame.K_BACKSPACE:
                    texto_apertura = texto_apertura[:-1]

                elif e.key == pygame.K_a and (mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META):
                    texto_apertura = ""

                elif e.key == pygame.K_v and (mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META):
                    pegado = leer_texto_portapapeles()
                    if pegado:
                        texto_apertura += pegado

                elif e.unicode:
                    texto_apertura += e.unicode

        # Fondo liso, sin patrón llamativo
        pantalla.fill(fondo)

        # Panel principal
        pygame.draw.rect(pantalla, panel, panel_rect)
        pygame.draw.rect(pantalla, panel_borde, panel_rect, 2)

        # Cabecera
        titulo = fuente_titulo.render("Nueva partida", True, texto)
        pantalla.blit(titulo, (margen_x, panel_rect.y + 34))

        subtitulo = fuente_subtitulo.render(
            "Configura el color del jugador y una apertura opcional.",
            True,
            texto_suave
        )
        pantalla.blit(subtitulo, (margen_x, panel_rect.y + 70))

        # Botón blancas
        hover_b = btn_blancas.collidepoint(mouse)
        pygame.draw.rect(
            pantalla,
            (240, 237, 228) if hover_b else claro,
            btn_blancas
        )
        pygame.draw.rect(pantalla, (120, 116, 108), btn_blancas, 1)

        txt_b = fuente_btn.render("Jugar con blancas", True, (30, 30, 28))
        pantalla.blit(
            txt_b,
            (
                btn_blancas.centerx - txt_b.get_width() // 2,
                btn_blancas.centery - txt_b.get_height() // 2
            )
        )

        # Botón negras
        hover_n = btn_negras.collidepoint(mouse)
        pygame.draw.rect(
            pantalla,
            (34, 34, 32) if hover_n else oscuro,
            btn_negras
        )
        pygame.draw.rect(pantalla, (120, 116, 108), btn_negras, 1)

        txt_n = fuente_btn.render("Jugar con negras", True, (235, 235, 235))
        pantalla.blit(
            txt_n,
            (
                btn_negras.centerx - txt_n.get_width() // 2,
                btn_negras.centery - txt_n.get_height() // 2
            )
        )

        # Separador
        pygame.draw.line(
            pantalla,
            (75, 72, 66),
            (margen_x, panel_rect.y + 180),
            (panel_rect.right - 48, panel_rect.y + 180)
        )

        # Campo de apertura
        label = fuente_label.render("Apertura a entrenar", True, texto)
        pantalla.blit(label, (margen_x, panel_rect.y + 194))

        pygame.draw.rect(pantalla, (28, 28, 26), input_rect)
        pygame.draw.rect(
            pantalla,
            verde if input_activo else (90, 86, 78),
            input_rect,
            2 if input_activo else 1
        )

        if texto_apertura:
            dibujar_texto_recortado(
                pantalla,
                texto_apertura,
                fuente_input,
                texto,
                input_rect,
                padding=10,
                mostrar_cursor=input_activo
            )
        else:
            dibujar_texto_recortado(
                pantalla,
                "Opcional",
                fuente_input,
                (120, 116, 108),
                input_rect,
                padding=10,
                mostrar_cursor=False
            )

        ayuda = fuente_ayuda.render(
            "Ctrl+V para pegar · Enter para aceptar · Esc para limpiar",
            True,
            texto_suave
        )
        pantalla.blit(ayuda, (margen_x, input_rect.bottom + 10))

        # Check: apertura guiada
        pygame.draw.rect(pantalla, (28, 28, 26), check_guiada_rect)
        pygame.draw.rect(
            pantalla,
            (118, 150, 86) if apertura_guiada else (90, 86, 78),
            check_guiada_rect,
            2
        )

        if apertura_guiada:
            marca = pygame.Rect(
                check_guiada_rect.x + 4,
                check_guiada_rect.y + 4,
                check_guiada_rect.width - 8,
                check_guiada_rect.height - 8
            )
            pygame.draw.rect(pantalla, (118, 150, 86), marca)

        texto_check = fuente_ayuda.render(
            "Guiada: mostrar movimientos desde la posición inicial",
            True,
            texto_suave
        )
        pantalla.blit(texto_check, (check_guiada_rect.right + 10, check_guiada_rect.y - 1))

        pygame.display.flip()
        reloj.tick(60)
    


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
                # Aumentamos el tamaño a 32x32 y subimos un poco la Y (-6) para centrar
                img_mini = pygame.transform.smoothscale(PIEZAS[clave], (32, 32))
                pantalla.blit(img_mini, (x_actual, y_inicio - 6))
            
            x_actual += 12 # Separamos un par de píxeles más para compensar el tamaño

    # ¡Ambas barras juntas en la zona superior!
    renderizar_bloque(piezas_top, texto_ventaja_top, y_inicio=20)
    renderizar_bloque(piezas_bot, texto_ventaja_bot, y_inicio=60)

def dibujar_historial_movimientos(pantalla, tablero_real, offset_visual, y_inicio=110):
    """
    Historial que sigue la jugada seleccionada en verde.
    Las flechas de navegación ahora están ancladas de forma relativa debajo de la tabla.
    """
    import pygame
    import chess

    pygame.font.init()
    fuente_texto = pygame.font.SysFont("Helvetica", 14, bold=True)
    fuente_num = pygame.font.SysFont("Helvetica", 14)
    x_base = ANCHO_TABLERO
    
    # Fondo del historial
    pygame.draw.rect(pantalla, (30, 28, 25), (x_base, y_inicio, ANCHO_PANEL, ALTO - y_inicio))
    pygame.draw.line(pantalla, (50, 50, 50), (x_base, y_inicio), (ANCHO, y_inicio), 2)

    tablero_fantasma = chess.Board()
    movimientos_san = []
    for mov in tablero_real.move_stack:
        movimientos_san.append(tablero_fantasma.san(mov))
        tablero_fantasma.push(mov)

    traduccion_es = str.maketrans("KQRBN", "RDTAC")
    textos_historial = []
    for i in range(0, len(movimientos_san), 2):
        turno_num = (i // 2) + 1
        mov_b = movimientos_san[i].translate(traduccion_es)
        mov_n = movimientos_san[i+1].translate(traduccion_es) if i + 1 < len(movimientos_san) else ""
        textos_historial.append((turno_num, mov_b, mov_n))

    total_movimientos = len(movimientos_san)
    indice_observado = total_movimientos - 1 + offset_visual
    
    max_lineas = 6 
    total_filas = len(textos_historial)
    
    if total_filas > 0:
        fila_observada = max(0, indice_observado // 2)
        indice_scroll = max(0, fila_observada - (max_lineas // 2))
        indice_scroll = min(indice_scroll, max(0, total_filas - max_lineas))
    else:
        indice_scroll = 0

    lineas_visibles = textos_historial[indice_scroll : indice_scroll + max_lineas]

    y_actual = y_inicio
    alto_fila = 26

    for i, (turno, mov_b, mov_n) in enumerate(lineas_visibles):
        idx_real_fila = indice_scroll + i
        color_fila = (40, 38, 35) if i % 2 == 0 else (34, 32, 29)
        pygame.draw.rect(pantalla, color_fila, (x_base, y_actual, ANCHO_PANEL, alto_fila))

        if idx_real_fila * 2 == indice_observado: 
            pygame.draw.rect(pantalla, (86, 126, 58), (x_base + 45, y_actual + 2, 60, 22), border_radius=4)
        elif idx_real_fila * 2 + 1 == indice_observado: 
            pygame.draw.rect(pantalla, (86, 126, 58), (x_base + 110, y_actual + 2, 60, 22), border_radius=4)

        pantalla.blit(fuente_num.render(f"{turno}.", True, (130, 130, 130)), (x_base + 10, y_actual + 5))
        pantalla.blit(fuente_texto.render(mov_b, True, (240, 240, 240)), (x_base + 50, y_actual + 5))
        if mov_n:
            pantalla.blit(fuente_texto.render(mov_n, True, (240, 240, 240)), (x_base + 115, y_actual + 5))
        y_actual += alto_fila

    # Botones de flechas fijados matemáticamente debajo de las 6 líneas
    y_botones = y_inicio + (max_lineas * alto_fila) + 15
    rect_izq = pygame.Rect(x_base + 25, y_botones, 55, 30)
    rect_der = pygame.Rect(x_base + 100, y_botones, 55, 30)

    color_btn_izq = (60, 60, 60) if abs(offset_visual) < total_movimientos else (40, 40, 40)
    color_btn_der = (60, 60, 60) if offset_visual < 0 else (40, 40, 40)

    pygame.draw.rect(pantalla, color_btn_izq, rect_izq, border_radius=5)
    pygame.draw.rect(pantalla, color_btn_der, rect_der, border_radius=5)

    fuente_flechas = pygame.font.SysFont("Helvetica", 16, bold=True)
    pantalla.blit(fuente_flechas.render("<", True, (200, 200, 200)), (rect_izq.centerx - 5, rect_izq.centery - 8))
    pantalla.blit(fuente_flechas.render(">", True, (200, 200, 200)), (rect_der.centerx - 5, rect_der.centery - 8))

    return offset_visual, rect_izq, rect_der


def dibujar_botones_admin(pantalla, apertura_actual, y_inicio=340):
    """
    Dibuja los botones en la base del panel, separados del historial.
    """
    import pygame
    pygame.font.init()
    fuente = pygame.font.SysFont("Helvetica", 12, bold=True)
    x_base = ANCHO_TABLERO + 15

    # 1. Botón Guardar PGN (Fijado en y=340)
    rect_pgn = pygame.Rect(x_base, y_inicio, 150, 30)
    pygame.draw.rect(pantalla, (60, 60, 60), rect_pgn, border_radius=4)
    texto_pgn = fuente.render("Descargar PGN", True, (240, 240, 240))
    pantalla.blit(texto_pgn, (x_base + 32, y_inicio + 8))

    # 2. Botón Apertura (Desplazado matemáticamente hacia abajo)
    y_btn_2 = y_inicio + 40
    rect_ap = pygame.Rect(x_base, y_btn_2, 150, 30)
    color_ap = (86, 126, 58) if apertura_actual else (60, 60, 60)
    pygame.draw.rect(pantalla, color_ap, rect_ap, border_radius=4)
    
    etiqueta = apertura_actual if apertura_actual else "Elegir Apertura"
    if len(etiqueta) > 18:
        etiqueta = etiqueta[:16] + "..."
        
    texto_ap = fuente.render(etiqueta, True, (240, 240, 240))
    pantalla.blit(texto_ap, (x_base + 10, y_btn_2 + 8)) 

    return rect_pgn, rect_ap

def leer_texto_portapapeles():
    """
    Lee texto del portapapeles en Windows sin usar tkinter.
    Evita errores Tcl_AsyncDelete al combinar Pygame con hilos.
    """
    import ctypes
    import pygame

    texto = ""

    # 1. Método principal en Windows: WinAPI
    try:
        CF_UNICODETEXT = 13
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        if user32.OpenClipboard(None):
            try:
                handle = user32.GetClipboardData(CF_UNICODETEXT)
                if handle:
                    puntero = kernel32.GlobalLock(handle)
                    if puntero:
                        try:
                            texto = ctypes.wstring_at(puntero)
                        finally:
                            kernel32.GlobalUnlock(handle)
            finally:
                user32.CloseClipboard()

    except Exception:
        texto = ""

    # 2. Respaldo: pygame.scrap
    if not texto:
        try:
            if not pygame.scrap.get_init():
                pygame.scrap.init()

            datos = pygame.scrap.get(pygame.SCRAP_TEXT)

            if datos:
                for codificacion in ("utf-8-sig", "utf-16", "utf-16le", "cp1252", "latin-1"):
                    try:
                        texto = datos.decode(codificacion)
                        break
                    except UnicodeDecodeError:
                        pass

        except Exception:
            texto = ""

    return limpiar_texto_pegado(texto)


def limpiar_texto_pegado(texto):
    """
    Limpia el texto pegado en el input de apertura.
    Si se copia una línea completa del JSON, extrae el nombre de la apertura.
    Si se copia un nombre con dos puntos, lo respeta entero.
    """
    import json
    import re

    if not texto:
        return ""

    texto = texto.replace("\x00", "")
    texto = texto.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    texto = " ".join(texto.split()).strip()

    texto_sin_coma = texto.rstrip(",")

    # Solo interpretamos como línea JSON si empieza por una clave entre comillas.
    # Ejemplo:
    # "e2e4 c7c5": "Defensa Siciliana",
    if re.match(r'^\s*"[^"]+"\s*:\s*', texto_sin_coma):
        try:
            objeto = json.loads("{" + texto_sin_coma + "}")
            if isinstance(objeto, dict) and objeto:
                return str(next(iter(objeto.values()))).strip()
        except Exception:
            pass

        coincidencia = re.match(
            r'^\s*"[^"]+"\s*:\s*"((?:\\.|[^"])*)"\s*$',
            texto_sin_coma
        )
        if coincidencia:
            try:
                return json.loads('"' + coincidencia.group(1) + '"').strip()
            except Exception:
                return coincidencia.group(1).strip()

    # Si se copia solo el valor entre comillas:
    # "Dragón: Ataque Yugoslavo"
    if len(texto_sin_coma) >= 2 and texto_sin_coma[0] == '"' and texto_sin_coma[-1] == '"':
        try:
            texto_sin_coma = json.loads(texto_sin_coma)
        except Exception:
            texto_sin_coma = texto_sin_coma[1:-1]

    texto_sin_coma = re.sub(r"[\x00-\x1f\x7f]", "", texto_sin_coma)

    return texto_sin_coma.strip()


def dibujar_texto_recortado(pantalla, texto, fuente, color, rect, padding=10, mostrar_cursor=False):
    """
    Dibuja texto dentro de un rectángulo sin limitar caracteres.
    Si el texto es largo, se muestra la parte final, como en un input profesional.
    """
    import pygame

    texto_visible = texto
    if mostrar_cursor and pygame.time.get_ticks() % 1000 < 500:
        texto_visible += "|"

    superficie = fuente.render(texto_visible, True, color)

    x = rect.x + padding
    if superficie.get_width() > rect.width - padding * 2:
        x = rect.right - padding - superficie.get_width()

    y = rect.centery - superficie.get_height() // 2

    clip_anterior = pantalla.get_clip()
    pantalla.set_clip(rect.inflate(-padding, -4))
    pantalla.blit(superficie, (x, y))
    pantalla.set_clip(clip_anterior)

def dibujar_editor_apertura(pantalla, texto_apertura, y_inicio=420):
    """
    Dibuja un editor compacto de apertura dentro del panel lateral.
    No limita caracteres: muestra la parte final del texto si es muy largo.
    """
    import pygame

    pygame.font.init()

    x_base = ANCHO_TABLERO + 15
    ancho_editor = 150

    fuente_titulo = pygame.font.SysFont("Segoe UI", 12, bold=True)
    fuente_input = pygame.font.SysFont("Segoe UI", 13)
    fuente_ayuda = pygame.font.SysFont("Segoe UI", 10)

    contenedor = pygame.Rect(x_base - 5, y_inicio, ancho_editor + 10, 86)
    input_rect = pygame.Rect(x_base, y_inicio + 25, ancho_editor, 30)

    pygame.draw.rect(pantalla, (30, 29, 26), contenedor, border_radius=8)
    pygame.draw.rect(pantalla, (118, 150, 86), contenedor, 1, border_radius=8)

    titulo = fuente_titulo.render("Apertura a entrenar", True, (235, 235, 235))
    pantalla.blit(titulo, (x_base, y_inicio + 7))

    pygame.draw.rect(pantalla, (20, 20, 18), input_rect, border_radius=5)
    pygame.draw.rect(pantalla, (118, 150, 86), input_rect, 2, border_radius=5)

    if texto_apertura:
        dibujar_texto_recortado(
            pantalla,
            texto_apertura,
            fuente_input,
            (245, 245, 245),
            input_rect,
            padding=8,
            mostrar_cursor=True
        )
    else:
        dibujar_texto_recortado(
            pantalla,
            "Ctrl+V o escribe...",
            fuente_input,
            (125, 122, 116),
            input_rect,
            padding=8,
            mostrar_cursor=True
        )

    ayuda = fuente_ayuda.render("Enter aplicar · Esc cancelar", True, (150, 145, 135))
    pantalla.blit(ayuda, (x_base, y_inicio + 62))