# Multi-drone cactus sorting for "The Farmer Was Replaced".
#
# Plan:
#   1. Every column gets planted with cactus  (one drone per column)
#   2. Every row gets sorted West -> East     (one drone per row)
#   3. Every column gets sorted South -> North (one drone per column)
#   4. Wait until every cactus is fully grown (one drone per column)
#   5. Harvest once -> the whole sorted field chains together
#
# Each step must completely finish before the next one starts, otherwise
# a column drone could swap cacti while a row drone is still sorting.


# ---------------------------------------------------------------
# Movement
# ---------------------------------------------------------------

# Move the drone to tile (x, y).
def go_to(x, y):
    while get_pos_x() < x:
        move(East)
    while get_pos_x() > x:
        move(West)
    while get_pos_y() < y:
        move(North)
    while get_pos_y() > y:
        move(South)


# ---------------------------------------------------------------
# Work for ONE line (a single row or column)
# ---------------------------------------------------------------

# Plant cactus on every tile of column x.
def plant_column(x):
    n = get_world_size()
    go_to(x, 0)
    for y in range(n):
        harvest()                       # clear whatever is here
        if get_ground_type() != Grounds.Soil:
            till()                      # cactus needs soil
        plant(Entities.Cactus)
        move(North)


# Cocktail shaker sort along one line.
# fwd  = direction the sizes should grow towards (East or North)
# back = the opposite direction (West or South)
# The drone must already stand on the first tile of the line.
def sort_line(fwd, back):
    n = get_world_size()
    swapped = True
    while swapped:
        swapped = False
        # walk forward, carrying big cacti to the end
        for i in range(n - 1):
            if measure() > measure(fwd):
                swap(fwd)
                swapped = True
            move(fwd)
        if not swapped:
            break
        # walk back, carrying small cacti to the start
        for i in range(n - 1):
            if measure(back) > measure():
                swap(back)
                swapped = True
            move(back)


# Sort row y so sizes grow from West to East.
def sort_row(y):
    go_to(0, y)
    sort_line(East, West)


# Sort column x so sizes grow from South to North.
def sort_column(x):
    go_to(x, 0)
    sort_line(North, South)


# Stand on each tile of column x until that cactus is fully grown.
def wait_column(x):
    n = get_world_size()
    go_to(x, 0)
    for y in range(n):
        while not can_harvest():
            pass
        move(North)


# ---------------------------------------------------------------
# Drone helpers
# ---------------------------------------------------------------

# spawn_drone() only accepts a function with NO arguments.
# make_job wraps "do work(i)" into such a function.
def make_job(work, i):
    def job():
        work(i)
    return job


# Run work(0), work(1), ... work(n-1), spreading them over as many
# drones as possible. If no drone is free, the main drone does the job
# itself. Returns only after every job has finished.
def run_on_all_lines(work):
    n = get_world_size()
    drones = []
    for i in range(n):
        job = make_job(work, i)
        drone = spawn_drone(job)
        if drone == None:
            job()
        else:
            drones.append(drone)
    for drone in drones:
        wait_for(drone)


# ---------------------------------------------------------------
# One full cactus round
# ---------------------------------------------------------------

def cactus_round():
    run_on_all_lines(plant_column)
    run_on_all_lines(sort_row)
    run_on_all_lines(sort_column)
    run_on_all_lines(wait_column)
    go_to(0, 0)
    harvest()                           # one harvest triggers the chain


# ---------------------------------------------------------------
# Main program
# ---------------------------------------------------------------

while True:
    cactus_round()
