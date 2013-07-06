'''
Created on May 3, 2013

@author: will
piece:   GameState.piece
dest:    (column,row)
pieces:  Dictionary of pieces
get_pos: return all possible positions (used for end game tracking)
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
    inc = 0
    base = 0
    
    if piece['color'] == 'white':
        inc = 1
        base = 1
    else:
        inc = -1
        base = 6
    
    #move forward one
    row = Board.Rows.index(pos[1])
    col = Board.Columns.index(pos[0])
    
    passant=[]
    attack={}
    attackable = []
    if row+inc in range(0,8):
        next_pos = (Board.Columns[col],
                    Board.Rows[row+inc])
        if not next_pos in pieces:
            #can move forward
            possible_positions += [next_pos]
            
            if row==base: 
                next_pos = (Board.Columns[col],
                            Board.Rows[row+(inc*2)])
                
                if not next_pos in pieces:
                    #can move forward two spaces
                    passant += [next_pos]
                    possible_positions += [next_pos]
        #check attack right
        if col+1 in range(0,8):
            next_pos = (Board.Columns[col+1],
                        Board.Rows[row+inc])
            pass_pos = (Board.Columns[col+1],
                        Board.Rows[row])
            if (next_pos in pieces and
                not pieces[next_pos]['color'] == piece['color']):
                #attack
                possible_positions += [next_pos]
                attackable += [next_pos]
            elif next_pos in pieces:
                support_positions += [next_pos]
            elif (pass_pos in pieces and
                  pieces[pass_pos]['can_passant']):
                #En passant
                attack[next_pos]=pass_pos
                possible_positions += [next_pos]
                
        #check attack left
        if row-1 in range(0,8):
            next_pos = (Board.Columns[col-1],
                        Board.Rows[row+inc])
            pass_pos = (Board.Columns[col-1],
                        Board.Rows[row])
            if (next_pos in pieces and
                not pieces[next_pos]['color'] == piece['color']):
                #attack
                possible_positions += [next_pos]
                attackable += [next_pos]
            elif next_pos in pieces:
                support_positions += [next_pos]
            elif (pass_pos in pieces and
                  pieces[pass_pos]['can_passant']):
                #En passant (French)
                attack[next_pos]=pass_pos
                possible_positions += [next_pos]  
    if get_pos:
        return {'possible_positions':possible_positions,
                'attackable_positions':attackable,
                'support_positions':support_positions}
    if dest in possible_positions:
        at = False
        if dest in attack:
            at = attack[dest]
        return {'can_move':True,
                'is_castle':False,
                'is_passant':dest in passant,
                'attack':at}
    else:
        return {'can_move':False}
