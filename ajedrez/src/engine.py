import chess
import random
import chess.polyglot

class ChessEngine:
    """
    Esta clase es el 'Cerebro' de nuestro juego. 
    Aquí se aplican las reglas del ajedrez y, en el futuro, vivirá la Inteligencia Artificial.
    No sabe nada de pantallas ni ratones, solo de lógica pura.
    """
    def __init__(self):
        # Creamos una instancia del tablero.
        # Al nacer, el objeto ya conoce la posición inicial de todas las piezas y de quién es el turno.
        self.board = chess.Board()

    def turno_actual(self):
        """Devuelve el color del jugador que tiene el turno (True para Blancas, False para Negras)."""
        return self.board.turn

    def pieza_en(self, casilla_sq):
        """Devuelve qué pieza hay en una casilla específica (números del 0 al 63)."""
        return self.board.piece_at(casilla_sq)

    def movimientos_validos_desde(self, casilla_sq):
        """Devuelve la lista de movimientos legales SÓLO para la pieza que hemos seleccionado."""
        return [m for m in self.board.legal_moves if m.from_square == casilla_sq]

    def intentar_movimiento(self, origen_sq, destino_sq):
        """
        Recibe dos casillas, crea el movimiento y verifica si es legal.
        Si es legal, lo ejecuta en el tablero virtual y devuelve True.
        """
        movimiento = chess.Move(origen_sq, destino_sq)
        
        # LÓGICA DE CORONACIÓN (Promoción)
        # Si movemos un peón y llega a la última fila (0 para negras, 7 para blancas),
        # lo convertimos automáticamente en Reina para simplificar el juego por ahora.
        pieza = self.board.piece_at(origen_sq)
        if pieza and pieza.piece_type == chess.PAWN:
            if chess.square_rank(destino_sq) == 0 or chess.square_rank(destino_sq) == 7:
                movimiento = chess.Move(origen_sq, destino_sq, promotion=chess.QUEEN)

        # Verificamos si la jugada (con o sin promoción) está en la lista de jugadas legales
        if movimiento in self.board.legal_moves:
            self.board.push(movimiento) # Ejecutamos el movimiento en el cerebro
            return True
        return False

    def hacer_movimiento_aleatorio(self):
        """
        Selecciona y ejecuta un movimiento legal al azar para el turno actual.
        Devuelve True si pudo mover, False si el juego ha terminado.
        """
        movimientos_legales = list(self.board.legal_moves)
        
        # Si no hay movimientos, es jaque mate o tablas
        if not movimientos_legales:
            return False 
            
        movimiento_elegido = random.choice(movimientos_legales)
        self.board.push(movimiento_elegido)
        return True

    def juego_terminado(self):
        """Devuelve True si la partida ha acabado (jaque mate, rey ahogado, etc.)."""
        return self.board.is_game_over()

    def reiniciar_juego(self):
        """Restablece el tablero a la posición inicial de ajedrez."""
        self.board.reset()
    
    def evaluar_tablero(self):
        """
        Función de evaluación heurística completa.
        Incluye tablas posicionales (PST) y control de repeticiones.
        """

        valores_piezas = {
            chess.PAWN: 100,
            chess.KNIGHT: 300,
            chess.BISHOP: 300,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 90000
        }
        
        # TABLAS DE PIEZA-CASILLA (PST)
        pst_peon = [
             0,  0,  0,  0,  0,  0,  0,  0,
             5, 10, 10,-20,-20, 10, 10,  5,
             5, -5,-10,  0,  0,-10, -5,  5,
             0,  0,  0, 20, 20,  0,  0,  0,
             5,  5, 10, 25, 25, 10,  5,  5,
            10, 10, 20, 30, 30, 20, 10, 10,
            50, 50, 50, 50, 50, 50, 50, 50,
             0,  0,  0,  0,  0,  0,  0,  0
        ]
        
        pst_caballo = [
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50
        ]

        pst_alfil = [
            -20,-10,-10,-10,-10,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5, 10, 10,  5,  0,-10,
            -10,  5,  5, 10, 10,  5,  5,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10, 10, 10, 10, 10, 10, 10,-10,
            -10,  5,  0,  0,  0,  0,  5,-10,
            -20,-10,-10,-10,-10,-10,-10,-20
        ]

        pst_torre = [
             0,  0,  0,  0,  0,  0,  0,  0,
             5, 10, 10, 10, 10, 10, 10,  5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
             0,  0,  0,  5,  5,  0,  0,  0
        ]

        pst_reina = [
            -20,-10,-10, -5, -5,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5,  5,  5,  5,  0,-10,
             -5,  0,  5,  5,  5,  5,  0, -5,
              0,  0,  5,  5,  5,  5,  0, -5,
            -10,  5,  5,  5,  5,  5,  0,-10,
            -10,  0,  5,  0,  0,  0,  0,-10,
            -20,-10,-10, -5, -5,-10,-10,-20
        ]

        # Fomenta esconderse en los laterales (enroque) y penaliza salir al centro
        pst_rey = [
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -20,-30,-30,-40,-40,-30,-30,-20,
            -10,-20,-20,-20,-20,-20,-20,-10,
             20, 20,  0,  0,  0,  0, 20, 20,
             20, 30, 10,  0,  0, 10, 30, 20
        ]

        puntuacion_total = 0
        
        for casilla in chess.SQUARES:
            pieza = self.board.piece_at(casilla)
            
            if pieza is not None:
                valor_material = valores_piezas.get(pieza.piece_type, 0)
                valor_posicional = 0
                
                casilla_tabla = casilla if pieza.color == chess.WHITE else chess.square_mirror(casilla)

                # Asignamos la tabla correspondiente a cada pieza
                if pieza.piece_type == chess.PAWN: valor_posicional = pst_peon[casilla_tabla]
                elif pieza.piece_type == chess.KNIGHT: valor_posicional = pst_caballo[casilla_tabla]
                elif pieza.piece_type == chess.BISHOP: valor_posicional = pst_alfil[casilla_tabla]
                elif pieza.piece_type == chess.ROOK: valor_posicional = pst_torre[casilla_tabla]
                elif pieza.piece_type == chess.QUEEN: valor_posicional = pst_reina[casilla_tabla]
                elif pieza.piece_type == chess.KING: valor_posicional = pst_rey[casilla_tabla]
                
                valor_final_pieza = valor_material + valor_posicional
                
                if pieza.color == chess.WHITE:
                    puntuacion_total += valor_final_pieza
                else:
                    puntuacion_total -= valor_final_pieza
        
        # --- LÓGICA DE FINALES (MOP-UP) ---
        # Si las blancas van ganando por mucho
        if puntuacion_total > 400:
            puntuacion_total += self.forzar_rey_esquina(chess.WHITE, chess.BLACK)
        # Si las negras (la IA) van ganando por mucho
        elif puntuacion_total < -400:
            puntuacion_total -= self.forzar_rey_esquina(chess.BLACK, chess.WHITE)
                    
        return puntuacion_total

    def minimax(self, profundidad, maximizando_blancas, alfa, beta):
        """
        Algoritmo Minimax con Poda Alfa-Beta, detección real de mates y empates neutros (0).
        """
        # --- COMPROBACIONES DE FIN DE PARTIDA REALES ---
        if self.board.is_checkmate():
            # Si gana el blanco devolvemos positivo, si gana el negro (IA) negativo.
            # Sumamos/restamos la profundidad para que la IA prefiera mates más rápidos.
            return -100000 - profundidad if self.board.turn == chess.WHITE else 100000 + profundidad
            
        if self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.is_repetition(2):
            return 0 # Las tablas de cualquier tipo valen exactamente 0

        # Caso base de profundidad del árbol principal
        if profundidad == 0:
            return self.quiescencia(alfa, beta, maximizando_blancas, profundidad_q=4)

        if maximizando_blancas:
            max_eval = -float('inf')
            for mov in self.board.legal_moves:
                self.board.push(mov)
                eval_actual = self.minimax(profundidad - 1, False, alfa, beta)
                self.board.pop()
                
                max_eval = max(max_eval, eval_actual)
                alfa = max(alfa, eval_actual)
                if beta <= alfa:
                    break 
            return max_eval
            
        else:
            min_eval = float('inf')
            for mov in self.board.legal_moves:
                self.board.push(mov)
                eval_actual = self.minimax(profundidad - 1, True, alfa, beta)
                self.board.pop()
                
                min_eval = min(min_eval, eval_actual)
                beta = min(beta, eval_actual)
                if beta <= alfa:
                    break
            return min_eval

    def hacer_movimiento_inteligente(self):
        """
        Inicia la búsqueda del mejor movimiento usando Minimax con Poda Alfa-Beta.
        """

        # COMPROBACIÓN PRIORITARIA: ¿Estamos en el libro de aperturas?
        mov_teorico = self.obtener_movimiento_libro()
        if mov_teorico:
            print("-> Jugada de libro de aperturas ejecutada por la IA.")
            self.board.push(mov_teorico)
            return True

        # Si ya no hay teoría en el libro, el motor clásico (Minimax) toma el control

        mejor_movimiento = None
        mejor_valor = float('inf') 
        
        # Valores iniciales para la poda
        alfa = -float('inf')
        beta = float('inf')
        
        movimientos_legales = list(self.board.legal_moves)
        if not movimientos_legales:
            return False

        for mov in movimientos_legales:
            self.board.push(mov)
            # Pasamos alfa y beta a la llamada inicial
            # Dejamos la profundidad en 2 (ahora que es más rápido, se lo puede permitir)
            valor_tablero = self.minimax(2, True, alfa, beta) 
            self.board.pop()

            if valor_tablero < mejor_valor:
                mejor_valor = valor_tablero
                mejor_movimiento = mov

            # Como el motor juega con negras, actualiza la cota superior (beta)
            beta = min(beta, valor_tablero)

        if mejor_movimiento:
            self.board.push(mejor_movimiento)
            return True
            
        return False

    def quiescencia(self, alfa, beta, maximizando_blancas, profundidad_q=4):
        """
        Búsqueda de Quiescencia optimizada.
        Añadido control de fin de partida y límite de profundidad para evitar congelamientos.
        """
        # 1. Comprobaciones terminales en quiescencia
        if self.board.is_checkmate():
            return -100000 if self.board.turn == chess.WHITE else 100000
        if self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.is_repetition(2):
            return 0

        eval_actual = self.evaluar_tablero()
        
        # Si llegamos al límite de seguridad de capturas, devolvemos la evaluación actual
        if profundidad_q == 0:
            return eval_actual

        if maximizando_blancas:
            if eval_actual >= beta:
                return beta
            alfa = max(alfa, eval_actual)
        else:
            if eval_actual <= alfa:
                return alfa
            beta = min(beta, eval_actual)

        for mov in self.board.generate_legal_captures():
            self.board.push(mov)
            # Pasamos el límite de profundidad restando 1
            eval_hijo = self.quiescencia(alfa, beta, not maximizando_blancas, profundidad_q - 1)
            self.board.pop()
            
            if maximizando_blancas:
                eval_actual = max(eval_actual, eval_hijo)
                alfa = max(alfa, eval_actual)
                if beta <= alfa:
                    break
            else:
                eval_actual = min(eval_actual, eval_hijo)
                beta = min(beta, eval_actual)
                if beta <= alfa:
                    break
                    
        return eval_actual
        
    def forzar_rey_esquina(self, color_amigo, color_enemigo):
        """
        Calcula una bonificación para obligar a la IA a dar jaque mate en los finales.
        Premia empujar al rey enemigo a los bordes y acercar el rey propio.
        """
        puntos = 0
        rey_enemigo_sq = self.board.king(color_enemigo)
        rey_amigo_sq = self.board.king(color_amigo)
        
        # Si por algún motivo no hay rey (algo raro en ajedrez estándar), salimos
        if rey_enemigo_sq is None or rey_amigo_sq is None:
            return 0
            
        # 1. Bonificación por empujar al rey enemigo a los bordes
        fila_enemiga = chess.square_rank(rey_enemigo_sq)
        col_enemiga = chess.square_file(rey_enemigo_sq)
        
        distancia_centro_fila = max(3 - fila_enemiga, fila_enemiga - 4)
        distancia_centro_col = max(3 - col_enemiga, col_enemiga - 4)
        distancia_centro = distancia_centro_fila + distancia_centro_col
        
        puntos += distancia_centro * 10
        
        # 2. Bonificación por acercar nuestro rey al suyo para ayudar al mate
        fila_amiga = chess.square_rank(rey_amigo_sq)
        col_amiga = chess.square_file(rey_amigo_sq)
        
        dist_reyes = abs(fila_enemiga - fila_amiga) + abs(col_enemiga - col_amiga)
        # 14 es la distancia máxima posible (7+7). Restamos la real para premiar la cercanía.
        puntos += (14 - dist_reyes) * 4
        
        return puntos

    def obtener_movimiento_libro(self):
        """
        Consulta el archivo .bin de la carpeta data.
        Devuelve una jugada teórica aleatoria elegida entre todas las opciones 
        disponibles en el libro para garantizar la variedad de aperturas.
        """
        ruta_libro = "data/aperturas.bin"
        try:
            with chess.polyglot.open_reader(ruta_libro) as reader:
                # Obtenemos la lista completa de todas las jugadas teóricas válidas para esta posición
                entradas = list(reader.find_all(self.board))
                if entradas:
                    import random
                    # Seleccionamos una al azar del libro completo (e4, d4, c4, Nf3, etc.)
                    entrada_elegida = random.choice(entradas)
                    return entrada_elegida.move
        except (FileNotFoundError, IndexError):
            return None
        return None

    def obtener_nombre_apertura(self):
        """
        Determina la apertura actual basada en la secuencia de jugadas (UCI)
        en lugar de FEN estáticos, permitiendo que el nombre persista en la interfaz.
        """
        # Convertimos el historial completo de movimientos a texto (ej: "e2e4 c7c5 g1f3")
        historial_uci = " ".join([mov.uci() for mov in self.board.move_stack])
        
        # Diccionario de líneas teóricas ordenadas por profundidad (de más específicas a generales)
        aperturas_uci = {
            "e2e4 e7e5 g1f3 b8c6 f1b5": "Apertura Española (Ruy López)",
            "e2e4 e7e5 g1f3 b8c6 f1c4": "Apertura Italiana",
            "e2e4 e7e5 g1f3 g8f6": "Defensa Petrov",
            "d2d4 d7d5 c2c4": "Gámbito de Dama",
            "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4": "Defensa Siciliana (Variante Abierta)",
            "e2e4 c7c5": "Defensa Siciliana",
            "e2e4 e7e6": "Defensa Francesa",
            "e2e4 c7c6": "Defensa Caro-Kann",
            "e2e4 g7g6": "Defensa Moderna / Pirc",
            "d2d4 d7d5": "Partida Cerrada (1.d4 d5)",
            "d2d4 g8f6 c2c4 g7g6": "Defensa India de Rey",
            "e2e4 e7e5": "Partida Abierta (1.e4 e5)",
            "e2e4": "Apertura de Peón de Rey (1.e4)",
            "d2d4": "Apertura de Peón de Dama (1.d4)",
            "g1f3": "Apertura Réti (1.Nf3)",
            "c2c4": "Apertura Inglesa (1.c4)"
        }
        
        # Comprobamos si el historial de la partida coincide con el inicio de alguna teoría
        for secuencia, nombre in aperturas_uci.items():
            if historial_uci.startswith(secuencia):
                # Si la partida está en las primeras fases (menos de 12 jugadas por bando)
                if len(self.board.move_stack) <= 24:
                    return nombre
                else:
                    return f"Fase Avanzada ({nombre})"
                    
        # Si el historial está vacío (tras iniciar o reiniciar con 'R')
        if len(self.board.move_stack) == 0:
            return "Posición Inicial"
            
        return "Medio Juego / Desarrollo Táctico"