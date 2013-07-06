'''
Created on Apr 29, 2013

@author: will

TODO:
draw determination
load game from file
serialize game to datastore
'''
import json
import Board
import Pawn,Rook,Knight,Bishop,King,Queen
import pprint
import re
import string
import time
import unittest

class GameState:
    def piece(self,color,piece,position):
        ret =  {'color':color,
                'piece':piece,
                'position':position,
                'can_castle':False,
                'can_passant':False}
        if piece == 'king' or piece == 'rook':
            ret['can_castle']=True
        return ret
    
    class Turn:
        def __init__(self,turn_num):
            self.white = False
            self.black = False
            self.turn_num = turn_num
            
        def WhoseTurn(self):
            if not self.white:
                return 'white'
            elif not self.black:
                return 'black'
            else:
                return 'done'
        def __str__(self):
            num = str(self.turn_num)+': '
            while len(num)<5:
                num+=' '
            return num + str(self.white)+'|==|\t'+str(self.black)
        def dump(self):
            ret = {'turn_num':self.turn_num}
            if self.white:
                ret['white']=self.white.toDict()
            if self.black:
                ret['black']=self.black.toDict()
            return ret
    class MoveNote:
        def __init__(self,info):
            if not ('piece' in info and
                'color' in info and
                'src' in info and
                'dest' in info):
                raise Exception('incomplete info')
            
            if not 'takes' in info:
                info['takes'] = False
            if not 'castle' in info:
                info['castle'] = False
            if not 'check' in info:
                info['check'] = False
            if not 'mate' in info:
                info['mate'] = False
            if not 'time' in info:
                info['time'] = int(time.time()*1000)
            self.info = info
        def __str__(self):
            ret = (self.info['color'] +' '+
                   self.info['piece']+': ')
            while len(ret)<15:
                ret+=' '
            ret += (str(self.info['src'][0])+str(self.info['src'][1])+'->'+
                    str(self.info['dest'][0])+str(self.info['dest'][1]))
            if self.info['takes']:
                ret += 'x'+str(self.info['takes'][0])+str(self.info['takes'][1])
            elif self.info['castle']:
                ret += ' castle'
            
            if self.check:
                ret +=' check'
            if self.mate:
                ret +=' mate'
            while len(ret)<30:
                ret += ' '
            return ret
        def toDict(self):
            return self.__dict__
            
    def __init__(self,pieces={},
                 moves=[],
                 status={'game':'in progress'},
                 debug=False):
        self.reserved = {'resign':self.resign,
                         'draw':self.draw}
        
        if len(pieces)>0:
            self.pieces = {}
            for piece_pos in pieces:
                pieces[piece_pos]['position']=(piece_pos[0],piece_pos[1])
                self.pieces[piece_pos[0],piece_pos[1]]=pieces[piece_pos]
                
        else:
            self.pieces = pieces
        self.status = status
        self.dead = {}
        self.moves = []
        for move in moves:
            turn = GameState.Turn(move['turn_num'])
            if 'white' in move:
                turn.white = GameState.MoveNote(move['white']['info'])
                if 'black' in move:
                    turn.black = GameState.MoveNote(move['black']['info'])
            self.moves += [turn]
       
        if len(self.pieces)==0:
            #initial board state
            self.initializeState()
        self.debug = debug
    def dumpPieces(self):
        ret = {}
        for piece_pos in self.pieces:
            ret[piece_pos[0]+piece_pos[1]]=self.pieces[piece_pos]
        return ret
    def dumpMoves(self):
        ret = []
        for turn in self.moves:
            ret += [turn.dump()]
        return ret
    def dumpStatus(self):
        return self.status
    def initializeState(self):
        self.pieces={}
        #start game
        self.moves = []
        self.moves += [GameState.Turn(0)]
        #pawns
        for col in Board.Columns:
            self.addPiece('white', 'pawn', col, '2')
            self.addPiece('black', 'pawn', col, '7')
        #rooks
        self.addPiece('white','rook','a','1')
        self.addPiece('white','rook','h','1')
        self.addPiece('black','rook','a','8')
        self.addPiece('black','rook','h','8')
        
        #knights
        self.addPiece('white','knight','b','1')
        self.addPiece('white','knight','g','1')
        self.addPiece('black','knight','b','8')
        self.addPiece('black','knight','g','8')
        
        #bishops
        self.addPiece('white','bishop','c','1')
        self.addPiece('white','bishop','f','1')
        self.addPiece('black','bishop','c','8')
        self.addPiece('black','bishop','f','8')
        
        #king + queen
        self.addPiece('white','queen','d','1')
        self.addPiece('white','king','e','1')
        self.addPiece('black','queen','d','8')
        self.addPiece('black','king','e','8')
        
    def addPiece(self,color,piece,col,row):
        self.pieces[col,row]=self.piece(color,
                                        piece,
                                        (col,row))

    def GetTurn(self):
        last_turn_num = len(self.moves)-1
        last_turn = self.moves[last_turn_num]
        if last_turn.WhoseTurn() == 'done':
            #turn over, create new turn
            self.moves += [GameState.Turn(last_turn_num+1)]
            return last_turn_num+1
        return last_turn_num
    def NextPlayer(self):
        return self.moves[self.GetTurn()].WhoseTurn()
    def LoadMoves(self,moves):

        for move in moves:
            
            outcome = self.AlgebraicMove(move)
            
            if not outcome['AlgebraicMove']:
                raise Exception(outcome['error'])

    def resign(self):
        self.status['game']='done'
        self.status['result']='resign'
        player = self.WhoseTurn()
        opp = {'white':'black',
               'black':'white'}
        self.status['winner']=opp[player]
        self.status['loser']=player
    def draw(self):
        self.status['game']='done'
        self.status['result']='draw'
        
        self.status['winner']=''
        self.status['loser']=''
    def AlgebraicMove(self,move,debug=False):
        turn_num = self.GetTurn()
        color = self.moves[turn_num].WhoseTurn()
        p = {'K':'king',
             'Q':'queen',
             'R':'rook',
             'B':'bishop',
             'N':'knight'}
        possible_pieces = []
        dest = None
        src = None
        piece_type = None
        promote = None
        src_row = None
        src_col = None
        
        
        if move in self.reserved:
            self.reserved[move]()
            return {'AlgebraicMove':True}
        #simple move
        reg_ex = ('(?P<piece_type>[KQRBN]?)'+
                  '(?P<disambig_col>[abcdefgh]?)'+
                  '(?P<disambig_row>[12345678]?)'+
                  '(?P<takes>x?)'+ #i don't care about this
                  '(?P<dest>[abcdefgh][12345678])'+
                  '(=(?P<promote>[KQRBN]))?')
        castle = ('(?P<castle_left>O-O-O)|'+
                  '(?P<castle_right>O-O)')
        result = re.search(castle,move)
        
        if result:
            home={'white':'1',
                  'black':'8'}
            row = home[color]
            src = 'e'+row
            if result.group('castle_left'):
                dest = 'c'+row
            elif result.group('castle_right'):
                dest = 'g'+row
                
            ret = self.MaybeMove(src,dest,None)
            if ret['MaybeMove']:
                return {'AlgebraicMove':True}
            else:
                return {'AlgebraicMove':False,
                        'error':ret['message']}
        result = re.search(reg_ex,move)
        
        if result.group('piece_type') in p:
            piece_type = p[result.group('piece_type')]
        else:
            piece_type = 'pawn'
        
        if result.group('disambig_col'):
            src_col = result.group('disambig_col')
        if result.group('disambig_row'):
            src_row = result.group('disambig_row')
        
        dest = result.group('dest')
        if (result.group('promote') and 
            len(result.group('promote'))>0):
            promote = p[result.group('promote')]
        
        if src_col and src_row:
            if debug:
                print((src_col,src_row),dest,promote)
            ret = self.MaybeMove((src_col,src_row),
                                  dest,
                                  promote)
            if ret['MaybeMove']:
                return {'AlgebraicMove':True}
            else:
                return {'AlgebraicMove':False,
                        'error':ret['error']}
        for piece_pos in self.pieces:
            if (self.pieces[piece_pos]['color']==color and
                self.pieces[piece_pos]['piece']==piece_type and
                (not src_col or
                 src_col == piece_pos[0]) and
                (not src_row or
                 src_row == piece_pos[1])):
                possible_pieces+=[piece_pos]
        
        if len(possible_pieces)==1:
            src = possible_pieces[0]
        elif len(possible_pieces)>1:
            for piece_pos in possible_pieces:
                
                pos = self.chk_dest(piece_pos,None,self.pieces,True)
                d =(dest[0],dest[1])
                if d in pos['possible_positions']:
                    src = piece_pos
                    break
        if debug:
            print(src,dest,promote)
        ret = self.MaybeMove(src,dest,promote,debug)
        if ret['MaybeMove']:
            return {'AlgebraicMove':True}
        else:
            return {'AlgebraicMove':False,
                    'error':ret['message']}
            
    def WhoseTurn(self):
        turn_num = self.GetTurn()
        return self.moves[turn_num].WhoseTurn()

    def MaybeMove(self,
                  pos_from,
                  pos_to,
                  promote=None,
                  debug=False): 
        if (not pos_from or
            not pos_to):
            return {'MaybeMove':False,
                    'error':'invalid move'}
        turn_num = self.GetTurn()
        try:
            a = pos_from[0]
            b = pos_from[1]
            x = pos_to[0]
            y = pos_to[1]
            #make sure move is on board
            if (a in Board.Columns and 
                b in Board.Rows and
                x in Board.Columns and
                y in Board.Rows):
                #make sure there is a piece at from position
                if (a,b) in self.pieces:
                    piece = self.pieces[a,b]
                    color = piece['color']
                    if not color == self.moves[turn_num].WhoseTurn():
                        return {'MaybeMove':False,
                                'message':'it is not your turn',
                                'error':'it is not your turn',
                                'from':pos_from,
                                'to':pos_to}
                    #make sure player owns that piece
                    if self.pieces[a,b]['color'] == color:
                        #see if piece can reach destination
                        move = self.chk_dest(src=self.pieces[a,b]['position'],
                                             dest=(x,y),
                                             pieces=self.pieces)
                        if move['can_move']:
                            opposite = {'white':'black',
                                        'black':'white'}
                            mate = ('mated' in move['end_game'][opposite[color]] and
                                    move['end_game'][opposite[color]]['mated'])
                            if move['end_game'][color]['checked']==True:
                                return {'MaybeMove':False,
                                        'message':'cannot end turn in check',
                                        'error':'cannot end turn in check',
                                        'from':(a,b),
                                        'to':(x,y)}
                            if promote in ['rook','knight','bishop','queen',None]:
                                self.Move(src=(a,b),
                                          dest=(x,y),
                                          info=move,
                                          turn_num=turn_num,
                                          promote=promote)
                                
                                
                                return{'MaybeMove':True,
                                       'message':'piece moved',
                                       'piece':self.pieces[x,y]['piece'],
                                       'from':(a,b),
                                       'mate':mate,
                                       'to':(x,y)}
                            else:
                                return {'MaybeMove':False,
                                        'error':'illegal move',
                                        'message':'cannot promote to '+promote,
                                        'from':(a,b),
                                        'to':(x,y)}
                        else:
                            return {'MaybeMove':False,
                                    'error':'illegal move',
                                    'message':'piece cannot move here',
                                    'from':(a,b),
                                    'to':(x,y)}
                    else:
                        return {'MaybeMove':False,
                                'error':'illegal move',
                                'message':'wrong team',
                                'from':(a,b),
                                'to':(x,y)}
                else:
                    return {'MaybeMove':False,
                            'error':'illegal move',
                            'message':'no piece found at position',
                            'from':(a,b),
                            'to':(x,y)}
            else:
                return {'MaybeMove':False,
                        'error':'illegal move',
                        'message':'position not on board',
                        'from':(a,b),
                        'to':(x,y)}
            
        
        except IndexError:
            raise Exception('IndexError')
            #return {'error':'IndexError'}

    def Move(self,src,dest,info,turn_num,promote):
        turn = self.moves[turn_num]
        player = self.pieces[src]['color']
        
        opposite = {'white':'black',
                    'black':'white'}
        opp = opposite[player]
        check = info['end_game'][opp]['checked']
        mate = info['end_game'][opp]['mated']
        
        if check and mate:
            self.status['game']='done'
            self.status['result']='check mate'
            self.status['winner']=player
            self.status['loser']=opp
        elif info['end_game']['draw']:
            self.status['game']='done'
            self.status['result']='draw'
        moved = GameState.MoveNote({'color':player,
                                    'piece':self.pieces[src]['piece'],
                                    'src':src,
                                    'dest':dest,
                                    'check':check,
                                    'mate':mate})
        p = self.pieces[src]
        p['can_castle'] = False
        p['can_passant'] = info['is_passant']
        p['position'] = dest
        
        if (dest in self.pieces):
            moved.info["takes"] = True

        #save move to move list
        if ('attack' in info and
            info['attack']):
            at = info['attack']
            moved.info["takes"] = True
            del self.pieces[at]
        if ('is_castle' in info and
            info['is_castle']):
            castle = info['is_castle']
            moved.castle = castle
            q = self.pieces[castle[0]]
            q['position'] = castle[1]
            self.pieces[castle[1]]=q
            del self.pieces[castle[0]]
        del self.pieces[src]
        
            
        if player == 'white':
            self.moves[turn_num].white = moved
            self.remove_passant('black')
        elif player == 'black':
            self.moves[turn_num].black = moved
            self.remove_passant('white')
        if info['promotable'] and not promote == None:
            p['piece']=promote
        self.pieces[dest]=p
    def remove_passant(self,color):
        for piece in self.pieces.values():
            if piece['color'] == color:
                piece['can_passant'] = False
                
    def chk_dest(self,src,dest,pieces,get_pos=False):
        moves = {'pawn':    Pawn.check_move,
                 'rook':    Rook.check_move,
                 'knight':  Knight.check_move,
                 'bishop':  Bishop.check_move,
                 'king':    King.check_move,
                 'queen':   Queen.check_move}
        
        piece = pieces[src]
        
        pos = moves[piece['piece']](piece=piece,
                                    dest=dest,
                                    pieces=pieces,
                                    get_pos=get_pos,
                                    game_state=self)
        last_row = {'white':'8',
                    'black':'1'}
        if (piece['piece']=='pawn' and 
            dest and
            dest[1]==last_row[piece['color']]):
            pos['promotable']=True
        else:
            pos['promotable']=False
        if not get_pos:
            if not pos['can_move']:
                #not valid move,done
                return pos
            else:
                #check end game
                #create copy of new game positions
                new_pieces = pieces.copy()
                new_piece = piece.copy()
                del new_pieces[src]
                new_piece['position'] = dest
                new_pieces[dest]=new_piece
                
                end_game = self.check_endgame(new_pieces)
                
                pos['end_game']=end_game
                return pos
                
        return pos
    def check_endgame(self,pieces):
        #moves by color and piece
        #used for block checks
        possible_moves = {'white':{},
                          'black':{}}
        #moves by color
        #used for escape checks
        all_moves = {'white':{'possible_positions':[],
                              'support_positions':[]},
                     'black':{'possible_positions':[],
                              'support_positions':[]}}
        kings = {'white':{},
                 'black':{}}
        #build list of attackable and supportable pieces
        for pos in pieces:
            piece = pieces[pos]
            if  piece['piece'] == 'king':
                kings[piece['color']][piece['position']] = self.chk_dest(src=piece['position'],
                                                                   dest=None,
                                                                   pieces=pieces,
                                                                   get_pos=True)
            else:
                possible_moves[piece['color']][piece['position']] = self.chk_dest(src=piece['position'],
                                                                                  dest=None,
                                                                                  pieces=pieces,
                                                                                  get_pos=True)
                
                all_moves[piece['color']]['possible_positions'] += possible_moves[piece['color']][piece['position']]['attackable_positions']
                all_moves[piece['color']]['support_positions'] += possible_moves[piece['color']][piece['position']]['support_positions']
        
        opposite = {'white':'black',
                    'black':'white'}
        checker = {'white':[],
                   'black':[]}
        
        #draws: (only the ones I can check here)
        #insufficient material
        #not in check, no legal moves
        insufficient_material = {'white':{},
                                 'black':{}}
        draw = False
        draw_reason = None
        for color in possible_moves:
            if len(possible_moves[color])==0:
                #king 
                insufficient_material[color]['can_mate']=False
            #count pieces
            piece_count = {}
            for piece_pos in possible_moves[color]:
                if pieces[piece_pos]['piece'] in piece_count:
                    piece_count[pieces[piece_pos]['piece']]+=1
                else:
                    piece_count[pieces[piece_pos]['piece']]=1
            insufficient_material[color]['piece_count']=piece_count
            if len(piece_count)==1:
                piece = list(piece_count.keys())[0]
                if piece in ['pawn','queen']:
                    #still has a pawn or queen
                    insufficient_material[color]['can_mate']=True
                
                
                
        for color in kings:
            for king_pos in kings[color]:
                opp = opposite[color]
                for piece_pos in possible_moves[opp]:
                    if king_pos in possible_moves[opp][piece_pos]['possible_positions']:
                        #save piece pos to see if it can be blocked
                        checker[opp] += [piece_pos]
        
        ret = {'white':{},
               'black':{}}
        for color in checker:
            #can be blocked?
            opp = opposite[color]
            my_king_pos = list(kings[color].keys())[0]
            opp_king_pos = list(kings[opp].keys())[0]
            if len(checker[color])==0:
                #no check, done
                ret[opp]['checked']=False
                continue
            elif len(checker[color])==1:
                ret[opp]['checked']=True
                can_be_killed = False
                can_be_blocked = False
                #kill checker
                
                if ((checker[color][0] in all_moves[color]['support_positions'] or
                     checker[color][0] in kings[color][my_king_pos]['support_positions']) and 
                    checker[color][0] in all_moves[opp]):
                    #has support, can't be killed by king
                    can_be_killed = True
                elif (not checker[color][0] in all_moves[color] and
                      (checker[color][0] in all_moves[opp] or
                       checker[color][0] in kings[opp][opp_king_pos])):
                    #no support can be killed by anything
                    
                    can_be_killed = True
                elif pieces[checker[color][0]]['piece']=='knight':
                    #cannot block a knight
                    can_be_blocked = False
                else:
                    #check for blocking move
                    vector = self.attack_vector(checker[color][0],opp_king_pos)
                    
                    for move in vector:
                        if (move in all_moves[color]['possible_positions']):
                            can_be_blocked = True
                ret[opp]['can_block']=can_be_blocked
                ret[opp]['can_kill']=can_be_killed
            else:
                #more then one checker, cannot block
                ret[opp]['checked']=True
                ret[opp]['can_block']=False
                ret[opp]['can_kill']=False
            #can escape
            can_escape = False
            for king_move in kings[opp][opp_king_pos]['possible_positions']:
                if (not king_move in all_moves[color]['possible_positions'] and
                    not king_move in all_moves[color]['support_positions'] and
                    not king_move in kings[color][my_king_pos]['support_positions']):
                    can_escape = True
                    
                    break
            ret[opp]['can_escape'] = can_escape
        for color in ret:
            if (ret[color]['checked'] and
                not ret[color]['can_block'] and
                not ret[color]['can_escape'] and
                not ret[color]['can_kill']):
                ret[color]['mated']=True
                
            else:
                ret[color]['mated']=False
        if draw:
            ret['draw']=True
        else:
            ret['draw']=False
        
        
        return ret
    
    def attack_vector(self,src,dst):
        
        a = (Board.Columns.index(src[0]),Board.Rows.index(src[1]))
        b = (Board.Columns.index(dst[0]),Board.Rows.index(dst[1]))
        
        
        x = b[0]-a[0]
        y = b[1]-a[1]
        
        l = max(abs(x),abs(y))
        if not x == 0:
            x = x/abs(x)
        if not y == 0:
            y = y/abs(y)
        
        t = lambda p: (a[0]+(p*x),a[1]+(p*y))
        v = []
        if l < 0:
            v = [t(q) for q in range(l,0)]
        else:
            v = [t(q) for q in range(0,l)]
        
        vector = []
        for p in v:
            d = (Board.Columns[int(p[0])],
                 Board.Rows[int(p[1])])
            
            if not (d in [dst]):
                vector += [d]
            
        return vector
    
    def turn_str(self):
        ret = ''
        for t in self.moves:
            ret += str(t) +'\n'
        return ret
    def __str__(self):
        ret = ''
        ret += '\t|----|----|----|----|----|----|----|----|\n'
        for row in reversed(Board.Rows):
            #
            ret += row+'\t|'
            for col in Board.Columns:
                
                if (col,row) in self.pieces:
                    p = self.pieces[(col,row)]
                    
                    ret += p['color'][0]+':'+p['piece'][:2]+'|'
                else:
                    ret += '    |'
            ret += '\n'
        ret += '\t|----|----|----|----|----|----|----|----|\n'
        ret += '\t  A    B    C    D    E    F    G    H   \n'
        return ret

def debug_move(gs,pos):
    p = gs.chk_dest(pos, None,gs.pieces, True)
    print(p)
    
class Test(unittest.TestCase):
    def setUp(self):
        self.gs = GameState(pieces={},
                            moves=[],
                            status={'game':'in progress'},
                            debug=False)
        
        self.line = '-------------------------------------------------------------'
        pass
    def tearDown(self):
        del self.gs
        pass
    def testKasparovsImmortal(self):
        #"Kasparov's Immortal"
        #Garry Kasparov vs Veselin Topalov
        #         white     black
        moves = ['e4',      'd6',
                 'd4',      'Nf6',
                 'Nc3',     'g6', 
                 'Be3',     'Bg7', 
                 'Qd2',     'c6', 
                 'f3',      'b5', 
                 'Nge2',    'Nbd7', 
                 'Bh6',     'Bxh6', 
                 'Qxh6',    'Bb7', 
                 'a3',      'e5', 
                 'O-O-O',   'Qe7', 
                 'Kb1',     'a6', 
                 'Nc1',     'O-O-O', 
                 'Nb3',     'exd4', 
                 'Rxd4',    'c5', 
                 'Rd1',     'Nb6', 
                 'g3',      'Kb8', 
                 'Na5',     'Ba8', 
                 'Bh3',     'd5', 
                 'Qf4',     'Ka7', 
                 'Rhe1',    'd4', 
                 'Nd5',     'Nbxd5', 
                 'exd5',    'Qd6', 
                 'Rxd4',    'cxd4', 
                 'Re7',     'Kb6', 
                 'Qxd4',    'Kxa5', 
                 'b4',      'Ka4', 
                 'Qc3',     'Qxd5', 
                 'Ra7',     'Bb7', 
                 'Rxb7',    'Qc4', 
                 'Qxf6',    'Kxa3', 
                 'Qxa6',    'Kxb4', 
                 'c3',      'Kxc3', 
                 'Qa1',     'Kd2', 
                 'Qb2',     'Kd1',    
                 'Bf1',     'Rd2', 
                 'Rd7',     'Rxd7', 
                 'Bxc4',    'bxc4', 
                 'Qxh8',    'Rd3', 
                 'Qa8',     'c3', 
                 'Qa4',     'Ke1', 
                 'f4',      'f5', 
                 'Kc1',     'Rd2', 
                 'Qa7']
        
        self.gs.LoadMoves(moves)
        print("Kasparov's Immortal")
        print("Garry Kasparov vs Veselin Topalov")
        print(str(self.gs))
        print(self.gs.status)
        self.assertEqual('in progress', self.gs.status['game'])
        print(self.line)
        pass
    def testTheGameoftheCentury(self):
        #"The Game of the Century" 
        #Donald Byrne vs Robert James Fischer
        moves = ['Nf3','Nf6',
                 'c4','g6',
                 'Nc3','Bg7',
                 'd4','O-O',
                 'Bf4','d5',
                 'Qb3','dxc4',
                 'Qxc4','c6',
                 'e4','Nbd7',
                 'Rd1','Nb6',
                 'Qc5','Bg4',
                 'Bg5','Na4',
                 'Qa3','Nxc3',
                 'bxc3','Nxe4',
                 'Bxe7','Qb6',
                 'Bc4','Nxc3',
                 'Bc5','Rfe8',
                 'Kf1','Be6',
                 'Bxb6','Bxc4',
                 'Kg1','Ne2',
                 'Kf1','Nxd4',
                 'Kg1','Ne2',
                 'Kf1','Nc3',
                 'Kg1','axb6',
                 'Qb4','Ra4',
                 'Qxb6','Nxd1',
                 'h3','Rxa2',
                 'Kh2','Nxf2',
                 'Re1','Rxe1',
                 'Qd8','Bf8',
                 'Nxe1','Bd5',
                 'Nf3','Ne4',
                 'Qb8','b5',
                 'h4','h5',
                 'Ne5','Kg7',
                 'Kg1','Bc5',
                 'Kf1','Ng3',
                 'Ke1','Bb4',
                 'Kd1','Bb3',
                 'Kc1','Ne2',
                 'Kb1','Nc3',
                 'Kc1','Rc2']
        
        self.gs.LoadMoves(moves)
        print("The Game of the Century")
        print("Donald Byrne vs Robert James Fischer")
        print(str(self.gs))
        print(self.gs.status)
        self.assertEqual('check mate', self.gs.status['result'])
        print(self.line)
        pass
    def testSherwinsForced(self):
        #Sherwin's Forced
        #Robert James Fischer vs James T Sherwin
        moves = ['e4','c5',
                 'Nf3','d6',
                 'd4','cxd4',
                 'Nxd4','Nf6',
                 'Nc3','a6',
                 'Bc4','e6',
                 'O-O','b5',
                 'Bb3','b4',
                 'Nb1','Bd7',
                 'Be3','Nc6',
                 'f3','Be7',
                 'c3','bxc3',
                 'Nxc6','Bxc6',
                 'Nxc3','O-O',
                 'Rc1','Qb8',
                 'Nd5','exd5',
                 'Rxc6','dxe4',
                 'fxe4','Qb5',
                 'Rb6','Qe5',
                 'Bd4','Qg5',
                 'Qf3','Nd7',
                 'Rb7','Ne5',
                 'Qe2','Bf6',
                 'Kh1','a5',
                 'Bd5','Rac8',
                 'Bc3','a4',
                 'Ra7','Ng4',
                 'Rxa4','Bxc3',
                 'bxc3','Rxc3',
                 'Rxf7','Rc1',
                 'Qf1','h5',
                 'Qxc1','Qh4',
                 'Rxf8','Kh7',
                 'h3','Qg3',
                 'hxg4','h4',     
                 'Be6']
        self.gs.LoadMoves(moves)
        print("Sherwin's Forced")
        print("Robert James Fischer vs James T Sherwin")
        
        print(str(self.gs))
        print(self.gs.status)
        print(self.line)
    def testFourQueens(self):
        moves = ['e4','c6',
                 'Nc3','d5',      
                 'Nf3','Bg4',
                 'h3','Bxf3',
                 'Qxf3','Nf6',
                 'd3','e6',
                 'g3','Bb4',
                 'Bd2','d4',
                 'Nb1','Bxd2',
                 'Nxd2','e5',
                 'Bg2','c5',
                 'O-O','Nc6',
                 'Qe2','Qe7',
                 'f4','O-O-O',    
                 'a3','Ne8',
                 'b4','cxb4',
                 'Nc4','f6',
                 'fxe5','fxe5',
                 'axb4','Nc7',
                 'Na5','Nb5',
                 'Nxc6','bxc6',
                 'Rf2','g6',
                 'h4','Kb7',
                 'h5','Qxb4',
                 'Rf7','Kb6',
                 'Qf2','a5',
                 'c4','Nc3',
                 'Rf1','a4',
                 'Qf6','Qc5',
                 'Rxh7','Rdf8',
                 'Qxg6','Rxh7',
                 'Qxh7','Rxf1',
                 'Bxf1','a3',
                 'h6','a2',
                 'Qg8','a1=Q',
                 'h7','Qd6',      
                 'h8=Q','Qa7',
                 'g4','Kc5',
                 'Qf8','Qae7',
                 'Qa8','Kb4',
                 'Qh2','Kb3',
                 'Qa1','Qa3',
                 'Qxa3','Kxa3',
                 'Qh6','Qf7',
                 'Kg2','Kb3',
                 'Qd2','Qh7',
                 'Kg3','Qxe4',
                 'Qf2','Qh1',
                 'resign']
        self.gs.LoadMoves(moves)
        print("Four Queens")
        print("Robert James Fischer vs Tigran Vartanovich Petrosian")
        
        print(str(self.gs))
        print(self.gs.status)
        print(self.line)
    def testMyT1(self):
        
        moves = ['e2e4','e7e5','f2f3','d7d6','d1e2','b8c6','g2g4','g8h6','b1c3','c8e6','c3d1','d8h4','draw']
        self.gs.debug = True
        self.gs.LoadMoves(moves)
        print("testMyT1")
        
        print(str(self.gs))
        print(self.gs.status)
        print(self.line)
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    '''
    moves = ['e2e4','e7e5','f2f3','d7d6','d1e2','b8c6','g2g4','g8h6','b1c3','c8e6','c3d1','d8h4']
    gs = GameState()
    gs.debug = True
    gs.LoadMoves(moves)
    print("testMyT1")
    
    print(str(gs))
    print(gs.status)
    '''