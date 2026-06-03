# src/engine.py
import json
import random
from typing import Dict, Optional, List
import chess
import chess.polyglot
import config  # Importamos centralizadamente la configuración

class ChessEngine:
    def __init__(self) -> None:
        self.board: chess.Board = chess.Board()
        self.diccionario_aperturas: Dict[str, str] = {}
        self._cargar_base_aperturas()

    def _cargar_base_aperturas(self) -> None:
        """Carga el catálogo de aperturas desde el archivo JSON externo."""
        try:
            with open(config.RUTA_JSON_APERTURAS, "r", encoding="utf-8") as f:
                self.diccionario_aperturas = json.load(f)
        except FileNotFoundError:
            self.diccionario_aperturas = {}

    def turno_actual(self) -> bool:
        """
        Devuelve el turno del jugador activo.
        True si es el turno de las Blancas, False si es el de las Negras.
        """
        return self.board.turn

    def pieza_en(self, casilla_sq: chess.Square) -> Optional[chess.Piece]:
        """Devuelve la pieza presente en una casilla concreta o None si está vacía."""
        return self.board.piece_at(casilla_sq)

    def movimientos_validos_desde(self, casilla_sq: chess.Square) -> List[chess.Move]:
        """
        Genera y filtra la lista de todos los movimientos legales 
        posibles que parten desde la casilla seleccionada.
        """
        return [mov for mov in self.board.legal_moves if mov.from_square == casilla_sq]

    def intentar_movimiento(self, origen: chess.Square, destino: chess.Square) -> bool:
        """
        Verifica si un movimiento humano es legal. Si lo es, lo ejecuta 
        en el tablero (gestionando la coronación automática a Reina) y devuelve True.
        """
        # 1. Intentamos el movimiento estándar
        movimiento_estandar = chess.Move(origen, destino)
        if movimiento_estandar in self.board.legal_moves:
            self.board.push(movimiento_estandar)
            return True
            
        # 2. Si no es legal, comprobamos si es un movimiento de promoción/coronación de peón
        movimiento_promocion = chess.Move(origen, destino, promotion=chess.QUEEN)
        if movimiento_promocion in self.board.legal_moves:
            self.board.push(movimiento_promocion)
            return True
            
        return False

    def reiniciar_juego(self) -> None:
        self.board.reset()

    def juego_terminado(self) -> bool:
        """
        Comprueba si la partida ha concluido por jaque mate, 
        tablas absolutas o repetición de posiciones.
        """
        return (
            self.board.is_checkmate() or 
            self.board.is_stalemate() or 
            self.board.is_insufficient_material() or 
            self.board.is_repetition(2)
        )

    def obtener_nombre_apertura(self) -> str:
        """
        Determina la apertura consultando el archivo JSON externo.
        Ordena secuencialmente por longitud de clave para evitar que las líneas
        generales tapen a las variantes específicas.
        """
        historial_uci: str = " ".join([mov.uci() for mov in self.board.move_stack])
        
        # --- REPARACIÓN DE LA ARQUITECTURA ---
        # Ordenamos las aperturas de la cadena más larga (variante específica) a la más corta
        aperturas_ordenadas = sorted(
            self.diccionario_aperturas.items(), 
            key=lambda x: len(x[0]), 
            reverse=True
        )
        
        for secuencia, nombre in aperturas_ordenadas:
            if historial_uci.startswith(secuencia):
                return nombre if len(self.board.move_stack) <= 16 else f"Fase Avanzada ({nombre})"
                    
        if len(self.board.move_stack) == 0:
            return "Posición Inicial"
        return "Medio Juego / Desarrollo Táctico"

    def obtener_movimiento_libro(self, modo: str = "uniforme") -> Optional[chess.Move]:
        """
        Consulta el archivo .bin de la carpeta data.
        Permite controlar la variedad de las respuestas de la IA mediante tres modos:
        'ponderado' (competitivo), 'uniforme' (máxima variedad) o 'principal' (determinista).
        """
        try:
            with chess.polyglot.open_reader(config.RUTA_LIBRO_APERTURAS) as reader:
                entradas = list(reader.find_all(self.board))
                
                # Filtro de seguridad: jugadas teóricas con peso > 0 y 100% legales
                entradas_validas = [
                    e for e in entradas 
                    if e.weight > 0 and e.move in self.board.legal_moves
                ]
                
                if entradas_validas:
                    import random
                    movimientos = [e.move for e in entradas_validas]
                    pesos = [e.weight for e in entradas_validas]
                    
                    if modo == "ponderado":
                        # Modo actual: respeta los pesos estadísticos (juego duro/competitivo)
                        eleccion = random.choices(movimientos, weights=pesos, k=1)
                        return eleccion[0]
                        
                    elif modo == "uniforme":
                        # MÁXIMA VARIEDAD: Todas las jugadas del libro tienen la misma probabilidad.
                        # Forzará al motor a jugar Escandinavas, Alekhines, Caro-Kanns, etc.
                        return random.choice(movimientos)
                        
                    elif modo == "principal":
                        # DETERMINISTA: Elige estrictamente la jugada con mayor peso del libro.
                        max_idx = pesos.index(max(pesos))
                        return movimientos[max_idx]
                        
        except (FileNotFoundError, IndexError):
            return None
        return None

    def evaluar_tablero(self) -> float:
        """
        Función de evaluación heurística lineal. 
        Garantiza un recorrido único por las 64 casillas sin bucles internos.
        """
        puntuacion_total: float = 0
        
        # Recorrido plano de 64 iteraciones estrictas
        for casilla in chess.SQUARES:
            pieza = self.board.piece_at(casilla)
            if pieza is not None:
                valor_material = config.VALORES_PIEZAS.get(pieza.piece_type, 0)
                valor_posicional = 0
                
                # Espejo para el bando negro
                casilla_tabla = casilla if pieza.color == chess.WHITE else chess.square_mirror(casilla)

                if pieza.piece_type == chess.PAWN: valor_posicional = config.PST_PEON[casilla_tabla]
                elif pieza.piece_type == chess.KNIGHT: valor_posicional = config.PST_CABALLO[casilla_tabla]
                elif pieza.piece_type == chess.BISHOP: valor_posicional = config.PST_ALFIL[casilla_tabla]
                elif pieza.piece_type == chess.ROOK: valor_posicional = config.PST_TORRE[casilla_tabla]
                elif pieza.piece_type == chess.QUEEN: valor_posicional = config.PST_REINA[casilla_tabla]
                elif pieza.piece_type == chess.KING: valor_posicional = config.PST_REY[casilla_tabla]
                
                valor_final_pieza = valor_material + valor_posicional
                
                if pieza.color == chess.WHITE:
                    puntuacion_total += valor_final_pieza
                else:
                    puntuacion_total -= valor_final_pieza
                    
        # --- LÓGICA DE FINALES (MOP-UP) DIRECTA ---
        # Evaluamos de forma externa y puramente secuencial
        if puntuacion_total > 400:
            puntuacion_total += self._forzar_rey_esquina(chess.WHITE, chess.BLACK)
        elif puntuacion_total < -400:
            puntuacion_total -= self._forzar_rey_esquina(chess.BLACK, chess.WHITE)
            
        return puntuacion_total

    def _forzar_rey_esquina(self, color_amigo: chess.Color, color_enemy: chess.Color) -> float:
        """
        Calcula la bonificación de arrinconamiento usando operaciones matemáticas puras.
        Sin bucles, sin condiciones de parada. O(1) estricto.
        """
        puntos_mopup = 0
        rey_enemigo_sq = self.board.king(color_enemy)
        rey_amigo_sq = self.board.king(color_amigo)
        
        if rey_enemigo_sq is None or rey_amigo_sq is None:
            return 0
            
        # Coordenadas del rey enemigo
        fila_enemiga = chess.square_rank(rey_enemigo_sq)
        col_enemiga = chess.square_file(rey_enemigo_sq)
        
        # Distancia del rey enemigo al centro (fomenta empujarlo al borde)
        distancia_centro_fila = max(3 - fila_enemiga, fila_enemiga - 4)
        distancia_centro_col = max(3 - col_enemiga, col_enemiga - 4)
        puntos_mopup += (distancia_centro_fila + distancia_centro_col) * 10
        
        # Distancia entre ambos reyes (fomenta la aproximación de nuestro rey)
        fila_amiga = chess.square_rank(rey_amigo_sq)
        col_amiga = chess.square_file(rey_amigo_sq)
        dist_reyes = abs(fila_enemiga - fila_amiga) + abs(col_enemiga - col_amiga)
        puntos_mopup += (14 - dist_reyes) * 4
        
        return puntos_mopup

    def quiescencia(self, alfa: float, beta: float, maximizando_blancas: bool) -> float:
        eval_actual = self.evaluar_tablero()
        if maximizando_blancas:
            if eval_actual >= beta: return beta
            alfa = max(alfa, eval_actual)
        else:
            if eval_actual <= alfa: return alfa
            beta = min(beta, eval_actual)

        for mov in self.board.generate_legal_captures():
            self.board.push(mov)
            puntuacion = self.evaluar_tablero()
            self.board.pop()
            
            if maximizando_blancas:
                eval_actual = max(eval_actual, puntuacion)
                alfa = max(alfa, eval_actual)
                if beta <= alfa: break
            else:
                eval_actual = min(eval_actual, puntuacion)
                beta = min(beta, eval_actual)
                if beta <= alfa: break
        return eval_actual

    def minimax(self, profundidad: int, maximizando_blancas: bool, alfa: float, beta: float) -> float:
        if self.board.is_checkmate():
            return -100000 - profundidad if self.board.turn == chess.WHITE else 100000 + profundidad
        if self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.is_repetition(2):
            return 0

        if profundidad == 0:
            return self.quiescencia(alfa, beta, maximizando_blancas)

        movimientos_legales = self._evaluar_y_ordenar_movimientos(list(self.board.legal_moves))

        if maximizando_blancas:
            max_eval = -float('inf')
            for mov in movimientos_legales:
                self.board.push(mov)
                eval_actual = self.minimax(profundidad - 1, False, alfa, beta)
                self.board.pop()
                max_eval = max(max_eval, eval_actual)
                alfa = max(alfa, eval_actual)
                if beta <= alfa: break 
            return max_eval
        else:
            min_eval = float('inf')
            for mov in movimientos_legales:
                self.board.push(mov)
                eval_actual = self.minimax(profundidad - 1, True, alfa, beta)
                self.board.pop()
                min_eval = min(min_eval, eval_actual)
                beta = min(beta, eval_actual)
                if beta <= alfa: break
            return min_eval

    def hacer_movimiento_inteligente(self, apertura_entrenamiento: str = "") -> bool:
        import random
        
        # =========================================================================
        # 1. MODO ENTRENAMIENTO ESTRICTO (Prioridad Absoluta)
        # =========================================================================
        if apertura_entrenamiento:
            mov_guia = self.obtener_siguiente_movimiento_guia(apertura_entrenamiento)
            if mov_guia and mov_guia in self.board.legal_moves:
                print(f"-> IA forzada por el guión de entrenamiento ({apertura_entrenamiento}): {mov_guia}")
                self.board.push(mov_guia)
                return True

        # =========================================================================
        # 2. CONSULTA AL LIBRO DE APERTURAS BINARIO (.bin)
        # =========================================================================
        # Si no hay guión activo o la teoría de la variante elegida ya terminó,
        # la IA recurre al libro general usando el modo que configures aquí:
        #   "uniforme" -> Máxima variedad aleatoria entre todas las opciones.
        #   "ponderado" -> Juego competitivo basado en estadísticas reales.
        #   "principal" -> Elige estrictamente la jugada con más peso del libro.
        mov_teorico = self.obtener_movimiento_libro(modo="principal")
        
        if mov_teorico:
            print(f"-> Jugada de libro ejecutada: {mov_teorico}")
            self.board.push(mov_teorico)
            return True

        # =========================================================================
        # 3. MOTOR CLÁSICO (Minimax + Poda Alfa-Beta + Ordenamiento a Profundidad 3)
        # =========================================================================
        # Si se sale completamente de la teoría, el motor calcula por fuerza bruta.
        movimientos_legales = list(self.board.legal_moves)
        if not movimientos_legales: 
            return False

        movimientos_ordenados = self._evaluar_y_ordenar_movimientos(movimientos_legales)
        mejores_movimientos = []
        mejor_valor = float('inf')
        alfa = -float('inf')
        beta = float('inf')

        for mov in movimientos_ordenados:
            self.board.push(mov)
            puntuacion_rama = self.minimax(3, True, alfa, beta) 
            self.board.pop()

            if puntuacion_rama < mejor_valor:
                mejor_valor = puntuacion_rama
                mejores_movimientos = [mov]
            elif puntuacion_rama == mejor_valor:
                mejores_movimientos.append(mov)
            beta = min(beta, puntuacion_rama)

        if not mejores_movimientos:
            mejores_movimientos = [movimientos_ordenados[0]]

        movimiento_final = random.choice(mejores_movimientos)
        self.board.push(movimiento_final)
        print(f"Movimiento de la IA realizado: {movimiento_final}. Turno de las blancas.")
        return True

    def _evaluar_y_ordenar_movimientos(self, movimientos: List[chess.Move]) -> List[chess.Move]:
        """
        Ordena la lista de movimientos legales priorizando capturas y jaques.
        Esto maximiza la eficiencia de la Poda Alfa-Beta disminuyendo los nodos visitados.
        """
        def score_movimiento(mov: chess.Move) -> int:
            puntuacion = 0
            if self.board.is_capture(mov):
                pieza_atacada = self.board.piece_at(mov.to_square)
                pieza_atacante = self.board.piece_at(mov.from_square)
                if pieza_atacada and pieza_atacante:
                    puntuacion += 1000 + (config.VALORES_PIEZAS.get(pieza_atacada.piece_type, 0) - 
                                          config.VALORES_PIEZAS.get(pieza_atacante.piece_type, 0) // 10)
            
            self.board.push(mov)
            if self.board.is_check():
                puntuacion += 500
            self.board.pop()
            
            return puntuacion

        # ¡CRUCIAL! Asegúrate de que esta línea exista y esté al final de la función principal
        return sorted(movimientos, key=score_movimiento, reverse=True)
    
    def forzar_inicio_teorico(self, nombre_apertura: str) -> None:
        """
        Reinicia el tablero y ejecuta automáticamente la secuencia de movimientos
        de la apertura indicada para empezar a jugar directamente desde esa fase.
        """
        self.reiniciar_juego()
        
        # Buscamos la secuencia UCI correspondiente en el diccionario cargado del JSON
        secuencia_uci = ""
        for uci, nombre in self.diccionario_aperturas.items():
            if nombre.lower() == nombre_apertura.lower():
                secuencia_uci = uci
                break
                
        if secuencia_uci and not secuencia_uci.startswith("//"):
            # Ejecutamos cada movimiento de la secuencia teórica en el tablero
            for mov_str in secuencia_uci.split():
                mov = chess.Move.from_uci(mov_str)
                if mov in self.board.legal_moves:
                    self.board.push(mov)
            print(f"[SISTEMA]: Tablero inicializado con éxito en la variante: {nombre_apertura}")
        else:
            print(f"[ALERTA]: No se encontró la apertura '{nombre_apertura}' en el JSON.")

    def obtener_siguiente_movimiento_guia(self, nombre_apertura: str) -> Optional[chess.Move]:
        """
        Compara el estado actual de la partida con una apertura del JSON.
        Devuelve el siguiente movimiento teórico que el jugador debe realizar
        para completar la variante, o None si ya se ha desviado o completado.
        """
        secuencia_uci = ""
        for uci, nombre in self.diccionario_aperturas.items():
            if nombre.lower() == nombre_apertura.lower():
                secuencia_uci = uci
                break
                
        if not secuencia_uci or secuencia_uci.startswith("//"):
            return None
            
        movimientos_teoria = secuencia_uci.split()
        movimientos_jugados = [mov.uci() for mov in self.board.move_stack]
        
        # Si el jugador ha seguido la teoría perfectamente hasta ahora
        if len(movimientos_jugados) < len(movimientos_teoria):
            # Comprobamos si lo que ya se ha jugado coincide con el inicio de la teoría
            es_fiel = True
            for i in range(len(movimientos_jugados)):
                if movimientos_jugados[i] != movimientos_teoria[i]:
                    es_fiel = False
                    break
            
            if es_fiel:
                # El siguiente movimiento que toca hacer es este:
                return chess.Move.from_uci(movimientos_teoria[len(movimientos_jugados)])
                
        return None