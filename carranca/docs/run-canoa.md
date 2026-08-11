# Canoa Screen Commands

```screen``` refers to the Linux command-line tool GNU Screen, a terminal multiplexer.

It allows you to:
   - Start a command (like flask run)
   - Detach from it and close your SSH/RDP session
   - Reattach later and continue exactly where you left off
   - -Keep long-running processes alive even if your connection drops

GNU Screen is not a windowing system nor physical terminal. It is a software tool that creates “virtual terminals” inside your real terminal.

## Start Canoa (in a screen session)

1. Check no Canoa session is already running:
   ```
   screen -ls
   ```
2. If one is active, kill it (replace `12345` with the actual session id):
   ```
   screen -X -S 12345 quit
   ```
3. Start a new screen session:
   ```
   screen -S canoa
   ```
4. Inside the screen session, go to the app dir and launch it -- no need to activate
   the venv yourself, `rema.sh` does it (`source ../.venv/bin/activate`):
   ```
   cd /home/desenv/canoa/carranca
   ../rema.sh
   ```
5. Detach, leaving it running: `Ctrl + A` then `D`

## Detach from screen (leave it running: stay detached)
Press: Ctrl + A then D

## List screen sessions
```
screen -ls
```

## Reattach to an existing screen session
```
screen -r canoa
```

## Attach to an attached (by someone else: Detach-Reattach) screen session
```
screen -dr 123456.canoa
```

## Kill a screen session
Outside screen:
```
screen -S canoa -X quit
```

Inside screen:
Press: Ctrl + A then K, confirm with y

## Kill running Canoa processes
```
ps aux | grep flask
kill -9 <PID>
```

## Kill running Canoa processes


# Power of Linux

## Working over SSH, current shell session:
```
    exit
    `or Ctrl + D
```
## Power off immediately
```
logout && sudo shutdown -h now
```

---
<small>_eof_</small>
