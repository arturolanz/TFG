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
import config  # Configuración general del proyecto
import unicodedata
import pygame

class ChessEngine:
    def __init__(self) -> None:
        self.board: chess.Board = chess.Board()
        self.diccionario_aperturas: Dict[str, str] = {}
        self.abortar_calculo = False  # Me permite cortar cálculos largos desde la interfaz
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
        # Primero pruebo el movimiento normal.
        movimiento_estandar = chess.Move(origen, destino)
        if movimiento_estandar in self.board.legal_moves:
            self.board.push(movimiento_estandar)
            return True
            
        # Si es promoción, por defecto corono a dama.
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
        
        # --- Búsqueda de la apertura más específica ---
        # Reviso antes las variantes largas para no quedarme con una línea demasiado general.
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
                
                # Solo uso entradas del libro con peso y que sigan siendo legales.
                entradas_validas = [
                    e for e in entradas 
                    if e.weight > 0 and e.move in self.board.legal_moves
                ]
                
                if entradas_validas:
                    import random
                    movimientos = [e.move for e in entradas_validas]
                    pesos = [e.weight for e in entradas_validas]
                    
                    if modo == "ponderado":
                        # Modo ponderado: respeta los pesos del libro.
                        eleccion = random.choices(movimientos, weights=pesos, k=1)
                        return eleccion[0]
                        
                    elif modo == "uniforme":
                        # Modo uniforme: prioriza variedad en la fase de apertura.
                        # Así el motor no repite siempre la misma respuesta.
                        return random.choice(movimientos)
                        
                    elif modo == "principal":
                        # Modo principal: opción determinista para pruebas.
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
        # AJUSTES FINOS DE EVALUACIÓN
        # =====================================================================
    
        # 1. Control del centro: d4, e4, d5 y e5.
        casillas_centrales = [chess.E4, chess.D4, chess.E5, chess.D5]
        control_blanco = sum(1 for c in casillas_centrales if tablero.is_attacked_by(chess.WHITE, c))
        control_negro = sum(1 for c in casillas_centrales if tablero.is_attacked_by(chess.BLACK, c))
        
        # Pequeño desempate por actividad central.
        puntuacion_total += (control_blanco - control_negro) * 0.2

        # 2. Penalización sencilla por peones doblados.
        peones_blancos = tablero.pieces(chess.PAWN, chess.WHITE)
        peones_negros = tablero.pieces(chess.PAWN, chess.BLACK)
        
        columnas_blancas = [chess.square_file(sq) for sq in peones_blancos]
        columnas_negras = [chess.square_file(sq) for sq in peones_negros]
        
        doblados_blancos = len(columnas_blancas) - len(set(columnas_blancas))
        doblados_negros = len(columnas_negras) - len(set(columnas_negras))
        
        puntuacion_total -= doblados_blancos * 0.3
        puntuacion_total += doblados_negros * 0.3

        # 3. Mop-up: ayuda a convertir ventajas grandes en mate.
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
            
        # Coordenadas básicas del rey rival.
        fila_enemiga = chess.square_rank(rey_enemigo_sq)
        col_enemiga = chess.square_file(rey_enemigo_sq)
        
        # Cuanto más lejos del centro esté el rey enemigo, mejor para el bando fuerte.
        distancia_centro_fila = max(3 - fila_enemiga, fila_enemiga - 4)
        distancia_centro_col = max(3 - col_enemiga, col_enemiga - 4)
        puntos_mopup += (distancia_centro_fila + distancia_centro_col) * 10
        
        # También interesa acercar nuestro rey al rey rival.
        fila_amiga = chess.square_rank(rey_amigo_sq)
        col_amiga = chess.square_file(rey_amigo_sq)
        dist_reyes = abs(fila_enemiga - fila_amiga) + abs(col_enemiga - col_amiga)
        puntos_mopup += (14 - dist_reyes) * 4
        
        return puntos_mopup

    def quiescencia(self, tablero, alfa: float, beta: float, maximizando_blancas: bool, limite_profundidad: int = 4) -> float:
        # Corte rápido si el cálculo se ha cancelado.
        if self.abortar_calculo:
            return 0
        pygame.event.pump()
        
        # Mate detectado dentro de la búsqueda de quiescencia.
        if tablero.is_checkmate():
            # Prefiero el mate más corto ajustando la puntuación con la profundidad restante.
            return -100000 - limite_profundidad if tablero.turn == chess.WHITE else 100000 + limite_profundidad
            
        if tablero.is_stalemate() or tablero.is_insufficient_material() or tablero.is_repetition(2):
            return 0

        eval_actual = self.evaluar_tablero(tablero)  # Evaluación de la posición actual del clon
        
        if limite_profundidad == 0:
            return eval_actual

        en_jaque = tablero.is_check()
        
        # Stand pat: evalúo la posición actual antes de seguir con capturas o jaques.
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

        # Ordeno primero las jugadas tácticas para que la poda trabaje mejor.
        movimientos_tacticos = self._evaluar_y_ordenar_movimientos(tablero, movimientos_tacticos)

        if maximizando_blancas:
            max_eval = eval_actual if not en_jaque else -float('inf')
            for mov in movimientos_tacticos:
                tablero.push(mov)
                # Recurro solo sobre posiciones tácticas.
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
                # Recurro solo sobre posiciones tácticas.
                puntuacion = self.quiescencia(tablero, alfa, beta, True, limite_profundidad - 1)
                tablero.pop()
                
                min_eval = min(min_eval, puntuacion)
                beta = min(beta, min_eval)
                if beta <= alfa: break
            return min_eval

    def minimax(self, tablero, profundidad: int, maximizando_blancas: bool, alfa: float, beta: float) -> float:
        # Corte rápido si el cálculo se ha cancelado.
        if self.abortar_calculo:
            return 0

        pygame.event.pump() 

        # Estados terminales usando siempre el tablero recibido.
        if tablero.is_checkmate():
            return -100000 - profundidad if tablero.turn == chess.WHITE else 100000 + profundidad
            
        if tablero.is_stalemate() or tablero.is_insufficient_material() or tablero.is_repetition(2):
            return 0

        if profundidad == 0:
            # Al llegar al límite, paso a quiescencia para no cortar una táctica abierta.
            return self.quiescencia(tablero, alfa, beta, maximizando_blancas)

        # Genero y ordeno movimientos del tablero de análisis.
        movimientos_legales = self._evaluar_y_ordenar_movimientos(tablero, list(tablero.legal_moves))

        if maximizando_blancas:
            max_eval = -float('inf')
            for mov in movimientos_legales:
                tablero.push(mov)  # Simulo el movimiento en el tablero local
                
                # Llamada recursiva sobre la posición simulada.
                eval_actual = self.minimax(tablero, profundidad - 1, False, alfa, beta)
                
                tablero.pop()  # Deshago el movimiento local
                
                max_eval = max(max_eval, eval_actual)
                alfa = max(alfa, eval_actual)
                if beta <= alfa: break
            return max_eval
        else:
            min_eval = float('inf')
            for mov in movimientos_legales:
                tablero.push(mov)  # Simulo el movimiento en el tablero local
                
                # Llamada recursiva sobre la posición simulada.
                eval_actual = self.minimax(tablero, profundidad - 1, True, alfa, beta)
                
                tablero.pop()  # Deshago el movimiento local
                
                min_eval = min(min_eval, eval_actual)
                beta = min(beta, eval_actual)
                if beta <= alfa: break
            return min_eval

    def hacer_movimiento_inteligente(self, apertura_entrenamiento: str = "") -> bool:
        import random
        
        # =========================================================================
        # 1. MODO ENTRENAMIENTO ESTRICTO
        # =========================================================================
        if apertura_entrenamiento:
            mov_guia = self.obtener_siguiente_movimiento_guia(apertura_entrenamiento)
            if mov_guia and mov_guia in self.board.legal_moves:
                print(f"-> IA forzada por el guion de entrenamiento ({apertura_entrenamiento}): {mov_guia}")
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
        # 3. MOTOR CLÁSICO (profundización iterativa + Alfa-Beta)
        # =========================================================================
        # Trabajo sobre una copia para no bloquear ni modificar el tablero real.
        # La interfaz sigue leyendo self.board mientras la IA calcula aparte.
        tablero_ia = self.board.copy()

        movimientos_legales = list(tablero_ia.legal_moves)
        if not movimientos_legales: 
            return False

        # Primer atajo: si hay mate en 1, se juega directamente.
        for mov in movimientos_legales:
            if self.abortar_calculo:  # Cancelación solicitada desde la interfaz
                    break

            tablero_ia.push(mov)
            if tablero_ia.is_checkmate():
                print(f"\n[INSTINTO ASESINO] Mate detectado al instante! Jugando: {mov.uci()}")
                tablero_ia.pop()
                
                # El mate directo se aplica en el tablero real.
                self.board.push(mov)
                return True
            tablero_ia.pop()

        # Orden inicial de movimientos antes de entrar en Minimax.
        movimientos_ordenados = self._evaluar_y_ordenar_movimientos(tablero_ia, movimientos_legales)
        soy_blancas = tablero_ia.turn == chess.WHITE
        
        material_tablero = sum(
            config.VALORES_PIEZAS.get(p.piece_type, 0) 
            for p in tablero_ia.piece_map().values() 
            if p.piece_type != chess.KING
        )

        if material_tablero < 2500:
            profundidad_maxima = 4
        else:
            profundidad_maxima = 3
        
        movimiento_final = movimientos_ordenados[0]
        registro_rayos_x = {}

        # Profundización iterativa: el motor aumenta la profundidad paso a paso.
        for profundidad_actual in range(1, profundidad_maxima + 1):
            
            if self.abortar_calculo:  # Si se cancela, salgo sin apurar más cálculo
                break

            mejor_valor = -float('inf') if soy_blancas else float('inf')
            alfa = -float('inf')
            beta = float('inf')
            mejores_movimientos_iteracion = []
            
            mate_encontrado = False

            for mov in movimientos_ordenados:
                tablero_ia.push(mov)  # Simulo en la copia
                
                # Minimax evalúa la rama desde la posición simulada.
                puntuacion_rama = self.minimax(tablero_ia, profundidad_actual, not soy_blancas, alfa, beta) 
                
                tablero_ia.pop()  # Deshago la simulación
                
                # Guardo los valores para mostrar el ranking de análisis.
                registro_rayos_x[mov.uci()] = puntuacion_rama

                if soy_blancas:
                    if puntuacion_rama > mejor_valor:
                        mejor_valor = puntuacion_rama
                        mejores_movimientos_iteracion = [mov]

                    alfa = max(alfa, puntuacion_rama)

                else:
                    if puntuacion_rama < mejor_valor:
                        mejor_valor = puntuacion_rama
                        mejores_movimientos_iteracion = [mov]

                    beta = min(beta, puntuacion_rama)

            # La mejor jugada de la capa actual pasa a explorarse primero.
            if mejores_movimientos_iteracion:
                movimiento_final = mejores_movimientos_iteracion[0]
                movimientos_ordenados.remove(movimiento_final)
                movimientos_ordenados.insert(0, movimiento_final)

            UMBRAL_MATE = 90000
            PROFUNDIDAD_MINIMA_MATE_FORZADO = 3

            if soy_blancas:
                mate_encontrado = mejor_valor > UMBRAL_MATE
            else:
                mate_encontrado = mejor_valor < -UMBRAL_MATE

            # Si se confirma una línea de mate, no tiene sentido seguir bajando más.
            if mate_encontrado and profundidad_actual >= PROFUNDIDAD_MINIMA_MATE_FORZADO:
                print(f"\n[INSTINTO ASESINO] Linea de mate detectada en la busqueda. Profundidad analizada: {profundidad_actual}.")
                break

        # =========================================================================
        # 4. EJECUCIÓN DE LA JUGADA DEFINITIVA
        # =========================================================================
        
        if self.abortar_calculo:  # Filtro final antes de tocar el tablero real
            print("\n[MOTOR] Cálculo zombi interceptado y destruido.")
            return False

        # Aplico en el tablero real la jugada elegida después de la búsqueda.
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
            
            # 1. Capturas y criterio MVV-LVA.
            if tablero.is_capture(mov):
                # En passant no deja pieza en la casilla destino, por eso lo trato aparte.
                if tablero.is_en_passant(mov):
                    puntuacion += 10000 
                else:
                    pieza_atacada = tablero.piece_at(mov.to_square)
                    pieza_atacante = tablero.piece_at(mov.from_square)
                    
                    if pieza_atacada and pieza_atacante:
                        valores = {chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 300, 
                                   chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 90000}
                        
                        valor_victima = valores.get(pieza_atacada.piece_type, 0)
                        valor_atacante = valores.get(pieza_atacante.piece_type, 0)
                        
                        puntuacion += 10000 + valor_victima - valor_atacante

                        # 2. Si la pieza estaba perdida, priorizo que capture algo antes de caer.
                        if tablero.is_attacked_by(not tablero.turn, mov.from_square):
                            puntuacion += 5000 + (valor_victima * 2)

            # 3. Promociones.
            if mov.promotion == chess.QUEEN:
                puntuacion += 9000
                
            # 4. Jaques: los mates completos los termina resolviendo Minimax.
            tablero.push(mov)
            # Evito comprobar mate aquí para no penalizar rendimiento.
            # Con is_check() ya subo estas jugadas en el orden.
            if tablero.is_check():
                puntuacion += 2000
            tablero.pop()
            
            # 5. Seguridad de la pieza tras mover.
            pieza_origen = tablero.piece_at(mov.from_square)
            if pieza_origen:
                tablero.push(mov)
                # Compruebo si el destino queda controlado por el rival.
                if tablero.is_attacked_by(tablero.turn, mov.to_square):
                    if pieza_origen.piece_type == chess.QUEEN:
                        puntuacion -= 8000  # Perder la dama pesa mucho
                    elif pieza_origen.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK]:
                        puntuacion -= 1000  # Castigo por dejar una pieza en prise
                tablero.pop()

            # 6. Centralización como desempate para jugadas tranquilas.
            if puntuacion == 0.0:
                fila_destino = chess.square_rank(mov.to_square)
                col_destino = chess.square_file(mov.to_square)
                # Distancia al centro geométrico del tablero.
                distancia_centro = abs(3.5 - col_destino) + abs(3.5 - fila_destino)
                # Más cerca del centro implica una pequeña bonificación.
                puntuacion += (7.0 - distancia_centro) * 0.05

            return puntuacion

        return sorted(movimientos, key=score_movimiento, reverse=True)
    
    def _normalizar_texto(self, texto: str) -> str:
        """
        Normaliza texto para comparar nombres de aperturas:
        ignora mayúsculas, tildes y espacios sobrantes.
        """
        texto = texto.lower().strip()
        texto = unicodedata.normalize("NFD", texto)
        texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
        texto = " ".join(texto.split())
        return texto

    def _buscar_secuencia_apertura(self, nombre_apertura: str) -> str:
        """
        Busca una apertura por nombre exacto o parcial.
        Si hay varias coincidencias, elige la más general.
        """
        objetivo = self._normalizar_texto(nombre_apertura)

        if not objetivo:
            return ""

        coincidencias = []

        for uci, nombre in self.diccionario_aperturas.items():
            if uci.startswith("//"):
                continue

            nombre_norm = self._normalizar_texto(nombre)

            if objetivo == nombre_norm:
                return uci

            if objetivo in nombre_norm:
                coincidencias.append((len(uci.split()), len(nombre), uci))

        if coincidencias:
            coincidencias.sort()
            return coincidencias[0][2]

        return ""

    def forzar_inicio_teorico(self, nombre_apertura: str) -> None:
        """
        Reinicia el tablero y ejecuta automáticamente la secuencia de movimientos
        de la apertura indicada para empezar a jugar directamente desde esa fase.
        """
        self.reiniciar_juego()
        
        # Localizo la secuencia UCI asociada al nombre recibido.
        secuencia_uci = self._buscar_secuencia_apertura(nombre_apertura)
                
        if secuencia_uci and not secuencia_uci.startswith("//"):
            # Reproduzco la variante hasta llegar a la posición de inicio.
            for mov_str in secuencia_uci.split():
                mov = chess.Move.from_uci(mov_str)
                if mov in self.board.legal_moves:
                    self.board.push(mov)
            print(f"[SISTEMA]: Tablero inicializado con exito en la variante: {nombre_apertura}")
        else:
            print(f"[ALERTA]: No se encontro la apertura '{nombre_apertura}' en el JSON.")

    def obtener_siguiente_movimiento_guia(self, nombre_apertura: str) -> Optional[chess.Move]:
        """
        Compara el estado actual de la partida con una apertura del JSON.
        Devuelve el siguiente movimiento teórico que el jugador debe realizar
        para completar la variante, o None si ya se ha desviado o completado.
        """
        secuencia_uci = self._buscar_secuencia_apertura(nombre_apertura)
                
        if not secuencia_uci or secuencia_uci.startswith("//"):
            return None
            
        movimientos_teoria = secuencia_uci.split()
        movimientos_jugados = [mov.uci() for mov in self.board.move_stack]
        
        # Solo hay guía si la partida todavía sigue la teoría.
        if len(movimientos_jugados) < len(movimientos_teoria):
            # Comparo lo jugado con el inicio de la línea teórica.
            es_fiel = True
            for i in range(len(movimientos_jugados)):
                if movimientos_jugados[i] != movimientos_teoria[i]:
                    es_fiel = False
                    break
            
            if es_fiel:
                # Devuelvo el siguiente movimiento previsto por la apertura.
                return chess.Move.from_uci(movimientos_teoria[len(movimientos_jugados)])
                
        return None

    def guardar_partida_pgn(self, resultado_str: str, color_humano: chess.Color, es_manual: bool = False) -> None:
        """
        Exporta la partida a formato PGN.
        - Si es_manual=False: Va a logs_partidas (rotación de 5).
        - Si es_manual=True: Va a partidas_descargadas (sin límite).
        """
        # Rutas de salida según sea guardado manual o log automático.
        carpeta_base = "../docs"
        sub_carpeta = "partidas_descargadas" if es_manual else "logs_partidas"
        directorio_final = os.path.join(carpeta_base, sub_carpeta)
        
        if not os.path.exists(directorio_final):
            os.makedirs(directorio_final)

        # Cabeceras básicas del archivo PGN.
        juego_pgn = chess.pgn.Game.from_board(self.board)
        juego_pgn.headers["Event"] = "Manual Export" if es_manual else "Auditoría TFG"
        juego_pgn.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
        juego_pgn.headers["White"] = "Humano" if color_humano == chess.WHITE else "IA Minimax"
        juego_pgn.headers["Black"] = "IA Minimax" if color_humano == chess.WHITE else "Humano"
        juego_pgn.headers["Result"] = resultado_str

        # Nombre único para no pisar partidas anteriores.
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_archivo = os.path.join(directorio_final, f"partida_{timestamp}.pgn")
        
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            f.write(str(juego_pgn))
                
        print(f"\n[SISTEMA] Partida guardada en: {ruta_archivo}")

        # Mantengo solo los últimos logs automáticos.
        if not es_manual:
            archivos_pgn = glob.glob(os.path.join(directorio_final, "*.pgn"))
            archivos_pgn.sort(key=os.path.getctime) 
            
            while len(archivos_pgn) > 5:
                archivo_viejo = archivos_pgn.pop(0)
                try:
                    os.remove(archivo_viejo)
                    print(f"[SISTEMA] Rotacion: Eliminado {archivo_viejo}")
                except OSError:
                    pass

    def solicitar_apertura_usuario(self):
        import tkinter as tk
        from tkinter import simpledialog
        
        # Tkinter se usa únicamente para esta ventana puntual.
        root = tk.Tk()
        root.attributes('-topmost', True)
        
        # Dejo withdraw desactivado porque aquí me dio más estabilidad.
        # root.withdraw()
        
        apertura = simpledialog.askstring("Apertura", "Introduce nombre:")
        root.destroy()
        
        # Libero la referencia a la ventana antes de salir.
        del root
        return apertura
