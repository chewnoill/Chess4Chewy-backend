'''
Created on Apr 27, 2013

@author: will
'''
'''
Created on Mar 21, 2013

@author: will
'''
import json
import DataStore
import Chess.GameLogic as Chess

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from gcm import GCM
from Shared.Secret import GCM_API_KEY

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, webapp2 World!')
    def post(self):
        callback = self.request.GET.get('callback')
        
        input = {}
        error = False
        ret = error_msg = {'error':'an error has occurred!',
                           'code':400,
                           'detail':'unknown error'}#default error message
        userAgent = 'unknown user agent'
        if 'User-Agent' in self.request.headers:
            userAgent = self.request.headers['User-Agent']
        elif 'user-agent' in self.request.headers:
            userAgent = self.request.headers['user-agent']
        try:
            input = json.loads(self.request.body)
        except ValueError:
            error_msg['code']=400
            error_msg['detail']='invalid input'
            error_msg['error']='bad input'
            error = True
        
        #type is always required
        missing = MissingRequiredFields(['type'],input)
        if missing:
            ret = missing
        else: 
            type = input['type']
            
            if type in dispatch:
                foo = dispatch[type]
                err = MissingRequiredFields(foo['required_fields'],input)
                if not err:
                    ret = foo['function'](input)
                else:
                    ret = err
            elif type == 'send_gcm':
                missing = MissingRequiredFields(['message','username'],input)
                if missing:
                    ret = missing
                else:
                    message = input['message']
                    username = input['username']
                    response = SendGCMMessage(username,message)
                    ret = {'detail':'message sent',
                           'message':message,
                           'response':response}
        try:
            #load structure into callback function for JS
            if callback:
                self.response.out.write(callback+'(')
            
            msg = json.dumps(ret)
            self.response.out.write(msg)
            if callback:
                self.response.out.write(')')
        except UnicodeDecodeError:
            raise Exception("UnicodeDecodeError: "+str(ret))
#----------------------------------------------------------------------------------------
#global functions
def MissingRequiredFields(fieldList,values):
    missing = []
    for field in fieldList:
        if (not field in values or
            len(values[field])==0):
            missing += [field]
    if len(missing)==0:
        return False
    else:
        return {'error':'required fields missing',
                'detail':str(missing)+' fields are required'}
    
def SendGCMMessage(username,message):
    gcm = GCM(GCM_API_KEY)
    reg_id = [DataStore.getPlayerGCMid(username)]
    if (reg_id == False or
        len(reg_id)==0):
        #do nothing
        return False
    response = gcm.json_request(registration_ids=reg_id, data=message)

    # Handling errors
    if 'errors' in response:
        return response['errors']
    else:
        #do i need to save this reg_id?
        return {'reg_id':reg_id}
    
#----------------------------------------------------------------------------------------
#user functions    
def register_user(values):
    #------------------------------------------------------------
    #required fields
    username = values['username'] 
    
    #------------------------------------------------------------
    #optional fields
    GCM_ID = None #used to send messages to mobile device
    password = None
    if 'GCM_ID' in values:
        GCM_ID = values['GCM_ID']
    if 'password' in values:
        password = values['password']
    success = DataStore.RegisterNewPlayer(username,password,GCM_ID)
    if success:
        ret = {'register_user':True,
               'detail':'user registration accepted'}
    else:
        ret = {'register_user':False,
               'error':'username already taken',
               'detail':username + 'has already been claimed'}
    return ret
#----------------------------------------------------------------------------------------
#game functions
def register_game(values):
    #------------------------------------------------------------
    #required fields
    username = values['username'] #required field
    
    #------------------------------------------------------------
    #optional fields
    invite_user = None
    password = None
    choose_color = 'Random'
    if ('invite_user' in values and 
        len(values['invite_user'])>0):
        invite_user = values['invite_user']
        #check if user exists?
    if 'password' in values:
        password = values['password']
        #check if password matches?
    if 'choose_color' in values:
        choose_color = values['choose_color']
        
    #------------------------------------------------------------    
    #register game    
    newGame = DataStore.RegisterNewGame(username,password,invite_user,choose_color)
    if newGame['RegisterNewGame'] == False:
        #game not created
        ret = {'register_game':False,
               'error':'game creation failed',
               'detail':newGame['error']}
    else:
        if not invite_user == None:
            #send message to user
            SendGCMMessage(invite_user,{'type':'game_invite',
                                        'game_id':newGame['game_id'],
                                        'invited_by':username})
        ret = {'register_game':True,
               'detail':'game created',
               'game_id':newGame['game_id']}
    return ret
def join_game(values):
    #------------------------------------------------------------
    #required fields
    username = values['username']
    game_id = values['game_id']
    #------------------------------------------------------------
    #optional fields
    password = None
    if 'password' in values:
        password = values['password']
    
    #------------------------------------------------------------
    #do some stuff
    ret = DataStore.JoinGame(game_id, username, password)
    if ret['JoinGame']:
        return {'join_game':True}
    else:
        return {'join_game':False,
                'error':ret['error']}
def submit_move(values):
    #------------------------------------------------------------
    #required fields
    username = values['username'] #required field
    game_id = values['game_id']
    move = values['move']
    #------------------------------------------------------------
    #optional fields
    password = None
    if 'password' in values:
        password = values['password']
    
    #------------------------------------------------------------
    #do some stuff
    ret = DataStore.SubmitMove(game_id, move, username, password)
    
    if ret['SubmitMove']:
        game = DataStore.GetGame(game_id)
        white_player = game['game'].white_player
        black_player = game['game'].black_player
        if not white_player == username:
            SendGCMMessage(white_player,{'type':username+'has moved',
                                         'game_id':game_id})
        else:
            SendGCMMessage(black_player,{'type':username+'has moved',
                                         'game_id':game_id})
        return {'submit_move':True}
    else:
        return {'submit_move':False,
                'error':ret['error']}
def get_game_state(values):
    #------------------------------------------------------------
    #required fields
    username = values['username'] #required field
    game_id = values['game_id'] #required field
    #------------------------------------------------------------
    #optional fields
    password = None
    if 'password' in values:
        password = values['password']
    #------------------------------------------------------------
    ret = DataStore.GetGameState(game_id,username,password)
    if ret['GetGameState']:
        return {'get_game_state':True,
                'game':ret['game']}
    else:
        return {'get_game_state':False,
                'error':ret['error']}
def offer_accept_draw(values):
    #------------------------------------------------------------
    #requires username,password,game_id
    username = values['username']
    password = values['password']
    game_id = values['game_id']
    TAG = 'offer_accept_draw'
    #------------------------------------------------------------
    #do it
    response = DataStore.OfferAcceptDraw(game_id, username, password)
    if response['OfferAcceptDraw']:
        return {TAG:True,
                'detail':response['detail']}
    else:
        return {TAG:False,
                'error':response['error']}
def decline_draw(values):
    #------------------------------------------------------------
    #requires username,password,game_id
    username = values['username']
    password = values['password']
    game_id = values['game_id']
    TAG = 'decline_draw'
    #------------------------------------------------------------
    #do it
    response = DataStore.DeclineOfferedDraw(game_id, username, password)
    if response['DeclineOfferedDraw']:
        return {TAG:True,
                'detail':response['detail']}
    else:
        return {TAG:False,
                'error':response['error']}
#----------------------------------------------------------------------------------------
#game list functions
def list_open_games(values):
    #------------------------------------------------------------
    #required fields
    username = values['username']
    
    #------------------------------------------------------------
    #do it
    ret = DataStore.ListOpenGames(username)
    if ret['ListOpenGames']:
        return {'list_open_games':True,
                'game_list':ret['game_list']}
    else:
        return {'list_open_games':False,
                'error':ret['error']}
def list_my_games(values):
    #------------------------------------------------------------
    #required fields
    username = values['username'] #required field
    #------------------------------------------------------------
    #optional fields
    password = None
    if 'password' in values:
        password = values['password']
    #------------------------------------------------------------
    #do some stuff
    ret = DataStore.MyGameList(username,password)
    if ret['MyGameList']:
        return {'list_my_games':True,
                'game_list':ret['game_list']}
    else:
        return {'list_my_games':False,
                'error':ret['error']}
def list_games(values):
    'TODO'
    return NotImplemented('list_games')
def list_live_games(values):
    'TODO'
    return NotImplemented('list_live_games')

def watch_game(values):
    'TODO'
    return NotImplemented('watch_game')

def NotImplemented(name):
    return {name:False,
            'error':'function not implemented yet'}
    
ToDo = {'required_fields':[],
        'function':NotImplemented              
        }
dispatch = {'register_user':{'required_fields':['username','password'],
                             'function':register_user},
            'register_game':{'required_fields':['username'],
                             'function':register_game},
            'join_game':{'required_fields':['username','game_id'],
                         'function':join_game},
            'list_open_games':{'required_fields':['username'],
                               'function':list_open_games},
            'list_my_games':{'required_fields':['username'],
                             'function':list_my_games},
            'list_games':{'required_fields':['username'],
                          'function':list_games},
            'list_live_games':{'required_fields':['username'],
                               'function':list_live_games},
            'submit_move':{'required_fields':['username','game_id','move'],
                           'function':submit_move},
            'get_game_state':{'required_fields':['username','game_id'],
                        'function':get_game_state},
            'watch_game':{'required_fields':['username','game_id'],
                          'function':watch_game},
            'offer_accept_draw':{'required_fields':['username','password','game_id'],
                                 'function':offer_accept_draw},
            'decline_draw':{'required_fields':['username','password','game_id'],
                                 'function':decline_draw},
            }
application = webapp.WSGIApplication([('/', MainPage)], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

