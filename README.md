Chess4Chewy Backend
====
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

##Currently supported functions

------------------------------------------------------------------
###Player functions
####register user:
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
```JSON
{
 "type":"get_game_state",
 "username": username,
 "password": password,
 "game_id": game_id
}
```
####submit move:
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
```JSON
{
 "type":"offer_accept_draw",
 "username": username,
 "password": password,
 "game_id": game_id,
}
```

####decline draw:
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
```JSON
{
 "type":"list_my_games",
 "username": username,
 "password": password
}
```
###Not yet implemented/used:
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
not used, might work
```JSON
{
 "type":"list_open_games",
 "username": username,
}
```
####list games:
not implemented.
```JSON
{
 "type":"list_open_games",
 "username": username,
 "password": password
}
```
####watch game:
not implemented.
```JSON
{
 "type":"watch_game",
 "username": username,
 "password": password,
 "game_id": game_id
}
```
