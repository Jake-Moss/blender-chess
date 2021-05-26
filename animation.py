#!/usr/bin/env python3
from __future__ import annotations # type hinting the self reference
import chess
import chess.pgn
import bpy
from mathutils import Vector
from math import radians
from typing import Tuple, Dict, List, Optional

def square_to_world_space(square: int) -> Tuple[float, float]:
    return ((square % 8) + 0.5, (square // 8) + 0.5)


def keyframes(array: List[Optional[CustomPiece]]):
    for piece in array:
        if piece is not None:
            piece.keyframe_insert(data_path="location", index=-1)


class CustomPiece():
    def __init__(self, pieceType: chess.Piece, blender_obj: bpy.types.Object,\
                 array: List[Optional[CustomPiece]], loc: int):
        self._pieceType = pieceType.piece_type # int
        self._colour = pieceType.color         # bool
        self._blender_obj = blender_obj.copy()
        self._array = array                    # reference to array containing self
        self._loc = loc                        # int (1d array index)

        x, y = square_to_world_space(self._loc)
        self._blender_obj.location = Vector((x, y, 0.1))

        # set material based on colour
        if self._colour:
            self._mat = bpy.data.materials["White pieces"]
        else:
            self._mat = bpy.data.materials["Black pieces"]
        self._blender_obj.active_material = self._mat


        if self._colour and self._pieceType == chess.KNIGHT:
            self._blender_obj.rotation_euler[2] = radians(180) #XYZ
        # add object to collection so its visable
        bpy.data.collections[['Black', 'White'][self._colour]].objects.link(self._blender_obj)

    def move(self, new_loc: int, zTo: float = 0.1):
        xTo, yTo = square_to_world_space(new_loc)
        self._blender_obj.location = Vector((xTo, yTo, zTo))
        print("Moved to ", self._blender_obj.location)

        self._array[new_loc] = self
        self._array[self._loc] = None

        self._loc = new_loc

    def die(self) -> CustomPiece:
        # TODO some animation here
        self.move(self._loc, zTo = 30)
        self._array[self._loc] = None
        self.keyframe_insert(data_path="location", index=-1) # TODO Move this somewhere else
        return self

    def keyframe_insert(self, *args, **kwargs):
        self._blender_obj.keyframe_insert(*args, **kwargs)

def make_move(board: chess.Board, move: chess.Move, array: List[Optional[CustomPiece]]):
    """
    Moves the pieces in blender based on the move from the library.

    See EOF for flow chart
    """
    locTo = move.to_square
    locFrom = move.from_square

    print(move, "   ", locFrom, " --> ", locTo)

    if board.is_castling(move):
        if board.turn: # White
            if board.is_kingside_castling(move):
                array[chess.H1].move(chess.F1)
            else: # queen side
                array[chess.A1].move(chess.D1)
        else: # Black
            if board.is_kingside_castling(move):
                array[chess.H8].move(chess.F8)
            else: # queen side
                array[chess.A8].move(chess.D8)

    else: # standard case
        if board.is_capture(move):# is en passant, great
            if board.is_en_passant(move): # normal capture
                captured_piece = array[board.ep_square].die() # TODO, do something with this
            else: # its a capture,
                captured_piece = array[locTo].die() # TODO, do something with this

    # if move.promotion is not None:
    #     # unlink somehow
    #     pieceType = move.promotion
    #     array[locTo] = CustomPiece(chess.Piece(pieceType, board.turn),\
    #                                SOURCE_PIECES[chess.piece_symbol(pieceType)],\
    #                                array, locTo)

    array[locFrom].move(locTo) # NOTE, piece moves always


def main(filename) -> Optional[chess.pgn.Game]:
    with open(filename) as pgn:
        game = chess.pgn.read_game(pgn)
        board = game.board()
        scene = bpy.context.scene

        global SOURCE_PIECES
        SOURCE_PIECES = {}
        for piece in bpy.data.collections["Pieces"].objects:
            # pieces[piece['Square']] = board.piece_at(chess.parse_square(piece['Square']))
            SOURCE_PIECES[piece['repr'].lower()] = piece

        array = [None for _ in range(64)]
        for position in range(64):
            piece = board.piece_at(position)
            if piece is not None:
                array[position] = CustomPiece(piece, SOURCE_PIECES[piece.symbol().lower()]\
                                              , array, position)

        number_of_frame = 0
        keyframes(array) # intial pos
        number_of_frame += 10
        for move in game.mainline_moves():
            scene.frame_set(number_of_frame)

            make_move(board, move, array)


            keyframes(array) # update blender
            board.push(move) # update python-chess

            number_of_frame += 10
        return game





if __name__ == "__main__":
    main("/home/jake/Uni/2nd year/COSC3000/ComputerGraphics/testing.pgn")



"""                     Flow chart
┌───────────────────────────────────────────────────────┐
│                                                       │
│   ┌──────────────┐             ┌─────────────────┐    │
├──►│Checks if move├── Castle ──►│Check side, move ├────┘
│   │ is a castle  │             │  right pieces   │
│   └──────┬───────┘             └─────────────────┘
│          │
│      No castle
│          │
│          ▼
│   ┌──────────────┐              ┌──────────────┐
│   │Checks if move├── Capture ──►│Checks if move├──────── Normal
│   │is a capture  │              │is en passant │         Capture
│   └──────┬───────┘              └──────┬───────┘           │
│          │                             │                   │
│      No capture                   en passant               │
│          │                             │                   │
│          ▼                             ▼                   ▼
│    ┌─────────────┐              ┌──────────────┐    ┌──────────────┐
│    │ Move piece  │              │Call .die and │    │Call .die on  │
│    └─────┬───────┘              │ move piece   │    │another pawn  │
│          │                      └──────┬───────┘    │and move piece│
│          │                             │            └──────┬───────┘
│          │                             │                   │
│          ├─────────────────────────────┴───────────────────┘
│          │
│          ▼
│    ┌──────────────┐                ┌─────────┐
│    │Checks if move├── Promotion ──►│Override │
│    │ is promotion │                │old piece│
│    └─────┬────────┘                └────┬────┘
│          │                              │
│          │                              │
│      No promotion                       │
│          │                              │
│          ▼                              │
│     ┌──────────────┐                    │
│     │Push move     │                    │
│     │internally    │                    │
└─────┤              │◄───────────────────┘
      │Add keyframes │
      │for all pieces│
      └──────────────┘
"""
