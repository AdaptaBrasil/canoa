# Linux `Screen` Command Guide

## What is Screen?
Screen is a terminal multiplexer that allows you to run processes in the background and reconnect to them later, even after disconnecting from SSH.

## Installation
```bash
# Ubuntu/Debian
sudo apt-get install screen

# CentOS/RHEL/Fedora
sudo yum install screen

# Arch Linux
sudo pacman -S screen
```

## Basic Usage

### Start a New Screen Session
```bash
# Start a named session
screen -S canoa

# Run Canoa
/home/desenv/canoa/carranca$../rema.sh

# Detach (continues running in background)
## control + A, then D
Ctrl+A → D

# Later, Reattach
screen -r canoa
```

## Key Commands (Inside Screen)

| Command   | Action
|-----------|--------
| Ctrl+A → D | **D**etach from screen (process keeps running) |
| Ctrl+A → K | **K**ill current screen window |
| Ctrl+A → C | **C**reate new window in session |
| Ctrl+A → N | **N**ext window |
| Ctrl+A → P | **P**revious window |
| Ctrl+A → " | List all windows |
| Ctrl+A → ? | Show help |

## Managing Screen Sessions

### List All Sessions
```bash
screen -ls
# Output example:
# There are screens on:
#     12345.canoa    (Detached)
#     67890.backup_job   (Attached)
```

### Reattach to Session
```bash
# Reattach to named session
screen -r canoa

# Reattach by ID
screen -r 12345

# Reattach to the only session (if only one exists)
screen -r

# Force reattach (if already attached elsewhere)
screen -dr canoa
```

### Kill/Terminate Session
```bash
# Kill specific session
screen -S canoa -X quit

# Kill by ID
screen -X -S 12345 quit

# Or attach and exit normally
screen -r canoa
exit
```

## Practical Examples

### Example 1: Long-Running Python Script
```bash
# Start named screen
screen -S data_processing

# Run your script
python process_data.py

# Detach: Ctrl+A then D
# Script continues running in background
```

### Example 2: Server/Service
```bash
# Start web server in screen
screen -S webserver
cd /var/www/myapp
python -m http.server 8080

# Detach and logout - server keeps running
```

### Example 3: Multiple Commands
```bash
# Start screen
screen -S monitoring

# Run first command
top
# Ctrl+A then C (create new window)

# Run second command
tail -f /var/log/syslog
# Ctrl+A then C (create another window)

# Navigate: Ctrl+A then N (next) or P (previous)
```

### Example 4: Direct Launch (Daemon Mode)
```bash
# Start process directly in detached screen
screen -dmS backup_job bash -c "rsync -avz /source /backup; echo Done"

# Check it's running
screen -ls

# View output later
screen -r backup_job
```

### Example 5: Script with Logging
```bash
# Run script with output logging
screen -dmS myapp bash -c "python app.py 2>&1 | tee app.log"

# View live output
screen -r myapp
```

## Advanced Tips

### Auto-name Windows
```bash
# In screen, run:
Ctrl+A then :
# Then type: title MyWindowName
```

### Send Commands to Detached Screen
```bash
# Execute command in detached screen
screen -S canoa -X stuff "ls -la\n"

# Useful for automation
screen -S backup -X stuff "backup.sh\n"
```

### Check if Process is Still Running
```bash
# List sessions
screen -ls

# If session exists, process is likely running
# Attach to verify
screen -r canoa
```

### Screen Configuration (~/.screenrc)
```bash
# Create ~/.screenrc for custom settings
echo "startup_message off" >> ~/.screenrc
echo "defscrollback 10000" >> ~/.screenrc
echo "hardstatus alwayslastline '%{= kG}[%{G}%H%{g}][%= %{=kw}%?%-Lw%?%{r}


# How to Fix a Screen Detached from Terminal (Zombie Process)

## Symptoms
Screen session exists, process is running, but terminal is "dead" (Ctrl+C doesn't work)

## Steps to Fix

### 1. Find the running process
```bash
ps aux | grep flask
# Note the PID (e.g., 388052)
```

### 2. Kill the process
```bash
kill <PID>
# or force kill if needed: kill -9 <PID>
```

### 3. Reattach to screen
```bash
screen -r canoa
# Verify you're in screen: echo $STY
```

### 4. Restart your app from
```bash
/home/desenv/canoa/carranca$./rema.sh
```

## Useful Commands

- `screen -ls` - list all screen sessions
- `ps -t pts/X` - see what's running on a specific terminal
- `ps -ef | grep <PID>` - find details about a process
- `sudo lsof -i :5000` - check what's using a specific port
- `Ctrl+A, D` - detach from screen (keeps app running)
- `screen -r <name>` - reattach to screen
- `echo $STY` - check if you're inside a screen session

## Understanding pts/X
- **pts** = Pseudo Terminal Slave
- Each terminal window/session gets a unique number (pts/0, pts/1, pts/5, etc.)
- It's like a unique ID for each terminal instance

## Notes
- Always start Flask with `host='0.0.0.0'` to make it accessible from the internet
- Screen keeps processes running even after you disconnect
- Use screen for long-running processes that need to survive terminal closures