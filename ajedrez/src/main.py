import pygame
import chess
import threading
import interfaz
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

    # Definimos la variable vacía para que no dé error si no estamos entrenando nada
    apertura_a_entrenar = ""

    # Define aquí qué apertura quieres construir en el tablero paso a paso
    # apertura_a_entrenar = "Siciliana: Variante Dragón"

    # Descomentar esta línea para arrancar directamente en la variante que quieras auditar:
    #motor.forzar_inicio_teorico("Siciliana: Variante Dragón")

    interfaz.cargar_imagenes()
    
    corriendo = True
    casilla_seleccionada = ()        # Guarda (fila, col) para pasárselo a Pygame (Dibujo)
    casilla_sq_seleccionada = None   # Guarda índice 0-63 para pasárselo a python-chess (Lógica)
    movimientos_validos = []         # Lista de jugadas legales de la pieza seleccionada

    # Variable de control para el estado del juego
    partida_finalizada = False
    mensaje_final = "" # Aquí guardaremos el texto dinámico

    # =================================================================
    # NUEVO: MOSTRAR MENÚ DE SELECCIÓN DE COLOR ANTES DE INICIAR
    # =================================================================
    color_humano = interfaz.pantalla_seleccion_color(pantalla, reloj, interfaz.ANCHO, interfaz.ALTO)

    # ---> VARIABLES CACHÉ PARA EVITAR LA CONDICIÓN DE CARRERA <---
    tablero_visual = motor.board.copy()
    nombre_apertura_cache = "Posición Inicial"
    mov_sugerido_cache = None
    estado_ia = {"calculando": False}

    # 2. BUCLE PRINCIPAL DEL JUEGO
    while corriendo:
    # --- GESTIÓN DE EVENTOS (Turno del Humano) ---
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                corriendo = False

            # --- EVENTOS DE RATÓN --- #
            # Bloqueamos los clics del usuario si la partida ya ha finalizado o si la máquina está pensando
            elif e.type == pygame.MOUSEBUTTONDOWN and not partida_finalizada and not estado_ia["calculando"]:
                ubicacion = pygame.mouse.get_pos()
                col = ubicacion[0] // interfaz.TAM_CASILLA
                fil = ubicacion[1] // interfaz.TAM_CASILLA
                
                casilla_clic_sq = chess.square(col, 7-fil)
                pieza = motor.pieza_en(casilla_clic_sq)

                # MODIFICADO: Adaptamos el clic según la perspectiva del color elegido
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
                        print("Movimiento realizado. Turno de las negras.")
                    
                    casilla_seleccionada = ()
                    casilla_sq_seleccionada = None
                    movimientos_validos = []

            # --- EVENTOS DE TECLADO --- #
            elif e.type == pygame.KEYDOWN:
                # Si pulsamos la tecla 'R' Y la partida ha terminado
                if e.key == pygame.K_r:
                    # 1. Reiniciamos la lógica del motor
                    motor.reiniciar_juego()
                    
                    # ---> NUEVO: Volvemos a lanzar el menú flotante para elegir bando <---
                    color_humano = interfaz.pantalla_seleccion_color(pantalla, reloj, interfaz.ANCHO, interfaz.ALTO)
                    
                    # 2. Limpiamos todas las variables de control visual
                    partida_finalizada = False
                    mensaje_final = ""
                    casilla_seleccionada = ()
                    casilla_sq_seleccionada = None
                    movimientos_validos = []
                    
                    print("\n--- PARTIDA REINICIADA ---")

                # ---> NUEVO: BOTÓN DE DEPURACIÓN (P) <---
                elif e.key == pygame.K_p:
                    print("\n--- HISTORIAL DE LA PARTIDA (EN CURSO) ---")
                    # Extraemos la partida directamente desde la memoria del tablero
                    juego_actual = chess.pgn.Game.from_board(motor.board)
                    print(juego_actual)
                    print("------------------------------------------\n")

        # --- COMPROBACIÓN GENERAL DE FIN DE PARTIDA ---
        if not estado_ia["calculando"] and motor.juego_terminado() and not partida_finalizada:
            partida_finalizada = True
            
            resultado_pgn = "*"

            # Analizamos la causa exacta del fin de partida para el cartel
            if motor.board.is_checkmate():
                # Si es jaque mate, gana el jugador que NO tiene el turno actual
                if motor.board.turn == chess.WHITE:
                    mensaje_final = "¡JAQUE MATE! Ganan las Negras"
                    resultado_pgn = "0-1"
                else:
                    mensaje_final = "¡JAQUE MATE! Ganan las Blancas"
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

            motor.guardar_partida_pgn(resultado_pgn, color_humano)

        # --- LÓGICA DE LA IA (Turno de la Máquina) ---
        if not estado_ia["calculando"] and motor.turno_actual() != color_humano and not partida_finalizada:
            
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
                # Esta es la única vez que se llama al motor
                motor.hacer_movimiento_inteligente(apertura_a_entrenar)
                estado_ia["calculando"] = False # Libera el candado al terminar
                print("Movimiento de la IA realizado.") # Avisa cuando de verdad acaba
                
            # Lanzamos el hilo. El daemon=True hace que muera si cerramos la ventana
            hilo_ia = threading.Thread(target=tarea_pensar)
            hilo_ia.daemon = True 
            hilo_ia.start()
            
            # Limpiamos las selecciones de la interfaz mientras la IA piensa
            casilla_seleccionada = ()
            casilla_sq_seleccionada = None
            movimientos_validos = []
       
        # 3. RENDERIZADO VISUAL (Se ejecuta en cada frame)
        interfaz.dibujar_tablero(pantalla)
        interfaz.dibujar_coordenadas(pantalla, color_humano)
        interfaz.resaltar_casillas(pantalla, casilla_seleccionada, movimientos_validos, color_humano)

        # 2. Actualizamos la "foto" SOLO si la IA ha terminado de pensar y el motor está libre
        if not estado_ia["calculando"]:
            tablero_visual = motor.board.copy()
            nombre_apertura_cache = motor.obtener_nombre_apertura()
            mov_sugerido_cache = motor.obtener_siguiente_movimiento_guia(apertura_a_entrenar)

        interfaz.resaltar_guia_teorica(pantalla, mov_sugerido_cache, color_humano)
        
        # 3. Dibujamos LA FOTO ESTÁTICA, nunca el motor.board directamente
        interfaz.dibujar_piezas(pantalla, tablero_visual, color_humano)
        interfaz.dibujar_barra_estado(pantalla, nombre_apertura_cache)

        # SI LA PARTIDA HA TERMINADO, PINTAMOS EL CARTEL EN INTERFAZ
        if partida_finalizada:
            interfaz.mostrar_mensaje_final(pantalla, mensaje_final)

        # Actualiza la ventana completa
        pygame.display.flip()
        reloj.tick(interfaz.MAX_FPS)

    pygame.quit()

if __name__ == "__main__":
    main()