'''
Created on May 3, 2013

@author: will
'''
import Board
def check_move(piece,
               dest,
               pieces,
               get_pos=False,
               game_state=None):
    possible_positions = []
    support_positions = []
    pos = piece['position']
    row = Board.Rows.index(pos[1])
    col = Board.Columns.index(pos[0])
    t_pos = [(col+1,row+2),
             (col-1,row+2),
             (col+2,row+1),
             (col-2,row+1),
             (col+2,row-1),
             (col-2,row-1),
             (col+1,row-2),
             (col-1,row-2)]
    
    r = range(0,8)
    for pos in t_pos:
        if (pos[0] in r and
            pos[1] in r):
            next_pos = (Board.Columns[pos[0]],Board.Rows[pos[1]])
            
            if(not next_pos in pieces or
               not pieces[next_pos]['color'] == piece['color']):
                possible_positions += [next_pos]
            elif next_pos in pieces:
                support_positions += [next_pos]
            
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
