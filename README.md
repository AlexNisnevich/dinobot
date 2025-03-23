**TODO update readme**

# Description

Discord Bot for posting [Dinosaur Comics](https://www.qwantz.com/) panels. 

# Installation

## Code

Install with virtualenv:
```
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Bot

1. Follow [these instructions](https://discordpy.readthedocs.io/en/stable/discord.html) to initialize the bot itself. The bot needs permissions to read messages.
2. Save your token to the `DISCORD_TOKEN` environment variable.
3. (optional) To enable dinosaur emoji responses, upload the included dino emoji in the Discord config panel and save the emoji ID in the format `<:emojiname:emojiid>` to the `EMOJI_ID` environment variable.
4. Invite Dinobot to your server.

# Usage

## Running the bot

To run the bot locally:
```python dinobot.py```

On a Linux server you may want to use `nohup` to keep the process running when you close the terminal:
```nohup python dinobot.py`

Or set it up as a systemd service. You can use this as a model for a systemd service file:
```
[Unit]
Description=dinobot

[Service]
WorkingDirectory=/home/ubuntu/dinobot
ExecStart=python3 /home/ubuntu/dinobot/dinobot.py

[Install]
WantedBy=multi-user.target
```

## Interacting with the bot

When the bot sees a message starting with `$qwantz`, it will try to respond with a Dinosaur Comics panel. Any exception will result in the bot sending an (unhelpful) error message instead.

Supported `$qwantz` syntax:
```
    $qwantz 				- post 2nd panel of random comic
    $qwantz [n]				- if n>5, post 2nd panel of nth comic
                            - if n≤5, post nth panel of random comic
    $qwantz [n] [i]			- post ith panel of nth comic
    $qwantz [search phrase] - post a panel containing that phrase (if any)
```

If an `EMOJI_ID` environment variable is provided, the bot will also respond with that emoji to messages containing variations on the words "dino" or "dinosaur".
