# HOW TO PLAY - TARGET PRACTICE 3D ARENA

## QUICK START (60 seconds)

### Step 1: Open Command Prompt/Terminal

**Windows:**
- Press `Win + R`
- Type `cmd`
- Press Enter

**Mac:**
- Press `Cmd + Space`
- Type `terminal`
- Press Enter

**Linux:**
- Press `Ctrl + Alt + T`

### Step 2: Go to Game Folder

In the terminal, type:
```
cd Downloads\TargetPracticeGame-main\TargetPracticeGame-main
```

(or navigate to wherever you downloaded the folder)

### Step 3: Run the Game

**Windows:**
```
python launch.py
```

**Mac/Linux:**
```
python3 launch.py
```

You should see:
```
============================================================
TARGET PRACTICE 3D ARENA
============================================================
[1] Start Server
[2] Start Client
[3] Exit
============================================================
[SELECT] Choose an option (1-3): 
```

---

## PLAY ON SAME COMPUTER (LOCAL)

### Terminal 1 - Start Server
```
python launch.py
```
Type: `1`

You should see:
```
============================================================
SERVER STARTED ON 0.0.0.0:5000
Maps: forest, warehouse, desert, ice, hangar
Difficulties: rookie, veteran, elite
============================================================

[CONNECT] 127.0.0.1:xxxxx joined
```

### Terminal 2 - Start Client
Open **another terminal window** in the same folder
```
python launch.py
```
Type: `2`

You'll see:
```
[INPUT] Enter server IP (default: localhost): 
```

Just press **Enter** (localhost means same computer)

The game will launch. You're ready to play!

---

## PLAY ON LOCAL NETWORK (2+ COMPUTERS)

### Find Server Computer's IP

**Windows Server Machine:**
- Open Command Prompt
- Type: `ipconfig`
- Look for "IPv4 Address" (usually 192.168.1.xxx)
- Write it down

**Mac/Linux Server Machine:**
- Open Terminal
- Type: `ifconfig`
- Look for "inet" address (usually 192.168.1.xxx)
- Write it down

### Server Machine
```
python launch.py
Type: 1
```

Leave it running

### Client Machine (Other Computer)
```
python launch.py
Type: 2
```

When it asks:
```
[INPUT] Enter server IP (default: localhost): 
```

Type the server's IP (e.g., `192.168.1.50`) and press Enter

The game will launch and connect to the server.

---

## IN-GAME CONTROLS

### Movement
- **W** - Move Forward
- **S** - Move Backward
- **A** - Strafe Left
- **D** - Strafe Right
- **Space** - Jump
- **Mouse** - Aim/Look Around

### Combat
- **Left Click** - Shoot
- **1** - Switch to Rifle
- **2** - Switch to Shotgun
- **3** - Switch to Sniper

### Menus
- **S** - Open Settings (from menu)
- **L** - View Leaderboard (from menu)
- **ESC** - Return to Menu
- **Q** - Change Difficulty (in settings)
- **E** - Change Map (in settings)

---

## MENU FLOW

### 1. MAIN MENU
```
┌────────────────────────────────────┐
│  TARGET PRACTICE 3D ARENA          │
│  LAN Multiplayer FPS               │
├────────────────────────────────────┤
│  SERVER IP: [localhost        ]    │
│  PLAYER NAME: [Enter name...  ]    │
├────────────────────────────────────┤
│  Press ENTER to PLAY               │
│  L - Leaderboard                   │
│  S - Settings                      │
└────────────────────────────────────┘
```

**What to do:**
1. Enter a player name (1-20 characters)
2. (Optional) Change server IP if not localhost
3. Press **ENTER** to start playing

### 2. SETTINGS MENU
```
┌────────────────────────────────────┐
│  GAME SETTINGS                     │
├────────────────────────────────────┤
│  WEAPON: RIFLE                     │
│  [1] Rifle  [2] Shotgun [3] Sniper│
├────────────────────────────────────┤
│  DIFFICULTY: VETERAN               │
│  [Q] Rookie -> Veteran -> Elite    │
├────────────────────────────────────┤
│  MAP: FOREST                       │
│  [E] Forest -> Warehouse -> ...    │
├────────────────────────────────────┤
│  Press M to Return                 │
└────────────────────────────────────┘
```

**What to do:**
- Press **1/2/3** to pick a weapon
- Press **Q** to cycle through difficulties
- Press **E** to cycle through maps
- Press **M** to go back to main menu

### 3. LEADERBOARD
```
┌────────────────────────────────────┐
│  LEADERBOARD                       │
├────────────────────────────────────┤
│  #1  John        2500   (rifle)    │
│  #2  Sarah       2100   (sniper)   │
│  #3  Mike        1850   (shotgun)  │
│  ...                               │
├────────────────────────────────────┤
│  Press M to Go Back                │
└────────────────────────────────────┘
```

### 4. GAMEPLAY
```
            ║  CROSSHAIR
         ┌──╫──┐
         │  ║  │
    ─────┤  ◉  ├─────
         │  ║  │
         └──╫──┘
   
TIME: 285s              MAP: FOREST
SCORE: 150              DIFFICULTY: VETERAN
KILLS: 15
ACC: 87%
WEAPON: RIFLE

      [RED STICK FIGURE TARGET]
```

**Gameplay:**
- Crosshair in center = your aiming point
- Red stick figures = targets to destroy
- Click to shoot
- Press 1/2/3 to switch weapons mid-game
- Press ESC to return to menu

### 5. GAME OVER
```
┌────────────────────────────────────┐
│  GAME OVER                         │
├────────────────────────────────────┤
│  FINAL SCORE: 250                  │
│  TARGETS DESTROYED: 25             │
│  ACCURACY: 82.5%                   │
├────────────────────────────────────┤
│  Press ENTER to Return to Menu     │
└────────────────────────────────────┘
```

Your score is automatically added to the leaderboard!

---

## TROUBLESHOOTING

### "Python not found"
**Solution:**
1. Download Python 3.10 from https://www.python.org/downloads/
2. During install, CHECK "Add Python to PATH"
3. Restart Command Prompt
4. Try again

### "ModuleNotFoundError: No module named 'arcade'"
**Solution:**
The launcher will auto-install it. Just run:
```
python launch.py
```

It downloads arcade automatically on first run.

### "Connection refused" or "Can't connect to server"
**Solution:**
1. Make sure server is running first
2. Double-check server IP address
   - Windows: `ipconfig` → IPv4 Address
   - Mac/Linux: `ifconfig` → inet
3. Try ping test:
   ```
   ping 192.168.1.50
   ```
   (Replace with actual server IP)

### "Game is very slow/laggy"
**Solution:**
1. Close other programs
2. Move closer to Wi-Fi router
3. Use wired Ethernet if possible
4. Check network: `ping 8.8.8.8` should be <50ms

### "I can't find the game folder"
**Solution:**
1. Open File Explorer (Windows) or Finder (Mac)
2. Look in Downloads folder
3. Find folder named "TargetPracticeGame-main"
4. Right-click → Open Terminal Here (Windows) or Open Terminal (Mac)

---

## GAME RULES

✅ **Objective:** Destroy as many red stick-figure targets as possible in 5 minutes

✅ **Scoring:**
- Each target destroyed = +10 points
- Accuracy matters (tracked at end)

✅ **Weapons:**
- **Rifle** - Balanced, medium fire rate
- **Shotgun** - High damage, close range, wide spread
- **Sniper** - One-shot kills, long range, slow fire rate

✅ **Difficulty:**
- **Rookie** - Slow targets, easy
- **Veteran** - Normal speed, balanced
- **Elite** - Fast targets, very hard

✅ **Leaderboard:**
- Saved automatically after each game
- Shows top 200 scores
- Visible to all players on LAN

---

## TIPS & TRICKS

🎯 **Aiming**
- Keep crosshair on target
- Lead moving targets slightly
- Sniper is hardest but most rewarding

🎯 **Strategy**
- Rifle is most consistent
- Shotgun best when targets get close
- Sniper for long-range practice

🎯 **Performance**
- Stay near Wi-Fi router for multiplayer
- Close Chrome/Discord for better FPS
- Use Ethernet cable for server machine

🎯 **Multiplayer**
- All players see same leaderboard
- Highest score wins
- Each player plays independently
- No PvP (only vs AI targets)

---

## EXAMPLE: FIRST TIME PLAYING

**Step-by-step:**

1. Download game folder
2. Open Command Prompt in the folder
3. Type: `python launch.py`
4. Type: `2` (start client)
5. Press Enter when it asks for server IP
6. Type your name: `John`
7. Press Enter to play
8. Game window opens with menu
9. Press ENTER to start
10. Use WASD + Mouse + Click to play
11. After 5 minutes, game ends and shows score
12. Press ENTER to return to menu

**You're done! You just played Target Practice 3D Arena!**

---

## NEED HELP?

If stuck:
1. Check this README
2. Make sure Python 3.9+ is installed
3. Make sure game folder is downloaded
4. Restart Command Prompt/Terminal
5. Try again

**Enjoy the game! 🎯**
