from kalah import reverse_board
from runner import Player
import math
import random
import copy
from graphviz import Graph
import seaborn
import time


INF = 99999999
color_hex = seaborn.color_palette('RdBu_r', 101).as_hex()
time_out = 0.5


def get_color_hex(winning_rate):
    # 0 <= winning_rate <= 1
    assert winning_rate >= 0. and winning_rate <= 1.
    return color_hex[int(winning_rate*100)]


class Tree:
    def __init__(self, board, node, edge, node_id, position=None, is_my_move=True, parent=None, is_game_over=False, is_free_turn=False):
        self.child = [None]*6 # the children nodes corresponding to nodes after picking 1st~6th holes each.
        self.parent = parent # the parent node
        self.position = position # the position chose in previous step. If self is not the root node, self.parent.child[self.position] is self
        if self.position is not None:
            assert self.position < 6 and self.position >= 0
        self.is_my_move = is_my_move
        self.board = tuple(board)
        self.is_game_over = is_game_over
        self.is_free_turn = is_free_turn

        self.cumulative_reward = 0. # cumulated reward of children and itself
        self.n = 0  # the number of times the child node was selected

        self.node_id = node_id
        self.node = node
        self.edge = edge

    def has_child(self):
        return bool(sum([int(c is not None) for c in self.child]))

    def expected_winning_rate(self):
        return self.cumulative_reward / self.n

    def UCB(self, N):
        winning_rate = self.expected_winning_rate() if self.is_my_move else 1 - self.expected_winning_rate()
        return winning_rate + math.sqrt(2 * math.log(N) / self.n)


class User(Player):
    def __init__(self, simulation_depth=6, number_of_simulation=1000):
        super().__init__()
        '''
        Check Player class in runner.py to get information about useful predefined functions
        e.g. move, get_score, is_empty, step
        '''
        self.root = None
        self.alpha = 0.5
        self.simulation_depth = simulation_depth
        self.number_of_simulation = number_of_simulation
        self.g = Graph(format='png', graph_attr={}, node_attr={'fontsize': '13'})	# visualization graph
        self.node_id = 0

    def build_node(self, board, position=None, is_my_move=True, parent=None, is_game_over=False, is_free_turn=False):
        node_id = str(self.node_id)
        self.node_id += 1

        # visualization
        if parent is None:	# build root node
            label = 'root'
            self.g.node(node_id, label=label, shape='circle', width='0.1')
            node = self.g.body[-1]
            edge = None
        else:  # expansion
            label = str(position) if parent.parent is None else ''
            shape = 'circle' if is_my_move else 'square'
            self.g.node(node_id, label=label, shape=shape, width='0.1')
            node = self.g.body[-1]
            self.g.edge(parent.node_id, node_id)
            edge = self.g.body[-1]
            if parent.parent is None:
                """
                Sort the children
                """
                pos_index = sorted([(c.position, c.node_id, c.node) for c in parent.child if c is not None] + [(position, node_id, node)], key=lambda c: c[0], reverse=True)
                graph_index = sorted(pos_index, key=lambda c: c[1], reverse=True)
                for gi in graph_index:
                    del self.g.body[self.g.body.index(gi[2])]
                for pi in pos_index:
                    self.g.body.insert(0, pi[2])

        return Tree(tuple(board), node, edge, node_id, position, is_my_move=is_my_move, parent=parent, is_game_over=is_game_over, is_free_turn=is_free_turn)

    def recycle_tree(self, node):
        """
        Recycle the past tree when updating the root for visualization
        """
        self.g.body.append(node.node)
        if node.edge is not None:
            self.g.body.append(node.edge)
            self.g.node(node.node_id, style='filled', color=get_color_hex(node.expected_winning_rate()))

        if not node.has_child():
             return
        for c in node.child:
            if c is None:
                continue
            self.recycle_tree(c)

    def initial_root(self, board):
        self.root = self.build_node(board)

    def update_root(self, position, board, is_my_move):
        '''
        Update the root as the selected child node
        '''
        del self.g
        self.g = Graph(format='png', graph_attr={'fixed_size': 'false'}, node_attr={'fontsize': '13'})

        if self.root.child[position] is None or self.root.child[position].is_my_move != is_my_move:
            self.root = self.build_node(board)
        else:
            self.root = self.root.child[position]
            del self.root.parent
            self.root.parent = None
            # change name in graph
            self.root.node = self.root.node.split("label="+str(self.root.position))[0] + "label=" + str('root') + self.root.node.split("label="+str(self.root.position))[1]
            self.root.edge = None
            for c in self.root.child:
                if c is not None:
                    c.node = c.node.split("label=\"\"")[0] + "label=" + str(c.position) + c.node.split("label=\"\"")[1]
        self.recycle_tree(self.root)

    def search(self, board):
        # ---- user's step ----
        '''
        repeat N simulations:
            1. Selection and Expansion
            2. Simulation
            3. Backpropagation
        '''
        #This is dummy for visualization example. You need to delete following
        ######################################################
        # while True:
        #     position = random.choice(range(6))
        #     if not self.is_empty(position, board, True):
        #         return position
        ######################################################

        start_time = time.time()
        for _ in range(self.number_of_simulation):
            # print("Iter ", _, ":")
            assert self.root.is_my_move
            if time.time() - start_time >= time_out:
                break
            selected_node = self.tree_policy()
            # print("node selected")
            # print(selected_node.board)
            reward = self.simulation(selected_node)
            # print("Reward: ", reward)
            self.backpropagation(selected_node, reward)

        # choose the action that leads to the highest expected winning rate
        expected = []
        for c in self.root.child:
            if c is None:
                expected.append(-INF)
            else:
                expected.append(c.expected_winning_rate())
        decision = self.root.child[expected.index(max(expected))]

        return decision.position

    #############################################
    # ----- MCTS algorithm step 1&2, 3, 4 ----- #
    #############################################
    def tree_policy(self):
        #Not implemented
        '''
        Do (1)Selection and (2)Expansion step
        return: the node selected for simulation
        '''

        # (1)Selection
        node = self.root # start from root node
        if node.is_game_over: # root node is game over
            return node # cannot perform expansion
        else:
            node = self.selection(node)
        # (2)Expansion
        # (2-1)check free_turn
        # (2-2)make new node

        while True:
            next_pos = self.best_action(node)
            # print(next_pos)
            new_board, new_over, new_free = self.step(next_pos, list(node.board), is_my_move=True)
            # print(new_board)
            if new_board is None:
                # print(new_board)
                continue
            else:
                node.child[next_pos] = self.build_node(new_board, position=next_pos, is_my_move=True, parent=node
                                                       , is_game_over=new_over, is_free_turn=new_free)
                break
        return node.child[next_pos]

        # raise NotImplementedError

    def selection(self, root):
        current_node = root
        while True:
            if sum([int(c is None) for c in current_node.child]) != 0:
                # print("root")
                return current_node
            else:
                # print("one of the children")
                # print(self.best_action(root))
                current_node = root.child[self.best_action(root)]
                # print("hello")
        # raise NotImplementedError

    #
    def simulation(self, selected_node):
        #Not implemented
        '''
        (3)Simulation
        '''
        next_board = list(selected_node.board)
        next_over = selected_node.is_game_over
        next_free = selected_node.is_free_turn
        while next_over is False:
            if next_free is True:
                new_board, new_over, new_free = self.default_policy(next_board, True)
                if new_board is None:
                    continue
                else:
                    next_board, next_over, next_free = new_board, new_over, new_free
            else:
                new_board, new_over, new_free = self.default_policy(next_board, False)
                if new_board is None:
                    continue
                else:
                    next_board, next_over, next_free = new_board, new_over, new_free
        # print(next_board)
        return self.evaluation(next_board)
        # while is game over true?
        #       step randomly to the leaf node  which is game over by default policy
        # return reward 1 if win 0 if lose
        # raise NotImplementedError

    def backpropagation(self, node, reward):
        '''
        Backpropagate the reward
        '''
        while node is not None:
            node.n += 1
            node.cumulative_reward += reward
            if node.parent is not None:
                self.g.node(node.node_id, style='filled', color=get_color_hex(node.expected_winning_rate()))
            node = node.parent

    #############################################
    # -------- subfunctions for MCTS ---------- #
    #############################################

    def max_ucb(self, node):
        ucb_val = []
        N = 0
        for count in range(len(node.child)):
            N += node.child[count].n
            # print(N)

        for count in range(len(node.child)):
            ucb = node.child[count].UCB(N)
            ucb_val.append(ucb)

        return ucb_val.index(max(ucb_val))

    def best_action(self, node):
        #Not implemented
        '''
        Case 1: if there exists unvisited child
            return unvisited
        Case 2: else
            return the child who has the maximum UCB
        '''
        #
        none_child = [i for i, e in enumerate([int(c is None) for c in node.child]) if e != 0
                          or self.is_empty(i, node.board) is False]
        # print(not_none_child)
        if len(none_child) != 0:
            position = random.choice(none_child)
            return position
        else:
            # print(node.board)
            return self.max_ucb(node)
        # raise NotImplementedError

    def default_policy(self, board, is_my_move):
        '''
        Randomly select non-empty position
        '''
        while True:
            # print("hello")
            position = random.choice(range(6))
            if not self.is_empty(position, board, is_my_move):
                break

        return self.step(position, list(board), is_my_move)

    def evaluation(self, board):
        '''
        Evaluate when game is over or reaches the last depth of simulation
        You can change this rewards to improve the performance
        '''
        user_score = board[6]
        oppo_score = board[-1]
        user_pieces = sum(board[:6])
        oppo_pieces = sum(board[7:-1])
        if self.is_game_over(board): # win: 1, dual: 0.5, lose: 0
            if user_score+user_pieces > oppo_score+oppo_pieces:
                reward = 1
            elif user_score+user_pieces == oppo_score+oppo_pieces:
                reward = 0.5
            else:
                reward = 0
        else:
            user_score += user_pieces * self.alpha
            oppo_score += oppo_pieces * self.alpha
            reward = user_score / (user_score + oppo_score)

        return reward

    #############################################
    # ----------- other functions ------------- #
    #############################################

    def is_game_over(self, board):
        if sum(board[:6]) == 0 or sum(board[7:-1]) == 0:
            return True
        else: return False

    def print_winning_rate(self, next_position):
        if self.root.child[next_position] is None or self.root.child[next_position].n == 0:
            return None
        else:
            return self.root.child[next_position].cumulative_reward / self.root.child[next_position].n