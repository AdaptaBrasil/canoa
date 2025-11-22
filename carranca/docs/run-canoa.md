# Canoa Screen Commands

```screen``` refers to the Linux command-line tool GNU Screen, a terminal multiplexer.

It allows you to:
   - Start a command (like flask run)
   - Detach from it and close your SSH/RDP session
   - Reattach later and continue exactly where you left off
   - -Keep long-running processes alive even if your connection drops

GNU Screen is not a windowing system nor physical terminal. It is a software tool that creates “virtual terminals” inside your real terminal.

## Start Canoa (in a screen session)
```
screen -S canoa
```

Then, inside screen, start your app normally
(see )
```
/home/desenv/canoa/carranca$ ../rema.sh

```

## Detach from screen (leave it running)
Press: Ctrl + A then D

## List screen sessions
```
screen -ls
```

## Reattach to an existing screen session
```
screen -r canoa
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

## Start a fresh Canoa instance
```
screen -S canoa
flask run
```

#