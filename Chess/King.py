'''
Created on May 3, 2013

@author: will
'''
import Board
import pprint
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
    t_pos = [(col+1,row),   #up
             (col+1,row-1), #up-left
             (col,row-1),   #left
             (col-1,row-1), #down-left
             (col-1,row),   #down
             (col-1,row+1), #down-right
             (col,row+1),   #right
             (col+1,row+1)] #right-up
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
    #dont check for castle if I'm just getting positions
    if get_pos:
        return {'possible_positions':possible_positions,
                'attackable_positions':possible_positions,
                'support_positions':support_positions}
    '''
    check castle
    1. king hasn't moved yet
    2. rook hasn't moved yet
    3. space between is clear
    4. no one can attack any spaces involved
    '''
    base = 0
    castle = {}
    
    if piece['color'] == 'white':
        base = '1'
    else:
        base = '8'
    if piece['can_castle']:
        rook = ('h',base)
        
        clearR = False #castle right is clear
        if (rook in pieces and
            pieces[rook]['can_castle']):
            #check spaces
            check = [('f',base),
                     ('g',base)]
            clearR = True
            for spot in check:
                if spot in pieces:
                    clearR = False
            
        rook = ('a',base)
        clearL = False #castle left is clear
        if (rook in pieces and
            pieces[rook]['can_castle']):
            #check spaces
            check = [('b',base),
                     ('c',base),
                     ('d',base)]
            t = 0
            clearL = True
            for spot in check:
                if spot in pieces:
                    clearL = False
        
        if clearL or clearR:
            calc_attackable = []
            for p in pieces.values():
                if not p['color'] == piece['color']:
                    calc_attackable += game_state.chk_dest(p['position'],None,pieces,True)
            if clearL:
                check = [('c',base),
                         ('d',base),
                         ('e',base)]
                add = True
                for p in check:
                    if p in calc_attackable:
                        add = False
                if add:
                    
                    castle[('c',base)]=[('a',base),('d',base)]
                    possible_positions += [('c',base)]
            if clearR:
                check = [('e',base),
                         ('f',base),
                         ('g',base)]
                add = True
                for p in check:
                    if p in calc_attackable:
                        add = False
                if add:
                    castle[('g',base)]=[('h',base),('f',base)]
                    possible_positions += [('g',base)]
    
    if dest in  possible_positions:
        rook = False
        if dest in castle:
            rook = castle[dest]
        return {'can_move':True,
                'is_castle':rook,
                'is_passant':False}
    else:
        return {'can_move':False}     
