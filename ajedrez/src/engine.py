# src/engine.py
import json
import random
import os
import glob
import datetime
from typing import Dict, Optional, List
import chess
import chess.polyglot
import chess.pgn
import config  # Importamos centralizadamente la configuración

class ChessEngine:
    def __init__(self) -> None:
        self.board: chess.Board = chess.Board()
        self.diccionario_aperturas: Dict[str, str] = {}
        self.abortar_calculo = False  # <--- NUEVO: Nuestro botón de pánico
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

    def evaluar_tablero(self, tablero) -> float:
        puntuacion_total: float = 0.0
        
        VALORES_SEGUROS = {
            chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 300,
            chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 90000
        }
        
        for casilla in chess.SQUARES:
            pieza = tablero.piece_at(casilla)
            if pieza is not None:
                valor_material = VALORES_SEGUROS.get(pieza.piece_type, 0)
                valor_posicional = 0
                
                casilla_tabla = casilla if pieza.color == chess.WHITE else chess.square_mirror(casilla)

                if pieza.piece_type == chess.PAWN: 
                    valor_posicional = config.PST_PEON[casilla_tabla]
                elif pieza.piece_type == chess.KNIGHT: 
                    valor_posicional = config.PST_CABALLO[casilla_tabla]
                elif pieza.piece_type == chess.BISHOP: 
                    valor_posicional = config.PST_ALFIL[casilla_tabla]
                elif pieza.piece_type == chess.ROOK: 
                    valor_posicional = config.PST_TORRE[casilla_tabla]
                elif pieza.piece_type == chess.QUEEN: 
                    valor_posicional = config.PST_REINA[casilla_tabla]
                elif pieza.piece_type == chess.KING: 
                    valor_posicional = config.PST_REY[casilla_tabla]
                
                valor_final_pieza = valor_material + valor_posicional
                
                if pieza.color == chess.WHITE:
                    puntuacion_total += valor_final_pieza
                else:
                    puntuacion_total -= valor_final_pieza
                    
        # =====================================================================
        # DESEMPATE ESTRATÉGICO DE GRANO FINO (Rompe las mesetas de evaluación)
        # =====================================================================
    
        # 1. CONTROL DEL CENTRO (Las 4 casillas críticas: d4, e4, d5, e5)
        casillas_centrales = [chess.E4, chess.D4, chess.E5, chess.D5]
        control_blanco = sum(1 for c in casillas_centrales if tablero.is_attacked_by(chess.WHITE, c))
        control_negro = sum(1 for c in casillas_centrales if tablero.is_attacked_by(chess.BLACK, c))
        
        # Otorgamos 0.2 puntos por cada ataque al centro
        puntuacion_total += (control_blanco - control_negro) * 0.2

        # 2. PENALIZACIÓN POR PEONES DOBLADOS (Estructura sólida)
        peones_blancos = tablero.pieces(chess.PAWN, chess.WHITE)
        peones_negros = tablero.pieces(chess.PAWN, chess.BLACK)
        
        columnas_blancas = [chess.square_file(sq) for sq in peones_blancos]
        columnas_negras = [chess.square_file(sq) for sq in peones_negros]
        
        doblados_blancos = len(columnas_blancas) - len(set(columnas_blancas))
        doblados_negros = len(columnas_negras) - len(set(columnas_negras))
        
        puntuacion_total -= doblados_blancos * 0.3
        puntuacion_total += doblados_negros * 0.3

        # 3. HEURÍSTICA DE LIMPIEZA (MOP-UP) PARA FORZAR EL JAQUE MATE
        if abs(puntuacion_total) > 400:
            if puntuacion_total > 0:
                puntuacion_total += self._forzar_rey_esquina(tablero, chess.WHITE, chess.BLACK)
            else:
                puntuacion_total -= self._forzar_rey_esquina(tablero, chess.BLACK, chess.WHITE)
                
        return puntuacion_total

    def _forzar_rey_esquina(self, tablero, color_amigo: chess.Color, color_enemy: chess.Color) -> float:
        """
        Calcula la bonificación de arrinconamiento usando operaciones matemáticas puras.
        Sin bucles, sin condiciones de parada. O(1) estricto.
        """
        puntos_mopup = 0
        rey_enemigo_sq = tablero.king(color_enemy)
        rey_amigo_sq = tablero.king(color_amigo)
        
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

    def quiescencia(self, tablero, alfa: float, beta: float, maximizando_blancas: bool, limite_profundidad: int = 4) -> float:
        # ---> NUEVO: Freno de emergencia instantáneo <---
        if self.abortar_calculo:
            return 0

        import pygame
        pygame.event.pump()
        
        # ---> NUEVO: DETECCIÓN DE MATE EN QUIESCENCIA <---
        if tablero.is_checkmate():
            # Sumamos/restamos el limite_profundidad para que la IA prefiera el mate más rápido posible
            return -100000 - limite_profundidad if tablero.turn == chess.WHITE else 100000 + limite_profundidad
            
        if tablero.is_stalemate() or tablero.is_insufficient_material() or tablero.is_repetition(2):
            return 0

        eval_actual = self.evaluar_tablero(tablero) # <--- Ahora lee la puntuación del clon
        
        if limite_profundidad == 0:
            return eval_actual

        en_jaque = tablero.is_check()
        
        # Soft-fail Stand Pat
        if not en_jaque:
            if maximizando_blancas:
                if eval_actual >= beta: return eval_actual
                alfa = max(alfa, eval_actual)
            else:
                if eval_actual <= alfa: return eval_actual
                beta = min(beta, eval_actual)

        if en_jaque:
            movimientos_tacticos = list(tablero.legal_moves)
        else:
            movimientos_tacticos = []
            for mov in tablero.legal_moves:
                if tablero.is_capture(mov) or tablero.gives_check(mov):
                    movimientos_tacticos.append(mov)

        # Arreglado el TypeError de los parámetros
        movimientos_tacticos = self._evaluar_y_ordenar_movimientos(tablero, movimientos_tacticos)

        if maximizando_blancas:
            max_eval = eval_actual if not en_jaque else -float('inf')
            for mov in movimientos_tacticos:
                tablero.push(mov)
                # Pasamos el tablero en la recursividad
                puntuacion = self.quiescencia(tablero, alfa, beta, False, limite_profundidad - 1)
                tablero.pop()
                
                max_eval = max(max_eval, puntuacion)
                alfa = max(alfa, max_eval)
                if beta <= alfa: break
            return max_eval
        else:
            min_eval = eval_actual if not en_jaque else float('inf')
            for mov in movimientos_tacticos:
                tablero.push(mov)
                # Pasamos el tablero en la recursividad
                puntuacion = self.quiescencia(tablero, alfa, beta, True, limite_profundidad - 1)
                tablero.pop()
                
                min_eval = min(min_eval, puntuacion)
                beta = min(beta, min_eval)
                if beta <= alfa: break
            return min_eval

    def minimax(self, tablero, profundidad: int, maximizando_blancas: bool, alfa: float, beta: float) -> float:
        # ---> NUEVO: Freno de emergencia instantáneo <---
        if self.abortar_calculo:
            return 0

        import pygame
        pygame.event.pump() 

        # 1. Reemplazamos self.board por tablero en los estados terminales
        if tablero.is_checkmate():
            return -100000 - profundidad if tablero.turn == chess.WHITE else 100000 + profundidad
            
        if tablero.is_stalemate() or tablero.is_insufficient_material() or tablero.is_repetition(2):
            return 0

        if profundidad == 0:
            # ¡OJO! Tu búsqueda de quiescencia también necesitará recibir este tablero clonado
            return self.quiescencia(tablero, alfa, beta, maximizando_blancas)

        # 2. Obtenemos los movimientos legales del tablero clonado
        # Si tu función _evaluar_y_ordenar_movimientos lee posiciones de piezas, pásale también 'tablero'
        movimientos_legales = self._evaluar_y_ordenar_movimientos(tablero, list(tablero.legal_moves))

        if maximizando_blancas:
            max_eval = -float('inf')
            for mov in movimientos_legales:
                tablero.push(mov) # Hacer movimiento en el tablero local
                
                # 3. Pasamos el tablero en la llamada recursiva
                eval_actual = self.minimax(tablero, profundidad - 1, False, alfa, beta)
                
                tablero.pop() # Deshacer movimiento en el tablero local
                
                max_eval = max(max_eval, eval_actual)
                alfa = max(alfa, eval_actual)
                if beta <= alfa: break
            return max_eval
        else:
            min_eval = float('inf')
            for mov in movimientos_legales:
                tablero.push(mov) # Hacer movimiento en el tablero local
                
                # 3. Pasamos el tablero en la llamada recursiva
                eval_actual = self.minimax(tablero, profundidad - 1, True, alfa, beta)
                
                tablero.pop() # Deshacer movimiento en el tablero local
                
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
        mov_teorico = self.obtener_movimiento_libro(modo="uniforme")
        
        if mov_teorico:
            print(f"-> Jugada de libro ejecutada: {mov_teorico}")
            self.board.push(mov_teorico)
            return True

        # =========================================================================
        # 3. MOTOR CLÁSICO (Con Profundización Iterativa y Corte Inmediato)
        # =========================================================================
        # ¡CAMBIO CLAVE!: Clonamos el tablero aquí. Toda la simulación pesada
        # ocurrirá en 'tablero_ia', dejando 'self.board' libre para el hilo principal.
        tablero_ia = self.board.copy()

        movimientos_legales = list(tablero_ia.legal_moves)
        if not movimientos_legales: 
            return False

        # Instinto Asesino O(1) (Mate en 1 directo) -> Ahora usa tablero_ia
        for mov in movimientos_legales:
            if self.abortar_calculo: # <--- NUEVO: Salir del bucle de movimientos al instante
                    break

            tablero_ia.push(mov)
            if tablero_ia.is_checkmate():
                print(f"\n[INSTINTO ASESINO] ¡Mate detectado al instante! Jugando: {mov.uci()}")
                tablero_ia.pop()
                
                # Si es mate directo, lo aplicamos al tablero REAL y salimos
                self.board.push(mov)
                return True
            tablero_ia.pop()

        # Pasamos 'tablero_ia' a tu función de ordenamiento por si analiza casillas/piezas
        movimientos_ordenados = self._evaluar_y_ordenar_movimientos(tablero_ia, movimientos_legales)
        soy_blancas = tablero_ia.turn == chess.WHITE
        
        material_tablero = sum(
            config.VALORES_PIEZAS.get(p.piece_type, 0) 
            for p in tablero_ia.piece_map().values() 
            if p.piece_type != chess.KING
        )
        profundidad_maxima = 5 if material_tablero < 4000 else 3
        
        movimiento_final = movimientos_ordenados[0]
        registro_rayos_x = {}

        # PROFUNDIZACIÓN ITERATIVA (El motor busca capa por capa)
        for profundidad_actual in range(1, profundidad_maxima + 1):
            
            if self.abortar_calculo:  # <--- NUEVO: Salimos del bucle si nos cancelan
                break

            mejor_valor = -float('inf') if soy_blancas else float('inf')
            alfa = -float('inf')
            beta = float('inf')
            mejores_movimientos_iteracion = []
            
            mate_encontrado = False

            for mov in movimientos_ordenados:
                tablero_ia.push(mov) # <--- CAMBIO: push en el clon
                
                # <--- CAMBIO: Pasamos 'tablero_ia' como primer argumento al minimax
                puntuacion_rama = self.minimax(tablero_ia, profundidad_actual, not soy_blancas, alfa, beta) 
                
                tablero_ia.pop() # <--- CAMBIO: pop en el clon
                
                # Guardamos los rayos X solo de la iteración más profunda completada
                registro_rayos_x[mov.uci()] = puntuacion_rama

                if soy_blancas:
                    if puntuacion_rama > mejor_valor:
                        mejor_valor = puntuacion_rama
                        mejores_movimientos_iteracion = [mov] 
                    alfa = max(alfa, puntuacion_rama)
                    if puntuacion_rama > 90000:  # Umbral de Jaque Mate
                        mate_encontrado = True
                else:
                    if puntuacion_rama < mejor_valor: 
                        mejor_valor = puntuacion_rama
                        mejores_movimientos_iteracion = [mov] 
                    beta = min(beta, puntuacion_rama)
                    if puntuacion_rama < -90000: # Umbral de Jaque Mate
                        mate_encontrado = True

            # Actualizamos el movimiento definitivo con lo aprendido en esta capa
            if mejores_movimientos_iteracion:
                movimiento_final = mejores_movimientos_iteracion[0]
                movimientos_ordenados.remove(movimiento_final)
                movimientos_ordenados.insert(0, movimiento_final)

            # EL CORTE ABSOLUTO: Si encontramos el mate, no calculamos profundidades mayores.
            if mate_encontrado:
                print(f"\n[CORTOCIRCUITO] Mate inevitable hallado a profundidad {profundidad_actual}. Búsqueda abortada.")
                break

        # =========================================================================
        # 4. EJECUCIÓN DE LA JUGADA DEFINITIVA
        # =========================================================================
        
        if self.abortar_calculo:  # <--- NUEVO: Filtro de seguridad final
            print("\n[MOTOR] Cálculo zombi interceptado y destruido.")
            return False

        # Una vez finalizada toda la búsqueda asíncrona, aplicamos el movimiento 
        # ganador en el tablero REAL para que se entere la interfaz gráfica.
        self.board.push(movimiento_final) 
        
        print(f"\n[RAYOS X] Ranking de jugadas (Profundidad alcanzada: {profundidad_actual}):")
        movimientos_ordenados_x = sorted(registro_rayos_x.items(), key=lambda x: x[1], reverse=soy_blancas)
        for mov_uci, punt in movimientos_ordenados_x:
            marca = " <=== ELEGIDA" if mov_uci == movimiento_final.uci() else ""
            print(f"Jugada {mov_uci}: {punt}{marca}")
            
        print(f"\nMovimiento de la IA realizado: {movimiento_final}.")
        return True

    def _evaluar_y_ordenar_movimientos(self, tablero, movimientos: List[chess.Move]) -> List[chess.Move]:
        """
        Ordena la lista de movimientos legales para optimizar la Poda Alfa-Beta.
        Aplica MVV-LVA, heurística Desperado y protección extendida de piezas.
        """
        def score_movimiento(mov: chess.Move) -> float:
            puntuacion = 0.0
            
            # 1. TÁCTICA MVV-LVA Y CAPTURAS
            if tablero.is_capture(mov): # <--- CAMBIO
                # Arreglo crítico: Las capturas al paso no tienen pieza en la casilla de destino
                if tablero.is_en_passant(mov): # <--- CAMBIO
                    puntuacion += 10000 
                else:
                    pieza_atacada = tablero.piece_at(mov.to_square) # <--- CAMBIO
                    pieza_atacante = tablero.piece_at(mov.from_square) # <--- CAMBIO
                    
                    if pieza_atacada and pieza_atacante:
                        valores = {chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 300, 
                                   chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 90000}
                        
                        valor_victima = valores.get(pieza_atacada.piece_type, 0)
                        valor_atacante = valores.get(pieza_atacante.piece_type, 0)
                        
                        puntuacion += 10000 + valor_victima - valor_atacante

                        # 2. EL INSTINTO "MUERE MATANDO"
                        if tablero.is_attacked_by(not tablero.turn, mov.from_square): # <--- CAMBIO
                            puntuacion += 5000 + (valor_victima * 2)

            # 3. PROMOCIONES DE PEÓN
            if mov.promotion == chess.QUEEN:
                puntuacion += 9000
                
            # 4. JAQUES AL REY (Mates gestionados por Minimax)
            tablero.push(mov) # <--- CAMBIO
            # BUG FIX: Eliminamos el is_checkmate() de aquí por rendimiento. 
            # El is_check() ya asegura que los mates se ordenen arriba.
            if tablero.is_check(): # <--- CAMBIO
                puntuacion += 2000
            tablero.pop() # <--- CAMBIO
            
            # 5. PENALIZACIÓN DE SEGURIDAD EXTENDIDA
            pieza_origen = tablero.piece_at(mov.from_square) # <--- CAMBIO
            if pieza_origen:
                tablero.push(mov) # <--- CAMBIO
                # Evaluamos si la casilla destino está controlada por el enemigo
                if tablero.is_attacked_by(tablero.turn, mov.to_square): # <--- CAMBIO
                    if pieza_origen.piece_type == chess.QUEEN:
                        puntuacion -= 8000  # Castigo catastrófico
                    elif pieza_origen.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK]:
                        puntuacion -= 1000  # Castigo severo por regalar piezas menores
                tablero.pop() # <--- CAMBIO

            # 6. BONIFICACIÓN DE CENTRALIZACIÓN (Desempate de movimientos silenciosos)
            # Si el movimiento no es una captura ni un jaque, le damos prioridad
            # a las piezas que se muevan hacia el centro del tablero.
            if puntuacion == 0.0:
                fila_destino = chess.square_rank(mov.to_square)
                col_destino = chess.square_file(mov.to_square)
                # Distancia matemática al centro exacto del tablero (3.5, 3.5)
                distancia_centro = abs(3.5 - col_destino) + abs(3.5 - fila_destino)
                # Las casillas centrales obtienen más decimales positivos (ej. +0.35)
                puntuacion += (7.0 - distancia_centro) * 0.05

            return puntuacion

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

    def guardar_partida_pgn(self, resultado_str: str, color_humano: chess.Color) -> None:
        """
        Exporta la partida actual a formato estándar PGN para su posterior análisis.
        Mantiene un sistema de rotación que elimina partidas viejas, dejando solo las 5 últimas.
        """
        directorio_logs = "logs_partidas"
        if not os.path.exists(directorio_logs):
            os.makedirs(directorio_logs)

        # 1. Creamos el archivo de partida desde el historial del tablero
        juego_pgn = chess.pgn.Game.from_board(self.board)
        
        # 2. Añadimos metadatos (Cabeceras)
        juego_pgn.headers["Event"] = "Auditoría TFG - Pruebas de Motor"
        juego_pgn.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
        juego_pgn.headers["White"] = "Humano" if color_humano == chess.WHITE else "IA Minimax"
        juego_pgn.headers["Black"] = "IA Minimax" if color_humano == chess.WHITE else "Humano"
        juego_pgn.headers["Result"] = resultado_str

        # 3. Guardamos el archivo con la marca de tiempo exacta
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_archivo = os.path.join(directorio_logs, f"partida_{timestamp}.pgn")
        
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            f.write(str(juego_pgn))
            
        print(f"\n[SISTEMA] Partida guardada en: {ruta_archivo}")

        # 4. SISTEMA DE ROTACIÓN (Mantener solo las 5 más recientes)
        archivos_pgn = glob.glob(os.path.join(directorio_logs, "*.pgn"))
        # Ordenamos de más antiguo a más nuevo basándonos en la fecha de creación
        archivos_pgn.sort(key=os.path.getctime) 
        
        # Mientras haya más de 5 archivos, borramos el primero (el más viejo)
        while len(archivos_pgn) > 5:
            archivo_viejo = archivos_pgn.pop(0)
            try:
                os.remove(archivo_viejo)
                print(f"[SISTEMA] Rotacion: Archivo antiguo eliminado ({archivo_viejo})")
            except OSError:
                pass