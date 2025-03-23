from io import BytesIO
import os
import random
import re
import traceback
import uuid

from bs4 import BeautifulSoup
import requests
from PIL import Image
import discord
from discord.ext import commands

# table of crop rectangles for the various panels. These were determined
# using a paint program on a downloaded comic.
SCALE = 735.0 / 900
CROP_RECTANGLES = [
	(0 * SCALE, 0 * SCALE, 297 * SCALE, 298 * SCALE),
	(298 * SCALE, 0 * SCALE, 458 * SCALE, 298 * SCALE),
	(457 * SCALE, 0 * SCALE, 899 * SCALE, 298 * SCALE),
	(0 * SCALE, 296 * SCALE, 239 * SCALE, 595 * SCALE),
	(237 * SCALE, 296 * SCALE, 604 * SCALE, 595 * SCALE),
	(602 * SCALE, 296 * SCALE, 899 * SCALE, 595 * SCALE),
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
DINO_REGEX = re.compile(r"\bdino(saur)?(s)?\b", re.IGNORECASE)

# number of results returned on each page of https://www.qwantz.com/search.php
SEARCH_RESULTS_PER_PAGE = 5


async def qwantz(channel, args):
	"""
	Entry point for responding to messages starting with $qwantz.
	Find an appropriate comic panel and post it.
	Supported syntaxes:
		$qwantz 				- post 2nd panel of random comic
		$qwantz [n]				- if n>5, post 2nd panel of nth comic
								- if n≤5, post nth panel of random comic
		$qwantz [n] [i]			- post ith panel of nth comic
		$qwantz [search phrase] - post a panel containing that phrase (if any)
	"""
	try:
		file_name = "{0}.gif".format(str(uuid.uuid4()))

		if len(args) == 0:
			# zero-argument syntax - pull 2nd panel of random comic
			url = find_random_comic_panel(file_name, 2 - 1)
		elif len(args) > 1 and args[0].isdigit() and args[1].isdigit():
			# $qwantz [comic_id] [panel_id] syntax - pull specific panel of specific comic
			url = fetch_comic_panel(file_name, f"https://www.qwantz.com/index.php?comic={args[0]}", int(args[1]) - 1)
		elif args[0].isdigit():
			# $qwantz [panel_id] or no-argument syntax - pull specific panel of random comic (default to 2nd panel)
			panel_number = int(args[0])
			if panel_number > 6:
				# ok probably the user just wants a specific comic then
				url = fetch_comic_panel(file_name, f"https://www.qwantz.com/index.php?comic={panel_number}", 2 - 1)
			else: 
				# make sure to subtract one to make the panel_number zero-indexed
				url = find_random_comic_panel(file_name, panel_number - 1)
		else:
			# $qwantz [search text] syntax - pull appropriate panel of comic matching search text
			url = find_comic_panel_by_text(file_name, " ".join(args))
		
		with open(file_name, 'rb') as fp:
			file_to_send = discord.File(fp, filename=file_name)
			await channel.send(f"Today is a good day I think for sending a [panel](<{url}>).", file=file_to_send)
		os.remove(file_name)
	except (ValueError, IndexError) as e:
		traceback.print_exc()
		await channel.send(random.choice(ERROR_MESSAGES))


def find_comic_panel_by_text(panel_name, search_text):#
	# Given search text, fetch a panel matching that text if possible and 
	# save it to the given filename. Throws an error if no matching panel.
	url = f"https://www.qwantz.com/search.php"
	payload = { "s" : search_text, "search": 1, "panel1": 1, "panel2": 1, "panel3": 1, "panel4": 1, "panel5": 1, "panel6": 1 }

	first_page = requests.post(url, data=payload)
	soup = BeautifulSoup(first_page.content, "html.parser")

	num_results_returned = int(soup.find("span", class_="grey").decode_contents().split()[0])
	comic_idx = random.randint(1, num_results_returned) - 1
	page_idx = comic_idx // SEARCH_RESULTS_PER_PAGE
	comic_idx_on_page = comic_idx % SEARCH_RESULTS_PER_PAGE

	payload["page"] = page_idx
	page = requests.post(url, data=payload)
	soup = BeautifulSoup(page.content, "html.parser")
	comic_url = soup.find("form").find_all("li")[comic_idx_on_page].find("a")["href"]
	return fetch_comic_panel(panel_name, comic_url, 1, search_text)


def find_random_comic_panel(panel_name, panel_number):
	# Look up a random comic, take the given panel number, and 
	# save it to the given filename.
	url = "https://www.qwantz.com/archive.php"
	page = requests.get(url)
	comic_url = random.sample(BeautifulSoup(page.content, "html.parser").find_all("a"), 1)[0]["href"]
	return fetch_comic_panel(panel_name, comic_url, panel_number)


def fetch_comic_panel(panel_name, comic_url, panel_number, search_text=None):
	# Extract the comic from the given URL, 
	# take a panel (either one matching search text if provided, or the given numbered panel),
	# and save it to the given filename.
	page = requests.get(comic_url)
	soup = BeautifulSoup(page.content, "html.parser")
	img_src = "https://qwantz.com/" + soup.find_all("img", class_="comic")[0]["src"]

	if search_text is not None:
		transcript_blocks = re.split(r"\<br/?\>\<br/?\>", soup.find("div", id="transcriptDiv").find("div", class_="padded").decode_contents())
		matching_idxs = [i for i in range(len(transcript_blocks)) if search_text in transcript_blocks[i].lower()]
		# prioritize panel_number if possible, otherwise just take a random matching panel
		panel_number = panel_number if panel_number in matching_idxs else random.sample(matching_idxs, 1)[0]

	png_data = requests.get(img_src)
	with Image.open(BytesIO(png_data.content)) as img:
		panel = img.crop(CROP_RECTANGLES[panel_number])
		panel.save(panel_name)
	return page.url


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
		args = message.content.lower().split(' ')[1:]
		await qwantz(message.channel, args)
	elif DINO_REGEX.search(message.content) and "EMOJI_ID" in os.environ:
		await message.add_reaction(os.environ["EMOJI_ID"])

bot.run(os.environ["DISCORD_TOKEN"])
