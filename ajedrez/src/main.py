import pygame
import chess
import threading
import interfaz
import sys
from engine import ChessEngine

def main():
    # 1. PREPARACIÓN E INICIALIZACIÓN
    pygame.init()
    # Hacemos la ventana más alta (512 de tablero + 40 de barra de estado)
    pantalla = pygame.display.set_mode((interfaz.ANCHO, interfaz.ALTO + 40))
    pygame.display.set_caption("Mi Motor de Ajedrez - TFG")
    reloj = pygame.time.Clock()
    
    # Instanciamos nuestras dos herramientas separadas: el cerebro y los ojos
    motor = ChessEngine()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # =================================================================
    # MOSTRAR MENÚ DE SELECCIÓN ANTES DE INICIAR
    # =================================================================
    color_humano, apertura_a_entrenar, apertura_guiada = interfaz.pantalla_seleccion_color(pantalla, reloj, interfaz.ANCHO, interfaz.ALTO)

    if apertura_a_entrenar:
        if apertura_guiada:
            motor.reiniciar_juego()
            print(f"\n[SISTEMA] Modo Apertura Guiada: {apertura_a_entrenar}")
        else:
            motor.forzar_inicio_teorico(apertura_a_entrenar)
            print(f"\n[SISTEMA] Apertura cargada desde posicion final: {apertura_a_entrenar}")

    interfaz.cargar_imagenes()
    
    corriendo = True
    casilla_seleccionada = ()        # Guarda (fila, col) para pasárselo a Pygame (Dibujo)
    casilla_sq_seleccionada = None   # Guarda índice 0-63 para pasárselo a python-chess (Lógica)
    movimientos_validos = []         # Lista de jugadas legales de la pieza seleccionada

    # Variable de control para el estado del juego
    partida_finalizada = False
    mensaje_final = "" # Aquí guardaremos el texto dinámico

    ocultar_cartel_final = False  # <--- AÑADIDO: Reseteamos la visibilidad del cartel

    # ---> NUEVO: Variables para la paginación del historial <---
    # Variables de la ventana deslizante
    offset_visual = 0
    movimientos_previos = 0
    rect_btn_izq = pygame.Rect(0, 0, 0, 0)
    rect_btn_der = pygame.Rect(0, 0, 0, 0)
    rect_btn_pgn = pygame.Rect(0, 0, 0, 0)      # <--- NUEVO
    rect_btn_apertura = pygame.Rect(0, 0, 0, 0) # <--- NUEVO

    # ---> VARIABLES CACHÉ PARA EVITAR LA CONDICIÓN DE CARRERA <---
    tablero_base_seguro = motor.board.copy()
    tablero_visual = motor.board.copy()
    nombre_apertura_cache = motor.obtener_nombre_apertura()
    mov_sugerido_cache = motor.obtener_siguiente_movimiento_guia(apertura_a_entrenar)

    estado_ia = {"calculando": False}
    ingresando_apertura = False  # Flag para saber si estamos escribiendo
    texto_apertura = ""
    resultado_pgn = "*"

    # 2. BUCLE PRINCIPAL DEL JUEGO
    while corriendo:
        # --- GESTIÓN DE EVENTOS ---
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                corriendo = False

            # --- EVENTOS DE RATÓN --- #
            elif e.type == pygame.MOUSEBUTTONDOWN:
                
                # 1. Viaje en el tiempo (Clic botones)
                if rect_btn_izq.collidepoint(e.pos):
                    # No podemos retroceder más allá de la jugada 1
                    offset_visual = max(-len(motor.board.move_stack), offset_visual - 1)
                elif rect_btn_der.collidepoint(e.pos):
                    # No podemos avanzar más allá del presente (0)
                    offset_visual = min(0, offset_visual + 1)
                
                # ---> NUEVO: Clics de Administración <---
                elif rect_btn_pgn.collidepoint(e.pos):
                    # Forzamos un guardado manual de la partida al instante
                    motor.guardar_partida_pgn(resultado_pgn, color_humano, es_manual=True)
                    print("\n[SISTEMA] Partida descargada en /docs/partidas_descargadas")
                
                # ---> ACTIVAR MODO ESCRITURA <---
                elif rect_btn_apertura.collidepoint(e.pos):
                    ingresando_apertura = True
                    texto_apertura = "" # Limpiamos para empezar a escribir
                
                # Si hacemos clic fuera del botón mientras escribimos, cancelamos
                elif ingresando_apertura:
                    ingresando_apertura = False

                elif partida_finalizada:
                    ocultar_cartel_final = True

                # 2. Clics en el entorno de juego
                elif not estado_ia["calculando"] and offset_visual == 0:
                    ubicacion = pygame.mouse.get_pos()
                    col = ubicacion[0] // interfaz.TAM_CASILLA
                    fil = ubicacion[1] // interfaz.TAM_CASILLA
                    
                    # --- BARRERA MATEMÁTICA ABSOLUTA ---
                    if 0 <= col <= 7 and 0 <= fil <= 7:
                        # Adaptamos el clic según la perspectiva
                        if color_humano == chess.WHITE:
                            casilla_clic_sq = chess.square(col, 7-fil)
                        else:
                            casilla_clic_sq = chess.square(7-col, fil)
                        
                        pieza = motor.pieza_en(casilla_clic_sq)

                        # LÓGICA DE SELECCIÓN INTELIGENTE
                        if pieza and pieza.color == motor.turno_actual():
                            casilla_seleccionada = (fil, col)
                            casilla_sq_seleccionada = casilla_clic_sq
                            movimientos_validos = motor.movimientos_validos_desde(casilla_clic_sq)
                        
                        elif casilla_sq_seleccionada is not None:
                            exito = motor.intentar_movimiento(casilla_sq_seleccionada, casilla_clic_sq)
                            if exito:
                                offset_visual = 0
                                tablero_base_seguro = motor.board.copy() 
                                print("Movimiento realizado.")
                            
                            # Limpiamos variables tras el intento
                            casilla_seleccionada = ()
                            casilla_sq_seleccionada = None
                            movimientos_validos = []
                    
                    else:
                        casilla_seleccionada = ()
                        casilla_sq_seleccionada = None
                        movimientos_validos = []

            # --- EVENTOS DE TECLADO --- #
            elif e.type == pygame.KEYDOWN:
                
                # 1. Si el modo escritura está activo (El usuario hizo clic en el botón)
                if ingresando_apertura:
                    mods = pygame.key.get_mods()

                    if e.key == pygame.K_RETURN:
                        ingresando_apertura = False
                        apertura_a_entrenar = texto_apertura.strip()

                        motor.reiniciar_juego()
                        if apertura_a_entrenar:
                            if apertura_guiada:
                                print(f"\n[SISTEMA] Modo Apertura Guiada: {apertura_a_entrenar}")
                            else:
                                motor.forzar_inicio_teorico(apertura_a_entrenar)
                                print(f"\n[SISTEMA] Apertura cargada desde posicion final: {apertura_a_entrenar}")

                        tablero_base_seguro = motor.board.copy()
                        tablero_visual = motor.board.copy()
                        offset_visual = 0

                        print(f"\n[SISTEMA] Apertura fijada: {apertura_a_entrenar}")

                    elif e.key == pygame.K_ESCAPE:
                        ingresando_apertura = False
                        texto_apertura = ""

                    elif e.key == pygame.K_BACKSPACE:
                        texto_apertura = texto_apertura[:-1]

                    elif e.key == pygame.K_v and (mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META):
                        pegado = interfaz.leer_texto_portapapeles()
                        if pegado:
                            texto_apertura += pegado

                    elif e.unicode:
                        texto_apertura += e.unicode
                
                # 2. Si no estamos escribiendo, procesamos juego normalmente
                else:
                    if e.key == pygame.K_r:
                        motor.abortar_calculo = True
                        motor.reiniciar_juego()

                        color_humano, apertura_a_entrenar, apertura_guiada = interfaz.pantalla_seleccion_color(
                            pantalla, reloj, interfaz.ANCHO, interfaz.ALTO
                        )

                        if apertura_a_entrenar:
                            if apertura_guiada:
                                motor.reiniciar_juego()
                                print(f"\n[SISTEMA] Modo Apertura Guiada: {apertura_a_entrenar}")
                            else:
                                motor.forzar_inicio_teorico(apertura_a_entrenar)
                                print(f"\n[SISTEMA] Apertura cargada desde posicion final: {apertura_a_entrenar}")


                        tablero_base_seguro = motor.board.copy()
                        tablero_visual = motor.board.copy()
                        nombre_apertura_cache = motor.obtener_nombre_apertura()
                        mov_sugerido_cache = motor.obtener_siguiente_movimiento_guia(apertura_a_entrenar)
                        offset_visual = 0

                        partida_finalizada = False
                        mensaje_final = ""
                        ocultar_cartel_final = False
                        casilla_seleccionada = ()
                        casilla_sq_seleccionada = None
                        movimientos_validos = []

                        print("\n--- PARTIDA REINICIADA ---")

                    elif e.key == pygame.K_p:
                        print("\n--- HISTORIAL DE LA PARTIDA (EN CURSO) ---")
                        juego_actual = chess.pgn.Game.from_board(motor.board)
                        print(juego_actual)
                        print("------------------------------------------\n")

                    elif e.key == pygame.K_LEFT:
                        offset_visual = max(-len(motor.board.move_stack), offset_visual - 1)
                    elif e.key == pygame.K_RIGHT:
                        offset_visual = min(0, offset_visual + 1)

        # --- COMPROBACIÓN GENERAL DE FIN DE PARTIDA ---
        if not estado_ia["calculando"] and motor.juego_terminado() and not partida_finalizada:
            partida_finalizada = True
            resultado_pgn = "*"

            if motor.board.is_checkmate():
                if motor.board.turn == chess.WHITE:
                    mensaje_final = "JAQUE MATE! Ganan las Negras"
                    resultado_pgn = "0-1"
                else:
                    mensaje_final = "JAQUE MATE! Ganan las Blancas"
                    resultado_pgn = "1-0"
            elif motor.board.is_stalemate():
                mensaje_final = "TABLAS: Rey Ahogado"
                resultado_pgn = "1/2-1/2"
            elif motor.board.is_insufficient_material():
                mensaje_final = "TABLAS: Material Insuficiente"
                resultado_pgn = "1/2-1/2"
            else:
                mensaje_final = "PARTIDA FINALIZADA (Tablas)"
                resultado_pgn = "1/2-1/2"
                
            print(f"\n{mensaje_final}")
            motor.guardar_partida_pgn(resultado_pgn, color_humano, es_manual=False)

        # --- LÓGICA DE LA IA (Turno de la Máquina) ---
        # (Aquí mantienes tu código de la IA exactamente como lo tienes)
        # --- LÓGICA DE LA IA (Turno de la Máquina) ---
        if not estado_ia["calculando"] and motor.turno_actual() != color_humano and not partida_finalizada:
            
            motor.abortar_calculo = False  # <--- NUEVO: Bajamos la bandera
            estado_ia["calculando"] = True # Bloqueamos para no lanzar 100 hilos
            print("La IA esta pensando en segundo plano...") # ¡Corregido el print!
            
            # 1. Hacemos la "foto" estática ANTES de mandarla a pensar
            tablero_visual = motor.board.copy()
            nombre_apertura_cache = motor.obtener_nombre_apertura()
            mov_sugerido_cache = motor.obtener_siguiente_movimiento_guia(apertura_a_entrenar)

            # --- SOLUCIÓN AL CONGELAMIENTO VISUAL ---
            interfaz.dibujar_tablero(pantalla)
            interfaz.dibujar_piezas(pantalla, motor.board, color_humano)
            pygame.display.flip() # Actualiza la ventana inmediatamente
            pygame.time.delay(10) 

            def tarea_pensar():
                try:
                    motor.hacer_movimiento_inteligente(apertura_a_entrenar)
                except IndexError:
                    # Si el tablero se resetea (tecla R) mientras la IA calcula, 
                    # el pop() dará error. Lo capturamos y matamos el hilo limpiamente.
                    print("\n[SISTEMA] Calculo de IA abortado por reinicio de partida.")
                finally:
                    # Aseguramos que la bandera se baje siempre, haya explotado o no
                    estado_ia["calculando"] = False    
            
            # Lanzamos el hilo. El daemon=True hace que muera si cerramos la ventana
            hilo_ia = threading.Thread(target=tarea_pensar)
            hilo_ia.daemon = True 
            hilo_ia.start()
            
            # Limpiamos las selecciones de la interfaz mientras la IA piensa
            casilla_seleccionada = ()
            casilla_sq_seleccionada = None
            movimientos_validos = []

        """
        # ---> SALTO AUTOMÁTICO AL ÚLTIMO MOVIMIENTO <---
        # Usamos la foto segura para saber si hay una jugada nueva de verdad
        if len(tablero_base_seguro.move_stack) != movimientos_previos:
            offset_visual = 0  # Forzamos la vuelta al presente
            movimientos_previos = len(tablero_base_seguro.move_stack)
        """

        # ==========================================================
        # 1. ACTUALIZACIÓN DEL ESTADO VISUAL (EL CORTAFUEGOS)
        # ==========================================================
        # Solo tomamos una nueva foto de la realidad si la IA NO está tocando el motor
        if not estado_ia["calculando"]:
            tablero_base_seguro = motor.board.copy()
            nombre_apertura_cache = motor.obtener_nombre_apertura()
            mov_sugerido_cache = motor.obtener_siguiente_movimiento_guia(apertura_a_entrenar)

        # ---> EL VIAJE EN EL TIEMPO (Siempre activo) <---
        # Generamos la foto visual a partir de la foto blindada, haya IA pensando o no
        tablero_visual = tablero_base_seguro.copy()
        for _ in range(abs(offset_visual)):
            if tablero_visual.move_stack:
                tablero_visual.pop()

        # ==========================================================
        # 2. RENDERIZADO VISUAL (Capas de abajo hacia arriba)
        # ==========================================================
        interfaz.dibujar_tablero(pantalla)
        interfaz.dibujar_coordenadas(pantalla, color_humano)
        
        # El panel lateral usa el tablero_visual para mostrar las piezas de esa época
        interfaz.dibujar_panel_lateral(pantalla, tablero_visual, color_humano)
        
        # ¡Llamadas limpias! Las funciones ya traen sus alturas blindadas de serie
        offset_visual, rect_btn_izq, rect_btn_der = interfaz.dibujar_historial_movimientos(
            pantalla, tablero_base_seguro, offset_visual
        )
        
        rect_btn_pgn, rect_btn_apertura = interfaz.dibujar_botones_admin(
            pantalla, apertura_a_entrenar
        )
        
        interfaz.resaltar_casillas(pantalla, casilla_seleccionada, movimientos_validos, color_humano)
        interfaz.dibujar_efectos_visuales(pantalla, tablero_visual, interfaz.TAM_CASILLA, color_humano)
        
        if offset_visual == 0:
            interfaz.resaltar_guia_teorica(pantalla, mov_sugerido_cache, color_humano)
            
        interfaz.dibujar_piezas(pantalla, tablero_visual, color_humano)
        
        # ==========================================================
        # 3. ESTADOS DE FIN DE PARTIDA: FOCO, BARRA Y CARTEL
        # ==========================================================
        if partida_finalizada:
            interfaz.dibujar_foco_teatral(pantalla, tablero_visual, interfaz.TAM_CASILLA, color_humano)
            texto_permanente = f"{mensaje_final}  |  Pulsa 'R' para reiniciar"
            interfaz.dibujar_barra_estado(pantalla, texto_permanente, es_final=True)
            
            if not ocultar_cartel_final:
                interfaz.mostrar_mensaje_final(pantalla, mensaje_final)
        else:
            interfaz.dibujar_barra_estado(pantalla, nombre_apertura_cache, es_final=False)

        # ---> CORRECCIÓN: Si el usuario ha forzado un reinicio de apertura <---
        # Nos aseguramos de que tablero_visual siempre sea una copia limpia 
        # de la base segura, sin importar si la IA está pensando.
        tablero_visual = tablero_base_seguro.copy()
        for _ in range(abs(offset_visual)):
            if tablero_visual.move_stack:
                tablero_visual.pop()

        if ingresando_apertura:
            interfaz.dibujar_editor_apertura(pantalla, texto_apertura)

        pygame.display.flip()
        reloj.tick(interfaz.MAX_FPS)

    pygame.quit()

if __name__ == "__main__":
    main()