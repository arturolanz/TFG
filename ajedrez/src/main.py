# src/main.py
import pygame
import chess
import threading
import interfaz
import sys
from engine import ChessEngine


def main():
    # Inicializamos Pygame y preparamos la ventana principal del juego.
    pygame.init()
    pantalla = pygame.display.set_mode((interfaz.ANCHO, interfaz.ALTO + 40))
    pygame.display.set_caption("Mi Motor de Ajedrez - TFG")
    reloj = pygame.time.Clock()

    # El motor se encarga de toda la lógica de ajedrez.
    motor = ChessEngine()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # Antes de empezar, el jugador elige color y, si quiere, una apertura para entrenar.
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

    interfaz.cargar_imagenes()

    corriendo = True

    # Variables usadas para seleccionar piezas y mostrar sus movimientos legales.
    casilla_seleccionada = ()
    casilla_sq_seleccionada = None
    movimientos_validos = []

    partida_finalizada = False
    mensaje_final = ""
    ocultar_cartel_final = False

    # Control del historial visual: permite retroceder y avanzar por la partida sin alterar el tablero real.
    offset_visual = 0
    rect_btn_izq = pygame.Rect(0, 0, 0, 0)
    rect_btn_der = pygame.Rect(0, 0, 0, 0)
    rect_btn_pgn = pygame.Rect(0, 0, 0, 0)
    rect_btn_apertura = pygame.Rect(0, 0, 0, 0)

    # Copias de seguridad para que la interfaz pueda dibujar sin depender del hilo de la IA.
    tablero_base_seguro = motor.board.copy()
    tablero_visual = motor.board.copy()
    nombre_apertura_cache = motor.obtener_nombre_apertura()
    mov_sugerido_cache = motor.obtener_siguiente_movimiento_guia(apertura_a_entrenar)

    estado_ia = {"calculando": False}
    ingresando_apertura = False
    texto_apertura = ""
    resultado_pgn = "*"

    # Bucle principal del juego.
    while corriendo:
        # Gestión de eventos de ventana, ratón y teclado.
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                corriendo = False

            elif e.type == pygame.MOUSEBUTTONDOWN:
                if rect_btn_izq.collidepoint(e.pos):
                    offset_visual = max(-len(motor.board.move_stack), offset_visual - 1)

                elif rect_btn_der.collidepoint(e.pos):
                    offset_visual = min(0, offset_visual + 1)

                elif rect_btn_pgn.collidepoint(e.pos):
                    motor.guardar_partida_pgn(resultado_pgn, color_humano, es_manual=True)
                    print("\n[SISTEMA] Partida descargada en /docs/partidas_descargadas")

                elif rect_btn_apertura.collidepoint(e.pos):
                    ingresando_apertura = True
                    texto_apertura = ""

                elif ingresando_apertura:
                    ingresando_apertura = False

                elif partida_finalizada:
                    ocultar_cartel_final = True

                # Solo permitimos mover piezas si la IA no está pensando y estamos viendo la posición actual.
                elif not estado_ia["calculando"] and offset_visual == 0:
                    ubicacion = pygame.mouse.get_pos()
                    col = ubicacion[0] // interfaz.TAM_CASILLA
                    fil = ubicacion[1] // interfaz.TAM_CASILLA

                    if 0 <= col <= 7 and 0 <= fil <= 7:
                        # Convertimos la casilla de pantalla a la casilla interna de python-chess.
                        if color_humano == chess.WHITE:
                            casilla_clic_sq = chess.square(col, 7 - fil)
                        else:
                            casilla_clic_sq = chess.square(7 - col, fil)

                        pieza = motor.pieza_en(casilla_clic_sq)

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

                            casilla_seleccionada = ()
                            casilla_sq_seleccionada = None
                            movimientos_validos = []

                    else:
                        casilla_seleccionada = ()
                        casilla_sq_seleccionada = None
                        movimientos_validos = []

            elif e.type == pygame.KEYDOWN:
                # Cuando se está escribiendo una apertura, el teclado se usa como editor de texto.
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

        # Comprobamos si la partida ha terminado y guardamos el PGN automáticamente.
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

        # Turno de la IA. Se ejecuta en otro hilo para que la ventana no se congele.
        if not estado_ia["calculando"] and motor.turno_actual() != color_humano and not partida_finalizada:
            motor.abortar_calculo = False
            estado_ia["calculando"] = True
            print("La IA esta pensando en segundo plano...")

            tablero_visual = motor.board.copy()
            nombre_apertura_cache = motor.obtener_nombre_apertura()
            mov_sugerido_cache = motor.obtener_siguiente_movimiento_guia(apertura_a_entrenar)

            interfaz.dibujar_tablero(pantalla)
            interfaz.dibujar_piezas(pantalla, motor.board, color_humano)
            pygame.display.flip()
            pygame.time.delay(10)

            def tarea_pensar():
                try:
                    motor.hacer_movimiento_inteligente(apertura_a_entrenar)
                except IndexError:
                    print("\n[SISTEMA] Calculo de IA abortado por reinicio de partida.")
                finally:
                    estado_ia["calculando"] = False

            hilo_ia = threading.Thread(target=tarea_pensar)
            hilo_ia.daemon = True
            hilo_ia.start()

            casilla_seleccionada = ()
            casilla_sq_seleccionada = None
            movimientos_validos = []

        # Actualizamos la información visual solo cuando la IA no está modificando el tablero.
        if not estado_ia["calculando"]:
            tablero_base_seguro = motor.board.copy()
            nombre_apertura_cache = motor.obtener_nombre_apertura()
            mov_sugerido_cache = motor.obtener_siguiente_movimiento_guia(apertura_a_entrenar)

        # Creamos el tablero que se va a dibujar, aplicando el retroceso del historial si hace falta.
        tablero_visual = tablero_base_seguro.copy()
        for _ in range(abs(offset_visual)):
            if tablero_visual.move_stack:
                tablero_visual.pop()

        # Dibujamos la escena completa en orden de capas.
        interfaz.dibujar_tablero(pantalla)
        interfaz.dibujar_coordenadas(pantalla, color_humano)
        interfaz.dibujar_panel_lateral(pantalla, tablero_visual, color_humano)

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

        # Si la partida acaba, mostramos el resultado por encima del tablero.
        if partida_finalizada:
            interfaz.dibujar_foco_teatral(pantalla, tablero_visual, interfaz.TAM_CASILLA, color_humano)
            texto_permanente = f"{mensaje_final}  |  Pulsa 'R' para reiniciar"
            interfaz.dibujar_barra_estado(pantalla, texto_permanente, es_final=True)

            if not ocultar_cartel_final:
                interfaz.mostrar_mensaje_final(pantalla, mensaje_final)
        else:
            interfaz.dibujar_barra_estado(pantalla, nombre_apertura_cache, es_final=False)

        if ingresando_apertura:
            interfaz.dibujar_editor_apertura(pantalla, texto_apertura)

        pygame.display.flip()
        reloj.tick(interfaz.MAX_FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
