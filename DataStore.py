'''
Created on Apr 27, 2013

@author: will
'''
from google.appengine.ext import db
from google.appengine.ext.db import BadKeyError 
import hashlib
import json
import random
import time
import datetime
import Chess.GameLogic as Chess

class ChessGame(db.Model):
    #game_id = db.StringProperty(required=True)  #automatically created
    white_player = db.StringProperty()
    black_player = db.StringProperty()
    players = db.StringListProperty()   #before the game starts, players will be here
    color_chosen = db.StringProperty()  #white,black, or random
                                        #the first player in ChessGame.players is this color
    viewers = db.StringListProperty()   #list of users to be notified on updates
    moveList = db.TextProperty()        #could be long, should be JSON formated list
    gamePieces = db.TextProperty()
    votes = db.IntegerProperty()        #total value of votes received
    voters = db.StringListProperty()    #list of users who have voted and their vote direction
    status = db.StringProperty()
    winner = db.StringProperty()
    isPublic = db.BooleanProperty(required = True)
    state = db.IntegerProperty(required = True)     #0: game not started
                                                    #1: game in progress
                                                    #2: game completed
    draw_offered = db.StringProperty()
    whose_turn = db.StringProperty()
    date_created = db.DateTimeProperty(auto_now = True)
    
#----------------------------------------------------------------------------------
#**********************************************************************************
#----------------------------------------------------------------------------------
#player stuff
class Player(db.Model):
    username = db.StringProperty(required=True)
    #google_id = db.StringProperty()
    gcm_id = db.StringProperty()        #GCM id to send updates to
    password = db.StringProperty()      #hashed password value
    rank = db.IntegerProperty()
    record = db.StringListProperty()    #JSON formated as: {wins:1,loses:0,draws:0}
    games = db.StringListProperty()     #list of user's games
    
def UsernameExists(username):
    found = db.GqlQuery("select * from Player where username='%s'" % username)
    player = found.get()
    if player == None:
        return False
    else:
        return True

def RegisterNewPlayer(username,password=None,gcm_id=None):
    valid = ValidateUsernamePassword(username,password)
    if (not valid['ValidateUsernamePassword'] and 
        valid['error']=='username does not exist'):
        #register new user
        new_player = Player(username=username,
                            password=hash(password),
                            gcm_id=gcm_id)
        new_player.put()
        return {'RegisterNewPlayer':True,
                'username':username}
    elif not valid['ValidateUsernamePassword']:
        return {'RegisterNewPlayer':False,
                'error':valid['error']}
    elif valid['ValidateUsernamePassword']:
        player = valid['player']
        #player exists already, maybe add/change/remove gcm_id
        player.gcm_id = gcm_id
        player.put()
        return {'RegisterNewPlayer':True,
                'username':username,
                'message':'already registered, gcm_id updated'}
def getPlayerGCMid(username):
    found = db.GqlQuery("select * from Player where username='%s'" % username)
    player = found.get()
    if player == None:
        return False #username not found
    elif player.gcm_id:
        return player.gcm_id
    else:
        return False #user has not registered for GCM
#hash password to be stored in db
def hash(pwd):
    if pwd == None:
        return None
    h = hashlib.new('sha256')
    h.update(pwd)
    return str(h.hexdigest())
def ValidateUsernamePassword(username,password=None):
    found = db.GqlQuery("select * from Player where username='%s'" % username)
    player = found.get()
    if player == None:
        return {'error':'username does not exist',
                'ValidateUsernamePassword':False}
    else:
        pwd = hash(password)
        if (player.password == pwd):
            return {'ValidateUsernamePassword':True,
                    'player':player}
        else:
            return {'error':'username/password combo do not match',
                    'ValidateUsernamePassword':False}
#----------------------------------------------------------------------------------
#**********************************************************************************
#----------------------------------------------------------------------------------
#game stuff
def RegisterNewGame(username,password=None,invite_user=None,choose_color='random'):
    #choose_color options ['black','white','random']
    valid = ValidateUsernamePassword(username,password)
    if not valid['ValidateUsernamePassword']:
        return {'RegisterNewGame':False,
                'error':valid['error']}
     
    
    if (not invite_user == None and
        not UsernameExists(invite_user)):
        
        return {'RegisterNewGame':False,
                'error':'invited user, '+invite_user+', does not exist'}
    else:
        #create new game
        new_game = ChessGame(isPublic=True,
                             moveList='[]',
                             gamePieces='{}',
                             state=0)
        new_game.color_chosen = choose_color
        if invite_user == None:
            new_game.players = [username]
            new_game.isPublic=True
            new_game.status = json.dumps({'game':'waiting for players to join'})
        else:
            new_game.players = [username,invite_user]
            new_game.isPublic = False
            new_game.status = json.dumps({'game':'playing'})
            new_game.state = 1
            t = StartGame(new_game)
            if not t['StartGame']:
                
                return {'RegisterNewGame':False,
                        'StartGame':False,
                        'error':t['error']}
        
        new_game.put()
        return {'RegisterNewGame':True,
                'game_id':str(new_game.key())}

def GetGame(key,debug=False):
    found = db.GqlQuery("select * from ChessGame where __key__=Key('%s')" % key)
    game = False
    try:
        game = found.get()
    except BadKeyError:
        return {'GetGame':False,
                'error':'bad key error'}
    if game:
        if debug:
            return {'GetGame':True,
                    'game':returnGame(game)}
        else:
            return {'GetGame':True,
                    'game':game}
    else:
        return {'GetGame':False,
                'error':'game key not found'}
def GetGameState(game_id,username,password=None):
    found = db.GqlQuery("select * from ChessGame where __key__=Key('%s')" % game_id)
    game = False
    try:
        game = found.get()
    except BadKeyError:
        return {'GetGame':False,
                'error':'bad key error'}
    if game.isPublic:
        return {'GetGameState':True,
                'game':returnGame(game)}
    else:
        valid = ValidateUsernamePassword(username,password)
        if not valid['ValidateUsernamePassword']:
            return {'GetGameState':False,
                    'error':valid['error']}
        elif username in game.players:
            return {'GetGameState':True,
                    'game':returnGame(game)}

#create object to be returned to user with game info
def returnGame(game,list_item=False):
    if list_item:
        move_list = json.loads(game.moveList)
        return {'game_id':str(game.key()),
                'game_id_human':str(game.key().id()),
                'white_player':game.white_player,
                'black_player':game.black_player,
                'players':game.players,
                'move_num':len(move_list),
                'status':json.loads(game.status),
                'whose_turn':game.whose_turn,
                'state':game.state,
                'draw_offered':game.draw_offered,
                'date_created':int(time.mktime(game.date_created.timetuple())*1000)}
    else:
        return {'white_player':game.white_player,
                'black_player':game.black_player,
                'gamePieces':json.loads(game.gamePieces),
                'moveList':json.loads(game.moveList),
                'status':json.loads(game.status),
                'whose_turn':game.whose_turn,
                'state':game.state,
                'draw_offered':game.draw_offered,
                'date_created':int(time.mktime(game.date_created.timetuple())*1000)}

def JoinGame(game_id,username,password=None):
    valid = ValidateUsernamePassword(username,password)
    if not valid['ValidateUsernamePassword']:
        return {'JoinGame':False,
                'error':valid['error']}
    
    found = db.GqlQuery("select * from ChessGame where __key__=Key('%s')" % game_id)
    game = found.get()
    if game:
        if game.isPublic:
            if len(game.players)<2:
                if username in game.players:
                    return {'JoinGame':False,
                            'error':'already joined game'}
                else:
                    game.players += [username]
                    game.put()
                    #start game
                    ret = StartGame(game)
                    return {'JoinGame':True,
                            'game_id':game_id}
            else:
                return {'JoinGame':False,
                        'error':'game full'}
        else:
            return {'JoinGame':False,
                    'error':'game is not public'}
    else:
        return {'JoinGame':False,
                'error':'game key not found'}
def UpdateGame(GSgame,DSgame):
    DSgame.gamePieces = json.dumps(GSgame.dumpPieces())
    DSgame.moveList = json.dumps(GSgame.dumpMoves())
    DSgame.status = json.dumps(GSgame.status)
    DSgame.whose_turn = GSgame.WhoseTurn()
    #if game is over change state, 
    #update winner
    #update user stats
    DSgame.put()
def CreateGame(username,password=None,invite_user=None):
    valid = ValidateUsernamePassword(username,password)
    if not valid['ValidateUsernamePassword']:
        return valid
    new_game = ChessGame()
    if invite_user == None:
        new_game.players = [username]
    else:
        new_game.players[username,invite_user]
        
    return new_game.key()

#----------------------------------------------------------------------------------
#game state management        
def StartGame(game):
    color = game.color_chosen.lower()
    if color == 'random':
        r = random.randint(0, 1)
        if r==0:
            color = 'white'
        else:
            color = 'black'
    
    if color == 'white':
        game.white_player = game.players[0]
        game.black_player = game.players[1]
        
    elif color == 'black':
        game.white_player = game.players[0]
        game.black_player = game.players[1]
        
    else:
        game.delete()
        return {'StartGame':False,
                'error':'invalid color, must be white, black, or random: '+color}
    game.status = json.dumps({'game':'in progress'})
    game.state = 1
    gs = Chess.GameState()
    UpdateGame(gs,game)
    
    return {'StartGame':True}
def SubmitMove(game_id, move, username, password=None,debug=False):
    TAG = 'SubmitMove'
    valid = ValidateUsernamePassword(username,password)
    if not valid['ValidateUsernamePassword']:
        return {TAG:False,
                'error':valid['error']}
    gotGame = GetGame(game_id)
    if gotGame['GetGame']:
        game = gotGame['game']
        #init game state
        pieces = json.loads(game.gamePieces)
        moves = json.loads(game.moveList)
        
        gs = Chess.GameState(pieces=pieces,
                             moves=moves)
        #maybe make move
        next_play = gs.NextPlayer()
        if ((next_play == 'white' and
             game.white_player==username) or
            (next_play == 'black' and
             game.black_player==username)):
            
            moved = gs.AlgebraicMove(move,debug=debug)
            
            if moved['AlgebraicMove']:
                
                UpdateGame(gs,game)
                return {TAG:True}
            else:
                return {TAG:False,
                        'error':moved['error']}
        else:
            return {TAG:False,
                    'error':'not your move'}
    else:
        return {TAG:False,
                'error':gotGame['error']}

def OfferAcceptDraw(game_id,username, password=None,debug=False):
    TAG = 'OfferAcceptDraw'
    valid = ValidateUsernamePassword(username,password)
    if not valid['ValidateUsernamePassword']:
        return {TAG:False,
                'error':valid['error']}
    gotGame = GetGame(game_id)
    if gotGame['GetGame']:
        game = gotGame['game']
        #init game state
        pieces = json.loads(game.gamePieces)
        moves = json.loads(game.moveList)
        
        gs = Chess.GameState(pieces=pieces,
                             moves=moves)
        if username in game.players:
                
            if game.offer_draw and len(game.offer_draw)>0:
                #draw has been offered already
                if game.offer_draw == username:
                    return {TAG:False,
                            'error':'already offered'}
                else:
                    #accept draw
                    gs.draw()
                    UpdateGame(gs,game)
                    return {TAG:True,
                            'detail':'the game is a draw'}
            else:
                game.offer_draw = username
                game.put()
                return {TAG:True,
                        'detail':'draw offered'}
        else:
            return {TAG:False,
                    'error':'you are not part of this game'}
    else:
        return {TAG:False,
                'error':gotGame['error']}
def DeclineOfferedDraw(game_id,username, password=None,debug=False):
    TAG = 'DeclineOfferedDraw'
    valid = ValidateUsernamePassword(username,password)
    if not valid['ValidateUsernamePassword']:
        return {TAG:False,
                'error':valid['error']}
    gotGame = GetGame(game_id)
    if gotGame['GetGame']:
        game = gotGame['game']
        if username in game.players:   
            if game.offer_draw and len(game.offer_draw)>0:
                #draw is declined
                game.offer_draw = ''
                game.put()
                {TAG:True,
                 'detail':'draw declined'}
            else:
                return {TAG:False,
                        'error':'draw not offered'}
        else:
            return {TAG:False,
                    'error':'you are not part of this game'}
    else:
        return {TAG:False,
                'error':gotGame['error']}
#----------------------------------------------------------------------------------
#game lists        

def GameList(username,start=0,limit=10):
    
    found = db.GqlQuery("select * from ChessGame where players in ('%s') and state=1 order by date_created desc" % username)
    ret = []
    for p in found.run(offset=start, limit=limit):
        move_list = json.loads(p.moveList)
        ret += [returnGame(p,True)]
    return {'GameList':True,
            'game_list':ret}
    
def ListOpenGames(username,start=0,limit=10):
    found = db.GqlQuery("select * from ChessGame where isPublic=True and state=0 order by date_created desc")
    stop = False
    ret = []
    tot = limit-start
    while (len(ret)<tot and
           not stop):
        t = 0
        set = found.run(offset=(t*tot)+start, 
                        limit=(t*tot)+start+tot)
        for p in set:
            t+=1
            if username in p.players:
                #ignore games user is already in
                continue
            
            
            game =  returnGame(p,True)
            
            ret += [game]
        if t<tot:
            stop=True
    return {'ListOpenGames':True,
            'game_list':ret}
        
def MyGameList(username,password=None,start=0,limit=10):
    valid = ValidateUsernamePassword(username,password)
    if valid['ValidateUsernamePassword']:
        ret = GameList(username,start,limit)
        return {'MyGameList':True,
                'game_list': ret['game_list']}
    else:
        return {'MyGameList':False,
                'error':'invalid username/password'}

    


        