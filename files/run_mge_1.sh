#!/bin/sh

screen -DmS "tf2-mge-1" "/home/steam/tf2_server/srcds_run_64" -console -usercon +ip YOUR_GAME_SERVERS_EXTERNAL_IP -game tf -insecure +map mge_training_v8_beta4b +servercfgfile "server_mge_1.cfg" +sv_setsteamaccount YOUR_STEAM_GLST_KEY_HERE -port 27015 -autoupdate -steamcmd_script "/home/steam/tf2_autoupdate.txt" -steam_dir "/home/steam/tf2_server"
