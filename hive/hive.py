"""
https://github.com/vidstige/hive

"""
import random
from collections import defaultdict
from copy import deepcopy
import numpy as np
import time
random.seed(42)

# Hex topology stuff
offsets = [
    (0, -1, 1), (1, -1, 0), (1, 0, -1),
    (0, 1, -1), (-1, 1, 0), (-1, 0, 1)]

def neighbours(c):
    """Returns cube hex neighbours"""
    x, y, z = c
    for ox, oy,oz in offsets:
        yield x + ox, y + oy, z + oz

def add(c1, c2):
    x1, y1, z1 = c1
    x2, y2, z2 = c2
    return x1 + x2, y1 + y2, z1 + z2

# Hive stuff
def find_contour(state, exclude=None):
    """Returns all contour coordinates of the hive"""
    contour = set()
    # All neighbours
    for coordinate in state.grid:
        if coordinate not in exclude:
            for neighbour in neighbours(coordinate):
                contour.add(neighbour)
    # ...except non-free
    contour.difference_update(set(state.grid.keys()))
    return contour

def trace_contour(state, coordinate, steps=1):
    """Returns the two coordinates n steps away from coordinate along
    the hive contour."""
    contour = find_contour(state, exclude=(coordinate,))
    visited = set()
    todo = [(coordinate, 0)]
    while todo:
        c, n = todo.pop()
        for neighbour in neighbours(c):
            if neighbour in contour and neighbour not in visited:
                visited.add(neighbour)
                if n == steps:
                    yield c
                else:
                    todo.append((neighbour, n + 1))

class Tile(object):
    name = None
    def moves(self, coordinate, state):
        return iter(())
    def __str__(self):
        return self.name
    def __repr__(self):
        return "{}()".format(self.__class__.__name__)
    def __deepcopy__(self, memo):
        return self  # don't copy

class Queen(Tile):
    name = 'queen'
    def moves(self, coordinate, state):
        return trace_contour(state, coordinate, steps=1)

class Spider(Tile):
    name = 'spider'
    def moves(self, coordinate, state):
        return trace_contour(state, coordinate, steps=3)

class Beetle(Tile):
    name = 'beetle'
    def moves(self, coordinate, state):
        coordinates = set(state.grid.keys())
        coordinates.remove(coordinate)
        for n in neighbours(coordinate):
            new_coords = coordinates.copy()
            new_coords.add(n)
            if one_hive(new_coords):
                yield n

class Ant(Tile):
    name = 'ant'
    def moves(self, coordinate, state):
        return find_contour(state, exclude=(coordinate,))

class Grasshopper(Tile):
    name = 'grasshopper'
    def moves(self, coordinate, state):
        for direction in offsets:
            p = add(coordinate, direction)
            # Grasshopper must jump over at least one piece
            if p in state.grid:
                while p in state.grid:
                    p = add(p, direction)
                yield p

queen = Queen()
spider = Spider()
beetle = Beetle()
ant = Ant()
grasshopper = Grasshopper()

class Player(object):
    def __init__(self, name):
        self.hand = {
            queen: 1,
            spider: 2,
            beetle: 2,  # for the movement they move like the queen
            ant: 3,
            grasshopper: 3,
        }

        self.name = name

    def __repr__(self):
        return "Player('{name}')".format(name=self.name)

class State(object):
    """Game state"""
    def __init__(self):
        self.grid = defaultdict(list)
        self.move_number = 0
        self.players = (Player('white'), Player('black'))

    def round(self):
        return self.move_number // 2

    def player(self):
        return self.players[self.move_number % len(self.players)]

    def opponent(self):
        return self.players[(self.move_number + 1) % len(self.players)]

    def do(self, move):
        """In the grid only the last element is visible (the rest are blocked)"""
        player = self.player()
        action, arg1, arg2 = move
        if action == 'place':
            tile, coordinate = arg1, arg2
            self.grid[coordinate].append((player, tile))
            player.hand[tile] -= 1
        elif action == 'move':
            if len(self.grid[arg1]) > 1:
                value = self.grid[arg1].pop(-1)
            else:
                value = self.grid.pop(arg1)[-1]
            self.grid[arg2].append(value)
        elif action == 'nothing':
            pass
        else:
            print("UNKNOWN MOVE")

        self.move_number += 1

def find(state, player_needle, tile_needle):
    for c, v in state.grid.items():
        for piece in v:
            player, tile = piece
            if tile == tile_needle and player == player_needle:
                return c
    return None

def is_looser(state, player):
    queen_coordinate = find(state, player, queen)
    if queen_coordinate:
        if all(n in state.grid for n in neighbours(queen_coordinate)):
            return True
    return False

def winner(state):
    white, black = state.players
    #if white_loose and black_loose:
    #    return None  # tie
    if is_looser(state, white):
        return black
    if is_looser(state, black):
        return white
    return None  # game has not ended

def placeable(state):
    """Returns all coordinates where the given player can
    _place_ a tile."""
    players = defaultdict(set)
    for coordinate, value in state.grid.items():
        player, _ = value[-1]
        for n in neighbours(coordinate):
            players[player].add(n)
    # All neighbours to any tile placed by current player...
    coordinates = players[state.player()]
    # ...except where the opponent is neighbour...
    for p in players:
        if p != state.player():
            coordinates.difference_update(players[p])
    # ...and you cannot place on top of another tile.
    coordinates.difference_update(state.grid.keys())

    return coordinates

def one_hive(coordinates):
    unvisited = set(coordinates)
    todo = [unvisited.pop()]
    while todo:
        node = todo.pop()
        for neighbour in neighbours(node):
            if neighbour in unvisited:
                unvisited.remove(neighbour)
                todo.append(neighbour)
    return not unvisited

def movements(state):
    for coordinate, value in state.grid.items():
        player, tile = value[-1]
        if player == state.player():
            coordinates = set(state.grid.keys())
            coordinates.remove(coordinate)
            for target in tile.moves(coordinate, state):
                new_coords = coordinates.copy()
                new_coords.add(target)
                if one_hive(new_coords):
                    yield ('move', coordinate, target)

def enumerate_hand(player, coordinates):
    """Fora given iterable of coordinates, enumerate all avilable tiles"""
    for tile, count in player.hand.items():
        if count > 0:
            for c in coordinates:
                yield 'place', tile, c

def available_moves(state):
    if not state.grid:
        # If nothing is placed, one must place something anywhere
        anywhere = (0, 0, 0)
        return enumerate_hand(state.player(), [anywhere])
    if len(state.grid) == 1:
        # If single tile is placed, opponent places at neighbour
        start_tile = next(iter(state.grid))
        return enumerate_hand(state.player(), list(neighbours(start_tile)))
    
    placements = placeable(state)
    # If queen is still on hand...
    if state.player().hand[queen] > 0:
        # ...it must be placed on round 4
        if state.round() + 1 == 4:
            return [('place', queen, c) for c in placements]
        # ...otherwise only placements...
        return list(enumerate_hand(state.player(), placements))
    # ...but normally placements and movements
    available = list(enumerate_hand(state.player(), placements)) + list(movements(state))
    if not available:
        return [('nothing', None, None)]
    return available


# AI stuff

def evaluate(state, player):
    white, black = state.players
    other = white if player == black else black

    player_queen = find(state, player, queen)
    other_queen = find(state, other, queen)
    player_free = len([n for n in neighbours(player_queen) if n not in state.grid]) if player_queen else 0
    other_free = len([n for n in neighbours(other_queen) if n not in state.grid]) if other_queen else 0
    return player_free - 2 * other_free

def minmax(state: State, player: Player, d: int, alpha: int, beta: int):
    if d <= 0:
        return None, evaluate(state, player), 1

    the_winner = winner(state)
    if the_winner:
        print("leaf!")
        return None, 1 if the_winner == player else -1, 1

    maximizing = state.player() == player 
    f = max if maximizing else min
    evaluations = {}
    nn = 0
    moves = available_moves(state)
    for move in moves:
        new_state = deepcopy(state)
        new_state.do(move)
        _, e, n = minmax(new_state, player, d - 1, alpha, beta)
        if maximizing:
            alpha = f(alpha, e)
        else:
            beta = f(beta, e)
        evaluations[move] = e
        nn += n
        if beta <= alpha:
            break

    best = f(evaluations, key=evaluations.get)
    return best, evaluations[best], nn

def main():
    state = State()
    round = 0
    won = None
    while won is None:
        print('Round %d' % round)
        for player in state.players:
            print("Player {}".format(player.name))
            the_moves = list(available_moves(state))
            #move = random.choice(the_moves)
            depth = 3
            inf = 2 ** 64
            t0 = time.time()
            move, _, n = minmax(state, player, depth, -inf, inf)
            t1 = time.time()
            total = t1 - t0
            print("  ", move, "after", n)
            print("{:.2f}ms/node".format(total / n * 1000))
            state.do(move)
            won = winner(state)
            if won is not None:
                break
        print('---')
        round += 1
    print('Winner :', won)
    return won, state


def random_game(n_rounds):
    state = State()
    round = 0
    won = None
    for i in range(n_rounds):
        print('Round %d' % i)
        for player in state.players:
            print("Player {}".format(player.name))
            the_moves = list(available_moves(state))
            move = random.choice(the_moves)
            print("  ", move)
            state.do(move)
            won = winner(state)
            if won is not None:
                break
    print('Winner :', winner(state))
    return won, state



if __name__ == "__main__":
    main()
    #random_game()