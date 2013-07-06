Chess4Chewy Backend
===================

To send information to the server and retrieve results,
JSON queries must be sent with a always required `type` 
field along with any other required fields as well.
Server will respond with the `type` value and a boolean
response indicating if it failed (`false`) or succeeded 
(`true`).  A failure will also contain an `error` message
with additional details.

The live instance of this server is hosted by Google at:
[chess4chewy.appspot.com](chess4chewy.appspot.com)

I have implemented a RESTful API to acomplish this task
as described below.


Currently supported functions
-----------------------------

###Player functions
####register user:
Registers a new user with the server.  `GCM_ID` (Google Cloud 
Messaging ID) is not required but the server can't send game 
updates without one.
```JSON
{
 "type":"register_user",
 "username": username,
 "password": password,
 "GCM_ID": GCM_ID
}
```

------------------------------------------------------------------
###Game state functions

####register new game:
```JSON
{
 "type":"register_game",
 "username": username,
 "password": password,
 
 "invite_user":username,
 "choose_color":"random"|"black"|"white"
}
```
####get game state:
Returns the current game state, includes a list of all previous 
moves and the current position and status of every piece on the 
board (and some other stuff).
```JSON
{
 "type":"get_game_state",
 "username": username,
 "password": password,
 "game_id": game_id
}
```
####submit move:
Submit a move to the server for a particular game.  As long as
the move is valid it will be accepted by the server.  If the 
opponount has a GCM_ID registered with the server they will be
notified of the game update.
```JSON
{
 "type":"submit_move",
 "username": username,
 "password": password,
 "game_id": game_id,
 "move": move
}
```

####offer/accept draw:
If the opponent has already offered a draw it will be accepted,
otherwise the opponent will be offered the draw.
```JSON
{
 "type":"offer_accept_draw",
 "username": username,
 "password": password,
 "game_id": game_id,
}
```

####decline draw:
If the game has an open draw offer it will be declined or 
rescinded.
```JSON
{
 "type":"decline_draw",
 "username": username,
 "password": password,
 "game_id": game_id,
}
```
------------------------------------------------------------------
###Game list functions:

####list my games:
Returns a list of games that the player is currently involved in,
along with some game state information.
```JSON
{
 "type":"list_my_games",
 "username": username,
 "password": password
}
```
Not yet implemented/used:
-------------------------
####join game:
Currently, the only way to join/start a game is to enter the user you wish to challenge 
when creating the game.
```JSON
{
 "type":"join_game",
 "username": username,
 "password": password,
 "game_id": game_id,
}
```
####list open games:
Should return a list of open games that a user can join using the above method `join_game`.

I haven't tested it, but it might work.

```JSON
{
 "type":"list_open_games",
 "username": username,
}
```
####list games:
not implemented.

Returns a list of public games a user can watch using the `watch_game` method.
```JSON
{
 "type":"list_games",
 "username": username,
 "password": password
}
```
####watch game:
not implemented.

Adds the user to the games viewer list.  User will be notified about all successful 
game moves.
```JSON
{
 "type":"watch_game",
 "username": username,
 "password": password,
 "game_id": game_id
}
```
