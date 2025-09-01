import os
import sys
import time
import subprocess
import socket
import psutil
import systemd.daemon

GLST_KEY = os.environ.get('GLST_KEY')

EXTERNAL_IP = "placeholder"
SERVER_PORT = "27017"
SERVER_DIR = "/home/steam/tf2_server"
SESSION_NAME = "tf2-minecraftworld"

CONSOLE_LOG = os.path.join(SERVER_DIR, "tf/console.log")

# Define the command to launch SRCDS
cmd = [
    os.path.join(SERVER_DIR, "srcds_run"),
    "-console",
    "-usercon",
    "+ip", EXTERNAL_IP,
    "-game", "tf",
    "+map", "minecraftworld_fix_v16",
    "+servercfgfile", "server_minecraftworld.cfg",
    "+mapcyclefile", "mapcycle_minecraftworld.txt",
    "+sv_setsteamaccount", GLST_KEY,
    "-port", SERVER_PORT,
    "-autoupdate",
    "-steamcmd_script", "/home/steam/tf2_autoupdate.txt",
    "-steam_dir", "/home/steam/.steam/steam/steamcmd",
    "-condebug",
    "-maxplayers", "32",
    "+sm_basepath", "addons/sourcemod_minecraftworld",
]

# Start SRCDS in a detached screen session and capture the PID
proc = subprocess.Popen(['screen', '-dmS', SESSION_NAME] + cmd)
screen_pid = proc.pid

# Notify systemd of the main PID
try:
    systemd.daemon.notify(f"MAINPID={screen_pid}")
except ImportError:
    print("systemd.daemon not available; skipping PID notification", file=sys.stderr)

# Wait for SRCDS to start by detecting "Connection to Steam servers successful." in console.log
while not os.path.exists(CONSOLE_LOG):
    time.sleep(1)
while True:
    with open(CONSOLE_LOG, "r") as f:
        content = f.read()
        if "Connection to Steam servers successful." in content:
            break
    time.sleep(1)

# Function to check if the screen session is running
def is_screen_running(session_name):
    try:
        output = subprocess.check_output(['screen', '-list'])
        return session_name in output.decode()
    except subprocess.CalledProcessError:
        return False

# Function to probe the server using Source Engine query
def probe_server():
    IP = "127.0.0.1"
    PORT = int(SERVER_PORT)
    QUERY = b'\xFF\xFF\xFF\xFF\x54Source Engine Query\x00'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    try:
        sock.sendto(QUERY, (IP, PORT))
        data, addr = sock.recvfrom(1024)
        if data:
            return True
        else:
            return False
    except Exception:
        return False
    finally:
        sock.close()

# Monitoring loop
while True:
    if not is_screen_running(SESSION_NAME):
        print("Server stopped normally", file=sys.stderr)
        sys.exit(0)
    # Check for ongoing updates before probing
    try:
        subprocess.check_output(["pgrep", "-f", "steamcmd"])
        time.sleep(5)
        continue
    except subprocess.CalledProcessError:
        pass
    # Probe the server; if no response, force termination
    if not probe_server():
        print("Server appears hung; terminating", file=sys.stderr)
        subprocess.call(['screen', '-S', SESSION_NAME, '-X', 'quit'])
        time.sleep(5)
        sys.exit(1)
    time.sleep(10)
