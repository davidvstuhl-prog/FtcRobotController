# Valley Life (prototype)

A playable Python/pygame prototype of a "do everything in one valley" survival + collecting game,
built to show that a game mixing fishing, farming, digging, mining, hunting, cooking and pets is doable.

## Run it

```bash
pip install pygame
python valley_life.py
```

Everything is in a single file (`valley_life.py`). The map is generated the same way every time, and
your progress saves to `valley_save.json` (autosave every minute and on quit). Delete that file, or
click **New game** on the title screen, to start over.

## Controls

| Key | Action |
|-----|--------|
| WASD / arrows | walk (SHIFT = sprint) |
| E | use: chop tree, mine rock (hold), plant/harvest, drink, talk to NPCs, serve diners, enter buildings |
| Hold F, aim with mouse, release | cast your fishing rod. Press F / SPACE / click on the **!** |
| Hold SPACE or mouse | reel: keep the fish inside the green box |
| Hold Q | dig up treasure (on grass/sand/cave), or dive for loot in deep water |
| Left click | throw spear / shoot (hunting) |
| R | eat the best food in your bag |
| B | build a campfire (3 logs) to cook anywhere |
| Z / mouse wheel | change selected seed |
| TAB / K / P / G / H | backpack / upgrade tree / pets / gem store / help |

## What's in it

- **Map**: mountains around a valley, a river, a lake and a pond, forests, a cave with ore, a town with buildings, garden plots
- **Survival**: health, food, water and oxygen (swimming) bars; you faint if health hits 0
- **Fishing**: power-meter cast, bite timing, a reel minigame; 24 fish across river/lake/deep/cave zones,
  day-only and night-only fish, weights, mutations (Shiny/Golden/Rainbow/Cosmic), worm bait, a list of fish you've found
- **Woodcutting**: timing-meter chops (PERFECT hits = 3x damage), 5 tree types, rare Ancient trees, trees grow back
- **Mining**: cave ore with pickaxe tiers (Stone → Mythril)
- **Digging**: hold-to-dig treasure with luck rolls, sparkle spots, holes that refill; diving uses up oxygen
- **Farming**: 12 plots (6 to unlock), 9 crops that grow in real time, Golden/Rainbow/Wet mutations, rain speeds growth
- **Hunting**: rabbits, deer, boars, bears, wolves at night, a rare Golden Stag; animals that run away or attack
- **Cooking**: scale & fillet fish, 9 recipes, a timing minigame that sets quality (Burnt → Gourmet)
- **Restaurant**: diners sit down, order dishes, pay and tip
- **NPC buyers**: townsfolk show up wanting wood, fish, ore, food and so on
- **Progression**: levels, an upgrade tree with 28 nodes, 6 gear lines (rods, axes, pickaxes, shovels, weapons, backpacks),
  storage chest, a quest chain with an arrow pointing to the goal, daily login reward
- **Pets**: 3 eggs, 18 pets in 6 rarities, a hatch animation, equip slots, pet bonuses
- **Gem store**: premium currency, potions, VIP, a limited-time starter pack. **All real-money prices are fake
  placeholders. Nothing is ever charged.**
