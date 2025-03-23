**TODO update readme**

# dinobot
Discord Bot for posting a panel of a random Dinosaur Comic. It defaults to panel two, which is usually the funniest, but you can specify another panel number. You know, out of six.

# what?
Yeah, you know, [Dinosaur Comics](https://www.qwantz.com/)?

# why.
Seemed like a good idea. Anyway, you will need to create a bot ([these are good instructions](https://discordpy.readthedocs.io/en/stable/discord.html)), add your token to a config.yaml, invite the bot to a server, and have the code running somewhere. The bot needs permissions to read messages. I made it into a service on a server, but whatever you want to do. It has some dependencies, but they should all be in pypi (bs4, Pillow, discord).

If you want your bot to be happy when it sees dinosaurs, you can upload an emoji to the application in the discord config panel, and then provide emojiid in the yaml file. The format is <:emojiname:emojiid>. A suggested emoji is included in this repo.

For the record, my systemd service file for dinobot looks like this:

```
[Unit]
Description=dinobot

[Service]
WorkingDirectory=/home/ubuntu/dinobot
ExecStart=python3 /home/ubuntu/dinobot/dinobot.py

[Install]
WantedBy=multi-user.target
```
