#!/bin/sh

SERVER_NAME="tf2-mge-1"
EXTERNAL_IP="changeme"
export SERVER_PORT="27015"
# Get your key at: https://steamcommunity.com/dev/managegameservers
# Note that each server requires a different key.
STEAM_GLST_KEY="changeme"

# Start the server in a detached screen session
screen -dmS ${SERVER_NAME} "/home/steam/tf2_server/srcds_run_64" -console -usercon +ip ${EXTERNAL_IP} -game tf -insecure +map mge_training_v8_beta4b +servercfgfile "server_mge_1.cfg" +sv_setsteamaccount ${STEAM_GLST_KEY} -port ${SERVER_PORT} -autoupdate -steamcmd_script "/home/steam/tf2_autoupdate.txt" -steam_dir "/home/steam/.steam/steam/steamcmd"

# Wait for SteamCMD to finish if an update is happening
while pgrep -f steamcmd >/dev/null; do
	sleep 5
done

# HACK (hardcoded value): Wait for SRCDS to finish
sleep 60

# A Source Engine query used to ensure the server never hangs after a restart, or other issues that keep it down
probe_server() {
	python3 - <<EOF
import socket
import os

IP = 127.0.0.1
PORT = int(os.environ.get('SERVER_PORT'))
QUERY = b'\xFF\xFF\xFF\xFF\x54Source Engine Query\x00'

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)

try:
    sock.sendto(QUERY, (IP, PORT))
    data, addr = sock.recvfrom(1024)
    if data:
        exit(0)
    else:
        exit(1)
except Exception:
    exit(1)
EOF
	return $?
}

# Monitoring loop
while true; do
	# Check if the screen session is still running
	if ! screen -list | grep -q "${SERVER_NAME}"; then
		echo "Server stopped normally" >&2
		exit 0
	fi

	# Check for ongoing updates before probing
	if pgrep -f steamcmd >/dev/null; then
		sleep 5 # Pause monitoring during update
		continue
	fi

	# Probe the server; if no response, force restart
	if ! probe_server; then
		echo "Server appears hung; terminating" >&2
		screen -S "${SERVER_NAME}" -X quit
		if [ $? -ne 0 ]; then
			echo "Failed to quit screen session ${SERVER_NAME}" >&2
		fi
		exit 1
	fi

	sleep 10 # Check every 10 seconds
done
