#!/usr/bin/env python3
"""
VALLEY LIFE  -  a playable prototype of a "do everything" survival / collecting game.

  Fish (cast + reel minigame), chop trees (timing hits), mine ore (cave), dig up treasure,
  dive for loot, farm crops (real-time growth + mutations), hunt animals, scale & cook food,
  run a restaurant, sell to wandering NPCs, hatch RNG pets, buy an upgrade tree, upgrade gear,
  and survive (health / food / water / oxygen).

  The "GEM STORE" uses FAKE placeholder prices. Nothing is ever charged - it is only there to
  show how a premium-currency shop would work.

Run:
    pip install pygame
    python valley_life.py
Delete valley_save.json to start over.
"""
import datetime
import json
import math
import os
import random
import sys

import pygame

W, H = 1280, 720
TS = 32                     # tile size in pixels
MW, MH = 140, 100           # map size in tiles
# When packaged as a Windows .exe (PyInstaller), keep the save next to the .exe, not in a temp folder.
HERE = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
SAVE_FILE = os.path.join(HERE, "valley_save.json")

WHITE = (255, 255, 255); BLACK = (0, 0, 0); GREY = (150, 150, 160)
PANEL = (30, 34, 50); PANEL2 = (44, 50, 72); PANEL3 = (66, 74, 104)
GREEN = (80, 200, 100); RED = (225, 70, 70); BLUE = (70, 150, 255); CYAN = (70, 220, 235)
ORANGE = (255, 150, 50); PURPLE = (170, 100, 255); GOLD = (255, 205, 60); PINK = (255, 110, 200)

RAR = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic"]
RCOL = {"Common": (205, 205, 205), "Uncommon": (90, 215, 90), "Rare": (80, 150, 255),
        "Epic": (185, 95, 255), "Legendary": (255, 190, 40), "Mythic": (255, 70, 170)}
RW = [55, 25, 12, 5.5, 2.2, 0.3]      # base rarity weights


def ridx(r):
    return RAR.index(r)


def clamp(v, a, b):
    return a if v < a else b if v > b else v


def shade(c, d):
    return tuple(clamp(int(k + d), 0, 255) for k in c[:3])


def fmt(n):
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1e6:.1f}M"
    if n >= 10_000:
        return f"{n / 1e3:.1f}K"
    return f"{n:,}"


def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


# ------------------------------------------------------------------ tiles
GRASS, SAND, SHALLOW, DEEP, PATH, CAVE, WALL, MOUNT, BRIDGE, PLOTT = range(10)
TILE_COL = {GRASS: (86, 162, 72), SAND: (216, 198, 134), SHALLOW: (72, 155, 215), DEEP: (34, 96, 178),
            PATH: (176, 146, 104), CAVE: (84, 78, 86), WALL: (42, 38, 48), MOUNT: (112, 112, 108),
            BRIDGE: (146, 104, 62), PLOTT: (112, 80, 50)}
WATER = (SHALLOW, DEEP)
SOLID = (WALL, MOUNT)

# ------------------------------------------------------------------ game data
# name, rarity, price, avg weight(kg), zones, extra difficulty, time, colour
FISH = [
    ("Minnow", "Common", 6, 0.2, "river", 0.0, "any", (170, 180, 170)),
    ("Bluegill", "Common", 8, 0.4, "lake", 0.0, "any", (90, 130, 200)),
    ("Perch", "Common", 10, 0.6, "lake river", 0.0, "any", (200, 190, 80)),
    ("Sardine", "Common", 9, 0.3, "deep", 0.0, "any", (160, 170, 190)),
    ("Cave Blindfish", "Common", 18, 0.5, "cave", 0.1, "any", (225, 215, 225)),
    ("Seaweed", "Common", 3, 0.3, "river lake deep", -0.2, "any", (60, 140, 60)),
    ("Old Boot", "Common", 2, 1.0, "river lake deep", -0.3, "any", (110, 80, 50)),
    ("Trout", "Uncommon", 22, 1.2, "river", 0.1, "any", (175, 140, 120)),
    ("Bass", "Uncommon", 25, 1.8, "lake", 0.1, "any", (80, 130, 70)),
    ("Mackerel", "Uncommon", 28, 1.0, "deep", 0.1, "any", (80, 120, 170)),
    ("Glow Shrimp", "Uncommon", 40, 0.1, "cave", 0.2, "any", (120, 255, 220)),
    ("Salmon", "Rare", 60, 4.0, "river", 0.2, "any", (250, 130, 110)),
    ("Catfish", "Rare", 70, 6.0, "lake", 0.2, "night", (120, 105, 80)),
    ("Tuna", "Rare", 85, 12.0, "deep", 0.3, "any", (60, 80, 140)),
    ("Pike", "Rare", 65, 5.0, "river lake", 0.3, "day", (120, 150, 90)),
    ("Crystal Eel", "Rare", 120, 2.0, "cave", 0.4, "any", (160, 220, 255)),
    ("River King", "Epic", 250, 9.0, "river", 0.4, "any", (220, 170, 60)),
    ("Moonfish", "Epic", 300, 3.0, "lake deep", 0.4, "night", (220, 220, 255)),
    ("Swordfish", "Epic", 350, 30.0, "deep", 0.5, "day", (70, 90, 160)),
    ("Magma Koi", "Epic", 400, 4.0, "cave", 0.5, "any", (255, 100, 40)),
    ("Golden Carp", "Legendary", 1200, 6.0, "river lake", 0.6, "any", (255, 210, 60)),
    ("Ghost Shark", "Legendary", 1800, 80.0, "deep", 0.7, "night", (200, 230, 255)),
    ("Lake Serpent", "Mythic", 8000, 150.0, "lake deep", 0.9, "any", (60, 200, 140)),
    ("Abyss Leviathan", "Mythic", 12000, 400.0, "cave deep", 1.0, "night", (130, 50, 170)),
]
MUTS = [("Shiny", 1.5, 70, (200, 255, 255)), ("Golden", 3, 22, GOLD), ("Rainbow", 8, 7, PINK), ("Cosmic", 20, 1, PURPLE)]
MUTCOL = {m[0]: m[3] for m in MUTS}
MUTCOL.update({"Wet": (120, 180, 255)})

# name, log value, hp, colour, rarity, spawn weight
TREES = [("Oak", 4, 6, (60, 140, 55), "Common", 50), ("Pine", 5, 8, (35, 105, 65), "Common", 30),
         ("Birch", 8, 10, (130, 185, 80), "Uncommon", 15), ("Maple", 18, 16, (215, 95, 40), "Rare", 4),
         ("Ancient", 150, 60, (245, 200, 60), "Legendary", 0.5)]
# name, tier needed, price, hp, colour, rarity, weight
ORES = [("Stone", 0, 3, 3, (135, 135, 135), "Common", 30), ("Coal", 0, 6, 5, (45, 45, 50), "Common", 25),
        ("Copper Ore", 1, 14, 8, (215, 125, 65), "Uncommon", 18), ("Iron Ore", 2, 28, 14, (205, 185, 165), "Uncommon", 12),
        ("Gold Ore", 3, 75, 24, (255, 210, 60), "Rare", 7), ("Crystal", 3, 140, 32, (140, 220, 255), "Epic", 5),
        ("Mythril", 4, 380, 55, (110, 255, 200), "Legendary", 2)]
TIER_NAMES = ["Wooden", "Copper", "Iron", "Gold", "Mythril"]
# name, rarity, price, colour
DIG = [("Dirt", "Common", 1, (120, 85, 55)), ("Pebble", "Common", 2, (160, 160, 160)), ("Worm", "Common", 3, (230, 130, 140)),
       ("Old Bottle", "Common", 5, (120, 200, 140)), ("Bone", "Uncommon", 12, (235, 230, 210)),
       ("Copper Coin", "Uncommon", 15, (210, 130, 70)), ("Arrowhead", "Uncommon", 18, (130, 130, 150)),
       ("Silver Ring", "Rare", 60, (220, 220, 235)), ("Fossil", "Rare", 80, (200, 180, 140)),
       ("Pirate Coin", "Rare", 70, (255, 200, 80)), ("Gold Idol", "Epic", 300, GOLD), ("Dino Skull", "Epic", 450, (240, 235, 220)),
       ("Ancient Crown", "Legendary", 2000, (255, 215, 90)), ("Alien Egg", "Mythic", 9000, (120, 255, 120))]
DIVE = [("Seashell", "Common", 4, (255, 220, 200)), ("Sand Dollar", "Common", 6, (230, 220, 180)),
        ("Coral", "Uncommon", 20, (255, 120, 120)), ("Pearl", "Rare", 90, (245, 245, 255)),
        ("Sunken Chest", "Epic", 500, (160, 110, 50)), ("Mermaid Scale", "Legendary", 2500, (80, 255, 220)),
        ("Trident", "Mythic", 10000, (255, 215, 60))]
ANIMALS = {
    "Rabbit": dict(hp=10, spd=120, beh="flee", dmg=0, size=9, col=(205, 195, 185), xp=6, w=40, night=40,
                   drops=[("Raw Meat", 1, 1, 1.0), ("Rabbit Foot", 1, 1, 0.25)]),
    "Deer": dict(hp=30, spd=115, beh="flee", dmg=0, size=14, col=(170, 120, 70), xp=12, w=25, night=15,
                 drops=[("Raw Meat", 2, 3, 1.0), ("Hide", 1, 1, 0.8), ("Antler", 1, 2, 0.4)]),
    "Boar": dict(hp=45, spd=95, beh="aggro", dmg=8, size=13, col=(110, 80, 60), xp=15, w=18, night=18,
                 drops=[("Raw Meat", 2, 3, 1.0), ("Hide", 1, 1, 0.6), ("Tusk", 1, 2, 0.5)]),
    "Wolf": dict(hp=50, spd=135, beh="aggro", dmg=10, size=12, col=(125, 125, 135), xp=20, w=0, night=22,
                 drops=[("Raw Meat", 1, 2, 1.0), ("Wolf Fang", 1, 1, 0.6)]),
    "Bear": dict(hp=140, spd=85, beh="aggro", dmg=20, size=20, col=(90, 60, 40), xp=50, w=4, night=4,
                 drops=[("Raw Meat", 4, 6, 1.0), ("Bear Pelt", 1, 1, 1.0)]),
    "Golden Stag": dict(hp=80, spd=150, beh="flee", dmg=0, size=15, col=(255, 210, 60), xp=150, w=0.8, night=0.8,
                        drops=[("Golden Antler", 1, 1, 1.0), ("Raw Meat", 3, 3, 1.0)]),
}
# name, seed price, grow seconds, sell, colour, gem price, hunger, thirst, rarity
CROPS = [("Carrot", 5, 20, 10, (255, 140, 40), 0, 6, 2, "Common"), ("Wheat", 8, 30, 14, (230, 200, 100), 0, 4, 0, "Common"),
         ("Corn", 15, 45, 28, (250, 220, 60), 0, 8, 2, "Common"), ("Tomato", 25, 60, 45, (230, 50, 40), 0, 6, 8, "Uncommon"),
         ("Berry", 40, 75, 65, (150, 50, 200), 0, 4, 6, "Uncommon"), ("Pumpkin", 100, 120, 180, (250, 140, 30), 0, 15, 5, "Rare"),
         ("Watermelon", 250, 180, 480, (70, 180, 70), 0, 8, 30, "Rare"),
         ("Dragonfruit", 800, 300, 1600, (240, 60, 150), 0, 12, 12, "Epic"),
         ("Starfruit", 0, 240, 4500, (255, 240, 80), 40, 20, 20, "Legendary")]
CROP = {c[0]: c for c in CROPS}
# name, ingredients, hunger, thirst, heal, base value, colour
RECIPES = [
    ("Grilled Fish", [("fillet", 1), ("wood", 1)], 30, 0, 5, 25, (230, 160, 90)),
    ("Roast Meat", [("meat", 1), ("wood", 1)], 40, 0, 10, 30, (170, 80, 50)),
    ("Veggie Stew", [("veg", 2), ("wood", 1)], 35, 20, 5, 35, (200, 120, 60)),
    ("Berry Juice", [("Berry", 2)], 0, 50, 5, 60, (200, 60, 140)),
    ("Fish Tacos", [("fillet", 1), ("Corn", 1), ("Tomato", 1), ("wood", 1)], 55, 5, 10, 90, (240, 200, 90)),
    ("Berry Pie", [("Berry", 3), ("Wheat", 2), ("wood", 1)], 50, 0, 10, 150, (170, 60, 120)),
    ("Pumpkin Soup", [("Pumpkin", 1), ("veg", 1), ("wood", 1)], 60, 25, 15, 220, (250, 150, 40)),
    ("Melon Smoothie", [("Watermelon", 1), ("Berry", 1)], 15, 100, 10, 500, (250, 110, 120)),
    ("Hunter's Feast", [("meat", 2), ("fillet", 1), ("veg", 2), ("wood", 2)], 100, 30, 50, 180, (200, 100, 60)),
]
GENERIC = {"fillet", "wood", "meat", "veg"}
QUAL = [("Burnt", 0.5, (90, 70, 60)), ("Good", 1.0, WHITE), ("Perfect", 1.6, GOLD), ("Gourmet", 2.5, PINK)]
QMULT = {q[0]: q[1] for q in QUAL}

# tools: name, coin price, gem price, stats...
RODS = [("Twig Rod", 0, 0, 0.0, 0.27, 1.00), ("Bamboo Rod", 250, 0, 0.15, 0.29, 0.90),
        ("Fiberglass Rod", 1200, 0, 0.35, 0.31, 0.80), ("Carbon Rod", 5000, 0, 0.70, 0.33, 0.70),
        ("Mythril Rod", 20000, 0, 1.20, 0.36, 0.60), ("Celestial Rod", 0, 400, 2.50, 0.42, 0.45)]
AXES = [("Stone Axe", 0, 0, 1.0), ("Copper Axe", 200, 0, 2.0), ("Iron Axe", 900, 0, 3.5), ("Steel Axe", 4000, 0, 6.0),
        ("Diamond Axe", 15000, 0, 10.0), ("Plasma Axe", 0, 350, 25.0)]
PICKS = [("Wooden Pickaxe", 0, 0, 1.0, 0), ("Copper Pickaxe", 300, 0, 2.0, 1), ("Iron Pickaxe", 1500, 0, 3.5, 2),
         ("Gold Pickaxe", 6000, 0, 6.0, 3), ("Mythril Pickaxe", 25000, 0, 10.0, 4), ("Laser Drill", 0, 400, 25.0, 4)]
SHOVELS = [("Rusty Shovel", 0, 0, 1.0, 0.0), ("Iron Shovel", 400, 0, 1.6, 0.2), ("Steel Shovel", 2000, 0, 2.4, 0.5),
           ("Golden Shovel", 9000, 0, 3.5, 1.0), ("Mega Digger", 0, 300, 6.0, 2.0)]
WEAPONS = [("Wooden Spear", 0, 0, 10, 480, 0.7), ("Stone Spear", 250, 0, 18, 520, 0.6), ("Hunting Bow", 1500, 0, 30, 750, 0.45),
           ("Crossbow", 6000, 0, 55, 850, 0.4), ("Laser Bow", 0, 350, 120, 1100, 0.18)]
BAGS = [("Pouch", 0, 0, 25), ("Satchel", 300, 0, 50), ("Rucksack", 1500, 0, 100), ("Explorer Pack", 6000, 0, 200),
        ("Bottomless Bag", 0, 250, 1000)]
TOOLS = {"rod": ("Rods", RODS), "axe": ("Axes", AXES), "pick": ("Pickaxes", PICKS), "shovel": ("Shovels", SHOVELS),
         "weapon": ("Weapons", WEAPONS), "bag": ("Backpacks", BAGS)}


def tool_desc(kind, t):
    if kind == "rod":
        return f"Luck +{int(t[3] * 100)}%   Reel zone {int(t[4] * 100)}   Bite speed x{1 / t[5]:.1f}"
    if kind == "axe":
        return f"Chop power {t[3]:g}"
    if kind == "pick":
        return f"Mine power {t[3]:g}   Can mine: {TIER_NAMES[t[4]]} tier rocks"
    if kind == "shovel":
        return f"Dig speed x{t[3]:g}   Treasure luck +{int(t[4] * 100)}%"
    if kind == "weapon":
        return f"Damage {t[3]}   Throws {1 / t[5]:.1f}/sec"
    return f"Holds {t[3]} items"


# id, name, desc, coin cost, level needed, prerequisite, column, row
SKILLS = [
    ("fish1", "Lucky Lure", "+20% fishing luck", 150, 2, None, 0, 0),
    ("fish2", "Steady Hands", "Bigger reel zone", 600, 4, "fish1", 0, 1),
    ("fish3", "Fish Whisperer", "Fish bite 30% faster", 2000, 7, "fish2", 0, 2),
    ("fish4", "Master Angler", "+60% luck, 2x mutations", 8000, 12, "fish3", 0, 3),
    ("wood1", "Sharp Edge", "+50% chop damage", 120, 2, None, 1, 0),
    ("wood2", "Lumberjack", "+1 log per tree", 500, 4, "wood1", 1, 1),
    ("wood3", "Sweet Spot", "Bigger PERFECT zone", 1800, 7, "wood2", 1, 2),
    ("wood4", "Timber!", "25% chance double logs", 6000, 11, "wood3", 1, 3),
    ("dig1", "Strong Arms", "Dig & mine 40% faster", 150, 2, None, 2, 0),
    ("dig2", "Treasure Sense", "+30% dig luck", 700, 5, "dig1", 2, 1),
    ("dig3", "Rich Veins", "+1 ore per rock", 2200, 8, "dig2", 2, 2),
    ("dig4", "Archaeologist", "+80% dig luck", 9000, 13, "dig3", 2, 3),
    ("hunt1", "Quick Throw", "Attack 30% faster", 200, 3, None, 3, 0),
    ("hunt2", "Tracker", "More animals spawn", 800, 5, "hunt1", 3, 1),
    ("hunt3", "Big Game", "Rare animals 3x more often", 2500, 9, "hunt2", 3, 2),
    ("hunt4", "Butcher", "2x meat & trophies", 7000, 12, "hunt3", 3, 3),
    ("farm1", "Green Thumb", "Crops grow 30% faster", 150, 2, None, 4, 0),
    ("farm2", "Big Harvest", "+1 crop per harvest", 900, 5, "farm1", 4, 1),
    ("farm3", "Mutation Magic", "3x crop mutations", 3000, 9, "farm2", 4, 2),
    ("farm4", "Garden Expert", "Crops grow 2x faster", 10000, 14, "farm3", 4, 3),
    ("cook1", "Home Chef", "Cooked food +25% value", 200, 3, None, 5, 0),
    ("cook2", "Popular Spot", "Diners come 2x faster", 1000, 6, "cook1", 5, 1),
    ("cook3", "Big Tipper", "Tips doubled", 3000, 9, "cook2", 5, 2),
    ("cook4", "Michelin Star", "Cooked food x2 value", 12000, 15, "cook3", 5, 3),
    ("surv1", "Iron Stomach", "Hunger/thirst 30% slower", 150, 2, None, 6, 0),
    ("surv2", "Deep Lungs", "2x oxygen underwater", 600, 4, "surv1", 6, 1),
    ("surv3", "Regeneration", "Heal 3x faster", 2000, 8, "surv2", 6, 2),
    ("surv4", "Merchant", "Everything sells +25%", 9000, 12, "surv3", 6, 3),
]
SKILL = {s[0]: s for s in SKILLS}
BRANCHES = ["Fishing", "Woodcutting", "Digging", "Hunting", "Farming", "Cooking", "Survival"]

# name, rarity, colour, bonus key, amount, description
PETS = [
    ("Bunny", "Common", (240, 240, 240), "speed", 0.08, "+8% walk speed"),
    ("Frog", "Common", (90, 200, 90), "fish_luck", 0.10, "+10% fishing luck"),
    ("Mole", "Common", (120, 90, 80), "dig_speed", 0.15, "+15% dig speed"),
    ("Duck", "Common", (250, 220, 80), "sell", 0.05, "+5% sell price"),
    ("Otter", "Uncommon", (150, 110, 80), "fish_luck", 0.25, "+25% fishing luck"),
    ("Beaver", "Uncommon", (140, 90, 50), "wood", 1, "+1 log per tree"),
    ("Fox", "Uncommon", (240, 130, 50), "hunt", 0.3, "+30% hunting damage"),
    ("Hedgehog", "Uncommon", (160, 130, 110), "dig_luck", 0.25, "+25% dig luck"),
    ("Owl", "Rare", (170, 140, 100), "xp", 0.5, "+50% XP"),
    ("Golden Retriever", "Rare", (230, 190, 90), "sell", 0.2, "+20% sell price"),
    ("Bee", "Rare", (255, 210, 40), "grow", 0.35, "Crops grow 35% faster"),
    ("Penguin", "Rare", (40, 40, 60), "oxygen", 1.0, "2x oxygen"),
    ("Panda", "Epic", (245, 245, 245), "hunger", 0.5, "Hunger drains 50% slower"),
    ("Unicorn", "Epic", (255, 170, 240), "all_luck", 0.4, "+40% ALL luck"),
    ("Kraken", "Epic", (170, 60, 120), "fish_luck", 0.8, "+80% fishing luck"),
    ("Phoenix", "Legendary", (255, 120, 40), "regen", 3.0, "Super health regen"),
    ("Dragon", "Legendary", (220, 40, 40), "all_luck", 1.0, "+100% ALL luck"),
    ("Cosmic Cat", "Mythic", (140, 90, 255), "all_luck", 2.5, "+250% ALL luck"),
]
PET = {p[0]: p for p in PETS}
EGGS = [("Common Egg", 500, 0, [60, 30, 9, 1, 0, 0], (235, 230, 210)),
        ("Rare Egg", 3000, 0, [0, 50, 35, 12, 3, 0], (100, 160, 255)),
        ("Mythic Egg", 0, 120, [0, 0, 40, 40, 17, 3], (255, 90, 200))]
GEM_PACKS = [(80, "$0.99"), (450, "$4.99"), (1000, "$9.99"), (2200, "$19.99"), (6000, "$49.99"), (14000, "$99.99")]
GEM_ITEMS = [("luck", "2x Luck Potion", "10 minutes of double luck", 50),
             ("coins", "2x Coins Potion", "10 minutes of double sell price", 60),
             ("grow", "Instant Grow", "Finish every crop right now", 25),
             ("heal", "Full Restore", "Max health, food, water, oxygen", 15),
             ("slot", "Extra Pet Slot", "Equip one more pet (max 4)", 200),
             ("vip", "VIP Pass", "Forever +50% coins & a gold crown", 500),
             ("coinsack", "Coin Sack", "Get 5,000 coins instantly", 100)]
SUPPLIES = [("Bandage", 30, 1, "Heals 40 health"), ("Water Bottle", 15, 1, "+50 water"),
            ("Snack Bar", 25, 1, "+30 food"), ("Worm", 20, 5, "5 worms = fishing bait (+luck)")]
PLOT_PRICES = [150, 300, 600, 1200, 2500, 5000]
BUYERS = [("Lumber Larry", "wood", (150, 100, 60)), ("Digger Dot", "dig", (200, 160, 90)),
          ("Miner Mo", "ore", (120, 120, 140)), ("Hungry Hank", "food", (220, 120, 80)),
          ("Fishmonger Fiona", "fish", (80, 160, 200)), ("Farmer Fran", "crop", (120, 190, 80)),
          ("Trapper Tom", "animal", (140, 90, 60))]
CATS = [("All", None), ("Fish", "fish"), ("Wood", "wood"), ("Ore", "ore"), ("Dig", "dig"), ("Animal", "animal"),
        ("Crop", "crop"), ("Food", "food"), ("Misc", "misc")]
# description, stat, amount, coins, gems, target
QUESTS = [
    ("Catch a fish! Aim at water, HOLD F, let go", "fish", 1, 50, 5, "river"),
    ("Chop 5 logs: press E at a tree on the GREEN", "logs", 5, 60, 5, "forest"),
    ("Dig up 3 things: HOLD Q on grass", "digs", 3, 60, 5, None),
    ("Sell your stuff at the MARKET", "sold", 1, 50, 5, "market"),
    ("Plant a seed: press E on a garden plot", "planted", 1, 40, 5, "garden"),
    ("Hunt an animal: CLICK to throw your spear", "kills", 1, 80, 10, None),
    ("Cook a meal at the KITCHEN", "cooked", 1, 80, 10, "cook"),
    ("Buy an upgrade at the UPGRADES hall", "skills", 1, 100, 10, "skills"),
    ("Hatch a pet at the PET HATCHERY", "hatched", 1, 100, 15, "pets"),
    ("Mine 5 ores in the CAVE (north-east)", "ores", 5, 150, 15, "cave"),
    ("Finish an order for a town NPC", "orders", 1, 150, 15, None),
    ("Open your RESTAURANT & serve a diner", "served", 1, 300, 25, "cook"),
]
BUILDINGS = [("HOME", "home", 60, 43, 5, 4, (180, 90, 70)), ("SHOP", "shop", 66, 43, 5, 4, (70, 130, 200)),
             ("MARKET", "market", 76, 43, 5, 4, (220, 170, 60)), ("UPGRADES", "skills", 82, 43, 5, 4, (130, 90, 200)),
             ("PET HATCHERY", "pets", 62, 56, 5, 4, (240, 140, 190)), ("KITCHEN", "cook", 76, 56, 6, 4, (200, 80, 60)),
             ("GEM STORE", "gems", 85, 56, 5, 4, (60, 200, 220))]
TABLES = [(74, 62), (77, 62), (80, 62), (83, 62)]

# ------------------------------------------------------------------ item database
ITEMS = {}


def reg(name, cat, base, rarity="Common", color=(200, 200, 200), tags=(), hunger=0, thirst=0, heal=0):
    ITEMS[name] = dict(cat=cat, base=base, rarity=rarity, color=color, tags=set(tags) | {name},
                       hunger=hunger, thirst=thirst, heal=heal)


for _f in FISH:
    reg(_f[0], "fish", _f[2], _f[1], _f[7], tags=("junk",) if _f[0] in ("Old Boot", "Seaweed") else ("fish",))
reg("Fish Fillet", "fish", 8, "Common", (250, 170, 150), tags=("fillet",))
reg("Fish Scales", "fish", 4, "Common", (170, 220, 230))
for _t in TREES:
    reg(_t[0] + " Log", "wood", _t[1], _t[4], shade(_t[3], -10), tags=("wood",))
for _o in ORES:
    reg(_o[0], "ore", _o[2], _o[5], _o[4])
for _d in DIG + DIVE:
    reg(_d[0], "dig", _d[2], _d[1], _d[3], tags=("bait",) if _d[0] == "Worm" else ())
reg("Raw Meat", "animal", 8, "Common", (200, 80, 80), tags=("meat",), hunger=10, heal=-5)
reg("Hide", "animal", 15, "Common", (160, 120, 80))
reg("Rabbit Foot", "animal", 30, "Uncommon", (230, 230, 230))
reg("Antler", "animal", 35, "Uncommon", (220, 200, 160))
reg("Tusk", "animal", 40, "Uncommon", (245, 240, 220))
reg("Wolf Fang", "animal", 70, "Rare", (230, 230, 240))
reg("Bear Pelt", "animal", 250, "Epic", (110, 70, 45))
reg("Golden Antler", "animal", 2500, "Legendary", GOLD)
for _c in CROPS:
    reg(_c[0], "crop", _c[3], _c[8], _c[4], tags=("veg",), hunger=_c[6], thirst=_c[7])
for _r in RECIPES:
    reg(_r[0], "food", _r[5], "Uncommon", _r[6], tags=("cooked",), hunger=_r[2], thirst=_r[3], heal=_r[4])
reg("Bandage", "misc", 10, "Common", (240, 240, 240), heal=40)
reg("Water Bottle", "misc", 5, "Common", (120, 190, 255), thirst=50)
reg("Snack Bar", "misc", 8, "Common", (200, 150, 90), hunger=30)


def make_noise(w, h, scale, seed):
    r = random.Random(seed)
    gw, gh = w // scale + 3, h // scale + 3
    g = [[r.random() for _ in range(gw)] for _ in range(gh)]

    def f(x, y):
        fx, fy = x / scale, y / scale
        x0, y0 = int(fx), int(fy)
        tx, ty = fx - x0, fy - y0
        tx = tx * tx * (3 - 2 * tx)
        ty = ty * ty * (3 - 2 * ty)
        a = g[y0][x0] + (g[y0][x0 + 1] - g[y0][x0]) * tx
        b = g[y0 + 1][x0] + (g[y0 + 1][x0 + 1] - g[y0 + 1][x0]) * tx
        return a + (b - a) * ty
    return f


def wrap(font, text, width):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if font.size(t)[0] > width and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


# ====================================================================== GAME
class Game:
    PERSIST = ["px", "py", "hp", "food", "water", "oxy", "coins", "gems", "level", "xp", "bag", "chest", "chest_cap",
               "tools", "pets", "equipped", "pet_slots", "seeds", "plots", "plots_unlocked", "stats", "quest_i",
               "quest_base", "rq", "boosts", "vip", "starter_bought", "restaurant", "tod", "day", "last_daily",
               "streak", "sel_seed"]

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Valley Life - prototype")
        self.clock = pygame.time.Clock()
        self._fonts = {}
        self.t = 0.0
        self.gen_world()
        self.reset_state()
        self.had_save = self.load()
        self.title = True
        self.menu = None
        self.tab = 0
        self.scroll = 0
        self.inv_filter = 0
        self.buttons = []
        self.popups = []
        self.notes = []
        self.floats = []
        self.parts = []
        self.banner = None
        self.shake = 0.0
        self.fish = None
        self.dig_prog = 0.0
        self.dig_tile = None
        self.cook = None
        self.hatch = None
        self.animals = []
        self.projs = []
        self.npcs = []
        self.diners = []
        self.campfires = []
        self.spawn_t = 0.0
        self.npc_t = 15.0
        self.diner_t = 6.0
        self.atk_cd = self.mine_cd = self.drink_cd = 0.0
        self.mouse = (0, 0)
        self.starter_left = 600.0
        self.last_full_offer = -999.0
        self.save_t = 0.0
        self.hurt = 0.0
        self.rain = 0.0
        self.next_rain = 150.0
        self.cam = (0.0, 0.0)
        self.pet_pos = []
        self.moving = False
        self.hover_tip = ""

    # ------------------------------------------------------------ helpers
    def font(self, size):
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]

    def text(self, s, pos, size=22, col=WHITE, anchor="tl", shadow=True):
        f = self.font(size)
        img = f.render(str(s), True, col)
        r = img.get_rect()
        setattr(r, {"tl": "topleft", "c": "center", "tr": "topright", "ml": "midleft", "mr": "midright",
                    "mt": "midtop"}[anchor], pos)
        if shadow:
            self.screen.blit(f.render(str(s), True, (0, 0, 0)), r.move(2, 2))
        self.screen.blit(img, r)
        return r

    def button(self, rect, label, cb, col=PANEL3, enabled=True, size=22, tcol=WHITE):
        r = pygame.Rect(rect)
        hover = r.collidepoint(self.mouse) and enabled
        c = col if enabled else (70, 70, 78)
        if hover:
            c = shade(c, 30)
        pygame.draw.rect(self.screen, shade(c, -50), r.move(0, 3), border_radius=10)
        pygame.draw.rect(self.screen, c, r, border_radius=10)
        pygame.draw.rect(self.screen, shade(c, 50), r, 2, border_radius=10)
        self.text(label, r.center, size, tcol if enabled else (160, 160, 160), "c")
        if enabled and cb:
            self.buttons.append((r, cb))
        return hover

    def note(self, text, col=WHITE):
        self.notes.append([text, col, 4.5])
        self.notes = self.notes[-6:]

    def float_text(self, x, y, text, col=WHITE, size=24):
        self.floats.append([x, y, text, col, 1.6, size])

    def burst(self, x, y, col, n=12, spd=120, life=0.7, size=4):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            s = random.uniform(spd * 0.3, spd)
            self.parts.append([x, y, math.cos(a) * s, math.sin(a) * s - 40, life, col, size])

    def do_banner(self, title, sub="", col=GOLD):
        self.banner = [title, sub, col, 3.0]

    def popup(self, title, lines, buttons=None, col=GOLD):
        self.popups.append(dict(title=title, lines=lines, buttons=buttons or [("OK", None, GREEN)], col=col))

    def inc(self, k, n=1):
        self.stats[k] = self.stats.get(k, 0) + n

    def has(self, sid):
        return sid in self.skills

    def pb(self, key):
        tot = 0.0
        for i in self.equipped:
            if 0 <= i < len(self.pets):
                p = PET[self.pets[i]]
                if p[3] == key:
                    tot += p[4]
        return tot

    def luck_all(self):
        return self.pb("all_luck") + (1.0 if self.boosts["luck"] > 0 else 0)

    def fish_luck(self):
        return (RODS[self.tools["rod"]][3] + 0.2 * self.has("fish1") + 0.6 * self.has("fish4")
                + self.pb("fish_luck") + self.luck_all())

    def dig_luck(self):
        return (SHOVELS[self.tools["shovel"]][4] + 0.3 * self.has("dig2") + 0.8 * self.has("dig4")
                + self.pb("dig_luck") + self.luck_all())

    def sell_mult(self):
        m = (1 + self.pb("sell")) * (1.5 if self.vip else 1) * (1.25 if self.has("surv4") else 1)
        return m * (2 if self.boosts["coins"] > 0 else 1)

    def bag_cap(self):
        return BAGS[self.tools["bag"]][3]

    @staticmethod
    def count(lst):
        return sum(s["count"] for s in lst)

    def roll_rarity(self, luck, available=range(6)):
        av = list(available)
        ws = [RW[i] * (1 + luck * i * 0.6) for i in av]
        return random.choices(av, ws)[0]

    def roll_mut(self, chance):
        if random.random() < chance:
            m = random.choices(MUTS, [x[2] for x in MUTS])[0]
            return m[0], m[1]
        return "", 1.0

    def is_night(self):
        return self.tod >= 0.72 or self.tod < 0.2

    def darkness(self):
        t = self.tod
        if 0.2 <= t < 0.65:
            a = 0.0
        elif 0.65 <= t < 0.75:
            a = (t - 0.65) / 0.1
        elif 0.1 <= t < 0.2:
            a = 1 - (t - 0.1) / 0.1
        else:
            a = 1.0
        return a * 165

    def mouse_world(self):
        return self.mouse[0] + self.cam[0], self.mouse[1] + self.cam[1]

    def tile_at(self, x, y):
        tx, ty = int(x // TS), int(y // TS)
        if 0 <= tx < MW and 0 <= ty < MH:
            return self.tiles[ty][tx]
        return MOUNT

    def solid(self, tx, ty):
        if not (0 <= tx < MW and 0 <= ty < MH):
            return True
        return self.tiles[ty][tx] in SOLID or (tx, ty) in self.blocked

    def can_walk(self, x, y, r=10):
        for cx, cy in ((x - r, y - r), (x + r, y - r), (x - r, y + r), (x + r, y + r)):
            if self.solid(int(cx // TS), int(cy // TS)):
                return False
        return True

    # ------------------------------------------------------------ item stacks
    def add_item(self, name, value, mut="", q="", count=1, lst=None):
        lst = self.bag if lst is None else lst
        cap = self.bag_cap() if lst is self.bag else self.chest_cap
        n = min(count, max(0, cap - self.count(lst)))
        if n < count and lst is self.bag:
            self.note("BACKPACK FULL! Sell stuff or get a bigger bag!", RED)
            if self.t - self.last_full_offer > 180 and self.tools["bag"] < 4:
                self.last_full_offer = self.t
                self.popup("BACKPACK FULL!", ["Your bag can't hold any more loot!",
                                              "Sell at the MARKET, store it at HOME,",
                                              "or get the BOTTOMLESS BAG (1000 slots)!"],
                           [("Bottomless Bag (250 gems)", lambda: self.buy_tool("bag", 4), PINK),
                            ("Later", None, PANEL3)], RED)
        if n <= 0:
            return 0
        for s in lst:
            if s["name"] == name and s["mut"] == mut and s["q"] == q:
                s["value"] = (s["value"] * s["count"] + value * n) / (s["count"] + n)
                s["count"] += n
                return n
        lst.append(dict(name=name, mut=mut, q=q, value=value, count=n))
        return n

    def take(self, spec, n, lst=None, dry=False):
        """Remove n units matching a tag/name (cheapest first). Returns total value or None."""
        lst = self.bag if lst is None else lst
        stacks = sorted([s for s in lst if spec in ITEMS[s["name"]]["tags"]], key=lambda s: s["value"])
        if sum(s["count"] for s in stacks) < n:
            return None
        if dry:
            return 0
        val, left = 0.0, n
        for s in stacks:
            k = min(left, s["count"])
            s["count"] -= k
            val += k * s["value"]
            left -= k
            if s["count"] <= 0:
                lst.remove(s)
            if left == 0:
                break
        return val

    def have(self, spec):
        return sum(s["count"] for s in self.bag if spec in ITEMS[s["name"]]["tags"])

    @staticmethod
    def iname(s):
        n = s["name"]
        if s["mut"]:
            n = s["mut"] + " " + n
        if s["q"]:
            n += f" ({s['q']})"
        return n

    # ------------------------------------------------------------ world generation
    def gen_world(self):
        R = random.Random(20261118)
        nb = make_noise(MW, MH, 6, 1)
        nf = make_noise(MW, MH, 10, 2)
        nr = make_noise(MW, MH, 8, 3)
        T = [[GRASS] * MW for _ in range(MH)]
        zone = {}
        for y in range(MH):
            for x in range(MW):
                if min(x, y, MW - 1 - x, MH - 1 - y) < 2 + nb(x, y) * 7:
                    T[y][x] = MOUNT
        lcx, lcy = 30, 76
        for y in range(MH):
            for x in range(MW):
                dd = ((x - lcx) / 14) ** 2 + ((y - lcy) / 10) ** 2 + (nr(x, y) - 0.5) * 0.4
                if dd < 0.4:
                    T[y][x] = DEEP
                    zone[(x, y)] = "deep"
                elif dd < 1.0:
                    T[y][x] = SHALLOW
                    zone[(x, y)] = "lake"
        for y in range(0, lcy):
            cx = int(40 + math.sin(y * 0.07) * 6 + (nr(5, y) - 0.5) * 8)
            for dx in range(-2, 3):
                x = cx + dx
                if 0 <= x < MW and T[y][x] not in WATER:
                    T[y][x] = DEEP if dx == 0 else SHALLOW
                    zone[(x, y)] = "river"
        for y in range(MH):
            for x in range(MW):
                dd = ((x - 106) / 6) ** 2 + ((y - 76) / 4.5) ** 2
                if dd < 0.3:
                    T[y][x] = DEEP
                    zone[(x, y)] = "deep"
                elif dd < 1:
                    T[y][x] = SHALLOW
                    zone[(x, y)] = "lake"
        # sand beaches
        for y in range(1, MH - 1):
            for x in range(1, MW - 1):
                if T[y][x] == GRASS and any(T[y + j][x + i] in WATER for i in (-1, 0, 1) for j in (-1, 0, 1)):
                    if R.random() < 0.85:
                        T[y][x] = SAND
        # town
        for y in range(40, 71):
            for x in range(50, 93):
                if T[y][x] not in WATER:
                    T[y][x] = GRASS
        for x in range(10, 98):
            for y in (52, 53):
                if T[y][x] in WATER:
                    T[y][x] = BRIDGE
                elif T[y][x] != MOUNT:
                    T[y][x] = PATH
        for y in range(40, 69):
            for x in (72, 73):
                T[y][x] = PATH
        # cave
        for y in range(3, 36):
            for x in range(91, 135):
                T[y][x] = WALL
        carved = set()
        for _ in range(7):
            x, y = 96, 33
            for _s in range(520):
                for j in (-1, 0, 1):
                    for i in (-1, 0, 1):
                        carved.add((x + i, y + j))
                dx, dy = R.choices([(1, 0), (-1, 0), (0, -1), (0, 1)], [3, 2, 3, 1.4])[0]
                x = clamp(x + dx, 93, 131)
                y = clamp(y + dy, 5, 33)
        for (x, y) in carved:
            T[y][x] = CAVE
        for y in range(33, 52):
            for x in (96, 97):
                T[y][x] = CAVE if y < 36 else PATH
        self.cave_entrance = (96.5 * TS, 37 * TS)
        far = max(carved, key=lambda p: dist(p[0], p[1], 96, 33))
        for y in range(far[1] - 3, far[1] + 4):
            for x in range(far[0] - 3, far[0] + 4):
                d = dist(x, y, far[0], far[1])
                if (x, y) in carved and d < 3.2:
                    T[y][x] = DEEP if d < 1.6 else SHALLOW
                    zone[(x, y)] = "cave"
        # garden plots
        self.plot_rects = []
        for r in range(2):
            for c in range(6):
                px, py = 52 + c * 3, 63 + r * 3
                for j in range(2):
                    for i in range(2):
                        T[py + j][px + i] = PLOTT
                self.plot_rects.append(pygame.Rect(px * TS, py * TS, 64, 64))
        self.tiles, self.zone = T, zone
        self.blocked = set()
        # buildings
        self.buildings = []
        for name, menu, bx, by, bw, bh, col in BUILDINGS:
            rect = pygame.Rect(bx * TS, by * TS, bw * TS, bh * TS)
            door = ((bx + bw / 2) * TS, (by + bh) * TS + 10)
            self.buildings.append(dict(name=name, menu=menu, rect=rect, door=door, col=col))
            for j in range(bh):
                for i in range(bw):
                    self.blocked.add((bx + i, by + j))
        for tx, ty in TABLES:
            self.blocked.add((tx, ty))
        # ores
        self.ores = []
        for (x, y) in sorted(carved):
            if T[y][x] != CAVE or dist(x, y, 96, 33) < 5 or R.random() > 0.16:
                continue
            if not any(T[y + j][x + i] == WALL for i in (-1, 0, 1) for j in (-1, 0, 1)):
                continue
            d = dist(x, y, 96, 33) / 35
            ws = [o[6] * (1 + d * 3) ** (k / 2) for k, o in enumerate(ORES)]
            k = R.choices(range(len(ORES)), ws)[0]
            self.ores.append(dict(x=x, y=y, o=k, hp=ORES[k][3], respawn=0.0))
            self.blocked.add((x, y))
        for _ in range(400):
            if sum(1 for o in self.ores if o["y"] > 36) >= 30:
                break
            x, y = R.randrange(MW), R.randrange(MH)
            if T[y][x] == GRASS and min(x, y, MW - 1 - x, MH - 1 - y) < 14 and not (48 <= x <= 94 and 38 <= y <= 72) \
                    and (x, y) not in self.blocked and y > 36:
                k = R.choice([0, 0, 1, 1, 2])
                self.ores.append(dict(x=x, y=y, o=k, hp=ORES[k][3], respawn=0.0))
                self.blocked.add((x, y))
        # trees
        self.trees = []
        for y in range(MH):
            for x in range(MW):
                if T[y][x] != GRASS or (48 <= x <= 94 and 38 <= y <= 72) or (x, y) in self.blocked:
                    continue
                n = nf(x, y)
                p = 0.5 if n > 0.58 else 0.22 if n > 0.5 else 0.025
                if R.random() < p:
                    k = R.choices(range(len(TREES)), [t[5] for t in TREES])[0]
                    self.trees.append(dict(x=x, y=y, t=k, hp=TREES[k][2], stump=0.0))
                    self.blocked.add((x, y))
        self.grass_tiles = [(x, y) for y in range(MH) for x in range(MW) if T[y][x] == GRASS
                            and (x, y) not in self.blocked and not (48 <= x <= 94 and 38 <= y <= 72)]
        self.water_tiles = [(x, y) for y in range(MH) for x in range(MW) if T[y][x] in WATER]
        self.shadows = []
        for _ in range(60):
            x, y = R.choice(self.water_tiles)
            self.shadows.append([x * TS + 16, y * TS + 16, R.uniform(-20, 20), R.uniform(-20, 20)])
        self.holes = {}
        self.sparkles = set()
        self.spawn = (62.5 * TS, 47 * TS + 18)
        bridge = next((x, 52) for x in range(10, 98) if T[52][x] == BRIDGE)
        self.poi = {"river": ((bridge[0] + 0.5) * TS, 51.5 * TS), "cave": self.cave_entrance,
                    "garden": self.plot_rects[0].center}
        for b in self.buildings:
            self.poi[b["menu"]] = b["door"]
        # pre-render map
        surf = pygame.Surface((MW * TS, MH * TS))
        for y in range(MH):
            for x in range(MW):
                t = T[y][x]
                c = shade(TILE_COL[t], R.randint(-8, 8))
                X, Y = x * TS, y * TS
                surf.fill(c, (X, Y, TS, TS))
                if t == GRASS:
                    for _ in range(3):
                        gx, gy = X + R.randint(2, 29), Y + R.randint(5, 29)
                        pygame.draw.line(surf, shade(c, -28), (gx, gy), (gx + R.randint(-2, 2), gy - 5))
                    if R.random() < 0.05:
                        fc = R.choice([(255, 240, 120), (255, 150, 200), (200, 200, 255), (255, 255, 255)])
                        pygame.draw.circle(surf, fc, (X + R.randint(6, 26), Y + R.randint(6, 26)), 3)
                elif t == SAND:
                    for _ in range(4):
                        surf.fill(shade(c, -25), (X + R.randint(2, 29), Y + R.randint(2, 29), 2, 2))
                elif t == MOUNT:
                    pygame.draw.polygon(surf, shade(c, 18), [(X, Y + TS), (X + 16, Y + R.randint(0, 10)), (X + TS, Y + TS)])
                    pygame.draw.polygon(surf, shade(c, -12), [(X + 16, Y + 6), (X + TS, Y + TS), (X + 20, Y + TS)])
                elif t == WALL:
                    for _ in range(3):
                        surf.fill(shade(c, R.randint(-10, 18)), (X + R.randint(0, 22), Y + R.randint(0, 22), 10, 8))
                elif t == CAVE:
                    for _ in range(3):
                        surf.fill(shade(c, -18), (X + R.randint(2, 28), Y + R.randint(2, 28), 3, 3))
                elif t == PATH:
                    for _ in range(3):
                        pygame.draw.circle(surf, shade(c, -22), (X + R.randint(4, 28), Y + R.randint(4, 28)), 2)
                elif t == BRIDGE:
                    for i in range(0, TS, 8):
                        pygame.draw.line(surf, shade(c, -35), (X + i, Y), (X + i, Y + TS), 2)
                elif t == PLOTT:
                    for i in range(4, TS, 8):
                        pygame.draw.line(surf, shade(c, -25), (X, Y + i), (X + TS, Y + i), 2)
                elif t in WATER:
                    if R.random() < 0.3:
                        pygame.draw.line(surf, shade(c, 25), (X + 6, Y + 14), (X + 18, Y + 14), 2)
        self.map_surf = surf
        mini = pygame.Surface((MW, MH))
        for y in range(MH):
            for x in range(MW):
                mini.set_at((x, y), TILE_COL[T[y][x]])
        for t in self.trees:
            mini.set_at((t["x"], t["y"]), (40, 100, 40))
        for b in self.buildings:
            r = b["rect"]
            mini.fill(b["col"], (r.x // TS, r.y // TS, r.w // TS, r.h // TS))
        self.mini = pygame.transform.scale(mini, (MW * 3 // 2, MH * 3 // 2))

    # ------------------------------------------------------------ state / save
    def reset_state(self):
        self.px, self.py = self.spawn
        self.hp = self.food = self.water = self.oxy = 100.0
        self.coins, self.gems, self.level, self.xp = 50, 25, 1, 0.0
        self.bag, self.chest, self.chest_cap = [], [], 100
        self.tools = dict(rod=0, axe=0, pick=0, shovel=0, weapon=0, bag=0)
        self.skills, self.discovered = set(), set()
        self.pets, self.equipped, self.pet_slots = [], [], 1
        self.seeds = {"Carrot": 5, "Wheat": 3}
        self.plots = [dict(crop=None, prog=0.0) for _ in range(12)]
        self.plots_unlocked = 6
        self.stats = {}
        self.quest_i, self.quest_base, self.rq = 0, 0, None
        self.boosts = {"luck": 0.0, "coins": 0.0}
        self.vip = self.starter_bought = self.restaurant = False
        self.tod, self.day, self.last_daily, self.streak, self.sel_seed = 0.28, 1, "", 0, 0
        self.facing = (0, 1)

    def save(self):
        d = {k: getattr(self, k) for k in self.PERSIST}
        d["skills"] = sorted(self.skills)
        d["discovered"] = sorted(self.discovered)
        try:
            with open(SAVE_FILE, "w") as fh:
                json.dump(d, fh)
        except OSError:
            pass

    def load(self):
        if not os.path.exists(SAVE_FILE):
            return False
        try:
            with open(SAVE_FILE) as fh:
                d = json.load(fh)
            for k in self.PERSIST:
                if k in d:
                    setattr(self, k, d[k])
            self.skills = set(d.get("skills", []))
            self.discovered = set(d.get("discovered", []))
            self.bag = [s for s in self.bag if s["name"] in ITEMS]
            self.chest = [s for s in self.chest if s["name"] in ITEMS]
            return True
        except (OSError, ValueError, KeyError, TypeError):
            self.reset_state()
            return False

    # ------------------------------------------------------------ start / popups
    def start(self, new=False):
        if new:
            self.reset_state()
            self.had_save = False
        self.title = False
        if not self.starter_bought:
            self.popup("STARTER PACK  -90% !!!", ["500 GEMS + Bamboo Rod + 1,000 coins", "Normally $9.99 ... TODAY ONLY $0.99",
                                                  "(Fake demo price - nothing is ever charged)"],
                       [("GET IT! (pretend $0.99)", self.buy_starter, PINK), ("Maybe later", None, PANEL3)], PINK)
        today = datetime.date.today()
        if self.last_daily != str(today):
            yest = str(today - datetime.timedelta(days=1))
            self.streak = self.streak + 1 if self.last_daily == yest else 1
            self.last_daily = str(today)
            s = min(self.streak, 7)
            self.coins += 100 * s
            self.gems += 5 * s
            self.popup(f"DAILY REWARD - DAY {self.streak}!", [f"+{100 * s} coins   +{5 * s} gems",
                                                              "Come back tomorrow for an even bigger reward!"],
                       [("COLLECT!", None, GREEN)], GOLD)
        if not self.had_save:
            self.show_help()

    def show_help(self):
        self.popup("HOW TO PLAY", ["WASD / Arrows - walk      SHIFT - sprint",
                                   "E - use stuff: chop tree, mine rock, plant/harvest, drink, talk, enter",
                                   "HOLD F, aim with mouse, let go - cast rod.  Press F/SPACE on the  !",
                                   "Reeling: HOLD SPACE or mouse - keep the fish in the green box",
                                   "HOLD Q - dig up treasure (or dive for loot in deep water)",
                                   "LEFT CLICK - throw spear (hunting)    R - eat best food",
                                   "B - build campfire (3 logs, cook anywhere)   Z - change seed",
                                   "TAB - backpack   K - upgrades   P - pets   G - gem store   H - help",
                                   "Watch your HEALTH, FOOD, WATER and OXYGEN bars!"],
                   [("LET'S GO!", None, GREEN)], CYAN)

    def buy_starter(self):
        def ok():
            self.gems += 500
            self.coins += 1000
            self.tools["rod"] = max(self.tools["rod"], 1)
            self.starter_bought = True
            self.do_banner("STARTER PACK!", "+500 gems  +1,000 coins  +Bamboo Rod", PINK)
        self.fake_buy("$0.99", "Starter Pack", ok)

    def fake_buy(self, price, what, fn):
        def go():
            fn()
            self.note("Fake purchase done - no money was used!", GREEN)
        self.popup("DEMO STORE - NOT REAL MONEY", [f"Item: {what}", f"Pretend price: {price}",
                                                     "This prototype has no real payments.", "Nothing will be charged. Ever."],
                   [("Pretend to buy!", go, GREEN), ("Cancel", None, PANEL3)], CYAN)

    def need_gems(self, cost):
        self.popup("NOT ENOUGH GEMS!", [f"You need {cost} gems but you only have {self.gems}.",
                                        "Get more in the GEM STORE!"],
                   [("Open Gem Store", lambda: self.open_menu("gems"), PINK), ("Cancel", None, PANEL3)], PINK)

    def open_menu(self, m):
        self.menu = m
        self.tab = 0
        self.scroll = 0
        self.fish = None

    def close_menu(self):
        self.menu = None

    # ------------------------------------------------------------ xp / quests
    def xp_need(self):
        return int(40 * self.level ** 1.45)

    def gain_xp(self, n):
        self.xp += n * (1 + self.pb("xp"))
        while self.xp >= self.xp_need():
            self.xp -= self.xp_need()
            self.level += 1
            self.gems += 5
            self.hp = 100
            self.do_banner(f"LEVEL {self.level}!", "+5 gems  -  new upgrades unlocked!", CYAN)
            self.burst(self.px, self.py, CYAN, 30, 220)

    def make_rq(self):
        opts = [("Catch {} fish", "fish", 5, 15), ("Chop {} logs", "logs", 15, 40), ("Dig up {} things", "digs", 8, 20),
                ("Mine {} ores", "ores", 10, 30), ("Hunt {} animals", "kills", 3, 8), ("Harvest {} crops", "harvested", 10, 25),
                ("Cook {} meals", "cooked", 3, 8), ("Serve {} diners", "served", 3, 8), ("Finish {} NPC orders", "orders", 2, 4)]
        d, s, a, b = random.choice(opts)
        n = random.randint(a, b) * (1 + self.level // 10)
        return [d.format(n), s, n, int(n * 15 * (1 + self.level * 0.2)), 5 + random.randint(0, 10), None]

    def cur_quest(self):
        if self.quest_i < len(QUESTS):
            return QUESTS[self.quest_i]
        if not self.rq:
            self.rq = self.make_rq()
            self.quest_base = self.stats.get(self.rq[1], 0)
        return self.rq

    def check_quest(self):
        desc, stat, amt, c, g, _ = self.cur_quest()
        if self.stats.get(stat, 0) - self.quest_base >= amt:
            self.coins += c
            self.gems += g
            self.do_banner("QUEST COMPLETE!", f"+{c} coins   +{g} gems", GREEN)
            self.burst(self.px, self.py, GOLD, 30, 200)
            if self.quest_i < len(QUESTS):
                self.quest_i += 1
            self.rq = None
            nq = self.cur_quest()
            self.quest_base = self.stats.get(nq[1], 0)

    def quest_target(self):
        tgt = self.cur_quest()[5]
        if tgt == "forest":
            best, bd = None, 1e9
            for t in self.trees:
                if t["stump"] <= 0:
                    d = dist(t["x"] * TS, t["y"] * TS, self.px, self.py)
                    if d < bd:
                        best, bd = t, d
            return (best["x"] * TS + 16, best["y"] * TS + 16) if best else None
        return self.poi.get(tgt) if tgt else None

    def rare_fx(self, name, ri, x, y):
        if ri >= 3:
            self.do_banner(f"{RAR[ri].upper()}!!", name, RCOL[RAR[ri]])
            self.shake = 0.25 + 0.15 * (ri - 3)
            self.burst(x, y, RCOL[RAR[ri]], 25 + ri * 8, 260)
        if ri == 4:
            self.gems += 5
            self.note("Legendary bonus: +5 gems!", GOLD)
        if ri == 5:
            self.gems += 25
            self.note("MYTHIC bonus: +25 gems!!!", PINK)

    # ------------------------------------------------------------ context / interact
    def near_building(self):
        for b in self.buildings:
            if dist(self.px, self.py, *b["door"]) < 58:
                return b
        return None

    def near_plot(self):
        for i, r in enumerate(self.plot_rects):
            if r.inflate(24, 24).collidepoint(self.px, self.py):
                return i
        return None

    def near_tree(self):
        best, bd = None, 54
        for t in self.trees:
            if t["stump"] > 0:
                continue
            d = dist(t["x"] * TS + 16, t["y"] * TS + 16, self.px, self.py)
            if d < bd:
                best, bd = t, d
        return best

    def near_ore(self):
        best, bd = None, 54
        for o in self.ores:
            if o["respawn"] > 0:
                continue
            d = dist(o["x"] * TS + 16, o["y"] * TS + 16, self.px, self.py)
            if d < bd:
                best, bd = o, d
        return best

    def near_water(self):
        tx, ty = int(self.px // TS), int(self.py // TS)
        return any(0 <= tx + i < MW and 0 <= ty + j < MH and self.tiles[ty + j][tx + i] in WATER
                   for i in (-1, 0, 1) for j in (-1, 0, 1))

    def context(self):
        b = self.near_building()
        if b:
            return "bld", b, f"[E] Enter {b['name']}"
        for n in self.npcs:
            if n["state"] == "wait" and dist(n["x"], n["y"], self.px, self.py) < 52:
                return "npc", n, f"[E] Give {n['cnt']}x {n['item']} to {n['name']}"
        for d in self.diners:
            if dist(d["x"], d["y"], self.px, self.py) < 56:
                return "diner", d, f"[E] Serve {d['dish']}"
        i = self.near_plot()
        if i is not None:
            p = self.plots[i]
            if i >= self.plots_unlocked:
                return "plot", i, "Locked plot - buy it in the SHOP"
            if p["crop"] is None:
                return "plot", i, f"[E] Plant {CROPS[self.sel_seed][0]}  (Z = change seed)"
            if p["prog"] >= 1:
                return "plot", i, f"[E] Harvest {p['crop']}!"
            return "plot", i, f"{p['crop']} growing... {int(p['prog'] * 100)}%"
        for c in self.campfires:
            if dist(c[0], c[1], self.px, self.py) < 50:
                return "fire", c, "[E] Cook at campfire"
        t = self.near_tree()
        if t:
            return "tree", t, f"[E] Chop {TREES[t['t']][0]} - hit when the needle is GREEN!"
        o = self.near_ore()
        if o:
            return "ore", o, f"[Hold E] Mine {ORES[o['o']][0]}"
        if self.near_water() and self.tile_at(self.px, self.py) != DEEP:
            return "water", None, "[E] Drink water    [Hold F] Fish"
        if self.tile_at(self.px, self.py) == DEEP:
            return "swim", None, "Swimming! [Hold Q] Dive for treasure - watch your OXYGEN!"
        return None, None, ""

    def interact(self):
        kind, obj, _ = self.context()
        if kind == "bld":
            self.open_menu(obj["menu"])
        elif kind == "npc":
            self.fulfill(obj)
        elif kind == "diner":
            self.serve(obj)
        elif kind == "plot":
            self.plot_action(obj)
        elif kind == "fire":
            self.open_menu("cook")
        elif kind == "tree":
            self.chop(obj)
        elif kind == "ore":
            self.mine(obj)
        elif kind == "water":
            if self.drink_cd <= 0:
                self.water = min(100, self.water + 25)
                self.drink_cd = 0.4
                self.float_text(self.px, self.py - 30, "+25 water", BLUE)

    # ------------------------------------------------------------ fishing
    def cast_power(self):
        x = ((self.t - self.fish["t0"]) * 1.3) % 2
        return 1 - abs(x - 1)

    def fish_down(self):
        if self.fish is None:
            if self.tile_at(self.px, self.py) == DEEP:
                self.note("You can't fish while swimming!", ORANGE)
                return
            self.fish = {"s": "charge", "t0": self.t}
        elif self.fish["s"] == "bite":
            self.hook()
        elif self.fish["s"] == "wait":
            self.fish = None
            self.note("Reeled the line back in.")

    def fish_up(self):
        f = self.fish
        if not f or f["s"] != "charge":
            return
        p = self.cast_power()
        mx, my = self.mouse_world()
        ang = math.atan2(my - self.py, mx - self.px)
        d = 40 + p * 240
        spot = self.find_cast_spot(ang, d)
        if spot:
            bx, by = spot
            zone = self.zone.get((int(bx // TS), int(by // TS)), "river")
            bait = self.take("bait", 1) is not None
            lure = RODS[self.tools["rod"]][5] * (0.7 if self.has("fish3") else 1) * (0.75 if self.rain > 0 else 1)
            self.fish = dict(s="wait", bx=bx, by=by, zone=zone, t=random.uniform(2.0, 6.5) * lure, perfect=p > 0.88, bait=bait)
            self.burst(bx, by, (200, 230, 255), 10, 90)
            if p > 0.88:
                self.float_text(self.px, self.py - 40, "PERFECT CAST! +luck", GOLD)
            if bait:
                self.float_text(self.px, self.py - 60, "Worm bait used +luck", PINK, 20)
        else:
            self.fish = None
            self.note("No water there! Point your MOUSE toward water.", ORANGE)

    def find_cast_spot(self, ang, d):
        """Forgiving cast: return the water tile centre closest to where the cast was aimed, or None."""
        def water_center(x, y):
            tx, ty = int(x // TS), int(y // TS)
            if 0 <= tx < MW and 0 <= ty < MH and self.tiles[ty][tx] in WATER:
                return tx * TS + 16.0, ty * TS + 16.0
            return None
        tx_, ty_ = self.px + math.cos(ang) * d, self.py + math.sin(ang) * d
        best, bd = None, 1e9
        # 1) the landing point, a ring around it, and every point along the cast line
        pts = [(tx_, ty_)]
        for r in (16, 32, 48, 64):
            for k in range(12):
                a = k * math.pi / 6
                pts.append((tx_ + math.cos(a) * r, ty_ + math.sin(a) * r))
        for s in range(20, int(d) + 72, 8):
            pts.append((self.px + math.cos(ang) * s, self.py + math.sin(ang) * s))
        for x, y in pts:
            c = water_center(x, y)
            if c:
                dd = dist(c[0], c[1], tx_, ty_)
                if dd < bd:
                    best, bd = c, dd
        if best:
            return best
        # 2) still nothing: sweep up to 70 degrees either side of the aim
        for k in range(1, 15):
            for sgn in (1, -1):
                a = ang + sgn * k * math.radians(5)
                for s in range(40, 300, 12):
                    c = water_center(self.px + math.cos(a) * s, self.py + math.sin(a) * s)
                    if c:
                        return c
        return None

    def roll_fish(self, zone, perfect, bait):
        night = self.is_night()
        cands = [f for f in FISH if zone in f[4].split() and (f[6] == "any" or (f[6] == "night") == night)]
        luck = self.fish_luck() + (0.25 if perfect else 0) + (0.35 if bait else 0)
        ri = self.roll_rarity(luck, sorted(set(ridx(f[1]) for f in cands)))
        f = random.choice([c for c in cands if ridx(c[1]) == ri])
        weight = f[3] * random.lognormvariate(0, 0.35)
        mut, mm = self.roll_mut(0.05 * (2 if self.has("fish4") else 1) * (1 + luck * 0.3))
        return dict(name=f[0], ri=ri, weight=weight, value=f[2] * (0.7 + 0.3 * weight / f[3]) * mm, mut=mut, diff=f[5])

    def hook(self):
        f = self.fish
        fi = self.roll_fish(f["zone"], f["perfect"], f["bait"])
        w = RODS[self.tools["rod"]][4] + (0.05 if self.has("fish2") else 0)
        self.fish = dict(s="reel", fish=fi, pos=0.5, vel=0.0, fpos=random.uniform(0.2, 0.8), ft=0.5, fnext=0.0,
                         prog=0.3, w=w, bx=f["bx"], by=f["by"])

    def update_fish(self, dt, keys):
        f = self.fish
        if not f:
            return
        if f["s"] == "wait":
            f["t"] -= dt
            if f["t"] <= 0:
                f["s"] = "bite"
                f["t"] = 1.1
                self.burst(f["bx"], f["by"], WHITE, 14, 120)
        elif f["s"] == "bite":
            f["t"] -= dt
            if f["t"] <= 0:
                self.fish = None
                self.note("Too slow! The fish got away...", ORANGE)
        elif f["s"] == "reel":
            hold = keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0] or keys[pygame.K_f]
            f["vel"] = clamp(f["vel"] + (2.0 if hold else -1.7) * dt, -0.85, 0.85)
            f["pos"] += f["vel"] * dt
            half = f["w"] / 2
            if f["pos"] < half:
                f["pos"], f["vel"] = half, 0
            if f["pos"] > 1 - half:
                f["pos"], f["vel"] = 1 - half, 0
            fi = f["fish"]
            f["fnext"] -= dt
            if f["fnext"] <= 0:
                # swim a short way from where it is (no teleporting across the bar), then pause a bit
                f["ft"] = clamp(f["fpos"] + random.uniform(-0.35, 0.35), 0.05, 0.95)
                f["fnext"] = random.uniform(0.9, 2.0) / (1 + fi["ri"] * 0.18)
            sp = 0.14 + fi["ri"] * 0.07 + fi["diff"] * 0.22
            f["fpos"] += clamp(f["ft"] - f["fpos"], -sp * dt, sp * dt)
            inside = abs(f["fpos"] - f["pos"]) < half
            f["prog"] += (0.13 if inside else -(0.07 + 0.035 * fi["ri"])) * dt
            if f["prog"] >= 1:
                self.catch(fi)
                self.fish = None
            elif f["prog"] <= 0:
                self.fish = None
                self.note("The fish broke free! Try again!", ORANGE)

    def catch(self, fi):
        if not self.add_item(fi["name"], fi["value"], mut=fi["mut"]):
            return
        self.inc("fish")
        self.gain_xp(4 * (fi["ri"] + 1) ** 2)
        if fi["name"] not in self.discovered:
            self.discovered.add(fi["name"])
            self.note(f"NEW FISH DISCOVERED: {fi['name']}!  ({len(self.discovered)}/{len(FISH)})", CYAN)
        label = (fi["mut"] + " " if fi["mut"] else "") + fi["name"]
        self.float_text(self.px, self.py - 40, f"{label} {fi['weight']:.1f}kg", RCOL[RAR[fi["ri"]]], 28)
        self.note(f"Caught {label} ({RAR[fi['ri']]}) worth {fmt(fi['value'])}c", RCOL[RAR[fi["ri"]]])
        self.burst(self.px, self.py, RCOL[RAR[fi["ri"]]], 14, 140)
        self.rare_fx(label, fi["ri"], self.px, self.py)

    # ------------------------------------------------------------ chopping / mining / digging
    def chop_zone(self):
        return 0.14 + (0.1 if self.has("wood3") else 0)

    def needle(self, t=None):
        # Even speed back and forth (a sine wave rushed through the middle and made PERFECT hard to hit).
        x = ((self.t if t is None else t) * 0.85) % 2
        return x if x < 1 else 2 - x

    def chop(self, t):
        # Count the hit if the needle was in the green at any moment in the last 0.12s (makes up for input lag).
        crit = any(abs(self.needle(self.t - k * 0.02) - 0.5) < self.chop_zone() / 2 for k in range(7))
        dmg = AXES[self.tools["axe"]][3] * (1.5 if self.has("wood1") else 1) * (3 if crit else 1)
        t["hp"] -= dmg
        x, y = t["x"] * TS + 16, t["y"] * TS + 10
        self.burst(x, y, (140, 100, 60), 6, 90, 0.5, 3)
        self.burst(x, y - 20, TREES[t["t"]][3], 5, 70, 0.6, 3)
        self.float_text(x, y - 30, ("PERFECT! -" if crit else "-") + f"{dmg:g}", GOLD if crit else WHITE, 26 if crit else 20)
        if crit:
            self.shake = 0.12
        if t["hp"] <= 0:
            name, val, hp, col, rar, _ = TREES[t["t"]]
            n = 1 + self.has("wood2") + int(self.pb("wood"))
            if self.has("wood4") and random.random() < 0.25:
                n *= 2
                self.float_text(x, y - 55, "TIMBER! x2", ORANGE, 30)
            got = self.add_item(name + " Log", val * random.uniform(0.9, 1.15), count=n)
            self.inc("logs", got)
            self.gain_xp(2 * got * (t["t"] + 1))
            self.note(f"+{got} {name} Log", (200, 160, 110))
            t["stump"] = 180 if t["t"] == 4 else 45
            self.burst(x, y, col, 25, 160)
            self.rare_fx("Ancient Tree felled!", ridx(rar), x, y)

    def mine(self, o):
        if self.mine_cd > 0:
            return
        name, tier, price, hp, col, rar, _ = ORES[o["o"]]
        pick = PICKS[self.tools["pick"]]
        self.mine_cd = 0.4 / (1.4 if self.has("dig1") else 1)
        x, y = o["x"] * TS + 16, o["y"] * TS + 16
        if pick[4] < tier:
            self.float_text(x, y - 20, f"Need a {TIER_NAMES[tier]} Pickaxe!", RED, 22)
            return
        o["hp"] -= pick[3] * (1.4 if self.has("dig1") else 1)
        self.burst(x, y, col, 6, 100, 0.4, 3)
        self.shake = max(self.shake, 0.05)
        if o["hp"] <= 0:
            n = 1 + self.has("dig3") + random.randint(0, 1)
            got = self.add_item(name, price * random.uniform(0.9, 1.2), count=n)
            self.inc("ores", got)
            self.gain_xp(3 * got * (tier + 1))
            self.note(f"+{got} {name}", col)
            self.float_text(x, y - 20, f"+{got} {name}", RCOL[rar])
            o["respawn"] = 60
            o["hp"] = hp
            self.rare_fx(name, ridx(rar), x, y)

    def finish_dig(self, tx, ty, dive):
        x, y = tx * TS + 16, ty * TS + 16
        luck = self.dig_luck()
        if (tx, ty) in self.sparkles:
            self.sparkles.discard((tx, ty))
            luck += 1.5
            self.float_text(x, y - 50, "SPARKLE SPOT BONUS!", GOLD, 24)
        if not dive and self.tiles[ty][tx] == CAVE and random.random() < 0.4:
            ok = [o for o in ORES if o[1] <= PICKS[self.tools["pick"]][4]]
            o = random.choices(ok, [k[6] for k in ok])[0]
            name, ri, value, col = o[0], ridx(o[5]), o[2], o[4]
        else:
            table = DIVE if dive else DIG
            ri = self.roll_rarity(luck, sorted(set(ridx(d[1]) for d in table)))
            d = random.choice([d for d in table if ridx(d[1]) == ri])
            name, value, col = d[0], d[2], d[3]
        mut, mm = self.roll_mut(0.03 * (1 + luck * 0.3))
        got = self.add_item(name, value * mm * random.uniform(0.9, 1.2), mut=mut)
        if not dive:
            self.holes[(tx, ty)] = 90.0
        if got:
            self.inc("digs")
            self.gain_xp(3 * (ri + 1))
            label = (mut + " " if mut else "") + name
            self.float_text(x, y - 30, f"Found: {label}!", RCOL[RAR[ri]], 26)
            self.note(f"Dug up {label} ({RAR[ri]})", RCOL[RAR[ri]])
            self.burst(x, y, col, 12, 120)
            self.rare_fx(label, ri, x, y)

    def update_dig(self, dt, keys):
        tx, ty = int(self.px // TS), int(self.py // TS)
        t = self.tiles[ty][tx]
        if not keys[pygame.K_q] or self.fish:
            self.dig_prog = max(0.0, self.dig_prog - dt)
            return
        if self.dig_tile != (tx, ty):
            self.dig_tile = (tx, ty)
            self.dig_prog = 0.0
        if t == DEEP:
            self.dig_prog += dt / 3.0
            self.oxy -= 8 * dt
            if random.random() < 0.3:
                self.parts.append([self.px + random.uniform(-8, 8), self.py, 0, -60, 0.6, (200, 230, 255), 3])
            if self.dig_prog >= 1:
                self.dig_prog = 0
                self.finish_dig(tx, ty, True)
        elif t in (GRASS, SAND, CAVE) and (tx, ty) not in self.holes:
            rate = SHOVELS[self.tools["shovel"]][3] * (1.4 if self.has("dig1") else 1) * (1 + self.pb("dig_speed")) / 2.0
            self.dig_prog += dt * rate
            if random.random() < 0.4:
                self.parts.append([self.px + random.uniform(-10, 10), self.py + 10, random.uniform(-60, 60), -90, 0.5,
                                   (120, 85, 55), 3])
            if self.dig_prog >= 1:
                self.dig_prog = 0
                self.finish_dig(tx, ty, False)
        else:
            self.dig_prog = 0

    # ------------------------------------------------------------ farming
    def plot_action(self, i):
        if i >= self.plots_unlocked:
            self.note("This plot is locked. Buy it in the SHOP (Supplies tab).", ORANGE)
            return
        p = self.plots[i]
        r = self.plot_rects[i]
        if p["crop"] is None:
            sel = CROPS[self.sel_seed][0]
            if self.seeds.get(sel, 0) <= 0:
                sel = next((c[0] for c in CROPS if self.seeds.get(c[0], 0) > 0), None)
            if not sel:
                self.note("No seeds! Buy some at the SHOP.", ORANGE)
                return
            self.seeds[sel] -= 1
            p["crop"], p["prog"] = sel, 0.0
            self.inc("planted")
            self.burst(r.centerx, r.centery, (120, 85, 55), 10, 80)
            self.float_text(r.centerx, r.y, f"Planted {sel}", GREEN)
        elif p["prog"] >= 1:
            c = CROP[p["crop"]]
            n = 1 + self.has("farm2") + random.randint(0, 1)
            m = 3 if self.has("farm3") else 1
            roll = random.random()
            if roll < 0.01 * m:
                mut, mm = "Rainbow", 15
            elif roll < 0.06 * m:
                mut, mm = "Golden", 5
            elif self.rain > 0 and random.random() < 0.3:
                mut, mm = "Wet", 2
            else:
                mut, mm = "", 1
            got = self.add_item(c[0], c[3] * mm * random.uniform(0.9, 1.1), mut=mut, count=n)
            if got:
                self.inc("harvested", got)
                self.gain_xp(3 * got * (ridx(c[8]) + 1))
                label = (mut + " " if mut else "") + c[0]
                self.float_text(r.centerx, r.y, f"+{got} {label}", MUTCOL.get(mut, c[4]), 26)
                self.burst(r.centerx, r.centery, c[4], 16, 120)
                if mut in ("Golden", "Rainbow"):
                    self.do_banner(f"{mut.upper()} {c[0].upper()}!", "Mutated crops sell for way more!", MUTCOL[mut])
                if random.random() < 0.3:
                    self.seeds[c[0]] = self.seeds.get(c[0], 0) + 1
                    self.note(f"Found a {c[0]} seed!", GREEN)
                p["crop"], p["prog"] = None, 0.0
        else:
            self.note(f"{p['crop']} is {int(p['prog'] * 100)}% grown. Patience!  (or Instant Grow in GEM STORE)")

    def grow_mult(self):
        return ((1.3 if self.has("farm1") else 1) * (2 if self.has("farm4") else 1) * (1 + self.pb("grow"))
                * (1.5 if self.rain > 0 else 1))

    # ------------------------------------------------------------ hunting
    def attack(self):
        if self.atk_cd > 0 or self.tile_at(self.px, self.py) == DEEP:
            return
        wpn = WEAPONS[self.tools["weapon"]]
        mx, my = self.mouse_world()
        a = math.atan2(my - self.py, mx - self.px)
        self.projs.append(dict(x=self.px, y=self.py - 6, vx=math.cos(a) * wpn[4], vy=math.sin(a) * wpn[4], life=0.8,
                               dmg=wpn[3] * (1 + self.pb("hunt")), a=a))
        self.atk_cd = wpn[5] * (0.7 if self.has("hunt1") else 1)

    def spawn_animal(self):
        cap = 14 + (6 if self.has("hunt2") else 0)
        if len(self.animals) >= cap:
            return
        night = self.is_night()
        kinds = list(ANIMALS)
        ws = []
        for k in kinds:
            w = ANIMALS[k]["night" if night else "w"]
            if k in ("Bear", "Golden Stag") and self.has("hunt3"):
                w *= 3
            ws.append(w)
        for _ in range(10):
            x, y = random.choice(self.grass_tiles)
            d = dist(x * TS, y * TS, self.px, self.py)
            if 450 < d < 1300:
                k = random.choices(kinds, ws)[0]
                a = ANIMALS[k]
                self.animals.append(dict(kind=k, x=x * TS + 16.0, y=y * TS + 16.0, hp=a["hp"], vx=0.0, vy=0.0,
                                         t=0.0, cd=0.0, flash=0.0))
                return

    def kill(self, an):
        spec = ANIMALS[an["kind"]]
        for item, lo, hi, ch in spec["drops"]:
            if random.random() < ch:
                n = random.randint(lo, hi) * (2 if self.has("hunt4") else 1)
                got = self.add_item(item, ITEMS[item]["base"] * random.uniform(0.9, 1.2), count=n)
                if got:
                    self.float_text(an["x"], an["y"] - 20 - 18 * spec["drops"].index((item, lo, hi, ch)),
                                    f"+{got} {item}", RCOL[ITEMS[item]["rarity"]], 22)
        self.inc("kills")
        self.gain_xp(spec["xp"])
        self.note(f"You hunted a {an['kind']}!", (230, 180, 120))
        self.burst(an["x"], an["y"], (200, 40, 40), 14, 120)
        if an["kind"] == "Bear":
            self.rare_fx("BEAR DOWN!", 3, an["x"], an["y"])
        if an["kind"] == "Golden Stag":
            self.rare_fx("GOLDEN STAG!", 4, an["x"], an["y"])

    def update_animals(self, dt):
        self.spawn_t -= dt
        if self.spawn_t <= 0:
            self.spawn_t = 1.5
            self.spawn_animal()
        for an in list(self.animals):
            s = ANIMALS[an["kind"]]
            d = dist(an["x"], an["y"], self.px, self.py) or 1
            an["cd"] -= dt
            an["flash"] -= dt
            if d > 1800:
                self.animals.remove(an)
                continue
            if s["beh"] == "flee" and (d < 170 or an["flash"] > -1.5):
                vx, vy = (an["x"] - self.px) / d * s["spd"] * 1.3, (an["y"] - self.py) / d * s["spd"] * 1.3
            elif s["beh"] == "aggro" and d < 260 and not self.menu:
                vx, vy = (self.px - an["x"]) / d * s["spd"], (self.py - an["y"]) / d * s["spd"]
                if d < s["size"] + 16 and an["cd"] <= 0:
                    an["cd"] = 1.0
                    self.hp -= s["dmg"]
                    self.hurt = 0.3
                    self.shake = 0.2
                    self.float_text(self.px, self.py - 30, f"-{s['dmg']}", RED, 28)
            else:
                an["t"] -= dt
                if an["t"] <= 0:
                    an["t"] = random.uniform(1, 3)
                    if random.random() < 0.4:
                        an["vx"] = an["vy"] = 0.0
                    else:
                        a = random.uniform(0, math.tau)
                        an["vx"], an["vy"] = math.cos(a) * s["spd"] * 0.35, math.sin(a) * s["spd"] * 0.35
                vx, vy = an["vx"], an["vy"]
            nx, ny = an["x"] + vx * dt, an["y"] + vy * dt
            r = max(6, s["size"] * 0.6)
            if self.can_walk(nx, an["y"], r) and self.tile_at(nx, an["y"]) not in WATER:
                an["x"] = nx
            else:
                an["vx"] *= -1
            if self.can_walk(an["x"], ny, r) and self.tile_at(an["x"], ny) not in WATER:
                an["y"] = ny
            else:
                an["vy"] *= -1
            an["dir"] = 1 if vx >= 0 else -1
        for p in list(self.projs):
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
            hit = False
            for an in self.animals:
                if dist(p["x"], p["y"], an["x"], an["y"]) < ANIMALS[an["kind"]]["size"] + 8:
                    an["hp"] -= p["dmg"]
                    an["flash"] = 0.2
                    self.float_text(an["x"], an["y"] - 25, f"-{int(p['dmg'])}", ORANGE, 22)
                    self.burst(p["x"], p["y"], (200, 40, 40), 5, 70)
                    if an["hp"] <= 0:
                        self.animals.remove(an)
                        self.kill(an)
                    hit = True
                    break
            if hit or p["life"] <= 0 or self.solid(int(p["x"] // TS), int(p["y"] // TS)):
                self.projs.remove(p)

    # ------------------------------------------------------------ npcs & restaurant
    def spawn_npc(self):
        names = {n["name"] for n in self.npcs}
        opts = [b for b in BUYERS if b[0] not in names]
        if not opts or len(self.npcs) >= 3:
            return
        name, cat, col = random.choice(opts)
        owned = [s["name"] for s in self.bag if ITEMS[s["name"]]["cat"] == cat and "junk" not in ITEMS[s["name"]]["tags"]]
        if owned and random.random() < 0.6:
            item = random.choice(owned)
        else:
            pool = [n for n, d in ITEMS.items() if d["cat"] == cat and ridx(d["rarity"]) <= 1
                    and n not in ("Fish Fillet", "Fish Scales", "Old Boot", "Seaweed")]
            item = random.choice(pool)
        cnt = random.randint(5, 12) if cat == "wood" else random.randint(1, 2) if cat == "food" else random.randint(2, 5)
        reward = int(ITEMS[item]["base"] * cnt * 1.8 + 25)
        sx = random.choice([51 * TS, 92 * TS])
        self.npcs.append(dict(name=name, cat=cat, item=item, cnt=cnt, reward=reward, gems=random.choice([0, 0, 1, 2, 3]),
                              col=col, x=float(sx), y=52.9 * TS, sx=sx, sy=52.9 * TS, tx=random.randint(56, 89) * TS + 16.0,
                              ty=random.randint(49, 54) * TS + 16.0, state="walk", timer=180.0, msg=""))

    def fulfill(self, n):
        if self.have(n["item"]) < n["cnt"]:
            self.note(f"{n['name']}: \"I need {n['cnt']}x {n['item']}! You have {self.have(n['item'])}.\"", ORANGE)
            return
        self.take(n["item"], n["cnt"])
        self.coins += n["reward"]
        self.gems += n["gems"]
        self.inc("orders")
        self.gain_xp(20)
        self.note(f"{n['name']} paid you {n['reward']} coins" + (f" + {n['gems']} gems!" if n["gems"] else "!"), GOLD)
        self.float_text(n["x"], n["y"] - 40, "THANK YOU!!", GOLD, 28)
        self.burst(n["x"], n["y"], GOLD, 16, 140)
        n["state"], n["tx"], n["ty"], n["msg"] = "leave", n["sx"], n["sy"], "Thanks!"

    def update_npcs(self, dt):
        self.npc_t -= dt
        if self.npc_t <= 0:
            self.npc_t = random.uniform(30, 50)
            self.spawn_npc()
        for n in list(self.npcs):
            dx, dy = n["tx"] - n["x"], n["ty"] - n["y"]
            d = math.hypot(dx, dy)
            if n["state"] in ("walk", "leave") and d > 3:
                n["x"] += dx / d * 80 * dt
                n["y"] += dy / d * 80 * dt
            elif n["state"] == "walk":
                n["state"] = "wait"
            elif n["state"] == "leave":
                self.npcs.remove(n)
                continue
            if n["state"] == "wait":
                n["timer"] -= dt
                if n["timer"] <= 0:
                    n["state"], n["tx"], n["ty"], n["msg"] = "leave", n["sx"], n["sy"], "Too slow..."
        if not self.restaurant:
            return
        self.diner_t -= dt
        free = [s for s in range(4) if not any(d["seat"] == s for d in self.diners)]
        if self.diner_t <= 0 and free:
            self.diner_t = random.uniform(18, 30) / (2 if self.has("cook2") else 1)
            owned = [s["name"] for s in self.bag if ITEMS[s["name"]]["cat"] == "food"]
            dish = random.choice(owned) if owned and random.random() < 0.6 else random.choice(RECIPES)[0]
            s = random.choice(free)
            tx, ty = TABLES[s]
            self.diners.append(dict(seat=s, dish=dish, x=tx * TS + 16, y=ty * TS + 46, patience=150.0,
                                    col=random.choice([(220, 120, 120), (120, 160, 230), (140, 210, 140), (230, 200, 110)])))
        for d in list(self.diners):
            d["patience"] -= dt
            if d["patience"] <= 0:
                self.diners.remove(d)
                self.note("A diner got tired of waiting and left!", ORANGE)

    def serve(self, d):
        stacks = [s for s in self.bag if s["name"] == d["dish"]]
        if not stacks:
            self.note(f"Diner wants {d['dish']} - cook it at the KITCHEN!", ORANGE)
            return
        s = max(stacks, key=lambda s: s["value"])
        val = s["value"]
        s["count"] -= 1
        if s["count"] <= 0:
            self.bag.remove(s)
        tip = val * random.uniform(0.1, 0.5) * (2 if self.has("cook3") else 1)
        pay = int(val * 1.5 * self.sell_mult() + tip)
        self.coins += pay
        self.inc("served")
        self.gain_xp(10)
        self.diners.remove(d)
        self.float_text(d["x"], d["y"] - 40, f"+{pay}c  (tip {int(tip)})", GOLD, 26)
        self.float_text(d["x"], d["y"] - 64, "5 STARS! *****", GOLD, 22)
        self.burst(d["x"], d["y"], GOLD, 14, 120)

    # ------------------------------------------------------------ cooking
    def plan(self, recipe):
        """Return True if the bag holds every ingredient (name-specific ones reserved first)."""
        counts = {id(s): s["count"] for s in self.bag}
        specs = sorted(recipe[1], key=lambda sp: sp[0] in GENERIC)
        for spec, n in specs:
            for s in sorted(self.bag, key=lambda s: s["value"]):
                if spec in ITEMS[s["name"]]["tags"] and counts[id(s)] > 0:
                    k = min(n, counts[id(s)])
                    counts[id(s)] -= k
                    n -= k
                if n == 0:
                    break
            if n > 0:
                return False
        return True

    def start_cook(self, recipe):
        if not self.plan(recipe):
            return
        val = 0.0
        for spec, n in sorted(recipe[1], key=lambda sp: sp[0] in GENERIC):
            val += self.take(spec, n) or 0
        self.cook = dict(r=recipe, val=val, pos=0.0, dir=1, spd=1.0, t=0.0)

    def cook_stop(self):
        c = self.cook
        off = abs(c["pos"] - 0.5)
        q = "Gourmet" if off < 0.04 else "Perfect" if off < 0.12 else "Good" if off < 0.35 else "Burnt"
        if c["t"] > 7:
            q = "Burnt"
        r = c["r"]
        value = (c["val"] * 1.3 + 15 + r[5] * 0.5) * QMULT[q] * (1.25 if self.has("cook1") else 1) * (2 if self.has("cook4") else 1)
        self.add_item(r[0], value, q=q)
        self.inc("cooked")
        self.gain_xp(8)
        col = {q_[0]: q_[2] for q_ in QUAL}[q]
        self.note(f"Cooked {r[0]} ({q})! Worth {fmt(value)}c", col)
        if q == "Gourmet":
            self.do_banner("GOURMET!!", f"{r[0]} worth {fmt(value)} coins", PINK)
        self.cook = None

    def scale_fish(self):
        done = 0
        for s in [s for s in self.bag if "fish" in ITEMS[s["name"]]["tags"]]:
            ri = ridx(ITEMS[s["name"]]["rarity"])
            nf = 1 + ri // 2
            while s["count"] > 0:
                if self.bag_cap() - self.count(self.bag) < nf:
                    break
                s["count"] -= 1
                self.add_item("Fish Fillet", s["value"] * 0.8 / nf, q=RAR[ri], count=nf)
                self.add_item("Fish Scales", s["value"] * 0.3)
                done += 1
            if s["count"] <= 0:
                self.bag.remove(s)
        if done:
            self.gain_xp(done)
            self.note(f"Scaled & filleted {done} fish!", (250, 170, 150))
        else:
            self.note("No fish to scale (or bag too full)!", ORANGE)

    # ------------------------------------------------------------ eating / survival
    def eat(self, s):
        it = ITEMS[s["name"]]
        if not (it["hunger"] or it["thirst"] or it["heal"]):
            return False
        qm = QMULT.get(s["q"], 1) if s["q"] in QMULT else 1
        self.food = min(100, self.food + it["hunger"] * (0.6 + 0.4 * qm))
        self.water = min(100, self.water + it["thirst"])
        self.hp = clamp(self.hp + it["heal"] * (0.6 + 0.4 * qm), 1, 100)
        s["count"] -= 1
        if s["count"] <= 0:
            self.bag.remove(s)
        parts = [f"+{it['hunger']} food" if it["hunger"] else "", f"+{it['thirst']} water" if it["thirst"] else "",
                 (f"+{it['heal']} hp" if it["heal"] > 0 else f"{it['heal']} hp (raw!)") if it["heal"] else ""]
        self.float_text(self.px, self.py - 40, "  ".join(p for p in parts if p), GREEN, 22)
        return True

    def eat_best(self):
        best, bs = None, 0
        for s in self.bag:
            it = ITEMS[s["name"]]
            sc = (min(it["hunger"], 100 - self.food) + min(it["thirst"], 100 - self.water)
                  + min(max(it["heal"], 0), 100 - self.hp) + min(it["heal"], 0))
            if sc > bs:
                best, bs = s, sc
        if best:
            self.eat(best)
        else:
            self.note("Nothing good to eat! Cook food, farm or buy snacks.", ORANGE)

    def build_fire(self):
        if self.take("wood", 3) is None:
            self.note("A campfire needs 3 logs. Go chop some trees!", ORANGE)
            return
        self.campfires.append([self.px, self.py + 20, 240.0])
        self.note("Campfire built! Press E near it to cook.", ORANGE)

    def die(self):
        lost = int(self.coins * 0.1)

        def revive():
            if self.gems < 10:
                self.need_gems(10)
                respawn()
                return
            self.gems -= 10
            self.hp, self.food, self.water, self.oxy = 100.0, 80.0, 80.0, 100.0
            self.note("Revived on the spot!", PINK)

        def respawn():
            self.coins -= lost
            self.px, self.py = self.spawn
            self.hp, self.food, self.water, self.oxy = 100.0, 60.0, 60.0, 100.0
        self.hp = 1
        self.fish = None
        self.popup("YOU FAINTED!", ["You ran out of health!", f"Respawn at home and lose {lost} coins...",
                                     "...or REVIVE right here for 10 gems!"],
                   [("REVIVE (10 gems)", revive, PINK), ("Respawn at home", respawn, PANEL3)], RED)

    # ------------------------------------------------------------ shop actions
    def buy_tool(self, kind, i):
        t = TOOLS[kind][1][i]
        if t[2]:
            if self.gems < t[2]:
                self.need_gems(t[2])
                return
            self.gems -= t[2]
        else:
            if self.coins < t[1]:
                self.note("Not enough coins!", RED)
                return
            self.coins -= t[1]
        self.tools[kind] = i
        self.do_banner("NEW GEAR!", t[0], CYAN)

    def buy_seed(self, c, n):
        if c[5]:
            if self.gems < c[5] * n:
                self.need_gems(c[5] * n)
                return
            self.gems -= c[5] * n
        else:
            if self.coins < c[1] * n:
                self.note("Not enough coins!", RED)
                return
            self.coins -= c[1] * n
        self.seeds[c[0]] = self.seeds.get(c[0], 0) + n
        self.sel_seed = CROPS.index(c)
        self.note(f"Bought {n} {c[0]} seed{'s' if n > 1 else ''}!", GREEN)

    def buy_supply(self, sup):
        name, price, n, _ = sup
        if self.coins < price:
            self.note("Not enough coins!", RED)
            return
        if self.add_item(name, ITEMS[name]["base"], count=n):
            self.coins -= price

    def buy_plot(self):
        k = self.plots_unlocked - 6
        if k >= len(PLOT_PRICES):
            return
        if self.coins < PLOT_PRICES[k]:
            self.note("Not enough coins!", RED)
            return
        self.coins -= PLOT_PRICES[k]
        self.plots_unlocked += 1
        self.note("New garden plot unlocked!", GREEN)

    def buy_storage(self):
        price = self.chest_cap * 5
        if self.coins < price:
            self.note("Not enough coins!", RED)
            return
        self.coins -= price
        self.chest_cap += 50
        self.note(f"Storage chest now holds {self.chest_cap}!", GREEN)

    def buy_skill(self, s):
        if self.coins < s[3]:
            self.note("Not enough coins!", RED)
            return
        self.coins -= s[3]
        self.skills.add(s[0])
        self.inc("skills")
        self.do_banner("UPGRADE UNLOCKED!", f"{s[1]}: {s[2]}", PURPLE)

    def sell(self, cat=None):
        total, n = 0.0, 0
        for s in list(self.bag):
            c = ITEMS[s["name"]]["cat"]
            if (cat is None and c != "misc") or c == cat:
                total += s["value"] * s["count"]
                n += s["count"]
                self.bag.remove(s)
        if not n:
            self.note("Nothing to sell!", ORANGE)
            return
        total = int(total * self.sell_mult())
        self.coins += total
        self.inc("sold", n)
        self.note(f"Sold {n} items for {fmt(total)} coins!", GOLD)
        self.float_text(self.px, self.py - 40, f"+{fmt(total)} coins", GOLD, 32)
        self.burst(self.px, self.py, GOLD, min(60, 10 + n), 200)
        if total >= 1000:
            self.do_banner("KA-CHING!", f"+{fmt(total)} coins", GOLD)

    def hatch_egg(self, i):
        name, coins, gems, ws, col = EGGS[i]
        if gems:
            if self.gems < gems:
                self.need_gems(gems)
                return
            self.gems -= gems
        else:
            if self.coins < coins:
                self.note("Not enough coins!", RED)
                return
            self.coins -= coins
        ri = random.choices(range(6), ws)[0]
        pet = random.choice([p for p in PETS if ridx(p[1]) == ri])
        self.pets.append(pet[0])
        if len(self.equipped) < self.pet_slots:
            self.equipped.append(len(self.pets) - 1)
        self.inc("hatched")
        self.hatch = dict(egg=i, t=0.0, pet=pet[0], roll=[random.choice(PETS)[0] for _ in range(28)] + [pet[0]], fx=False)

    def toggle_pet(self, i):
        if i in self.equipped:
            self.equipped.remove(i)
        elif len(self.equipped) < self.pet_slots:
            self.equipped.append(i)
        else:
            self.note("All pet slots full! Unequip one or buy a slot in the GEM STORE.", ORANGE)

    def gem_item(self, gid, cost):
        if self.gems < cost:
            self.need_gems(cost)
            return
        if gid == "slot" and self.pet_slots >= 4:
            self.note("You already have the max pet slots!", ORANGE)
            return
        if gid == "vip" and self.vip:
            self.note("You already have VIP!", ORANGE)
            return
        self.gems -= cost
        if gid == "luck":
            self.boosts["luck"] += 600
        elif gid == "coins":
            self.boosts["coins"] += 600
        elif gid == "grow":
            for p in self.plots:
                if p["crop"]:
                    p["prog"] = 1.0
        elif gid == "heal":
            self.hp = self.food = self.water = self.oxy = 100.0
        elif gid == "slot":
            self.pet_slots += 1
        elif gid == "vip":
            self.vip = True
        elif gid == "coinsack":
            self.coins += 5000
        self.do_banner("ACTIVATED!", dict((g[0], g[1]) for g in GEM_ITEMS)[gid], PINK)

    # ------------------------------------------------------------ events
    def handle(self, ev):
        if ev.type == pygame.QUIT:
            self.save()
            pygame.quit()
            sys.exit()
        if ev.type == pygame.MOUSEMOTION:
            self.mouse = ev.pos
        elif ev.type == pygame.MOUSEWHEEL:
            if self.menu:
                self.scroll = max(0, self.scroll - ev.y)
            else:
                self.sel_seed = (self.sel_seed - ev.y) % len(CROPS)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.mouse = ev.pos
            for r, cb in reversed(self.buttons):
                if r.collidepoint(ev.pos):
                    if self.popups:
                        self.popups.pop()
                    if cb:
                        cb()
                    return
            if self.popups or self.title or self.hatch:
                if self.hatch and self.hatch["t"] > 3.6:
                    self.hatch = None
                return
            if self.cook:
                self.cook_stop()
                return
            if self.menu:
                return
            if self.fish:
                if self.fish["s"] == "bite":
                    self.hook()
                return
            self.attack()
        elif ev.type == pygame.KEYDOWN:
            k = ev.key
            if self.popups:
                if k in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    p = self.popups.pop()
                    if k != pygame.K_ESCAPE and p["buttons"][0][1]:
                        p["buttons"][0][1]()
                return
            if self.title:
                if k in (pygame.K_RETURN, pygame.K_SPACE):
                    self.start()
                return
            if self.hatch:
                if self.hatch["t"] > 3.6:
                    self.hatch = None
                return
            if self.cook:
                if k in (pygame.K_SPACE, pygame.K_e):
                    self.cook_stop()
                return
            if k == pygame.K_ESCAPE:
                if self.menu:
                    self.menu = None
                else:
                    self.popup("PAUSED", ["Your game saves automatically every minute."],
                               [("Resume", None, GREEN), ("Help", self.show_help, PANEL3),
                                ("Save & Quit", self.quit, RED)], CYAN)
                return
            toggles = {pygame.K_TAB: "inv", pygame.K_g: "gems", pygame.K_k: "skills", pygame.K_p: "pets"}
            if k in toggles:
                m = toggles[k]
                if self.menu == m or (m == "inv" and self.menu == "home"):
                    self.menu = None
                else:
                    self.open_menu(m)
                return
            if k == pygame.K_h:
                self.show_help()
                return
            if self.menu:
                return
            if k == pygame.K_e:
                self.interact()
            elif k == pygame.K_f:
                self.fish_down()
            elif k == pygame.K_SPACE and self.fish and self.fish["s"] == "bite":
                self.hook()
            elif k == pygame.K_r:
                self.eat_best()
            elif k == pygame.K_b:
                self.build_fire()
            elif k == pygame.K_z:
                self.sel_seed = (self.sel_seed + 1) % len(CROPS)
        elif ev.type == pygame.KEYUP and ev.key == pygame.K_f:
            self.fish_up()

    def quit(self):
        self.save()
        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------ update
    def update(self, dt):
        keys = pygame.key.get_pressed()
        busy = bool(self.menu or self.popups or self.hatch or self.cook)
        # time & weather
        self.tod += dt / 360
        if self.tod >= 1:
            self.tod -= 1
            self.day += 1
        if self.rain > 0:
            self.rain -= dt
        else:
            self.next_rain -= dt
            if self.next_rain <= 0:
                self.rain = random.uniform(45, 75)
                self.next_rain = random.uniform(150, 260)
                self.note("It's raining! Crops grow faster, fish bite faster.", BLUE)
        for b in self.boosts:
            self.boosts[b] = max(0.0, self.boosts[b] - dt)
        if not self.starter_bought:
            self.starter_left = max(0.0, self.starter_left - dt)
        for v in ("atk_cd", "mine_cd", "drink_cd", "hurt", "shake"):
            setattr(self, v, max(0.0, getattr(self, v) - dt))
        tile = self.tile_at(self.px, self.py)
        # movement
        self.moving = False
        reeling = self.fish and self.fish["s"] == "reel"
        if not busy and not reeling:
            dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
            dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
            if dx or dy:
                ln = math.hypot(dx, dy)
                dx, dy = dx / ln, dy / ln
                self.facing = (dx, dy)
                sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                spd = 150 * (1 + self.pb("speed")) * (1.55 if sprint else 1)
                spd *= 0.55 if tile == DEEP else 0.75 if tile == SHALLOW else 1
                nx = self.px + dx * spd * dt
                if self.can_walk(nx, self.py):
                    self.px = nx
                ny = self.py + dy * spd * dt
                if self.can_walk(self.px, ny):
                    self.py = ny
                self.moving = True
                if self.fish and self.fish["s"] in ("charge", "wait", "bite"):
                    self.fish = None
                if sprint:
                    self.food -= dt * 0.15
        # survival
        if not busy:
            drain = (0.7 if self.has("surv1") else 1) * (1 - min(0.8, self.pb("hunger")))
            self.food = max(0.0, self.food - 100 / 420 * dt * drain)
            self.water = max(0.0, self.water - 100 / 300 * dt * drain)
            if tile == DEEP:
                omult = (2 if self.has("surv2") else 1) * (1 + self.pb("oxygen"))
                self.oxy = max(0.0, self.oxy - 100 / (16 * omult) * dt)
            else:
                self.oxy = min(100.0, self.oxy + 45 * dt)
            if self.food <= 0:
                self.hp -= 1.5 * dt
            if self.water <= 0:
                self.hp -= 2 * dt
            if self.oxy <= 0:
                self.hp -= 12 * dt
                if random.random() < 0.05:
                    self.float_text(self.px, self.py - 30, "NO AIR!", RED)
            if self.food > 40 and self.water > 40 and self.hp < 100:
                self.hp = min(100.0, self.hp + (0.8 * (3 if self.has("surv3") else 1) + self.pb("regen")) * dt)
            if self.hp <= 0:
                self.die()
            self.update_dig(dt, keys)
            if keys[pygame.K_e] and self.mine_cd <= 0:
                kind, obj, _ = self.context()
                if kind == "ore":
                    self.mine(obj)
            self.update_fish(dt, keys)
        self.update_animals(dt)
        self.update_npcs(dt)
        # world regrowth
        gm = self.grow_mult()
        for i in range(self.plots_unlocked):
            p = self.plots[i]
            if p["crop"] and p["prog"] < 1:
                p["prog"] = min(1.0, p["prog"] + dt / CROP[p["crop"]][2] * gm)
        for t in self.trees:
            if t["stump"] > 0:
                t["stump"] -= dt
                if t["stump"] <= 0:
                    t["t"] = random.choices(range(len(TREES)), [x[5] for x in TREES])[0]
                    t["hp"] = TREES[t["t"]][2]
        for o in self.ores:
            if o["respawn"] > 0:
                o["respawn"] -= dt
        for h in list(self.holes):
            self.holes[h] -= dt
            if self.holes[h] <= 0:
                del self.holes[h]
        while len(self.sparkles) < 12:
            x, y = random.choice(self.grass_tiles)
            self.sparkles.add((x, y))
        for c in list(self.campfires):
            c[2] -= dt
            if c[2] <= 0:
                self.campfires.remove(c)
        for s in self.shadows:
            nx, ny = s[0] + s[2] * dt, s[1] + s[3] * dt
            if self.tile_at(nx, ny) in WATER:
                s[0], s[1] = nx, ny
            else:
                s[2], s[3] = -s[2] + random.uniform(-5, 5), -s[3] + random.uniform(-5, 5)
        # fx
        for f in list(self.floats):
            f[1] -= 40 * dt
            f[4] -= dt
            if f[4] <= 0:
                self.floats.remove(f)
        for p in list(self.parts):
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 200 * dt
            p[4] -= dt
            if p[4] <= 0:
                self.parts.remove(p)
        for n in list(self.notes):
            n[2] -= dt
            if n[2] <= 0:
                self.notes.remove(n)
        if self.banner:
            self.banner[3] -= dt
            if self.banner[3] <= 0:
                self.banner = None
        if self.hatch:
            self.hatch["t"] += dt
        if self.cook:
            c = self.cook
            c["t"] += dt
            c["spd"] = 1.0 + c["t"] * 0.25
            c["pos"] += c["dir"] * c["spd"] * dt
            if c["pos"] > 1:
                c["pos"], c["dir"] = 1.0, -1
            if c["pos"] < 0:
                c["pos"], c["dir"] = 0.0, 1
            if c["t"] > 7:
                self.cook_stop()
        # pets follow
        while len(self.pet_pos) < len(self.equipped):
            self.pet_pos.append([self.px, self.py])
        self.pet_pos = self.pet_pos[:len(self.equipped)]
        for k, pp in enumerate(self.pet_pos):
            a = math.pi / 2 + (k - (len(self.pet_pos) - 1) / 2) * 0.9 - math.atan2(self.facing[0], self.facing[1])
            tx, ty = self.px + math.cos(a) * 38, self.py + math.sin(a) * 30
            pp[0] += (tx - pp[0]) * min(1, dt * 4)
            pp[1] += (ty - pp[1]) * min(1, dt * 4)
        if not busy:
            self.check_quest()
        self.save_t += dt
        if self.save_t > 60:
            self.save_t = 0
            self.save()
        # camera
        cx = clamp(self.px - W / 2, 0, MW * TS - W)
        cy = clamp(self.py - H / 2, 0, MH * TS - H)
        if self.shake > 0:
            cx += random.uniform(-6, 6)
            cy += random.uniform(-6, 6)
        self.cam = (cx, cy)

    # ------------------------------------------------------------ drawing: world
    def w2s(self, x, y):
        return int(x - self.cam[0]), int(y - self.cam[1])

    def on_screen(self, x, y, m=80):
        sx, sy = self.w2s(x, y)
        return -m < sx < W + m and -m < sy < H + m

    def draw_world(self):
        if self.title:
            self.cam = (72 * TS - W / 2 + math.sin(self.t * 0.1) * 300, 52 * TS - H / 2)
        cx, cy = int(self.cam[0]), int(self.cam[1])
        sc = self.screen
        sc.blit(self.map_surf, (0, 0), pygame.Rect(cx, cy, W, H))
        x0, y0 = cx // TS, cy // TS
        # water shimmer & fish shadows
        for ty in range(y0, min(MH, y0 + H // TS + 2)):
            for tx in range(x0, min(MW, x0 + W // TS + 2)):
                if self.tiles[ty][tx] in WATER and (tx * 7 + ty * 13) % 5 == 0:
                    ox = math.sin(self.t * 2 + tx + ty) * 6
                    sx, sy = tx * TS - cx, ty * TS - cy
                    pygame.draw.line(sc, (150, 200, 245), (sx + 8 + ox, sy + 20), (sx + 18 + ox, sy + 20), 2)
        for s in self.shadows:
            if self.on_screen(s[0], s[1]):
                sx, sy = self.w2s(s[0], s[1])
                pygame.draw.ellipse(sc, (25, 70, 130), (sx - 9, sy - 4, 18, 8))
        for (tx, ty), tl in self.holes.items():
            if self.on_screen(tx * TS, ty * TS):
                sx, sy = self.w2s(tx * TS, ty * TS)
                pygame.draw.ellipse(sc, (70, 45, 30), (sx + 4, sy + 8, 24, 16))
                pygame.draw.ellipse(sc, (40, 25, 15), (sx + 8, sy + 11, 16, 10))
        for (tx, ty) in self.sparkles:
            if self.on_screen(tx * TS, ty * TS):
                sx, sy = self.w2s(tx * TS + 16, ty * TS + 16)
                r = 4 + 3 * abs(math.sin(self.t * 4 + tx))
                pygame.draw.line(sc, (255, 250, 180), (sx - r, sy), (sx + r, sy), 2)
                pygame.draw.line(sc, (255, 250, 180), (sx, sy - r), (sx, sy + r), 2)
        self.draw_plots()
        for tx, ty in TABLES:
            sx, sy = self.w2s(tx * TS, ty * TS)
            pygame.draw.rect(sc, (150, 100, 60), (sx + 2, sy + 4, 28, 22), border_radius=4)
            pygame.draw.rect(sc, (240, 240, 240), (sx + 4, sy + 6, 24, 6))
        for c in self.campfires:
            if self.on_screen(c[0], c[1]):
                sx, sy = self.w2s(c[0], c[1])
                pygame.draw.line(sc, (110, 70, 40), (sx - 12, sy + 6), (sx + 12, sy - 2), 5)
                pygame.draw.line(sc, (110, 70, 40), (sx - 12, sy - 2), (sx + 12, sy + 6), 5)
                for i in range(3):
                    r = 9 - i * 3 + math.sin(self.t * 12 + i) * 2
                    pygame.draw.circle(sc, [(255, 90, 30), (255, 170, 40), (255, 240, 120)][i], (sx, sy - 6 - i * 3), max(2, int(r)))
        # y-sorted objects
        objs = []
        for t in self.trees:
            if self.on_screen(t["x"] * TS, t["y"] * TS):
                objs.append((t["y"] * TS + 28, 0, t))
        for o in self.ores:
            if self.on_screen(o["x"] * TS, o["y"] * TS):
                objs.append((o["y"] * TS + 24, 1, o))
        for b in self.buildings:
            if self.on_screen(b["rect"].centerx, b["rect"].centery, 260):
                objs.append((b["rect"].bottom, 2, b))
        for a in self.animals:
            if self.on_screen(a["x"], a["y"]):
                objs.append((a["y"], 3, a))
        for n in self.npcs:
            objs.append((n["y"], 4, n))
        for d in self.diners:
            objs.append((d["y"], 5, d))
        for k, pp in enumerate(self.pet_pos):
            objs.append((pp[1], 6, k))
        if not self.title:
            objs.append((self.py, 7, None))
        objs.sort(key=lambda o: o[0])
        fns = [self.draw_tree, self.draw_ore, self.draw_building, self.draw_animal, self.draw_npc, self.draw_diner,
               self.draw_pet_world, self.draw_player]
        for _, kind, o in objs:
            fns[kind](o)
        for p in self.projs:
            sx, sy = self.w2s(p["x"], p["y"])
            ex, ey = sx - math.cos(p["a"]) * 22, sy - math.sin(p["a"]) * 22
            pygame.draw.line(sc, (130, 90, 50), (sx, sy), (ex, ey), 3)
            pygame.draw.circle(sc, (200, 200, 210), (sx, sy), 3)
        for p in self.parts:
            sx, sy = self.w2s(p[0], p[1])
            pygame.draw.circle(sc, p[5], (sx, sy), max(1, int(p[6] * min(1, p[4] * 2))))
        if self.fish and not self.title:
            self.draw_fishing_world()
        # lighting
        inside_cave = self.tile_at(self.px, self.py) in (CAVE, WALL) and not self.title
        a = 205 if inside_cave else self.darkness()
        if self.rain > 0:
            a = max(a, 60)
        if a > 0:
            dark = pygame.Surface((W, H), pygame.SRCALPHA)
            dark.fill((8, 8, 30, int(a)))
            lights = [] if self.title else [(*self.w2s(self.px, self.py), 170)]
            lights += [(*self.w2s(c[0], c[1]), 150) for c in self.campfires]
            for b in self.buildings:
                lights.append((*self.w2s(*b["door"]), 70))
            for lx, ly, rad in lights:
                for i in range(6, 0, -1):
                    pygame.draw.circle(dark, (8, 8, 30, int(a * (i / 6) ** 1.6)), (lx, ly), int(rad * i / 6))
            sc.blit(dark, (0, 0))
        if self.rain > 0:
            for _ in range(140):
                x, y = random.randrange(W), random.randrange(H)
                pygame.draw.line(sc, (170, 190, 240), (x, y), (x - 4, y + 12), 1)
        for f in self.floats:
            sx, sy = self.w2s(f[0], f[1])
            self.text(f[2], (sx, sy), f[5], f[3], "c")

    def draw_plots(self):
        sc = self.screen
        for i, r in enumerate(self.plot_rects):
            if not self.on_screen(r.x, r.y):
                continue
            sx, sy = self.w2s(r.x, r.y)
            if i >= self.plots_unlocked:
                s = pygame.Surface((64, 64), pygame.SRCALPHA)
                s.fill((0, 0, 0, 120))
                sc.blit(s, (sx, sy))
                self.text("LOCKED", (sx + 32, sy + 32), 18, GREY, "c")
                continue
            p = self.plots[i]
            pygame.draw.rect(sc, (90, 62, 38), (sx, sy, 64, 64), 3, border_radius=4)
            if not p["crop"]:
                continue
            c = CROP[p["crop"]]
            g = p["prog"]
            for (ox, oy) in ((16, 18), (46, 18), (16, 46), (46, 46)):
                x, y = sx + ox, sy + oy
                if g < 0.33:
                    pygame.draw.circle(sc, (110, 200, 90), (x, y + 6), 3)
                elif g < 0.66:
                    pygame.draw.line(sc, (60, 150, 60), (x, y + 8), (x, y - 4), 3)
                    pygame.draw.circle(sc, (90, 190, 80), (x - 4, y - 2), 5)
                    pygame.draw.circle(sc, (90, 190, 80), (x + 4, y - 4), 5)
                else:
                    pygame.draw.line(sc, (60, 150, 60), (x, y + 8), (x, y - 8), 3)
                    pygame.draw.circle(sc, (80, 180, 70), (x, y - 6), 9)
                    rr = 5 if g >= 1 else 3
                    bob = math.sin(self.t * 5 + ox) * 2 if g >= 1 else 0
                    pygame.draw.circle(sc, c[4], (x + 3, int(y - 4 + bob)), rr)
            if g >= 1 and int(self.t * 3) % 2 == 0:
                self.text("READY!", (sx + 32, sy - 6), 18, GOLD, "c")
            elif g < 1:
                pygame.draw.rect(sc, (30, 30, 30), (sx + 4, sy + 58, 56, 5))
                pygame.draw.rect(sc, GREEN, (sx + 4, sy + 58, int(56 * g), 5))

    def draw_tree(self, t):
        sc = self.screen
        sx, sy = self.w2s(t["x"] * TS + 16, t["y"] * TS + 16)
        name, val, hp, col, rar, _ = TREES[t["t"]]
        pygame.draw.ellipse(sc, (40, 80, 35), (sx - 14, sy + 6, 28, 10))
        if t["stump"] > 0:
            pygame.draw.ellipse(sc, (120, 85, 50), (sx - 8, sy - 2, 16, 10))
            pygame.draw.ellipse(sc, (170, 130, 80), (sx - 6, sy - 2, 12, 6))
            return
        pygame.draw.rect(sc, (110, 75, 45) if name != "Birch" else (230, 230, 220), (sx - 4, sy - 12, 8, 22))
        if name == "Pine":
            for i in range(3):
                pygame.draw.polygon(sc, shade(col, i * 10), [(sx - 18 + i * 3, sy - 6 - i * 12), (sx, sy - 30 - i * 12),
                                                             (sx + 18 - i * 3, sy - 6 - i * 12)])
        else:
            big = 1.5 if name == "Ancient" else 1
            if name == "Ancient":
                pygame.draw.circle(sc, (255, 240, 150), (sx, sy - 28), int(28 + 3 * math.sin(self.t * 3)), 3)
            for ox, oy, r in ((-8, -22, 13), (8, -22, 13), (0, -32, 15)):
                pygame.draw.circle(sc, shade(col, -15), (sx + int(ox * big), sy + int(oy * big) + 2), int(r * big))
                pygame.draw.circle(sc, col, (sx + int(ox * big), sy + int(oy * big)), int(r * big))
            if name == "Maple":
                pygame.draw.circle(sc, (255, 160, 60), (sx - 5, sy - 34), 4)
        if t["hp"] < hp:
            pygame.draw.rect(sc, (30, 30, 30), (sx - 18, sy + 14, 36, 5))
            pygame.draw.rect(sc, GREEN, (sx - 18, sy + 14, int(36 * t["hp"] / hp), 5))

    def draw_ore(self, o):
        sc = self.screen
        sx, sy = self.w2s(o["x"] * TS + 16, o["y"] * TS + 16)
        name, tier, price, hp, col, rar, _ = ORES[o["o"]]
        if o["respawn"] > 0:
            for i in range(3):
                pygame.draw.circle(sc, (100, 100, 100), (sx - 8 + i * 8, sy + 8), 3)
            return
        pts = [(sx - 14, sy + 10), (sx - 12, sy - 6), (sx - 2, sy - 13), (sx + 11, sy - 8), (sx + 14, sy + 10)]
        pygame.draw.polygon(sc, (110, 108, 112), pts)
        pygame.draw.polygon(sc, (70, 68, 72), pts, 2)
        for ox, oy in ((-5, -2), (5, 2), (2, -7)):
            pygame.draw.circle(sc, col, (sx + ox, sy + oy), 3 if tier < 3 else 4)
        if ridx(rar) >= 3 and int(self.t * 4 + o["x"]) % 3 == 0:
            pygame.draw.circle(sc, WHITE, (sx + 4, sy - 6), 2)
        if o["hp"] < hp:
            pygame.draw.rect(sc, (30, 30, 30), (sx - 16, sy + 14, 32, 5))
            pygame.draw.rect(sc, ORANGE, (sx - 16, sy + 14, int(32 * o["hp"] / hp), 5))

    def draw_building(self, b):
        sc = self.screen
        r = b["rect"]
        sx, sy = self.w2s(r.x, r.y)
        col = b["col"]
        pygame.draw.rect(sc, (0, 0, 0), (sx + 6, sy + 22, r.w, r.h - 16), border_radius=6)
        pygame.draw.rect(sc, (225, 210, 185), (sx, sy + 18, r.w, r.h - 18), border_radius=4)
        pygame.draw.polygon(sc, shade(col, -40), [(sx - 10, sy + 34), (sx + r.w // 2, sy - 14), (sx + r.w + 10, sy + 34)])
        pygame.draw.polygon(sc, col, [(sx - 6, sy + 30), (sx + r.w // 2, sy - 8), (sx + r.w + 6, sy + 30)])
        dx = sx + r.w // 2
        pygame.draw.rect(sc, (90, 60, 40), (dx - 14, sy + r.h - 38, 28, 38), border_radius=4)
        pygame.draw.circle(sc, GOLD, (dx + 8, sy + r.h - 18), 3)
        for wx in (sx + 18, sx + r.w - 42):
            pygame.draw.rect(sc, (150, 210, 250), (wx, sy + 52, 24, 20))
            pygame.draw.rect(sc, (90, 60, 40), (wx, sy + 52, 24, 20), 3)
        sign = pygame.Rect(0, 0, max(90, self.font(22).size(b["name"])[0] + 16), 26)
        sign.center = (dx, sy + 38)
        pygame.draw.rect(sc, shade(col, -60), sign, border_radius=6)
        self.text(b["name"], sign.center, 22, WHITE, "c")
        if b["menu"] == "gems":
            for i in range(4):
                a = self.t * 2 + i * 1.57
                pygame.draw.circle(sc, (180, 255, 255), (int(dx + math.cos(a) * 60), int(sy + 40 + math.sin(a) * 30)), 3)
        if b["menu"] == "cook" and self.restaurant:
            self.text("OPEN", (dx, sy - 26), 24, GREEN, "c")

    def draw_animal(self, a):
        sc = self.screen
        s = ANIMALS[a["kind"]]
        sx, sy = self.w2s(a["x"], a["y"])
        z = s["size"]
        d = a.get("dir", 1)
        col = WHITE if a["flash"] > 0 else s["col"]
        pygame.draw.ellipse(sc, (30, 60, 30), (sx - z, sy + z // 2, z * 2, z // 2 + 3))
        pygame.draw.ellipse(sc, col, (sx - z, sy - z // 2, z * 2, int(z * 1.2)))
        hx = sx + d * z
        pygame.draw.circle(sc, col, (hx, sy - z // 2), int(z * 0.6))
        pygame.draw.circle(sc, BLACK, (hx + d * int(z * 0.25), sy - z // 2 - 2), 2)
        k = a["kind"]
        if k == "Rabbit":
            pygame.draw.ellipse(sc, col, (hx - 4, sy - z - 10, 4, 12))
            pygame.draw.ellipse(sc, col, (hx + 1, sy - z - 10, 4, 12))
        elif k in ("Deer", "Golden Stag"):
            ac = (255, 240, 150) if k == "Golden Stag" else (120, 90, 60)
            pygame.draw.line(sc, ac, (hx, sy - z), (hx - 6, sy - z - 12), 2)
            pygame.draw.line(sc, ac, (hx, sy - z), (hx + 6, sy - z - 12), 2)
            if k == "Golden Stag":
                pygame.draw.circle(sc, (255, 255, 200), (sx, sy - z), int(z + 8 + 3 * math.sin(self.t * 5)), 2)
        elif k == "Boar":
            pygame.draw.line(sc, WHITE, (hx + d * 6, sy - z // 2 + 3), (hx + d * 10, sy - z // 2 - 2), 2)
        elif k == "Bear":
            pygame.draw.circle(sc, col, (hx - 6, sy - z - 2), 5)
            pygame.draw.circle(sc, col, (hx + 6, sy - z - 2), 5)
        elif k == "Wolf":
            pygame.draw.polygon(sc, col, [(hx - 5, sy - z), (hx - 2, sy - z - 10), (hx + 1, sy - z)])
        if s["beh"] == "aggro" and dist(a["x"], a["y"], self.px, self.py) < 260:
            self.text("!", (sx, sy - z - 26), 28, RED, "c")
        if a["hp"] < s["hp"]:
            pygame.draw.rect(sc, (30, 30, 30), (sx - 18, sy - z - 14, 36, 5))
            pygame.draw.rect(sc, RED, (sx - 18, sy - z - 14, int(36 * a["hp"] / s["hp"]), 5))

    def draw_person(self, sx, sy, body, hat=None):
        sc = self.screen
        pygame.draw.ellipse(sc, (0, 0, 0), (sx - 11, sy + 10, 22, 7))
        pygame.draw.circle(sc, body, (sx, sy), 12)
        pygame.draw.circle(sc, (255, 220, 180), (sx, sy - 16), 9)
        pygame.draw.circle(sc, BLACK, (sx - 3, sy - 17), 2)
        pygame.draw.circle(sc, BLACK, (sx + 3, sy - 17), 2)
        if hat:
            pygame.draw.rect(sc, hat, (sx - 9, sy - 28, 18, 6))

    def bubble(self, sx, sy, lines, col=WHITE):
        f = self.font(18)
        w = max(f.size(l)[0] for l in lines) + 14
        h = 18 * len(lines) + 8
        r = pygame.Rect(sx - w // 2, sy - h, w, h)
        pygame.draw.rect(self.screen, (255, 255, 255), r, border_radius=8)
        pygame.draw.polygon(self.screen, WHITE, [(sx - 6, r.bottom), (sx + 6, r.bottom), (sx, r.bottom + 8)])
        for i, l in enumerate(lines):
            self.text(l, (r.centerx, r.y + 13 + i * 18), 18, (30, 30, 40) if i else (20, 90, 160), "c", False)

    def draw_npc(self, n):
        sx, sy = self.w2s(n["x"], n["y"])
        self.draw_person(sx, sy, n["col"], shade(n["col"], -50))
        self.text(n["name"], (sx, sy + 24), 18, WHITE, "c")
        if n["state"] == "wait":
            self.bubble(sx, sy - 34, [f"WANT: {n['cnt']}x {n['item']}",
                                      f"Pays {n['reward']}c" + (f" + {n['gems']} gems" if n["gems"] else "")])
        elif n["msg"]:
            self.bubble(sx, sy - 34, [n["msg"]])

    def draw_diner(self, d):
        sx, sy = self.w2s(d["x"], d["y"])
        self.draw_person(sx, sy, d["col"])
        self.bubble(sx, sy - 34, ["Order:", d["dish"]])
        pygame.draw.rect(self.screen, (30, 30, 30), (sx - 20, sy + 16, 40, 5))
        frac = d["patience"] / 150
        pygame.draw.rect(self.screen, GREEN if frac > 0.4 else RED, (sx - 20, sy + 16, int(40 * frac), 5))

    def draw_pet(self, sx, sy, name, scale=1.0):
        sc = self.screen
        p = PET[name]
        col = p[2]
        r = int(10 * scale)
        if ridx(p[1]) >= 4:
            pygame.draw.circle(sc, RCOL[p[1]], (sx, sy), int(r + 5 * scale + 2 * math.sin(self.t * 5)), max(1, int(2 * scale)))
        pygame.draw.circle(sc, shade(col, -40), (sx, sy + int(2 * scale)), r)
        pygame.draw.circle(sc, col, (sx, sy), r)
        pygame.draw.circle(sc, col, (sx - int(6 * scale), sy - int(9 * scale)), int(4 * scale))
        pygame.draw.circle(sc, col, (sx + int(6 * scale), sy - int(9 * scale)), int(4 * scale))
        ec = WHITE if sum(col) < 200 else BLACK
        pygame.draw.circle(sc, ec, (sx - int(4 * scale), sy - int(2 * scale)), max(1, int(2 * scale)))
        pygame.draw.circle(sc, ec, (sx + int(4 * scale), sy - int(2 * scale)), max(1, int(2 * scale)))

    def draw_pet_world(self, k):
        if k >= len(self.equipped):
            return
        pp = self.pet_pos[k]
        sx, sy = self.w2s(pp[0], pp[1] + math.sin(self.t * 6 + k) * 3)
        self.draw_pet(sx, sy, self.pets[self.equipped[k]])

    def draw_player(self, _):
        sc = self.screen
        sx, sy = self.w2s(self.px, self.py)
        tile = self.tile_at(self.px, self.py)
        if tile == DEEP:
            pygame.draw.circle(sc, (180, 220, 255), (sx, sy), int(16 + 3 * math.sin(self.t * 4)), 2)
            pygame.draw.circle(sc, (255, 220, 180), (sx, sy - 4), 10)
            pygame.draw.circle(sc, BLACK, (sx - 3, sy - 6), 2)
            pygame.draw.circle(sc, BLACK, (sx + 3, sy - 6), 2)
        else:
            bob = abs(math.sin(self.t * 12)) * 3 if self.moving else 0
            body = (220, 60, 60) if self.hurt > 0 else (60, 120, 220)
            self.draw_person(sx, int(sy - bob), body, (40, 160, 90) if not self.vip else None)
            if self.vip:
                pygame.draw.polygon(sc, GOLD, [(sx - 9, sy - 25 - bob), (sx - 9, sy - 33 - bob), (sx - 4, sy - 28 - bob),
                                               (sx, sy - 35 - bob), (sx + 4, sy - 28 - bob), (sx + 9, sy - 33 - bob),
                                               (sx + 9, sy - 25 - bob)])
        if self.dig_prog > 0:
            pygame.draw.rect(sc, (20, 20, 20), (sx - 30, sy + 22, 60, 9), border_radius=4)
            pygame.draw.rect(sc, (200, 150, 90), (sx - 30, sy + 22, int(60 * self.dig_prog), 9), border_radius=4)
            ang = math.sin(self.t * 14) * 0.6
            pygame.draw.line(sc, (140, 140, 150), (sx + 10, sy - 4), (sx + 10 + int(math.sin(ang) * 16), sy + 14), 3)

    def draw_fishing_world(self):
        f = self.fish
        sc = self.screen
        sx, sy = self.w2s(self.px, self.py)
        if f["s"] == "charge":
            p = self.cast_power()
            pygame.draw.rect(sc, (20, 20, 20), (sx + 22, sy - 50, 12, 60), border_radius=4)
            col = GOLD if p > 0.88 else GREEN
            pygame.draw.rect(sc, col, (sx + 22, sy + 10 - int(60 * p), 12, int(60 * p)), border_radius=4)
            mx, my = self.mouse
            pygame.draw.line(sc, (255, 255, 255), (sx, sy), (mx, my), 1)
            self.text("POWER", (sx + 28, sy - 66), 16, WHITE, "c")
            return
        bx, by = self.w2s(f["bx"], f["by"])
        bob = math.sin(self.t * 4) * 2 if f["s"] == "wait" else math.sin(self.t * 30) * 4
        pygame.draw.line(sc, (60, 40, 20), (sx + 6, sy - 6), (sx + 22, sy - 34), 3)
        pygame.draw.line(sc, (230, 230, 230), (sx + 22, sy - 34), (bx, by + bob), 1)
        pygame.draw.circle(sc, RED, (bx, int(by + bob)), 6)
        pygame.draw.circle(sc, WHITE, (bx, int(by + bob) - 3), 3)
        if f["s"] == "bite":
            s = 40 + int(8 * math.sin(self.t * 20))
            self.text("!", (bx, by - 30), s, GOLD, "c")
            self.text("PRESS F / SPACE / CLICK!", (bx, by - 60), 24, GOLD, "c")

    # ------------------------------------------------------------ drawing: hud
    def bar(self, x, y, w, h, frac, col, label):
        sc = self.screen
        pygame.draw.rect(sc, (15, 15, 22), (x - 2, y - 2, w + 4, h + 4), border_radius=8)
        pygame.draw.rect(sc, shade(col, -130), (x, y, w, h), border_radius=6)
        if frac > 0.01:
            c = col
            if frac < 0.25 and int(self.t * 4) % 2 == 0:
                c = shade(col, 70)
            pygame.draw.rect(sc, c, (x, y, max(8, int(w * clamp(frac, 0, 1))), h), border_radius=6)
        self.text(label, (x + 8, y + h // 2 + 1), 18, WHITE, "ml")

    def draw_hud(self):
        sc = self.screen
        y = 14
        for lbl, v, col in (("HEALTH", self.hp, (230, 60, 70)), ("FOOD", self.food, (240, 150, 50)),
                            ("WATER", self.water, (70, 150, 255))):
            self.bar(16, y, 230, 22, v / 100, col, f"{lbl}  {int(v)}")
            y += 30
        if self.oxy < 100 or self.tile_at(self.px, self.py) == DEEP:
            self.bar(16, y, 230, 22, self.oxy / 100, CYAN, f"OXYGEN  {int(self.oxy)}")
            y += 30
        hrs = int(self.tod * 24)
        mins = int((self.tod * 24 - hrs) * 60) // 10 * 10
        wtxt = "  Raining" if self.rain > 0 else ""
        self.text(f"Day {self.day}   {hrs:02d}:{mins:02d} {'Night' if self.is_night() else 'Day'}{wtxt}", (16, y + 2), 20,
                  (220, 220, 240))
        y += 26
        # quest
        desc, stat, amt, c, g, _ = self.cur_quest()
        prog = clamp(self.stats.get(stat, 0) - self.quest_base, 0, amt)
        lines = wrap(self.font(20), desc, 260)
        qh = 46 + 18 * len(lines) + 26
        box = pygame.Rect(16, y, 280, qh)
        s = pygame.Surface(box.size, pygame.SRCALPHA)
        s.fill((20, 22, 36, 200))
        sc.blit(s, box)
        pygame.draw.rect(sc, GOLD, box, 2, border_radius=8)
        self.text("QUEST", (26, y + 6), 22, GOLD)
        self.text(f"+{c}c +{g} gems", (box.right - 10, y + 8), 18, (255, 230, 150), "tr")
        for i, l in enumerate(lines):
            self.text(l, (26, y + 28 + i * 18), 20)
        by_ = y + 30 + 18 * len(lines)
        pygame.draw.rect(sc, (40, 40, 50), (26, by_, 260, 14), border_radius=6)
        pygame.draw.rect(sc, GREEN, (26, by_, int(260 * prog / amt), 14), border_radius=6)
        self.text(f"{int(prog)}/{amt}", (156, by_ + 7), 16, WHITE, "c")
        # top right money
        x = W - 16
        r = pygame.Rect(0, 0, 170, 36)
        r.topright = (x, 12)
        pygame.draw.rect(sc, (20, 22, 36), r, border_radius=18)
        pygame.draw.circle(sc, GOLD, (r.x + 20, r.centery), 11)
        self.text("c", (r.x + 20, r.centery), 20, (140, 100, 0), "c", False)
        self.text(fmt(self.coins), (r.x + 40, r.centery), 26, GOLD, "ml")
        r2 = pygame.Rect(0, 0, 170, 36)
        r2.topright = (r.x - 10, 12)
        pygame.draw.rect(sc, (20, 22, 36), r2, border_radius=18)
        pygame.draw.polygon(sc, CYAN, [(r2.x + 20, r2.y + 6), (r2.x + 30, r2.centery), (r2.x + 20, r2.bottom - 6),
                                       (r2.x + 10, r2.centery)])
        self.text(fmt(self.gems), (r2.x + 38, r2.centery), 26, CYAN, "ml")
        self.button((r2.right - 34, r2.y + 4, 28, 28), "+", lambda: self.open_menu("gems"), PINK, size=28)
        # level
        lv = pygame.Rect(0, 0, 350, 22)
        lv.topright = (x, 56)
        pygame.draw.rect(sc, (20, 22, 36), lv, border_radius=10)
        xw = int(lv.w * self.xp / self.xp_need())
        if xw > 20:
            pygame.draw.rect(sc, PURPLE, (lv.x, lv.y, xw, lv.h), border_radius=10)
        self.text(f"LEVEL {self.level}   {int(self.xp)}/{self.xp_need()} XP", lv.center, 18, WHITE, "c")
        # menu buttons
        bx = W - 16
        for label, m, col in (("HELP [H]", None, PANEL3), ("GEMS [G]", "gems", PINK), ("PETS [P]", "pets", (200, 110, 170)),
                              ("UPGRADES [K]", "skills", PURPLE), ("BAG [TAB]", "inv", (70, 140, 200))):
            w = self.font(20).size(label)[0] + 20
            cb = self.show_help if m is None else (lambda m=m: self.open_menu(m))
            self.button((bx - w, 86, w, 30), label, cb, col, size=20)
            bx -= w + 6
        # boosts
        yy = 124
        for k, v in self.boosts.items():
            if v > 0:
                self.text(f"2x {k.upper()}  {int(v) // 60}:{int(v) % 60:02d}", (W - 16, yy), 20, PINK, "tr")
                yy += 22
        if self.vip:
            self.text("VIP  +50% coins", (W - 16, yy), 20, GOLD, "tr")
            yy += 22
        if not self.starter_bought and self.starter_left > 0:
            sl = int(self.starter_left)
            self.button((W - 236, yy + 4, 220, 32), f"STARTER PACK -90%  {sl // 60}:{sl % 60:02d}",
                        lambda: self.open_menu("gems"), (210, 60, 150), size=19)
            yy += 40
        # notes
        for i, n in enumerate(reversed(self.notes)):
            self.text(n[0], (W - 16, yy + 6 + i * 24), 21, n[1], "tr")
        # context hint
        kind, obj, hint = self.context()
        if self.fish and self.fish["s"] == "charge":
            hint = "Release F to cast!  (GOLD = perfect cast)"
        elif self.fish and self.fish["s"] == "wait":
            hint = "Waiting for a bite...  (moving cancels)"
        elif self.fish:
            hint = ""
        if hint:
            f = self.font(26)
            w = f.size(hint)[0] + 30
            r = pygame.Rect(W // 2 - w // 2, H - 98, w, 36)
            s = pygame.Surface(r.size, pygame.SRCALPHA)
            s.fill((10, 10, 20, 190))
            sc.blit(s, r)
            self.text(hint, r.center, 26, WHITE, "c")
        if kind == "tree":
            self.draw_chop_meter(obj)
        seed = CROPS[self.sel_seed][0]
        bag = f"Bag {self.count(self.bag)}/{self.bag_cap()}"
        self.text(f"{bag}    Seed: {seed} x{self.seeds.get(seed, 0)} [Z]    Rod: {RODS[self.tools['rod']][0]}    "
                  f"Weapon: {WEAPONS[self.tools['weapon']][0]}", (16, H - 54), 20, (230, 230, 240))
        self.text("WASD move | E use | Hold F fish | Hold Q dig | Click hunt | R eat | B campfire | Esc pause",
                  (16, H - 28), 19, (190, 190, 210))
        # minimap
        mw, mh = self.mini.get_size()
        mx, my = W - mw - 16, H - mh - 16
        pygame.draw.rect(sc, (10, 10, 20), (mx - 4, my - 4, mw + 8, mh + 8), border_radius=6)
        sc.blit(self.mini, (mx, my))
        pygame.draw.circle(sc, WHITE, (mx + int(self.px / TS * 1.5), my + int(self.py / TS * 1.5)), 4)
        pygame.draw.circle(sc, RED, (mx + int(self.px / TS * 1.5), my + int(self.py / TS * 1.5)), 3)
        tg = self.quest_target()
        if tg:
            pygame.draw.circle(sc, GOLD, (mx + int(tg[0] / TS * 1.5), my + int(tg[1] / TS * 1.5)), 4, 2)
            d = dist(tg[0], tg[1], self.px, self.py)
            if d > 220:
                a = math.atan2(tg[1] - self.py, tg[0] - self.px)
                sx, sy = self.w2s(self.px, self.py)
                cx, cy = sx + math.cos(a) * 70, sy + math.sin(a) * 70
                pts = [(cx + math.cos(a) * 16, cy + math.sin(a) * 16), (cx + math.cos(a + 2.5) * 12, cy + math.sin(a + 2.5) * 12),
                       (cx + math.cos(a - 2.5) * 12, cy + math.sin(a - 2.5) * 12)]
                pulse = shade(GOLD, 40 * math.sin(self.t * 6))
                pygame.draw.polygon(sc, pulse, pts)
                self.text(f"{int(d / TS)}m", (cx, cy + 20), 18, GOLD, "c")
        if self.fish and self.fish["s"] == "reel":
            self.draw_reel()
        if self.hurt > 0:
            s = pygame.Surface((W, H), pygame.SRCALPHA)
            s.fill((255, 0, 0, int(self.hurt * 250)))
            sc.blit(s, (0, 0))

    def draw_banner(self):
        if self.banner:
            t, sub, col, life = self.banner
            k = min(1, (3 - life) * 6)
            size = int(40 + 30 * k)
            self.text(t, (W // 2, 150), size, col, "c")
            if sub:
                self.text(sub, (W // 2, 150 + size // 2 + 16), 28, WHITE, "c")

    def draw_chop_meter(self, t):
        sx, sy = self.w2s(t["x"] * TS + 16, t["y"] * TS - 50)
        w = 120
        r = pygame.Rect(sx - w // 2, sy - 10, w, 14)
        pygame.draw.rect(self.screen, (20, 20, 20), r.inflate(4, 4), border_radius=6)
        pygame.draw.rect(self.screen, (170, 60, 60), r, border_radius=6)
        z = self.chop_zone()
        pygame.draw.rect(self.screen, GREEN, (sx - int(w * z / 2), r.y, int(w * z), r.h))
        nx = r.x + int(w * self.needle())
        pygame.draw.rect(self.screen, WHITE, (nx - 2, r.y - 4, 4, r.h + 8))

    def draw_reel(self):
        f = self.fish
        fi = f["fish"]
        sc = self.screen
        w, h = 620, 44
        x, y = W // 2 - w // 2, H - 200
        panel = pygame.Rect(x - 20, y - 60, w + 40, 130)
        s = pygame.Surface(panel.size, pygame.SRCALPHA)
        s.fill((10, 14, 30, 220))
        sc.blit(s, panel)
        rc = RCOL[RAR[fi["ri"]]]
        pygame.draw.rect(sc, rc, panel, 3, border_radius=10)
        self.text(f"??? ({RAR[fi['ri']]})" + ("  MUTATED!" if fi["mut"] else ""), (W // 2, y - 40), 28, rc, "c")
        self.text("HOLD SPACE / MOUSE  -  keep the fish inside the green box!", (W // 2, y - 16), 20, WHITE, "c")
        pygame.draw.rect(sc, (30, 60, 110), (x, y, w, h), border_radius=8)
        zw = int(w * f["w"])
        zx = x + int(w * f["pos"]) - zw // 2
        inside = abs(f["fpos"] - f["pos"]) < f["w"] / 2
        zs = pygame.Surface((zw, h), pygame.SRCALPHA)
        zs.fill((80, 230, 120, 170 if inside else 110))
        sc.blit(zs, (zx, y))
        pygame.draw.rect(sc, (140, 255, 170), (zx, y, zw, h), 2, border_radius=6)
        fx = x + int(w * f["fpos"])
        fc = shade(rc, 0)
        pygame.draw.ellipse(sc, fc, (fx - 14, y + 12, 28, 20))
        pygame.draw.polygon(sc, fc, [(fx + 12, y + 22), (fx + 22, y + 12), (fx + 22, y + 32)])
        pygame.draw.circle(sc, BLACK, (fx - 7, y + 20), 2)
        pygame.draw.rect(sc, (40, 40, 50), (x, y + h + 10, w, 14), border_radius=6)
        pygame.draw.rect(sc, GREEN if inside else ORANGE, (x, y + h + 10, int(w * clamp(f["prog"], 0, 1)), 14), border_radius=6)

    # ------------------------------------------------------------ menus
    def panel(self, title, w=1060, h=640):
        x, y = (W - w) // 2, (H - h) // 2
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        self.screen.blit(s, (0, 0))
        pygame.draw.rect(self.screen, PANEL, (x, y, w, h), border_radius=16)
        pygame.draw.rect(self.screen, PANEL3, (x, y, w, h), 3, border_radius=16)
        self.text(title, (x + 24, y + 16), 44, GOLD)
        self.text(f"{fmt(self.coins)} coins    {fmt(self.gems)} gems", (x + w - 70, y + 26), 24, WHITE, "tr")
        self.button((x + w - 56, y + 14, 40, 40), "X", self.close_menu, RED, size=28)
        return x, y, w, h

    def tabs(self, x, y, names, w=124):
        for i, n in enumerate(names):
            self.button((x + i * (w + 6), y, w, 34), n, lambda i=i: self.set_tab(i), GOLD if i == self.tab else PANEL3,
                        size=20, tcol=BLACK if i == self.tab else WHITE)

    def set_tab(self, i):
        self.tab = i
        self.scroll = 0

    def menu_shop(self):
        x, y, w, h = self.panel("SHOP")
        names = [TOOLS[k][0] for k in TOOLS] + ["Seeds", "Supplies"]
        self.tabs(x + 20, y + 70, names, 122)
        ry = y + 120
        if self.tab < len(TOOLS):
            kind = list(TOOLS)[self.tab]
            for i, t in enumerate(TOOLS[kind][1]):
                r = pygame.Rect(x + 20, ry + i * 80, w - 40, 72)
                cur = self.tools[kind]
                pygame.draw.rect(self.screen, PANEL2 if i != cur else (40, 80, 60), r, border_radius=10)
                gem = t[2] > 0
                self.text(t[0], (r.x + 16, r.y + 10), 30, PINK if gem else WHITE)
                self.text(tool_desc(kind, t), (r.x + 16, r.y + 42), 22, (200, 210, 230))
                price = f"{t[2]} gems" if gem else ("FREE" if t[1] == 0 else f"{fmt(t[1])} coins")
                self.text(price, (r.right - 200, r.centery), 26, CYAN if gem else GOLD, "mr")
                if i == cur:
                    self.button((r.right - 170, r.y + 16, 150, 40), "EQUIPPED", None, (40, 120, 70), False)
                elif i < cur:
                    self.button((r.right - 170, r.y + 16, 150, 40), "OWNED", None, PANEL3, False)
                else:
                    can = self.gems >= t[2] if gem else self.coins >= t[1]
                    self.button((r.right - 170, r.y + 16, 150, 40), "BUY", lambda k=kind, i=i: self.buy_tool(k, i),
                                (PINK if gem else GREEN) if can else (120, 80, 80))
        elif self.tab == len(TOOLS):
            for i, c in enumerate(CROPS):
                r = pygame.Rect(x + 20, ry + i * 56, w - 40, 50)
                pygame.draw.rect(self.screen, PANEL2, r, border_radius=10)
                pygame.draw.circle(self.screen, c[4], (r.x + 26, r.centery), 13)
                self.text(f"{c[0]} seed", (r.x + 50, r.y + 8), 26, RCOL[c[8]])
                self.text(f"Grows in {c[2]}s   Sells for ~{c[3]}c   You own: {self.seeds.get(c[0], 0)}", (r.x + 50, r.y + 30), 19,
                          (200, 210, 230))
                price = f"{c[5]} gems" if c[5] else f"{c[1]} coins"
                self.text(price, (r.right - 260, r.centery), 24, CYAN if c[5] else GOLD, "mr")
                self.button((r.right - 240, r.y + 8, 100, 34), "Buy 1", lambda c=c: self.buy_seed(c, 1), GREEN, size=22)
                self.button((r.right - 130, r.y + 8, 110, 34), "Buy 5", lambda c=c: self.buy_seed(c, 5), GREEN, size=22)
        else:
            rows = [(s[0], s[3], f"{s[1]} coins", lambda s=s: self.buy_supply(s)) for s in SUPPLIES]
            k = self.plots_unlocked - 6
            if k < len(PLOT_PRICES):
                rows.append(("Garden Plot", f"Unlock plot #{self.plots_unlocked + 1} (you have {self.plots_unlocked}/12)",
                             f"{fmt(PLOT_PRICES[k])} coins", self.buy_plot))
            rows.append(("Storage Upgrade", f"Home chest +50 slots (now {self.chest_cap})", f"{fmt(self.chest_cap * 5)} coins",
                         self.buy_storage))
            for i, (n, d, p, cb) in enumerate(rows):
                r = pygame.Rect(x + 20, ry + i * 72, w - 40, 64)
                pygame.draw.rect(self.screen, PANEL2, r, border_radius=10)
                self.text(n, (r.x + 16, r.y + 8), 28)
                self.text(d, (r.x + 16, r.y + 38), 21, (200, 210, 230))
                self.text(p, (r.right - 200, r.centery), 26, GOLD, "mr")
                self.button((r.right - 170, r.y + 12, 150, 40), "BUY", cb, GREEN)

    def menu_market(self):
        x, y, w, h = self.panel("MARKET")
        m = self.sell_mult()
        self.text(f"Sell price multiplier: x{m:.2f}   (pets, VIP, skills & 2x Coins potion raise this!)", (x + 24, y + 70), 22,
                  (200, 220, 255))
        ry = y + 110
        grand = 0
        for i, (label, cat) in enumerate(CATS[1:8]):
            stacks = [s for s in self.bag if ITEMS[s["name"]]["cat"] == cat]
            n = sum(s["count"] for s in stacks)
            v = sum(s["count"] * s["value"] for s in stacks) * m
            grand += v
            r = pygame.Rect(x + 20, ry + i * 60, w - 40, 52)
            pygame.draw.rect(self.screen, PANEL2, r, border_radius=10)
            self.text(label, (r.x + 16, r.centery), 30, WHITE, "ml")
            self.text(f"{n} items", (r.x + 220, r.centery), 24, (200, 210, 230), "ml")
            self.text(f"{fmt(v)} coins", (r.right - 200, r.centery), 26, GOLD, "mr")
            self.button((r.right - 170, r.y + 8, 150, 36), "SELL", lambda c=cat: self.sell(c), GREEN if n else PANEL3, n > 0)
        self.button((x + w // 2 - 220, y + h - 92, 440, 64), f"SELL EVERYTHING  ({fmt(grand)} coins)", lambda: self.sell(None),
                    GOLD, grand > 0, 32, BLACK)

    def menu_inv(self, chest=False):
        x, y, w, h = self.panel("HOME - STORAGE" if chest else "BACKPACK")
        self.tabs(x + 20, y + 66, [c[0] for c in CATS], 106)
        if self.tab != self.inv_filter:
            self.inv_filter = self.tab
        cat = CATS[self.tab][1]
        cols = 3 if chest else 6
        area_w = (w - 60) // 2 if chest else w - 40

        def grid(lst, gx, title, action, act_label):
            self.text(title, (gx, y + 110), 24, GOLD)
            items = [s for s in lst if cat is None or ITEMS[s["name"]]["cat"] == cat]
            items.sort(key=lambda s: -s["value"] * s["count"])
            cw = (area_w - (cols - 1) * 8) // cols
            maxrows = 6
            start = min(self.scroll, max(0, (len(items) - 1) // cols - maxrows + 1)) * cols
            for k, s in enumerate(items[start:start + cols * maxrows]):
                cx = gx + (k % cols) * (cw + 8)
                cy = y + 140 + (k // cols) * 74
                it = ITEMS[s["name"]]
                r = pygame.Rect(cx, cy, cw, 66)
                hov = r.collidepoint(self.mouse)
                pygame.draw.rect(self.screen, shade(PANEL2, 20 if hov else 0), r, border_radius=8)
                pygame.draw.rect(self.screen, RCOL[it["rarity"]], r, 2, border_radius=8)
                pygame.draw.circle(self.screen, it["color"], (cx + 18, cy + 22), 10)
                if s["mut"]:
                    pygame.draw.circle(self.screen, MUTCOL.get(s["mut"], WHITE), (cx + 18, cy + 22), 13, 2)
                nm = self.iname(s)
                while self.font(19).size(nm)[0] > cw - 40 and len(nm) > 4:
                    nm = nm[:-2]
                self.text(nm, (cx + 34, cy + 8), 19, RCOL[it["rarity"]])
                self.text(f"x{s['count']}", (cx + 34, cy + 28), 20)
                self.text(f"{fmt(s['value'])}c ea", (cx + cw - 8, cy + 28), 18, GOLD, "tr")
                lab = act_label(s)
                if lab:
                    self.text(lab, (cx + 34, cy + 47), 16, (170, 220, 170))
                if action:
                    self.buttons.append((r, lambda s=s: action(s)))
            total = len(items)
            if total > cols * maxrows:
                self.text(f"Scroll for more ({total} stacks)", (gx, y + h - 60), 18, GREY)

        def eat_lbl(s):
            it = ITEMS[s["name"]]
            return "click: eat/drink" if (it["hunger"] or it["thirst"] or it["heal"] > 0) else ""

        if chest:
            def to_chest(s):
                n = self.add_item(s["name"], s["value"], s["mut"], s["q"], s["count"], self.chest)
                s["count"] -= n
                if s["count"] <= 0:
                    self.bag.remove(s)
                if n == 0:
                    self.note("Storage full! Upgrade it in the SHOP.", RED)

            def to_bag(s):
                n = self.add_item(s["name"], s["value"], s["mut"], s["q"], s["count"])
                s["count"] -= n
                if s["count"] <= 0:
                    self.chest.remove(s)
            grid(self.bag, x + 20, f"Backpack {self.count(self.bag)}/{self.bag_cap()}", to_chest, lambda s: "click: store")
            grid(self.chest, x + 40 + area_w, f"Storage chest {self.count(self.chest)}/{self.chest_cap}", to_bag,
                 lambda s: "click: take")
            self.button((x + 20, y + h - 52, 200, 38), "STORE ALL", lambda: [to_chest(s) for s in list(self.bag)], GREEN, size=22)
            self.button((x + 40 + area_w, y + h - 52, 200, 38), "TAKE ALL", lambda: [to_bag(s) for s in list(self.chest)],
                        BLUE, size=22)
        else:
            grid(self.bag, x + 20, f"Backpack {self.count(self.bag)}/{self.bag_cap()}   ({BAGS[self.tools['bag']][0]})",
                 self.eat, eat_lbl)
            self.text(f"Fish discovered: {len(self.discovered)}/{len(FISH)}      Pets: {len(self.pets)}      "
                      f"Seeds: " + ", ".join(f"{k} x{v}" for k, v in self.seeds.items() if v), (x + 20, y + h - 40), 20,
                      (200, 210, 230))

    def menu_home(self):
        self.menu_inv(True)

    def menu_skills(self):
        x, y, w, h = self.panel("UPGRADE TREE")
        self.text(f"Level {self.level}  -  level up by doing anything! Upgrades cost coins.", (x + 24, y + 66), 22, (200, 220, 255))
        cw = (w - 40) // 7
        bh = 104
        tip = ""
        for c, b in enumerate(BRANCHES):
            self.text(b, (x + 20 + c * cw + cw // 2, y + 104), 22, GOLD, "c")
        for s in SKILLS:
            sid, name, desc, cost, lvl, pre, c, r = s
            bx, by = x + 20 + c * cw + 4, y + 124 + r * (bh + 12)
            rect = pygame.Rect(bx, by, cw - 8, bh)
            if pre:
                pygame.draw.line(self.screen, GREEN if pre in self.skills else (80, 80, 90), (rect.centerx, by - 12),
                                 (rect.centerx, by), 4)
            owned = sid in self.skills
            avail = not owned and (pre is None or pre in self.skills) and self.level >= lvl
            col = (40, 120, 70) if owned else (PANEL3 if avail else (50, 52, 62))
            if avail and self.coins >= cost:
                col = (120, 80, 200)
            pygame.draw.rect(self.screen, col, rect, border_radius=10)
            pygame.draw.rect(self.screen, GOLD if avail else shade(col, 40), rect, 2, border_radius=10)
            for i, l in enumerate(wrap(self.font(20), name, cw - 20)[:2]):
                self.text(l, (rect.centerx, by + 16 + i * 18), 20, WHITE, "c")
            if owned:
                self.text("OWNED", (rect.centerx, by + bh - 20), 20, (170, 255, 170), "c")
            else:
                self.text(f"{fmt(cost)}c", (rect.centerx, by + bh - 40), 22, GOLD, "c")
                self.text(f"Lv {lvl}", (rect.centerx, by + bh - 20), 18, WHITE if self.level >= lvl else RED, "c")
            if rect.collidepoint(self.mouse):
                tip = f"{name}: {desc}" + ("" if owned else f"   (cost {fmt(cost)} coins, needs level {lvl}"
                                           + (f", needs {SKILL[pre][1]}" if pre else "") + ")")
            if avail:
                self.buttons.append((rect, lambda s=s: self.buy_skill(s)))
        self.text(tip or "Hover an upgrade to see what it does. Click to buy.", (x + w // 2, y + h - 28), 22, WHITE, "c")

    def menu_pets(self):
        x, y, w, h = self.panel("PET HATCHERY")
        self.text("Pets follow you and give BONUSES. Rarer = stronger!", (x + 24, y + 66), 22, (200, 220, 255))
        for i, e in enumerate(EGGS):
            r = pygame.Rect(x + 20, y + 100 + i * 150, 400, 138)
            pygame.draw.rect(self.screen, PANEL2, r, border_radius=12)
            wob = math.sin(self.t * 3 + i) * 3
            pygame.draw.ellipse(self.screen, shade(e[4], -40), (r.x + 22, r.y + 22 + wob, 64, 84))
            pygame.draw.ellipse(self.screen, e[4], (r.x + 18, r.y + 18 + wob, 64, 84))
            pygame.draw.circle(self.screen, WHITE, (r.x + 38, r.y + 40 + int(wob)), 6)
            self.text(e[0], (r.x + 100, r.y + 12), 30, e[4])
            chances = [f"{RAR[k][:4]} {p}%" for k, p in enumerate(e[3]) if p]
            self.text("  ".join(chances[:3]), (r.x + 100, r.y + 44), 18, (210, 210, 230))
            self.text("  ".join(chances[3:]), (r.x + 100, r.y + 62), 18, (255, 200, 120))
            price = f"{e[2]} gems" if e[2] else f"{fmt(e[1])} coins"
            self.button((r.x + 100, r.y + 86, 280, 40), f"HATCH  ({price})", lambda i=i: self.hatch_egg(i),
                        PINK if e[2] else GREEN, size=24)
        px = x + 440
        self.text(f"YOUR PETS   equipped {len(self.equipped)}/{self.pet_slots}", (px, y + 100), 26, GOLD)
        self.button((px + 360, y + 96, 240, 32), "+ PET SLOT (200 gems)", lambda: self.gem_item("slot", 200), PINK, size=20)
        if not self.pets:
            self.text("No pets yet - hatch an egg!", (px, y + 150), 24, GREY)
        order = sorted(range(len(self.pets)), key=lambda i: (i not in self.equipped, -ridx(PET[self.pets[i]][1])))
        start = min(self.scroll, max(0, len(order) - 9))
        for k, i in enumerate(order[start:start + 9]):
            p = PET[self.pets[i]]
            r = pygame.Rect(px, y + 136 + k * 54, w - 460, 48)
            pygame.draw.rect(self.screen, (40, 80, 60) if i in self.equipped else PANEL2, r, border_radius=8)
            self.draw_pet(r.x + 28, r.centery + 3, p[0], 1.1)
            self.text(p[0], (r.x + 56, r.y + 6), 24, RCOL[p[1]])
            self.text(f"{p[1]} - {p[5]}", (r.x + 56, r.y + 28), 18, (210, 210, 230))
            eq = i in self.equipped
            self.button((r.right - 130, r.y + 7, 120, 34), "UNEQUIP" if eq else "EQUIP", lambda i=i: self.toggle_pet(i),
                        RED if eq else GREEN, size=20)
        if len(order) > 9:
            self.text(f"Scroll for more ({len(order)} pets)", (px, y + h - 30), 18, GREY)

    def menu_gems(self):
        x, y, w, h = self.panel("GEM STORE")
        self.text("DEMO ONLY: every price here is FAKE. Nothing is ever charged.", (x + 24, y + 64), 22, (255, 180, 220))
        top = y + 96
        if not self.starter_bought:
            r = pygame.Rect(x + 20, top, w - 40, 76)
            c = shade((200, 50, 140), 25 * math.sin(self.t * 4))
            pygame.draw.rect(self.screen, c, r, border_radius=12)
            sl = int(self.starter_left)
            self.text("STARTER PACK  -90%!", (r.x + 18, r.y + 10), 34, WHITE)
            self.text(f"500 gems + Bamboo Rod + 1,000 coins     Offer ends in {sl // 60}:{sl % 60:02d}!", (r.x + 18, r.y + 46), 22,
                      (255, 230, 250))
            self.button((r.right - 240, r.y + 16, 220, 44), "$0.99  (fake)", self.buy_starter, GOLD, size=26, tcol=BLACK)
            top += 90
        self.text("GET GEMS", (x + 24, top), 28, CYAN)
        for i, (g, price) in enumerate(GEM_PACKS):
            cx, cy = x + 20 + (i % 3) * 152, top + 34 + (i // 3) * 170
            r = pygame.Rect(cx, cy, 144, 160)
            pygame.draw.rect(self.screen, PANEL2, r, border_radius=12)
            for k in range(min(5, 1 + i)):
                gx, gy = r.centerx - 20 + (k % 3) * 20 - (k // 3) * -10, r.y + 34 + (k // 3) * 16
                pygame.draw.polygon(self.screen, CYAN, [(gx, gy - 12), (gx + 10, gy), (gx, gy + 12), (gx - 10, gy)])
            self.text(f"{fmt(g)}", (r.centerx, r.y + 82), 32, CYAN, "c")
            if i == 5:
                self.text("BEST VALUE!", (r.centerx, r.y + 8), 18, GOLD, "mt")
            elif i == 2:
                self.text("POPULAR", (r.centerx, r.y + 8), 18, PINK, "mt")
            self.button((r.x + 10, r.bottom - 50, r.w - 20, 40), price,
                        lambda g=g, p=price: self.fake_buy(p, f"{g} gems",
                                                           lambda: (setattr(self, "gems", self.gems + g),
                                                                    self.do_banner(f"+{fmt(g)} GEMS!", "", CYAN))),
                        GREEN, size=24)
        ix = x + 500
        self.text("SPEND GEMS", (ix, top), 28, PINK)
        for i, (gid, name, desc, cost) in enumerate(GEM_ITEMS):
            r = pygame.Rect(ix, top + 34 + i * 58, w - 520, 52)
            pygame.draw.rect(self.screen, PANEL2, r, border_radius=10)
            self.text(name, (r.x + 14, r.y + 6), 24)
            self.text(desc, (r.x + 14, r.y + 30), 18, (200, 210, 230))
            self.button((r.right - 130, r.y + 8, 120, 36), f"{cost} gems", lambda gid=gid, c=cost: self.gem_item(gid, c), PINK,
                        size=22)

    def menu_cook(self):
        x, y, w, h = self.panel("KITCHEN")
        self.text("Click COOK, then press SPACE when the marker is in the middle!", (x + 24, y + 66), 22, (200, 220, 255))
        for i, rcp in enumerate(RECIPES):
            r = pygame.Rect(x + 20, y + 100 + i * 58, 620, 52)
            ok = self.plan(rcp)
            pygame.draw.rect(self.screen, PANEL2 if ok else (40, 42, 54), r, border_radius=10)
            pygame.draw.circle(self.screen, rcp[6], (r.x + 24, r.centery), 13)
            self.text(rcp[0], (r.x + 48, r.y + 6), 24, WHITE if ok else GREY)
            ings = []
            for spec, n in rcp[1]:
                have = self.have(spec)
                ings.append((f"{n}x {spec if spec not in GENERIC else 'any ' + spec} ({have})", GREEN if have >= n else RED))
            cx_ = r.x + 48
            for t, c in ings:
                rr = self.text(t, (cx_, r.y + 30), 17, c)
                cx_ = rr.right + 12
            self.button((r.right - 110, r.y + 8, 96, 36), "COOK", lambda rc=rcp: self.start_cook(rc), ORANGE, ok, 22)
        rx = x + 660
        nfish = self.have("fish")
        pygame.draw.rect(self.screen, PANEL2, (rx, y + 100, w - 680, 150), border_radius=12)
        self.text("SCALE & FILLET", (rx + 16, y + 110), 28, (250, 170, 150))
        self.text("Turn raw fish into Fish Fillets", (rx + 16, y + 142), 20, (210, 210, 230))
        self.text("(+ Fish Scales). Rare fish = more!", (rx + 16, y + 162), 20, (210, 210, 230))
        self.button((rx + 16, y + 192, w - 712, 44), f"SCALE {nfish} FISH", self.scale_fish, (220, 120, 100), nfish > 0, 24)
        pygame.draw.rect(self.screen, PANEL2, (rx, y + 270, w - 680, 300), border_radius=12)
        self.text("RESTAURANT", (rx + 16, y + 280), 28, GOLD)
        if not self.restaurant:
            for i, l in enumerate(["Open tables outside the kitchen.", "Diners order dishes and pay", "1.5x value + TIPS!"]):
                self.text(l, (rx + 16, y + 314 + i * 22), 20, (210, 210, 230))
            self.button((rx + 16, y + 400, w - 712, 50), "OPEN IT! (400 coins)", self.open_restaurant, GREEN, size=24)
        else:
            self.text(f"OPEN!  Diners waiting: {len(self.diners)}", (rx + 16, y + 314), 22, GREEN)
            for i, d in enumerate(self.diners):
                have = any(s["name"] == d["dish"] for s in self.bag)
                self.text(f"Table {d['seat'] + 1}: {d['dish']}", (rx + 16, y + 344 + i * 26), 20, GREEN if have else WHITE)
            self.text("Walk to a diner and press E to serve.", (rx + 16, y + 540), 18, GREY)

    def open_restaurant(self):
        if self.coins < 400:
            self.note("Need 400 coins to open the restaurant!", RED)
            return
        self.coins -= 400
        self.restaurant = True
        self.diner_t = 3
        self.do_banner("RESTAURANT OPEN!", "Diners will sit at the tables outside", GOLD)

    def draw_cooking(self):
        self.buttons = []
        c = self.cook
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 170))
        self.screen.blit(s, (0, 0))
        self.text(f"COOKING: {c['r'][0]}", (W // 2, 220), 50, ORANGE, "c")
        self.text("Press SPACE (or click) when the marker is in the PINK middle!", (W // 2, 270), 26, WHITE, "c")
        w, x, y = 700, W // 2 - 350, 320
        zones = [(0, 0.15, (90, 60, 50)), (0.15, 0.38, (120, 160, 120)), (0.38, 0.46, GOLD), (0.46, 0.54, PINK),
                 (0.54, 0.62, GOLD), (0.62, 0.85, (120, 160, 120)), (0.85, 1, (90, 60, 50))]
        for a, b, col in zones:
            pygame.draw.rect(self.screen, col, (x + int(a * w), y, int((b - a) * w) + 1, 50))
        pygame.draw.rect(self.screen, WHITE, (x, y, w, 50), 3)
        mx = x + int(c["pos"] * w)
        pygame.draw.polygon(self.screen, WHITE, [(mx - 12, y - 20), (mx + 12, y - 20), (mx, y)])
        pygame.draw.rect(self.screen, WHITE, (mx - 2, y, 4, 50))
        for i, (a, txt) in enumerate(((0.07, "BURNT"), (0.26, "GOOD"), (0.5, "GOURMET"), (0.74, "GOOD"), (0.93, "BURNT"))):
            self.text(txt, (x + int(a * w), y + 70), 20, WHITE, "c")
        self.text(f"{max(0, 7 - c['t']):.1f}s", (W // 2, y + 110), 30, RED if c["t"] > 5 else WHITE, "c")
        self.button((W // 2 - 100, y + 150, 200, 54), "STOP!", self.cook_stop, ORANGE, size=32)

    def draw_hatch(self):
        self.buttons = []
        hd = self.hatch
        t = hd["t"]
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((0, 0, 20, 210))
        self.screen.blit(s, (0, 0))
        e = EGGS[hd["egg"]]
        cx, cy = W // 2, H // 2 - 20
        if t < 1.3:
            wob = math.sin(t * 40) * (6 + t * 10)
            pygame.draw.ellipse(self.screen, e[4], (cx - 60 + wob, cy - 80, 120, 160))
            if t > 0.6:
                pygame.draw.lines(self.screen, BLACK, False, [(cx - 30 + wob, cy - 10), (cx - 10 + wob, cy + 5),
                                                              (cx + 5 + wob, cy - 12), (cx + 25 + wob, cy + 6)], 3)
            self.text("HATCHING...", (cx, cy + 130), 40, WHITE, "c")
        elif t < 3.6:
            u = (t - 1.3) / 2.3
            ease = 1 - (1 - u) ** 3
            name = hd["roll"][int(ease * (len(hd["roll"]) - 1))]
            p = PET[name]
            pygame.draw.rect(self.screen, RCOL[p[1]], (cx - 220, cy - 50, 440, 100), 4, border_radius=14)
            self.draw_pet(cx - 150, cy, name, 2.2)
            self.text(name, (cx - 90, cy - 14), 40, RCOL[p[1]], "ml")
            self.text(p[1], (cx - 90, cy + 22), 26, RCOL[p[1]], "ml")
        else:
            p = PET[hd["pet"]]
            ri = ridx(p[1])
            if not hd["fx"]:
                hd["fx"] = True
                if ri >= 3:
                    self.shake = 0.4
                    self.do_banner(f"{p[1].upper()} PET!!!", p[0], RCOL[p[1]])
            for k in range(12):
                a = self.t * 1.5 + k * math.tau / 12
                pygame.draw.line(self.screen, shade(RCOL[p[1]], -60), (cx, cy - 30),
                                 (cx + math.cos(a) * 300, cy - 30 + math.sin(a) * 300), 6)
            self.draw_pet(cx, cy - 30, p[0], 5)
            self.text(f"You got: {p[0]}!", (cx, cy + 80), 54, RCOL[p[1]], "c")
            self.text(f"{p[1]}  -  {p[5]}", (cx, cy + 124), 28, WHITE, "c")
            self.button((cx - 260, cy + 160, 240, 54), "AWESOME!", lambda: setattr(self, "hatch", None), GREEN, size=30)
            self.button((cx + 20, cy + 160, 240, 54), "HATCH AGAIN", self.hatch_again, PINK, size=28)

    def hatch_again(self):
        i = self.hatch["egg"]
        self.hatch = None
        self.hatch_egg(i)

    def draw_popup(self):
        p = self.popups[-1]
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 160))
        self.screen.blit(s, (0, 0))
        f = self.font(24)
        w = max(560, max(f.size(l)[0] for l in p["lines"]) + 80)
        h = 150 + 30 * len(p["lines"])
        r = pygame.Rect(W // 2 - w // 2, H // 2 - h // 2, w, h)
        pygame.draw.rect(self.screen, PANEL, r, border_radius=18)
        pygame.draw.rect(self.screen, p["col"], r, 4, border_radius=18)
        self.text(p["title"], (r.centerx, r.y + 34), 44, p["col"], "c")
        for i, l in enumerate(p["lines"]):
            self.text(l, (r.centerx, r.y + 76 + i * 30), 24, WHITE, "c")
        bw = min(260, (w - 40) // len(p["buttons"]) - 12)
        total = len(p["buttons"]) * (bw + 12) - 12
        for i, (lbl, cb, col) in enumerate(p["buttons"]):
            self.button((r.centerx - total // 2 + i * (bw + 12), r.bottom - 66, bw, 48), lbl, cb, col,
                        size=24 if len(lbl) < 18 else 20)
            if cb is None:
                self.buttons.append((pygame.Rect(r.centerx - total // 2 + i * (bw + 12), r.bottom - 66, bw, 48), None))

    def draw_title(self):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((0, 0, 20, 150))
        self.screen.blit(s, (0, 0))
        bounce = math.sin(self.t * 2) * 6
        self.text("VALLEY LIFE", (W // 2, 180 + bounce), 120, GOLD, "c")
        self.text("Fish  -  Chop  -  Mine  -  Dig  -  Farm  -  Hunt  -  Cook  -  Pets", (W // 2, 260), 34, WHITE, "c")
        self.text("a Python prototype", (W // 2, 296), 24, (190, 200, 230), "c")
        self.button((W // 2 - 160, 360, 320, 74), "CONTINUE" if self.had_save else "PLAY!", self.start, GREEN, size=44)
        if self.had_save:
            self.button((W // 2 - 120, 452, 240, 48), "New game", lambda: self.start(True), PANEL3, size=26)
        self.text("Gem store prices are FAKE placeholders - no real money, ever.", (W // 2, H - 40), 22, (255, 190, 230), "c")

    def draw(self):
        self.buttons = []
        self.draw_world()
        if self.title:
            self.draw_title()
        else:
            self.draw_hud()
            if self.menu:
                getattr(self, "menu_" + self.menu)()
            if self.cook:
                self.draw_cooking()
            if self.hatch:
                self.draw_hatch()
            self.draw_banner()
        if self.popups:
            self.buttons = []
            self.draw_popup()

    # ------------------------------------------------------------ main loop
    def run(self):
        while True:
            dt = min(self.clock.tick(60) / 1000.0, 0.05)
            self.t += dt
            for ev in pygame.event.get():
                self.handle(ev)
            if not self.title:
                self.update(dt)
            self.draw()
            pygame.display.flip()


if __name__ == "__main__":
    Game().run()
