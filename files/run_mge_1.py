import os
import sys
import time
import subprocess
import socket

GLST_KEY = os.environ.get('GLST_KEY')

EXTERNAL_IP = "placeholder"
SERVER_PORT = "27015"

SERVER_DIR = "/home/steam/tf2_server"
CONSOLE_LOG = os.path.join(SERVER_DIR, "tf/console.log")

# Launch SRCDS with subprocess
cmd = [
    os.path.join(SERVER_DIR, "srcds_run_64"),
    "-console",
    "-usercon",
    "+ip", EXTERNAL_IP,
    "-game", "tf",
    "-insecure",
    "+map", "mge_training_v8_beta4b",
    "+servercfgfile", "server_mge_1.cfg",
    "+sv_setsteamaccount", GLST_KEY,
    "-port", SERVER_PORT,
    "-autoupdate",
    "-steamcmd_script", "/home/steam/tf2_autoupdate.txt",
    "-steam_dir", "/home/steam/.steam/steam/steamcmd",
    "-condebug"
]

proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

# Wait for SteamCMD to finish if an update is happening
while True:
    try:
        subprocess.check_output(["pgrep", "-f", "steamcmd"])
        time.sleep(5)
    except subprocess.CalledProcessError:
        break

# Wait for SRCDS to start by detecting "Connection to Steam servers successful." in console.log
while not os.path.exists(CONSOLE_LOG):
    time.sleep(1)

while True:
    with open(CONSOLE_LOG, "r") as f:
        content = f.read()
        if "Connection to Steam servers successful." in content:
            break
    time.sleep(1)

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
    if proc.poll() is not None:
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
        proc.terminate()
        time.sleep(5)
        if proc.poll() is None:
            proc.kill()
        sys.exit(1)

    time.sleep(10)
