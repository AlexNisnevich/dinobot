from bs4 import BeautifulSoup
import requests
from PIL import Image
from io import BytesIO
import discord
from discord.ext import commands
import uuid
import os
import yaml
import random
import re

# table of crop rectangles for the various panels. These were determined
# using a paint program on a downloaded comic.
CROP_RECTANGLES = [
	(0, 0, 297, 298),
	(298, 0, 458, 298),
	(457, 0, 899, 298),
	(0, 296, 239, 595),
	(237, 296, 604, 595),
	(602, 296, 899, 595),
]

# we have canned error messages for if commands are bogus. They are not helpful.
# they are, however, from the comic. 50? Why not.
ERROR_MESSAGES = [
	"Sherlock Holmes, who we all already deduced was the world's greatest detective, frowned. He was faced with a new crime! And it was a crime unlike any he'd seen before. This crime......was a COMPUTER CRIME.",
	"I can't even use a computer anymore, my hands go right through the keys!",
	"Babbage's Analytical Engine was designed in the 1830s! Sherlock COULD be familiar with basic computer stuff.",
	"A poster with just a picture of a computer and a cellphone and beneath that it says \"ANYWAY, I STARE AT THESE A LOT\"!!",
	"You ever see what I do with my computers? I drop 'em by accident and then get new ones.",
	"Is the future TRULY full of computers doing a crappier job than we'd do, but for helluva cheaper??",
	"Ah. So we're explaining a simple language concept via a complicated CS concept.",
	"A lot of things we do today are mediated by the computers on the internet!",
	"I read 150 stories last year and not ONE included an embarrassing display of ignorance regarding the actual bandwidth capacities of 2400 baud modems.",
	"Am I TRULY a Luddite now??",
	"IT'S LOOM SMASHING TIME",
	"I'm tired of doing things on computers!",
	"Dracula is canonically a hacker with an immortal dog??",
	"That was your FIRST old man story. It had no point except to point out that when you were younger things were different than they are now. I think we should acknowledge it, like a first grey hair!",
	"Unfortunately, the machine used an older and obsolete SCSI bus type. To even get it to spin up, Maldives was reduced to daisy-chaining a SCSI to IDE bridge with an IDE to SATA adapter, hoping that would work. It didn't!!",
	"Okay, so we all know computers can turn electricity into bad tweets. But did you know that's not intentional? When they were invented, tweets weren't even a thing yet!!",
	"That's just a bunch of strange computers that now I'm renting instead of owning!!",
	"Do you know that millennials use COMPUTERS more often than seniors do, and seniors use computers precisely the correct amount?",
	"Deduce all you want, SHERLOCK, but it's not gonna help you with figuring out that runtime error!",
	"And since trillions outweigh the mere BILLIONS alive today, I am, therefore, the most important person on the planet.",
	"SILENCE! YOU WILL HURT THE FEELINGS OF THE PRECURSOR OF TRILLIONS OF LIVES AND THAT'S THE WORST THING IT'S POSSIBLE TO DO",
	"BALONEY, I say. Baloney!",
	"HOLLA",
	"\"Aw frig,\" Maldives muttered. \"Here we go.\"",
	"There's lots of nothing, and everything else is a rounding error.",
	"Failure is just success rounded down, my friend!",
	"ERROR - DOUBLE SELF DESTRUCT INITIATED",
	"ERROR 5x290F",
	"Sorry, babies! YOU HAVE TO GROW UP SOMETIME. It's time to learn some harsh truths!",
	"...so I keep on making that same error over and over until nobody wants to be my friend because I'm \"the weird one\" who keeps making mistakes, WHICH I NEVER EVEN KNEW I WAS MAKING??",
	"I didn't know adjectives suffered from overflow errors!!",
	"Hey Jude! Your make is bad! You should fix that / compiler error!",
	"In today's society, knowing a little about computers can go a long way! They're not magic boxes. In fact, the more you learn about them the less magical they'll be!",
	"HAH HAH, JUST KIDDING! EVERYONE SUCKS THE SAME.",
	"Language is HARD, dudes!",
	"Paranoia?? Man, I'm proposing a vast worldwide conspiracy where people work to HELP ME OUT ON DEMAND and LET ME LEARN ABOUT BOATS AND POKÉMON.",
	"Um, I DOUBLE CHECKED THE NUMBER SYSTEM?",
	"ERROR 5000: NOT ACTUALLY A COMPUTER, UTAHRAPTOR",
	"I had to pick something!! It's all that came to mind!",
	"Here Lies T-Rex: Hey I Bet He's Still Wicked Handsome!",
	"I am Matthew Broderick: computer hacker!",
	"ERROR 22: IDEA IS TOO AWESOME",
	"TESTING THE PUNCHING MACHINE",
	"HTTP error code jokes? Seriously?",
	"Shakespeare! Are you listening to your MP3s again?!",
	"Upon closer inspection, forget THAT noise!",
	"THE·EVALUATION·OF·THAT STATEMENT·RESULTS·IN·A NULL·OUTPUT·SET",
	"NEW·PROGRAM·ENGAGED: 10 IGNORE WHAT UTAHRAPTOR SAYS 20 UTAHRAPTOR IS LAME 30 GOTO 10",
	"I have been working on a script: a noir about a computer programmer who gets involved in a snuff film conspiracy. The title? (A)bort, (R)etry, (M)urder!",
	"STACK OVERFLOW!",
]

# regex to look for "dino[saur][s]" in text, so we can react to it
DINO_REGEX = re.compile(r'\bdino(saur)?(s)?\b')

# our emoji we use when we're happy
EMOJI_ID = "<:trex:1346715043210854400>"

# fetch_panel will save off panel 2 from a random comic, and return the URL
# of the comic
def fetch_panel(panel_name, panel_number):
	URL = "https://www.gocomics.com/random/dinosaur-comics"
	page = requests.get(URL)
	img_src = BeautifulSoup(page.content, 'html.parser').find_all('picture', class_='item-comic-image')[0].find('img')['src']

	# fetch the image and chop out panel 2
	# luckily, these offsets never change
	png_data = requests.get(img_src)
	with Image.open(BytesIO(png_data.content)) as img:
		panel = img.crop(CROP_RECTANGLES[panel_number])
		panel.save(panel_name)
	return page.url

def start_bot(bot):
	f = open('config.yaml')
	config_map = yaml.safe_load(f)
	f.close()	
	bot.run(config_map['discordtoken'])

def create_bot():
	intents = discord.Intents.default()
	intents.message_content = True

	# note that we're using the lower level Client instead of Commands, because
	# we want to listen for certain words in all messages, and the framework
	# doesn't let us do that as well as use the commands framework
	return discord.Client(intents=intents)


# create our bot to add our event handler to it
bot = create_bot()

# main message handler - we're going to look for our commands here,
# as well as the word "dino[saurs]", which will make us happy.
@bot.event
async def on_message(message):
	if message.author == bot.user:
		return

	if message.content.startswith('$qwantz'):
		# split the message, and send the first word after the command
		# (if any) as the first parameter
		parts = message.content.split(' ')
		# default to the second panel, if we don't have a parameter
		# we send it in as a two, though, because it has to match
		# what the user would send 
		await qwantz(message.channel, parts[1] if len(parts) > 1 else 2)
	elif DINO_REGEX.search(message.content):
		await message.add_reaction(EMOJI_ID)

# we're going to default to the second panel, if the user doesn't provide
# an option, because that's usually the funniest panel
# note that the panel numbers are one-indexed, because it's a human
# on the other end. I mean, probably.
async def qwantz(channel, target_panel):
	# we need to be careful with the panel parameter, because some 
	# smartass in one of my server is definitely going to try 
	# "$qwantz -1", "$qwantz 42069", and/or "$qwantz beer"
	try:
		panel_number = int(target_panel)
		# this is dumb, but a negative index for a panel number could
		# be here (see: smartasses), and python will just treat it as an index 
		# from the end of the list of panels. That is goofy, so we'll just 
		# return an error in that case. Again, not a helpful one.
		if panel_number < 1:
			raise IndexError("Nice try.")
		file_name = "{0}.gif".format(str(uuid.uuid4()))
		# make sure to subtract one to make the panel_number zero-indexed
		url = fetch_panel(file_name, panel_number - 1)
		with open(file_name, 'rb') as fp:
			file_to_send = discord.File(fp, filename=file_name)
			await channel.send("Today is a good day I think for sending a [panel]({0}).".format(url), file=file_to_send)
		os.remove(file_name)
	except (ValueError, IndexError) as e:
		await channel.send(random.choice(ERROR_MESSAGES))

# start up our bot (using the token from the YAML file)
start_bot(bot)
