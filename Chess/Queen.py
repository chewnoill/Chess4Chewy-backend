'''
Created on May 3, 2013

@author: will
'''
import Board
import Bishop,Rook
def check_move(piece,
               dest,
               pieces,
               get_pos=False,
               game_state=None):
    possible_positions = []
    support_positions = []
    bishop = Bishop.check_move(piece,dest,pieces,True)
    rook = Rook.check_move(piece, dest,pieces,True)
    possible_positions = bishop['possible_positions']+rook['possible_positions']
    support_positions = bishop['support_positions']+rook['support_positions']
    if get_pos:
        return {'possible_positions':possible_positions,
                'attackable_positions':possible_positions,
                'support_positions':support_positions}
    if dest in  possible_positions:
        return {'can_move':True,
                'is_castle':False,
                'is_passant':False}
    else:
        return {'can_move':False}

