# Setup Guide - Target Practice Game

## Prerequisites

- **Python 3.7 or higher**
- **pip** (Python package manager)
- **Network connection** (LAN)

## Step-by-Step Setup

### 1. Clone or Download the Repository

```bash
git clone https://github.com/levi2134i/TargetPracticeGame.git
cd TargetPracticeGame
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or if you use Python 3 specifically:

```bash
pip3 install -r requirements.txt
```

### 3. Find Your Server Machine IP

**Windows:**
```bash
ipconfig
```
Look for "IPv4 Address" under your network adapter (usually something like `192.168.x.x`)

**Mac/Linux:**
```bash
ifconfig
```
Look for `inet` address under your active network interface

### 4. Start the Server

**Windows:**
```bash
python server.py
```

**Mac/Linux:**
```bash
python3 server.py
```

You should see:
```
[SERVER] Started on 0.0.0.0:5000
[SERVER] Waiting for connections...
```

**Note the IP address of this machine!**

### 5. Connect Clients

On each client machine, run:

**Windows:**
```bash
python client.py <SERVER_IP>
```

**Mac/Linux:**
```bash
python3 client.py <SERVER_IP>
```

Replace `<SERVER_IP>` with the actual server IP. For example:

```bash
python3 client.py 192.168.1.50
```

### 6. Easy Launch Scripts

For convenience, use the provided scripts:

**Windows:**
- Server: Double-click `run_server.bat`
- Client: Double-click `run_client.bat` and enter the server IP

**Mac/Linux:**
```bash
chmod +x run_server.sh run_client.sh

# Terminal 1 (Server)
./run_server.sh

# Terminal 2+ (Clients)
./run_client.sh
```

## Network Setup for Multiple Machines

### Local Area Network (LAN) Play

1. Ensure all machines are connected to the **same WiFi network** or **Ethernet switch**
2. No internet required - purely local network
3. Server IP must be accessible from client machines

### Testing Connectivity

**Windows:**
```bash
ping <server_ip>
```

**Mac/Linux:**
```bash
ping -c 4 <server_ip>
```

If ping succeeds, network connectivity is working.

### Firewall Configuration

If clients can't connect, you may need to allow port 5000 through your firewall:

**Windows Firewall:**
1. Open "Windows Defender Firewall with Advanced Security"
2. Click "Inbound Rules" → "New Rule"
3. Select "Port" → Next
4. Select "TCP" and enter port "5000" → Next
5. Allow the connection → Next → Finish

**macOS:**
```bash
sudo defaults write /Library/Preferences/com.apple.alf globalstate -int 1
```

**Linux (UFW):**
```bash
sudo ufw allow 5000/tcp
```

## Game Settings

### Customize Server

Edit `server.py` to change:

```python
# Change port (default 5000)
server = GameServer(host='0.0.0.0', port=5000)

# Max players, game duration, etc.
# Modify constants in the code
```

### Customize Client

Edit `client.py` to change:

```python
# Game duration (seconds)
self.game_duration = 300  # 5 minutes

# Player speed
self.player.speed = 5

# Window resolution
self.width = 800
self.height = 600
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'pygame'"

```bash
pip install pygame
```

### "Connection refused" or "Can't connect to server"

1. Verify server is running: `python server.py`
2. Check correct IP address
3. Test with: `ping <server_ip>`
4. Check firewall settings (port 5000)

### "Address already in use"

Port 5000 is already taken. Change it in `server.py`:

```python
server = GameServer(port=5001)  # Use different port
```

Then connect clients with:
```bash
python client.py <SERVER_IP>:5001
```

### Game is slow or laggy

1. Check network latency: `ping <server_ip>`
2. Reduce number of targets in `client.py`
3. Close other network applications
4. Ensure server has adequate resources

## Performance Optimization

### For More Players

1. Run server on a dedicated machine
2. Increase server-side buffer sizes
3. Reduce graphics quality on clients if needed

### For Better Latency

1. Use wired Ethernet instead of WiFi
2. Ensure router isn't overloaded
3. Keep distance to WiFi router minimal

## Next Steps

1. **Read** `README.md` for game controls and features
2. **Play** your first game!
3. **Customize** settings as desired
4. **Invite friends** to play over LAN

## Still Having Issues?

- Check server console for error messages
- Verify network connectivity between machines
- Try running on localhost first: `python client.py localhost`
- Check Python version: `python --version`

Good luck and have fun! 🎯
