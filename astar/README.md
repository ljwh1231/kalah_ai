# Kalah AI using A* algorithm
- run game
```bash
python3 runner.py
```

- player_v1.py heuristic:  
```
ℎ_1(s) = (# of pieces in holes in oppo’s side) - (# of pieces in holes in user side)
```

- player_v2.py heuristic

    - *f-hole* : hole that player can **get free turn** if player picks the hole

    - *c-hole* : hole in opponent's side that user can **capture the pieces** in the hole in current turn
    
```
ℎ_21(s) = (# of oppo’s f-holes) - (# of user’s f-holes)

ℎ_22(s) = {(# of pieces in oppo’s c-hole) + (# of oppo’s c-hole)} – {(# of pieces in user’s c-hole) + (# of user’s c-hole)}

ℎ_2(s) = ℎ_1(s) + ℎ_21(s) + ℎ_22(s)
```