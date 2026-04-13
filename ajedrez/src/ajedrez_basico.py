import chess

#Creamos una instancia del tablero
#Al nacer, el objeto ya conoce la posición inicial de todas las piezas
tablero = chess.Board()

#1. Ver el tablero en la consola
print("Posicion Inicial:")
print(tablero)

#2. Ver quién mueve (True para Blancas, False para negras)
print(f"\n¿Mueven las blancas?: {tablero.turn == chess.WHITE}")

#3. Listar movimientos legales
# Esto es vital para mi IA: nunca intentará una jugada imposible
print("\nMovimientos legales posibles:")
for mov in tablero.legal_moves:
    print(mov)

# Realizar el famoso movimiento de peón de rey (e2 a e4)
movimiento = chess.Move.from_uci("e2e4")
if movimiento in tablero.legal_moves:
    tablero.push(movimiento)
    print("\nTablero después de 1. e4:")
    print(tablero)
