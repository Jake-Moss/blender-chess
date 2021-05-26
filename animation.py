#!/usr/bin/env python3
#
import chess
import chess.pgn
import bpy
from mathutils import Vector
from typing import Tuple, Dict


def square_to_world_space(square: int) -> Tuple[float, float]:
    return ((square % 8) + 0.5, (square // 8) + 0.5)


def make_move(board: chess.Board, move: chess.Move, pieces: Dict):
    squareFrom = move.from_square
    xFrom, yFrom = square_to_world_space(squareFrom)

    squareTo = move.to_square
    xTo, yTo = square_to_world_space(squareTo)


    if board.is_capture(move):
        captured = pieces[chess.square_name(squareTo)]
        captured.location.z = 30
        pieces.pop(chess.square_name(squareTo))

    selected = pieces[chess.square_name(squareFrom)]
    pieces.pop(chess.square_name(squareFrom))

    selected.location.x = xTo
    selected.location.y = yTo

    selected["Square"] = chess.square_name(squareTo)
    pieces[selected['Square']] = selected
    keyframe_insert(pieces)

def keyframe_insert(pieces: Dict):
    for piece in pieces.values():
        piece.keyframe_insert(data_path="location", index=-1)

def main(filename) -> chess.pgn.Game:
    print("test")
    with open(filename) as pgn:
        game = chess.pgn.read_game(pgn)
        board = game.board()
        scene = bpy.context.scene


        pieces = {}
        for colour in ('White', 'Black'):
            for piece in bpy.data.collections[colour].objects:
                # pieces[piece['Square']] = board.piece_at(chess.parse_square(piece['Square']))
                pieces[piece['Square']] = piece


        print(pieces)
        number_of_frame = 0
        for move in game.mainline_moves():
            scene.frame_set(number_of_frame)

            print(move)
            make_move(board, move, pieces)

            board.push(move)
            number_of_frame += 10
        return game





if __name__ == "__main__":
    main("/home/jake/Uni/2nd year/COSC3000/ComputerGraphics/testing.pgn")
