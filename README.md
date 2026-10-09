# Target Practice - 2D LAN Shooting Game

A fun, multiplayer 2D target practice shooting game with LAN TCP networking support, multiple maps, leaderboards, and configurable game settings.

## Features

✅ **2D Graphics** - Fast-paced pixel-based shooting action  
✅ **LAN TCP Multiplayer** - Play with friends over local network  
✅ **Multiple Maps** - Forest, Urban, Desert, Arctic environments  
✅ **Leaderboards** - Global score tracking and rankings  
✅ **Game Settings** - Adjustable difficulty and game modes  
✅ **Real-time Stats** - Track kills, accuracy, and scores  
✅ **Cross-platform** - Windows, Mac, Linux support  

## Requirements

- Python 3.7+
- pygame 2.5.2+

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running the Game

### Step 1: Start the Server

Run this on one machine (the "host"):

```bash
python server.py
```

The server will start listening on `0.0.0.0:5000`. Note the IP address of the machine running the server.

### Step 2: Connect Clients

On each client machine, run:

```bash
python client.py <SERVER_IP>
```

Replace `<SERVER_IP>` with the actual IP address of the server machine. For example:

```bash
python client.py 192.168.1.100
```

If playing on the same machine, use:

```bash
python client.py localhost
```

## How to Play

### Main Menu
- **Enter Server IP**: Type the IP address of the game server
- **Enter Player Name**: Choose your player name
- **Press ENTER**: Connect and start playing
- **Press L**: View the global leaderboard

### In-Game Controls

| Control | Action |
|---------|--------|
| **W** | Move Up |
| **A** | Move Left |
| **S** | Move Down |
| **D** | Move Right |
| **Mouse Move** | Aim |
| **Left Click** | Shoot |
| **ESC** | Return to Menu |

### Scoring

- **Hit Target**: +10 points
- **Destroy Target**: +1 kill
- **Game Duration**: 5 minutes per match
- **Accuracy**: Tracked throughout the game

## Game Modes

### Targets
Destroy moving targets to earn points. Targets move randomly around the map and bounce off walls. When you destroy a target, a new one spawns.

### Maps

1. **Forest** (Green) - Classic nature setting
2. **Urban** (Gray) - City environment
3. **Desert** (Sandy) - Desert wasteland
4. **Arctic** (Light Blue) - Frozen terrain

## Server Configuration

Edit `server.py` to customize:

```python
server = GameServer(host='0.0.0.0', port=5000)  # Change port here
```

## Leaderboard

Scores are automatically saved to `leaderboard.json` on the server. The leaderboard persists between game sessions and tracks:

- Player name
- Final score
- Map played
- Timestamp

Top 100 scores are maintained.

## Network Requirements

- TCP port 5000 (default) must be open
- All clients must be able to reach the server IP
- Low latency recommended (LAN play)
- Works best with <100ms ping

## Troubleshooting

### Can't connect to server
- Verify server is running: `python server.py`
- Check correct IP address of server
- Ensure firewall allows port 5000
- Test connectivity: `ping <server_ip>`

### Leaderboard not updating
- Check `leaderboard.json` exists in the server directory
- Verify server has write permissions
- Restart server if needed

### Game lags
- Reduce number of targets
- Move closer to server (lower latency)
- Close other network applications

## Game Development

### Architecture

**Server** (`server.py`):
- Manages game state
- Handles player connections
- Broadcasts updates
- Maintains leaderboard
- Runs on port 5000

**Client** (`client.py`):
- Handles rendering
- Processes player input
- Communicates with server
- Manages local game state

### Protocol

JSON-based TCP protocol over raw sockets:

```json
{
  "type": "update_score",
  "player_id": "192.168.1.50:12345",
  "score": 250,
  "kills": 25,
  "accuracy": 85.5
}
```

## Future Features

- [ ] Weapon variations
- [ ] Power-ups (rapid fire, accuracy boost)
- [ ] Enemy AI
- [ ] Competitive modes (team vs team)
- [ ] Custom game settings
- [ ] Replay system
- [ ] Sound effects & music

## Performance

- **Tickrate**: 60 FPS client-side
- **Network Updates**: Real-time with buffering
- **Max Players**: Tested up to 10 simultaneous clients
- **Latency**: Optimized for <100ms network delay

## License

MIT License - Feel free to modify and distribute

## Contributing

Fork, modify, and submit pull requests. All contributions welcome!

## Support

For issues, questions, or suggestions, open an issue on GitHub.

---

**Have fun shooting! 🎯**
