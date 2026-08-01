"""Mock game-ops data for the game-ops MCP server."""

SERVERS = {
    "SRV-1001": {"region": "us-east", "players_online": 842, "status": "healthy"},
    "SRV-1002": {"region": "eu-west", "players_online": 1290, "status": "degraded"},
    "SRV-1003": {"region": "us-west", "players_online": 410, "status": "healthy"},
}

INCIDENTS = [
    {"incident_id": "INC-501", "region": "eu-west", "summary": "Matchmaking latency spike above 2s p95", "status": "open"},
    {"incident_id": "INC-502", "region": "us-east", "summary": "Leaderboard write lag", "status": "resolved"},
]
