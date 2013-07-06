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
    t = (col,row)
    limit = lambda z: (z[0] in range(8) and z[1] in range(8)) 
    #up right
    diag = lambda x,t: (t[0]+x,t[1]+x)
    u = [diag(x,t) for x in range(1,8)]
    
    for p in u:
        if not limit(p):
            break
        next_pos = (Board.Columns[p[0]],
                    Board.Rows[p[1]])
        
        if (next_pos in pieces and
            pieces[next_pos]['color'] == piece['color']):
            support_positions += [next_pos]
            break
        elif next_pos in pieces:
            possible_positions += [next_pos]
            break
        else:
            possible_positions += [next_pos]
    #up left
    diag = lambda x,t: (t[0]-x,t[1]+x)
    u = [diag(x,t) for x in range(1,8)]
    
    for p in u:
        if not limit(p):
            break
        next_pos = (Board.Columns[p[0]],
                    Board.Rows[p[1]])
        if (next_pos in pieces and
            pieces[next_pos]['color'] == piece['color']):
            support_positions += [next_pos]
            break
        elif next_pos in pieces:
            possible_positions += [next_pos]
            break
        else:
            possible_positions += [next_pos]
    #down left
    diag = lambda x,t: (t[0]-x,t[1]-x)
    u = [diag(x,t) for x in range(1,8)]
    
    for p in u:
        if not limit(p):
            break
        next_pos = (Board.Columns[p[0]],
                    Board.Rows[p[1]])
        
        if (next_pos in pieces and
            pieces[next_pos]['color'] == piece['color']):
            support_positions += [next_pos]
            break
        elif next_pos in pieces:
            possible_positions += [next_pos]
            break
        else:
            possible_positions += [next_pos]
    #down right
    
    diag = lambda x,t: (t[0]+x,t[1]-x)
    u = [diag(x,t) for x in range(1,8)]
    
    for p in u:
        if not limit(p):
            break
        
        next_pos = (Board.Columns[p[0]],
                    Board.Rows[p[1]])
        if (next_pos in pieces and
            pieces[next_pos]['color'] == piece['color']):
            support_positions += [next_pos]
            break
        elif next_pos in pieces:
            possible_positions += [next_pos]
            break
        else:
            possible_positions += [next_pos]
    
    if get_pos:
        return {'possible_positions':possible_positions,
                'attackable_positions':possible_positions,
                'support_positions':support_positions}
    
    if dest in possible_positions:
        return {'can_move':True,
                'is_castle':False,
                'is_passant':False}
    else:
        return {'can_move':False}
