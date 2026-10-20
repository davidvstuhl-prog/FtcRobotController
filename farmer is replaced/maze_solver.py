# Maze solver for "The Farmer Was Replaced".
# Works on any farm size: everything is based on get_world_size().
#
# Plan:
#   1. Plant a bush and use Weird Substance on it -> a maze grows
#   2. Follow the wall on our right hand until we stand on the treasure
#   3. Harvest the treasure (gives gold), then start over


# The four directions in clockwise order.
# Turning right = one step forward in this list, turning left = one step back.
DIRECTIONS = [North, East, South, West]


# ---------------------------------------------------------------
# Making the maze
# ---------------------------------------------------------------

# How much Weird Substance a maze covering the whole farm needs.
# The bigger the farm and the more maze upgrades, the more it costs.
def substance_needed():
    return get_world_size() * 2 ** (num_unlocked(Unlocks.Mazes) - 1)


# Plant a bush under the drone and turn it into a maze.
# Returns False if we don't have enough Weird Substance.
def make_maze():
    amount = substance_needed()
    if num_items(Items.Weird_Substance) < amount:
        print("Not enough Weird Substance")
        return False
    harvest()                           # clear the tile
    plant(Entities.Bush)
    use_item(Items.Weird_Substance, amount)
    return True


# ---------------------------------------------------------------
# Solving the maze
# ---------------------------------------------------------------

# Right-hand rule: keep your right hand on the wall and walk.
# In a maze with no loops this always reaches every tile, so it
# always finds the treasure, whatever the maze size.
#
# At every step we try, in this order:
#   turn right, go straight, turn left, turn around
# and take the first direction that isn't blocked by a wall.
def solve_maze():
    facing = 0                          # index into DIRECTIONS, start facing North
    while get_entity_type() != Entities.Treasure:
        for turn in [1, 0, 3, 2]:       # right, straight, left, back
            new_facing = (facing + turn) % 4
            if move(DIRECTIONS[new_facing]):
                facing = new_facing
                break


# ---------------------------------------------------------------
# One full maze round
# ---------------------------------------------------------------

# Returns False when we run out of Weird Substance.
def maze_round():
    if not make_maze():
        return False
    solve_maze()
    harvest()                           # collect the treasure
    return True


# ---------------------------------------------------------------
# Main program
# ---------------------------------------------------------------

while maze_round():
    pass
