# JoeBot

the bot of Joe, a collection of useful or trolly tools within the Discord server.


## Getting Started

### Local Development

[Install uv][uv-install] and run `uv sync`. This will:

- Install Python
- Configures a Virtual Environment
- Installs the bot's dependencies

### Docker Compose

The bot can be run using Docker Compose, which will simplify additional depenendencies for development and deployments.

```bash
docker compose up --build -d
```

### Setting up Discord

- Create a [Discord App][discord-app]
- Disable "Public Bot" in the "Bot" tab
- Create and copy the Token in the "Bot" tab to the `.env` file
- Enable the "Privileged Gateway Intents" in the "Bot" tab
- Change the installation context to "Guild Install" in the Installation tab
- run `uv run python install_url.py` to generate an installation URL with default permissions


[uv-install]: https://docs.astral.sh/uv/getting-started/installation/
[discord-app]: https://discord.com/developers/applications/