Chess
=====

###Move validator

Main entry point is in [GameLogic.py](GameLogic.py).
Which manages the game state and makes sure all moves
are valid, returning relevant errors when they are not.
Check, Check-Mate, Castle, and en-passant rules are 
enforced here as well.

Possible moves for individual piece types have been 
split into separate source files.  

###Not yet implemented

Forced draw/stalemate rules due to insufficient material, 
inablity to move are not enforced; but players can manually 
offer and accept a draw.

