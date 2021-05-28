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
        self._inital_loc = loc
        self._loc = loc                        # int (1d array index)

        x, y = square_to_world_space(self._loc)
        self._blender_obj.location = Vector((x, y, 0.3))

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

    def move(self, new_loc: int, zTo: float = 0.3):
        xTo, yTo = square_to_world_space(new_loc)
        self._blender_obj.location = Vector((xTo, yTo, zTo))
        print("Moved to ", self._blender_obj.location)

        self._array[new_loc] = self
        self._array[self._loc] = None

        self._loc = new_loc

    def die(self) -> CustomPiece:
        self._array[self._loc] = None
        # TODO some animation here
        self.keyframe_insert(data_path="location", frame=FRAME_COUNT-6)

        xTo, yTo = square_to_world_space(self._loc)
        self._blender_obj.location = Vector((xTo, yTo, 2.1))
        self.keyframe_insert(data_path="location", frame=FRAME_COUNT+3)

        if self._colour:
            self._inital_loc += -16
        else:
            self._inital_loc += 16
        xTo, yTo = square_to_world_space(self._inital_loc)
        self._blender_obj.location = Vector((xTo, yTo, 2.1))
        self.keyframe_insert(data_path="location", frame=FRAME_COUNT+21)

        xTo, yTo = square_to_world_space(self._inital_loc)
        self._blender_obj.location = Vector((xTo, yTo, 0.1))
        self.keyframe_insert(data_path="location", frame=FRAME_COUNT+29)

        return self

    def hide_now(self):
        self._blender_obj.keyframe_insert(data_path="hide_render", frame=FRAME_COUNT)
        self._blender_obj.hide_render = True
        self._blender_obj.keyframe_insert(data_path="hide_render", frame=FRAME_COUNT+1)

    def show_now(self):
        self._blender_obj.hide_render = True
        self._blender_obj.keyframe_insert(data_path="hide_render", frame=FRAME_COUNT)
        self._blender_obj.hide_render = False
        self._blender_obj.keyframe_insert(data_path="hide_render", frame=FRAME_COUNT+1)

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

    if move.promotion is not None:
        array[locFrom].move(locTo) # NOTE, piece moves always
        array[locTo].keyframe_insert(data_path="location", index=-1)
        array[locTo].hide_now()
        # unlink somehow
        pieceType = move.promotion
        array[locTo] = CustomPiece(chess.Piece(pieceType, board.turn),\
                                   SOURCE_PIECES[chess.piece_symbol(pieceType)],\
                                   array, locTo)
        array[locTo].show_now()


    else:
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
            if (piece := board.piece_at(position)) is not None:
                array[position] = CustomPiece(piece, SOURCE_PIECES[piece.symbol().lower()]\
                                              , array, position)

        camera_parent = bpy.data.collections["Collection"].objects['Camera parent']

        global FRAME_COUNT
        FRAME_COUNT = 0
        keyframes(array) # intial pos
        FRAME_COUNT += 10
        for move in game.mainline_moves():
            scene.frame_set(FRAME_COUNT)

            make_move(board, move, array)


            keyframes(array) # update blender

            camera_parent.rotation_euler[2] += radians(2) #XYZ
            camera_parent.keyframe_insert(data_path="rotation_euler", index=-1)

            board.push(move) # update python-chess

            FRAME_COUNT += 10
            keyframes(array) # update blender
            FRAME_COUNT += 3

        confetti = bpy.data.collections["Board"].objects['Confetti source']
        print(board.outcome())
        if board.outcome() is not None:
            winner = board.outcome().winner
            king_square = board.king(winner)
            xTo, yTo = square_to_world_space(king_square)
            confetti.location = Vector((xTo, yTo, 3))
            bpy.data.particles["Confetti"].frame_start = FRAME_COUNT
            bpy.data.particles["Confetti"].frame_end = FRAME_COUNT + 12

        print(FRAME_COUNT)
        for _ in range(5):
            scene.frame_set(FRAME_COUNT)
            camera_parent.rotation_euler[2] += radians(2) #XYZ
            camera_parent.keyframe_insert(data_path="rotation_euler", index=-1)

            FRAME_COUNT += 13

        bpy.data.scenes[0].frame_start = 1
        bpy.data.scenes[0].frame_end = FRAME_COUNT - 13
        return game





if __name__ == "__main__":
    # main("/home/jake/Uni/2nd year/COSC3000/ComputerGraphics/pgn/carlsen_nakamura_2021.pgn")
    # main("/home/jake/Uni/2nd year/COSC3000/ComputerGraphics/pgn/testing.pgn")
    # main("/home/jake/Uni/2nd year/COSC3000/ComputerGraphics/pgn/Garry Kasparov_vs_Veselin Topalov_1999.pgn")
    # main("/home/jake/Uni/2nd year/COSC3000/ComputerGraphics/pgn/kramnik_kasparov_2001.pgn")
    main("/home/jake/Uni/2nd year/COSC3000/ComputerGraphics/pgn/grischuk_ponomariov_2000.pgn")


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
