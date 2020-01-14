from kalah import Kalah, reverse_board
import copy
import inspect
import os


class Player:
    def __init__(self):
        return
    
    def move(self, position, board, is_my_move=True):
        '''
        returns the board after given movement.
        you can get either your's or opponent's movement with the parameter "is_my_move"
        '''
        board = copy.deepcopy(board)
        prediction = Kalah(board)
        if not is_my_move:
            prediction.board = reverse_board(board)

        prediction.move(position)
        board = prediction.board
            
        if not is_my_move:
            board = reverse_board(board)
        return board, prediction.is_game_over()
    
    def get_score(self, board, is_mine=True):
        '''
        returns current score
        is_mine is True --> returns my score
        is_mine is False --> returns opponent's score
        '''
        if is_mine:
            return board[6]
        else:
            return board[-1]    
        
    def is_empty(self, position, board, is_mine=True):
        '''
        returns whether the given position is empty or not
        '''
        if is_mine:
            return 0 >= board[position]
        else:
            return 0 >= board[position+7]
        
    def step(self, pos, board, is_my_move=True):
        if self.is_empty(pos, board, is_mine=is_my_move):
            return None, None
        new_board, over = self.move(pos, board, is_my_move)
        return new_board, over
    
        
class Opponent(Player):
    def __init__(self):
        super().__init__()

    def loop(self, step, board, is_my_move=True):
        if step == 0 or sum([int(self.is_empty(i, board, is_my_move)) for i in range(6)]) == 6:
            return (self.get_score(board)-self.get_score(board, is_mine=False))*10+(sum(board[:6])-sum(board[7:-1]))*1, None
        step -= 1
        score = []
        position = []
        for i in range(6):
            board_i, over_i = self.step(i, board, is_my_move)
            if board_i is None:
                continue
            score_i, j = self.loop(step, board, not is_my_move)
            score.append(score_i)
            position.append(i)
        
        return sum(score)/len(position), position[score.index(max(score))]
    
    def search(self, board):
        '''
        N step search
        returns the position which has the maximum score after N step
        '''
        N = 5
        predicted_score, next_position = self.loop(N, board)
        return next_position


class Mercy(Player):
    '''
    Notice User to the next movement of Opponent
    '''
    def __init__(self):
        super().__init__()
        self.__opponent = Opponent()
        self.__board = None
    def set_board(self, board):
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        if calframe[1][3] != 'run_game' or os.path.split(calframe[1].filename)[-1] != 'runner.py':
            print("Cheating is not allowed")
            exit(-1)
        self.__board = board

    def response(self, position):
        board, over = self.step(position, self.__board)
        if over:
            return None
        return self.__opponent.search(reverse_board(board))


class Runner:
    def __init__(self, num_of_games=1):
        # player_v1 : v1 heuristic
        # player_v2 : v2 heuristic
        from player_v1 import User
        self.user = User()
        self.opponent = Opponent()
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.num_of_games = num_of_games
    
    def score_board(self, ith, result):
        print(str(ith)+"th game over!")
        if result == 1:
            self.wins += 1
        elif result == 0:
            self.draws += 1
        else:
            self.losses += 1
        print("Total wins:\t"+str(self.wins))
        print("Total draws:\t"+str(self.draws))
        print("Total losses:\t"+str(self.losses))
        print("Total winning rate:\t"+str(float(self.wins / (ith+1))*100)+"%")
        return


    def run_game(self):
        for i in range(self.num_of_games):
            print("New game!")
            new_game = Kalah([4, 4, 4, 4, 4, 4, 0, 4, 4, 4, 4, 4, 4, 0])
            turn = 0
            print(str(turn)+"th turn")
            new_game.show_board()
            while not new_game.game_over:
                self.user.mercy.set_board(copy.deepcopy(new_game.board))
                if new_game.player:
                    next_position = self.user.search(copy.deepcopy(new_game.get_board()))
                else:
                    next_position = self.opponent.search(copy.deepcopy(new_game.get_board()))

                tmp_score, free_turn = new_game.move(next_position)
                turn += 1
                print(str(turn)+"th turn")
                new_game.show_board(tmp_score, free_turn)
                new_game.is_game_over()
                
            new_game.show_board()
            self.score_board(i, new_game.result())

if __name__ == '__main__':
    runner = Runner(1)
    runner.run_game()