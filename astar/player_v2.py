from kalah import reverse_board
from runner import Player, Mercy


class Node:
    def __init__(self, tag, parentNode, board, pos, f, g, h):
        self.tag = tag
        self.parent = parentNode
        self.board = board
        self.pos = pos
        self.f = f
        self.g = g
        self.h = h


class User(Player):
    def __init__(self):
        super().__init__()
        self.mercy = Mercy()
        '''
        Check Player class in runner.py to get information about useful predefined functions
        e.g. move, get_score, is_empty, step
        '''

    def search(self, board, step=1):
        '''
        board: board information before move
        step: # of steps after move
        '''
        f_compare = []
        for i in range(6):
            next_board, next_over = self.step(i, board, is_my_move=True)
            if next_board is None:
                continue
            first_g = self.g(1, next_board)
            first_h = self.h(next_board)
            first_f = first_g + first_h

            first = Node("first", None, next_board, i, first_f, first_g, first_h)

            if next_over is True:
                f_compare.append(first)

            oppo_pos = self.mercy.response(i)
            if oppo_pos is None:
                continue
            sec_board, sec_over = self.step(oppo_pos, next_board, is_my_move=False)
            oppo_g = self.g(2, sec_board)
            oppo_h = self.h(sec_board)
            oppo_f = oppo_g + oppo_h

            second = Node("second", first, sec_board, i, oppo_f, oppo_g, oppo_h)

            if sec_over is True:
                f_compare.append(second)

            for j in range(6):
                # print(i, j)
                final_board, final_over = self.step(j, sec_board, is_my_move=True)
                if final_board is None:
                    continue
                final_g = self.g(3, final_board)
                final_h = self.h(final_board)
                final_f = final_g + final_h

                final = Node("final", second, final_board, j, final_f, final_g, final_h)
                # print(i, j, final.f)
                f_compare.append(final)

        min_f = 100000000
        next_pos = 0
        # print(len(f_compare))
        for i in range(len(f_compare)):
            if f_compare[i].tag == "first":
                # print("hello")
                if f_compare[i].f < min_f:
                    min_f = f_compare[i].f
                    # print("F: ", min_f)
                    next_pos = f_compare[i].pos
            elif f_compare[i].tag == "second":
                if f_compare[i].parent.f < min_f:
                    min_f = f_compare[i].f
                    # print("F: ", min_f)
                    next_pos = f_compare[i].parent.pos
            elif f_compare[i].tag == "final":
                if f_compare[i].f < min_f:
                    min_f = f_compare[i].f
                    # print("F: ", min_f)
                    next_pos = f_compare[i].parent.parent.pos

        return next_pos

        #     reverse_board(response[0])
        #     third_pos = 0
        #     while third_pos != 6:
        #         result = self.step(third_pos, response[0])
        #         g = self.g(step, result)
        #         h = self.h(result)
        #         f = g + h
        #         f_val.append(f)
        #         print(f)
        #     pos += 1
        # print(f_val)

        # raise NotImplementedError

    def g(self, step, board):
        '''
        cost function
        '''
        return step - self.get_score(board) + self.get_score(board, is_mine=False)

    def h(self, board):  # Not implemented!
        '''
        heuristic function
        v1: h1
        v2: h1 + h21 + h22
        '''
        # return self.h1(board)
        return self.h1(board) + self.h21(board) + self.h22(board)

    def h1(self, board):
        '''
        (# of pieces in holes in oppo’s side) - (# of pieces in holes in user side)
        '''
        oppo_num = 0
        user_num = 0
        for i in range(6):
            user_num += board[i]
            oppo_num += board[i + 7]

        return oppo_num - user_num

    def h21(self, board):
        '''
        (# of oppo’s f-holes) - (# of user’s f-holes)
        '''
        oppo_f_hole = 0
        user_f_hole = 0
        for i in range(14):
            if i is 6 or i is 13:
                continue
            if i in range(0, 6):
                if i + board[i] == 6:
                    user_f_hole += 1
            elif i in range(7, 13):
                if i + board[i] == 13:
                    oppo_f_hole += 1

        return oppo_f_hole - user_f_hole
        # raise NotImplementedError

    def h22(self, board):
        '''
        {(# of pieces in oppo’s c-hole) + (# of oppo’s c-hole)} – {(# of pieces in user’s c-hole) + (# of user’s c-hole)}
        '''
        oppo_c_hole = []
        user_c_hole = []

        oppo_c_hole_pieces = 0
        user_c_hole_pieces = 0

        for i in range(0, 14):
            if i == 6 or i == 13:
                 continue
            if board[i] == 0:
                continue
            if i in range(0, 6):
                if i + board[i] < 6:
                    if board[i + board[i]] == 0:
                        c_hole_idx = 12 - (i + board[i])
                        if c_hole_idx in user_c_hole:
                            continue
                        else:
                            user_c_hole.append(c_hole_idx)
                            user_c_hole_pieces += board[c_hole_idx]
                    else:
                        continue
                elif i + board[i] - 13 >= 0 and i + board[i] - 13 < i:
                    if board[i + board[i] - 13] == 0:
                        c_hole_idx = 25 - (i + board[i])
                        if c_hole_idx in user_c_hole:
                            continue
                        else:
                            user_c_hole.append(c_hole_idx)
                            user_c_hole_pieces += board[c_hole_idx] + 1
                    else:
                        continue
            elif i in range(7, 13):
                if i + board[i] < 13:
                    if board[i + board[i]] == 0:
                        c_hole_idx = 12 - (i + board[i])
                        if c_hole_idx in oppo_c_hole:
                            continue
                        else:
                            oppo_c_hole.append(c_hole_idx)
                            oppo_c_hole_pieces += board[c_hole_idx]
                    else:
                        continue
                elif i + board[i] - 13 >= 7 and i + board[i] - 13 < i:
                    if board[i + board[i] - 13] == 0:
                        c_hole_idx = 25 - (i + board[i])
                        if c_hole_idx in user_c_hole:
                            continue
                        else:
                            oppo_c_hole.append(c_hole_idx)
                            oppo_c_hole_pieces += board[c_hole_idx] + 1
                    else:
                        continue
        return (oppo_c_hole_pieces + len(oppo_c_hole)) - (user_c_hole_pieces + len(user_c_hole))
        # raise NotImplementedError