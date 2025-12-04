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

### 4. Restart your app
```bash
./rema.sh
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