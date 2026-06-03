import pygame
import chess
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
    interfaz.cargar_imagenes()
    
    corriendo = True
    casilla_seleccionada = ()        # Guarda (fila, col) para pasárselo a Pygame (Dibujo)
    casilla_sq_seleccionada = None   # Guarda índice 0-63 para pasárselo a python-chess (Lógica)
    movimientos_validos = []         # Lista de jugadas legales de la pieza seleccionada

    # Variable de control para el estado del juego
    partida_finalizada = False
    mensaje_final = "" # Aquí guardaremos el texto dinámico

    # 2. BUCLE PRINCIPAL DEL JUEGO
    while corriendo:
    # --- GESTIÓN DE EVENTOS (Turno del Humano) ---
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                corriendo = False

            # --- EVENTOS DE RATÓN --- #
            # Bloqueamos los clics del usuario si la partida ya ha finalizado
            elif e.type == pygame.MOUSEBUTTONDOWN and not partida_finalizada:
                ubicacion = pygame.mouse.get_pos()
                col = ubicacion[0] // interfaz.TAM_CASILLA
                fil = ubicacion[1] // interfaz.TAM_CASILLA
                
                casilla_clic_sq = chess.square(col, 7-fil)
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
                if e.key == pygame.K_r and partida_finalizada:
                    # 1. Reiniciamos la lógica del motor
                    motor.reiniciar_juego()
                    
                    # 2. Limpiamos todas las variables de control visual
                    partida_finalizada = False
                    mensaje_final = ""
                    casilla_seleccionada = ()
                    casilla_sq_seleccionada = None
                    movimientos_validos = []
                    
                    print("\n--- PARTIDA REINICIADA ---")

        # --- COMPROBACIÓN GENERAL DE FIN DE PARTIDA ---
        if motor.juego_terminado() and not partida_finalizada:
            partida_finalizada = True
            
            # Analizamos la causa exacta del fin de partida para el cartel
            if motor.board.is_checkmate():
                # Si es jaque mate, gana el jugador que NO tiene el turno actual
                if motor.board.turn == chess.WHITE:
                    mensaje_final = "¡JAQUE MATE! Ganan las Negras"
                else:
                    mensaje_final = "¡JAQUE MATE! Ganan las Blancas"
            elif motor.board.is_stalemate():
                mensaje_final = "TABLAS: Rey Ahogado"
            elif motor.board.is_insufficient_material():
                mensaje_final = "TABLAS: Material Insuficiente"
            else:
                mensaje_final = "PARTIDA FINALIZADA (Tablas)"
                
            print(f"\n{mensaje_final}")

        # --- LÓGICA DE LA IA (Turno de la Máquina) ---
        if not motor.turno_actual() and not partida_finalizada:
            print("La IA está pensando...")
            
            # --- SOLUCIÓN AL CONGELAMIENTO VISUAL ---
            # 1. Forzamos un dibujado del tablero con tu jugada recién hecha
            interfaz.dibujar_tablero(pantalla)
            interfaz.dibujar_piezas(pantalla, motor.board)
            pygame.display.flip() # Actualiza la ventana inmediatamente
            
            # Opcional: Una pausa minúscula de hardware para que el SO respire
            pygame.time.delay(10) 
            
            # 2. Ahora sí, la IA bloquea el hilo para calcular, pero el tablero ya está actualizado
            motor.hacer_movimiento_inteligente() 
            
            casilla_seleccionada = ()
            casilla_sq_seleccionada = None
            movimientos_validos = []
            
            print("Movimiento de la IA realizado. Turno de las blancas.")
       
        # 3. RENDERIZADO VISUAL (Se ejecuta en cada frame)
        interfaz.dibujar_tablero(pantalla)
        interfaz.resaltar_casillas(pantalla, casilla_seleccionada, movimientos_validos)
        interfaz.dibujar_piezas(pantalla, motor.board)

        # NUEVO: Obtenemos el nombre detectado por el motor y lo dibujamos abajo
        nombre_apertura = motor.obtener_nombre_apertura()
        interfaz.dibujar_barra_estado(pantalla, nombre_apertura)

        # SI LA PARTIDA HA TERMINADO, PINTAMOS EL CARTEL EN INTERFAZ
        if partida_finalizada:
            interfaz.mostrar_mensaje_final(pantalla, mensaje_final)

        # Actualiza la ventana completa
        pygame.display.flip()
        reloj.tick(interfaz.MAX_FPS)

    pygame.quit()

if __name__ == "__main__":
    main()