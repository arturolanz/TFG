import os
import chess
import random
import chess.polyglot
import json

class ChessEngine:
    """
    Esta clase es el 'Cerebro' de nuestro juego. 
    Aquí se aplican las reglas del ajedrez y, en el futuro, vivirá la Inteligencia Artificial.
    No sabe nada de pantallas ni ratones, solo de lógica pura.
    """
    def __init__(self):
        self.board = chess.Board()
        
        # Detectamos dinámicamente la raíz del proyecto para evitar el FileNotFoundError
        ruta_src = os.path.dirname(os.path.abspath(__file__)) # C:\ProyectoTFG\ajedrez\src
        ruta_raiz = os.path.dirname(ruta_src)                 # C:\ProyectoTFG\ajedrez
        
        self.ruta_json = os.path.join(ruta_raiz, "data", "aperturas.json")
        self.ruta_bin = os.path.join(ruta_raiz, "data", "aperturas.bin")
        
        self.diccionario_aperturas = {}
        self._cargar_base_aperturas()

    def _cargar_base_aperturas(self):
        """Carga el archivo JSON con control de errores explícito en consola."""
        try:
            with open(self.ruta_json, "r", encoding="utf-8") as f:
                self.diccionario_aperturas = json.load(f)
        except FileNotFoundError:
            print(f"\n[ERROR CRÍTICO]: No se encontró el archivo en: {self.ruta_json}")
            self.diccionario_aperturas = {}

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
        Inicia la toma de decisiones combinando teoría de libros y Minimax.
        Solucionado el problema de predictibilidad mediante la gestión aleatoria de empates.
        """
        import random

        # 1. COMPROBACIÓN PRIORITARIA: Libro de aperturas
        mov_teorico = self.obtener_movimiento_libro()
        if mov_teorico:
            print(f"-> Jugada de libro de aperturas ejecutada por la IA: {mov_teorico}")
            self.board.push(mov_teorico)
            return True

        # 2. Si no hay libro, entra Minimax clásico
        mejores_movimientos = []
        mejor_valor = float('inf') 
        alfa = -float('inf')
        beta = float('inf')
        
        movimientos_legales = list(self.board.legal_moves)
        if not movimientos_legales:
            return False

        for mov in movimientos_legales:
            self.board.push(mov)
            valor_tablero = self.minimax(2, True, alfa, beta) 
            self.board.pop()

            # --- SISTEMA DE DESEMPATE ALEATORIO TÁCTICO ---
            if valor_tablero < mejor_valor:
                mejor_valor = valor_tablero
                mejores_movimientos = [mov] # Encontrado un nuevo mínimo absoluto, reiniciamos lista
            elif valor_tablero == mejor_valor:
                mejores_movimientos.append(mov) # Empate exacto, añadimos como opción alternativa

            beta = min(beta, valor_tablero)

        if mejores_movimientos:
            # Seleccionamos una opción al azar de entre todas las que empatan con la puntuación óptima
            mejor_movimiento = random.choice(mejores_movimientos)
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
        """Consulta el archivo .bin usando la nueva ruta absoluta resuelta."""
        try:
            with chess.polyglot.open_reader(self.ruta_bin) as reader:
                entradas = list(reader.find_all(self.board))
                entradas_validas = [e for e in entradas if e.weight > 0]
                
                if entradas_validas:
                    movimientos = [e.move for e in entradas_validas]
                    pesos = [e.weight for e in entradas_validas]
                    eleccion = random.choices(movimientos, weights=pesos, k=1)
                    return eleccion[0]
        except (FileNotFoundError, IndexError):
            return None
        return None

    def obtener_nombre_apertura(self):
        """
        Determina la apertura ordenando el diccionario por longitud 
        para evitar que las líneas generales tapen a las variantes específicas.
        """
        historial_uci = " ".join([mov.uci() for mov in self.board.move_stack])
        
        # --- SOLUCIÓN AL BUG DE COINCIDENCIAS ---
        # Ordenamos las aperturas de la cadena más larga (más específica) a la más corta
        aperturas_ordenadas = sorted(
            self.diccionario_aperturas.items(), 
            key=lambda x: len(x[0]), 
            reverse=True
        )
        
        for secuencia, nombre in aperturas_ordenadas:
            if historial_uci.startswith(secuencia):
                if len(self.board.move_stack) <= 16:
                    return nombre
                else:
                    return f"Fase Avanzada ({nombre})"
                    
        if len(self.board.move_stack) == 0:
            return "Posición Inicial"
            
        return "Medio Juego / Desarrollo Táctico"