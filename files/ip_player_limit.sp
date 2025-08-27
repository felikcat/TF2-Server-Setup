#pragma semicolon 1
#pragma newdecls required

#include <sourcemod>

#define PLUGIN_VERSION "1.0"

public Plugin myinfo = 
{
    name = "IP Player Limit",
    author = "Generic",
    description = "Limits the number of players per IP address to a maximum of 2",
    version = PLUGIN_VERSION,
    url = ""
};

public void OnPluginStart()
{
    // No additional initialization required for this plugin.
}

public void OnClientConnected(int client)
{
    if (IsFakeClient(client))
    {
        return;
    }

    char clientIP[16];
    GetClientIP(client, clientIP, sizeof(clientIP));

    int count = 0;
    for (int i = 1; i <= MaxClients; i++)
    {
        if (IsClientConnected(i) && i != client)
        {
            char otherIP[16];
            GetClientIP(i, otherIP, sizeof(otherIP));
            if (StrEqual(clientIP, otherIP, true))
            {
                count++;
            }
        }
    }

    if (count >= 2)
    {
        KickClient(client, "This server limits connections to 2 players per IP address.");
    }
}