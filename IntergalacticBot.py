import discord, os, time, requests, datetime, schedule, asyncio, logging, random
from datetime import datetime, timezone, timedelta
from discord import app_commands
from discord.ext import commands
from collections import defaultdict
from dotenv import load_dotenv
from helper import utilities

DEBUG = False
# DEBUG = True

load_dotenv()
SECRET_KEY = os.getenv('DISCORD_TOKEN') if not DEBUG else os.getenv('DISCORD_TOKEN_TEST')
CSE_KEY = os.getenv('CSE_KEY')
CSE_ENGINE_ID = os.getenv('CSE_ENGINE_ID')

logger = logging.getLogger()
logging.basicConfig(filename="stats.log", level=logging.INFO)
# {"setting": "data", "user": 129837182, "msg_channel": 1928371}
config = {}

# stats.db is a database that holds bank information, upgrades, transactions, and stats.
# Takes in a discord user id as the identifier.
# The GC Vault has discord_id of 0.

# Tables:
# GC Vault discord_id = 0
# Current Pet discord_id = 0
# 
# TABLE users
#                      discord_id INTEGER PRIMARY KEY,
#                      balance NUMERIC DEFAULT 10000
# 
# TABLE stats
#                      stat_name TEXT,
#                      count INTEGER
# 
# TABLE upgrades
#                      user_id INTEGER FOREIGN KEY,
#                      upgrade_name TEXT,
#                      upgrade_level INTEGER
# 
# TABLE old_balance
#                      discord_id INTEGER FOREIGN KEY,
#                      balance NUMERIC DEFAULT 10000
# 
# TABLE last_coin
#                      discord_id INTEGER FOREIGN KEY,
#                      coin TEXT,
#                      count INTEGER
# 
# TABLE cwar_result
#                      discord_id INTEGER FOREIGN KEY,
#                      winner TEXT,
#                      count INTEGER DEFAULT 0,
# TABLE pet
#                      discord_id INTEGER FOREIGN KEY,
#                      pet_name TEXT,
#                      count INTEGER DEFAULT 0,
#                      cost NUMERIC DEFAULT 0,
# 
# TABLE fortune
#                      discord_id INTEGER FOREIGN KEY,
#                      count NUMERIC,
# 
# TABLE user_networth
#                      discord_id INTEGER FOREIGN KEY,
#                      networth NUMERIC,
# 
# TABLE transactions
#                      discord_id INTEGER FOREIGN KEY,
#                      username TEXT,
#                      type TEXT,
#                      transaction_amount NUMERIC,
#                      balance NUMERIC,
#                      created_at DATETIME DEFAULT CURRENT_TIMESTAMP

# Scheduled runner.
async def schedule_runner():
    await client.wait_until_ready()

    while not client.is_closed():
        schedule.run_pending()
        await asyncio.sleep(1)


# Hourly task to change status.
def task_change_status():
    asyncio.create_task(change_status())


def task_update_leaderboard():
    asyncio.create_task(leaderboards())

def task_send_pet_to_history():
    asyncio.create_task(send_pet_to_history())

async def change_status():
    new_status = random.choice(config["status"])
    await client.change_presence(activity=discord.CustomActivity(name=new_status))


config = utilities.load_config()
utilities.create_tables_if_not_exist()


# Stores messages from users in order to rate limit them.
user_messages = defaultdict(list)

# If a user hits the limit of how many messages they can receive from the bot, it'll prevent 
# the user from getting a new one. Resets based on time_window
def is_rate_limited(user_id) -> bool:
    current_time = time.time()
    user_message_time = user_messages[user_id]

    # Checks the oldest timestamp, if it was longer than the set time_window, it'll clear all of
    # that user's timestamps.
    if len(user_message_time) > 0 and current_time - user_message_time[0] > config['time_window']:
        user_message_time = []
    user_messages[user_id] = user_message_time
    is_limited = len(user_message_time) >= config['max_messages']
    if is_limited:
        utilities.increment_stat("rate limited")
        logger.info(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{user_id},rate limited,1')
    return is_limited


# Any time a user gets a response from the bot, it'll add the timestamp of their message
# to a list, which will be used to limit the amount of messages per user.
def increment_rate_counter(user_id) -> None:
    current_time = time.time()
    user_message_time = user_messages[user_id]
    user_message_time.append(current_time)
    user_messages[user_id] = user_message_time


intents = discord.Intents.default()
intents.typing = True
intents.presences = True
intents.members = True
intents.message_content = True
intents.voice_states = True
intents.reactions = True
client = commands.Bot(command_prefix="!", owner_id=config["op"], intents=intents, case_insensitive=True)
command_tree = client.tree


# Decorator to confirm the command is being used by the owner.
# Will prevent others from using it.
def is_owner():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.id == client.owner_id
    return app_commands.check(predicate)


@command_tree.command(name="sync", description="Sync command tree.")
@is_owner()
async def sync(interaction: discord.Interaction) -> None:
    synced = await command_tree.sync()
    utilities.increment_stat("sync")
    logger.info(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},synced,1')
    await interaction.response.send_message(f"Synced {len(synced)} commands globally.", ephemeral=True)


# Owner only command, DM's the owner the current data of how many times a command has been run.
@command_tree.command(name="give_stats")
@is_owner()
async def give_stats(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("Grabbing stats...", ephemeral=True)
    utilities.increment_stat("stats called")
    logger.info(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},stats called,1')
    stats = utilities.get_all_stats()
    output_stats = '{:23} | {:8}\n'.format("```Stat", "Count")
    output_stats = output_stats + f'{"-"*50}\n'
    
    for stat_name in stats:
        output_stats = output_stats + "{:20} | {:8,}\n".format(stat_name, stats[stat_name])
    
    output_stats = output_stats + '```'

    user = await client.fetch_user(config["op"])
    await user.send(f"{output_stats}")


# Force change the status of the bot by randomly picking a new one again.
# !!!!! Does not reset the timer when the bot would naturally change its status. !!!!!
@command_tree.command(name="status_change")
@is_owner()
async def status_change(interaction: discord.Interaction) -> None:
    await change_status()
    await interaction.response.send_message("Status changed.", ephemeral=True)


# Prevents the bot from running in DMs.
async def is_guild(interaction: discord.Interaction) -> bool:
    if interaction.guild is None:
        return False
    return True


client.add_check(is_guild)


# Sends a meme help message.
@command_tree.command(name="help", description="Helps the user.")
@app_commands.guild_only()
async def help(interaction: discord.Interaction) -> None:
    utilities.increment_stat("help")
    logger.info(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},help,1')
    await interaction.response.send_message("Why do you need help?\n988 - Crisis helpline.\n\n\
https://gist.github.com/ToekneeT/a99a3c3e5db6b6234e62410422d43d8f")


# Does a quick latency check.
@command_tree.command(name="ping", description="Tests latency.")
@app_commands.guild_only()
@app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild.id, i.user.id))
async def ping(interaction: discord.Interaction) -> None:
    utilities.increment_stat("ping")
    ping = {round(client.latency * 1000)}
    logger.info(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},{ping},1')
    await interaction.response.send_message(f"Pong! ({ping}ms)")


# Rolls a number between x and y. Default is 1 - 100.
# Can change the lower or upper bound separately.
@command_tree.command(name="roll", description="Roll a number between 1 and n.")
@app_commands.guild_only()
async def roll(interaction: discord.Interaction, lower_bound: int = 1, upper_bound: int = 100) -> None:
    user_id: int = interaction.user.id
    user_fortune: int = utilities.get_user_fortune(user_id)
    rolled = random.randint(lower_bound, upper_bound)
    log_text: str = f"Range: {lower_bound} - {upper_bound} OG: {rolled} "

    if user_fortune > 0:
        rolled = utilities.fortune_roll(user_id, user_fortune, rolled, random.randint(lower_bound, upper_bound))
        log_text += f'fortune affected roll: {rolled} '
    elif user_fortune < 0:
        rolled = utilities.fortune_roll(user_id, user_fortune, rolled, random.randint(lower_bound, upper_bound), favor_high=False)
        log_text += f'fortune affected roll: {rolled} '

    utilities.increment_stat("rolls")
    await interaction.response.send_message(
        f"Rolling a number between {lower_bound}-{upper_bound}: **{rolled}**")
    
    logger.info(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},{log_text}')


# Does a google search. By default shows the top 2 results.
# Can configure which page it looks at and how many responses it gives.
# Does not give the long description to avoid cluttering the chat, but 
# can be asked to include the long description in the command.
@command_tree.command(name="search", description="Searches the web.")
@app_commands.guild_only()
@app_commands.checks.cooldown(1, 15, key=lambda i: (i.guild.id, i.user.id))
async def search(interaction: discord.Interaction,
    query: str,
    page: int = 1,
    results:int = 2,
    long_description: bool = False
    ) -> None:

    if results > 5:
        await interaction.response.send_message(f"Results too high. <= 5", ephemeral=True)
        return

    await interaction.response.send_message(f"Searching for {query}.")
    # Appends the query to stats.
    logger.info(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},searches,[{query}]')
    start = (page - 1) * results + 1
    url = f"https://www.googleapis.com/customsearch/v1?key={CSE_KEY}&cx={CSE_ENGINE_ID}&q={query}&start={start}"
    data = requests.get(url).json()
    search_items = data.get("items")

    # Grabs the information for each result.
    for i, search_item in enumerate(search_items[:results], start=1):
        try:
            big_description = search_item["pagemap"]["metatags"][0]["og:description"]
        except KeyError:
            big_description = "N/A"

        title = search_item.get("title")
        snippet = search_item.get("snippet")
        link = search_item.get("link")
        await interaction.channel.send(f"{'='*10} Result #{i + start-1} {'='*10}")
        await interaction.channel.send(f"Title: {title}")
        await interaction.channel.send(f"Description: {snippet}")
        if long_description:
            await interaction.channel.send(f'Long Description: {big_description}')
        await interaction.channel.send(f"{link}\n")


@command_tree.command(name="elusive_hunter", description="Assigns the Elusive Hunter role to you.")
@app_commands.guild_only()
async def elusive(interaction: discord.Interaction) -> None:
    guild = client.get_guild(config["igp"])
    role = guild.get_role(config["elusive_role"])
    if interaction.guild != guild:
        await interaction.response.send_message("Can't be used in this server.", ephemeral=True)
        return
    await interaction.user.add_roles(role)
    await interaction.response.send_message("You've been assigned the Elusive Hunter role.", ephemeral=True)


@command_tree.error
async def on_slash_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    try:
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f'This command is on cooldown. Try again after {error.retry_after:.2f} seconds.', ephemeral=True)
            logger.error(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{error},{interaction.user.name},1')
        elif isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("You don't have permissions to do this.", ephemeral=True)
            logging.error(f'{interaction.user.name}\nPermission error: {error}')
        else:
            await interaction.response.send_message(f'{interaction.user.name}\nAn error occurred: {str(error)}.', ephemeral=True)
            logger.error(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{error},{interaction.user.name},1')

    except discord.errors.InteractionResponded:
        logging.error("Interaction responded before.")


# Update the leaderboards.
@client.command(name="update")
@commands.is_owner()
async def update(ctx: commands.Context):
    await leaderboards()


@client.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CheckFailure):
        logger.error(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{error},{ctx.author},1')
    elif isinstance(error, commands.CommandOnCooldown):
        logger.error(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{error},{ctx.author},1')
    # This conditional goes hand in hand with the memes.py Caged Iguana secret.
    # This specific user isn't in the IGP server, making it so that trying to @ this member
    # leads to an error.
    elif isinstance(error, commands.MemberNotFound) and str(error).split()[1] == f'"{config["chase"]}"':
        if "Caged Iguana" not in utilities.get_user_pets(ctx.author.id):
            utilities.add_pet_to_user(ctx.author.id, "Caged Iguana", 0)
            await ctx.send(f'🎉 <@{ctx.author.id}> has been awarded the Caged Iguana for capturing the user! 🎉')
            utilities.increment_stat("Caged Iguana")
            logger.info(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {ctx.author} claimed Caged Iguana')
    else:
        logger.error(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{error},{ctx.author},1')


async def leaderboards():
    guild = client.get_guild(config["snax"])
    guild_two = client.get_guild(config["igp"])
    channel = client.get_channel(config["snax_leaderboard"])
    leaderboard = await channel.fetch_message(config["leaderboard"])

    # Local time is PST, but I want Central time.
    # Get the minutes away from UTC time and convert to hours.
    # Add 3 to get central.
    timezone_offset = -5#(-time.timezone / 3600) + 3
    tzinfo = timezone(timedelta(hours=timezone_offset))
    now = datetime.now(tzinfo)
    current_time = now.strftime("%m-%d-%Y %H:%M")


    standings = f'{"="*10} The current standings (<t:{int(time.time())}:R>) {"="*10}\n'
    standings = standings + '{:23} | {:8}\n'.format("```Player", "Balance")
    standings = standings + f'{"-"*50}\n'

    sorted_users = utilities.get_users_sorted_by_balance()
    for user_id, balance in sorted_users:
        old_balance = utilities.get_old_balance(user_id)
        try:
            username = await guild.fetch_member(user_id)
            username = username.display_name
        except discord.NotFound:
            try:
                username = await guild_two.fetch_member(user_id)
                username = username.display_name
            except discord.NotFound:
                try:
                    username = await client.fetch_user(user_id)
                    username = username.name
                except discord.NotFound:
                    continue

        difference = balance - old_balance
        
        if old_balance != 0:
            percent_diff = (difference / old_balance) * 100
        else:
            percent_diff = 0

        if difference > 0:
            sym = "+"
        elif difference == 0:
            sym = ""
            percent_diff = 0
        else:
            sym = "-"
        standings = standings + '{:20} | {:11,.0f} ({}, {}%)\n'.format(username, balance, f'{sym}{abs(difference):,.0f}', f'{sym}{abs(percent_diff):,.1f}')

    standings = standings + f'```Galactic Coin Vault: **{utilities.get_balance(0):,.2f}**'

    utilities.store_previous_balance()
    
    # Attempts to edit message, but if message got deleted or disappeared, send a new message out,
    # save the new message id for future edits.
    try:
        await leaderboard.edit(content=standings)
    except discord.NotFound:
        new_board = await channel.send(f'{standings}')
        config["leaderboard"] = new_board.id
        utilities.save_config(config)
    
    # Send to another channel.
    channel = client.get_channel(config["bot_auto_msg"])
    leaderboard = await channel.fetch_message(config["igp_leaderboard"])
    try:
        await leaderboard.edit(content=standings)
    except discord.NotFound:
        new_board = await channel.send(f'{standings}')
        config["igp_leaderboard"] = new_board.id
        utilities.save_config(config)


async def send_pet_to_history():
    guild = client.get_guild(config["igp"])
    channel = client.get_channel(config["pet_history"])
    role = guild.get_role(config["elusive_role"])
    current_pet_info: str = utilities.get_current_pet()
    await channel.send(f'<t:{int(time.time())}:R>\n{current_pet_info[0]}\nPrice: {current_pet_info[1]:,} GC')
    if "Elusive" in current_pet_info[0].split():
        await channel.send(f'{role.mention} An Elusive pet has appeared! <a:donkk:1268199157542289420>')


async def send_gc_reward_message(channel_id: int) -> None:
    await client.wait_until_ready()
    channel = client.get_channel(channel_id)
    while not client.is_closed():
        reward = random.randint(100, 1000)
        content = f"React to this message to receive {reward:,} GC."
        message = await channel.send(content)
        claimed_users = set()

        def check(reaction, user):
            return reaction.message.id == message.id and user != client.user

        try:
            # Keep checking for reactions, breaks out of the loop after the timeout occurs.
            # as the timeout throws an asyncio.TimeoutError
            while True:
                reaction, user = await client.wait_for('reaction_add', timeout=random.randint(600, 1800), check=check)
                if reaction and user.id not in claimed_users:
                    claimed_users.add(user.id)
                    utilities.get_balance(user.id)
                    adjusted_reward = reward * ((utilities.get_upgrade_level("Claim Multiplier", user.id) * 0.5) + 1)
                    if adjusted_reward != reward:
                        await channel.send(f"<a:Yoink:1276035178807955508> {user.display_name} has claimed {adjusted_reward:,.2f} GC from the original {reward:,} GC!")
                        logger.info(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{user.name},claimed,{adjusted_reward}')
                    else:
                        await channel.send(f"<a:Yoink:1276035178807955508> {user.display_name} has claimed {reward:,.2f} GC!")
                        logger.info(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{user.name},claimed,{reward}')

                    utilities.update_balance(user.id, adjusted_reward)
                    user_balance: float = utilities.get_balance(user.id)
                    utilities.add_transaction_to_history(user.id, user.name, "claim", adjusted_reward, user_balance)

        except asyncio.TimeoutError:
            pass
        await message.delete()

        interval = random.randint(1800, 4500)
        await asyncio.sleep(interval)



# Payout interest if anyone has it.
def payout_bank_interest():
    interest_key = {
        1: .00003,
        2: .00006,
        3: .00009,
        4: .00012,
        5: .000178,
    }
    users = utilities.get_all_bank_interest()
    if users:
        for user_id, level in users:
            user_balance = utilities.get_balance(user_id)
            interest = user_balance * interest_key[level]
            utilities.update_balance(user_id, interest)
            # utilities.add_transaction_to_history(user_id, "", "interest", interest, utilities.get_balance(user_id))


@client.event
async def on_ready() -> None:
    print(f"We have logged in as {client.user}")
    new_status = random.choice(config["status"])
    await client.change_presence(activity=discord.CustomActivity(name=new_status))
    # await client.load_extension(f'cogs.casino')
    # await client.load_extension(f'cogs.upgrades')
    # await client.load_extension(f'cogs.memes')
    # await client.load_extension(f'cogs.cwar')
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await client.load_extension(f'cogs.{filename[:-3]}')
    await command_tree.sync()

    client.loop.create_task(schedule_runner())

    # Task to change status every 60 minutes since the bot has run.
    schedule.every(60).minutes.do(task_change_status)
    schedule.every().hour.at(":00").do(task_update_leaderboard)
    schedule.every().hour.at(":00").do(payout_bank_interest)
    # schedule.every().hour.at(":00").do(utilities.change_current_pet)
    # Instead of using every(30).minutes, it changes at every :00 and :30
    # as the every(30) minutes would be on bot startup, whereas I want the
    # pet to change every hour or 30 minute marker.
    schedule.every().hour.at(":00").do(utilities.change_current_pet)
    schedule.every().hour.at(":30").do(utilities.change_current_pet)
    schedule.every().hour.at(":00").do(task_send_pet_to_history)
    schedule.every().hour.at(":30").do(task_send_pet_to_history)
    
    client.loop.create_task(send_gc_reward_message(config["snax_gamble"]))
    client.loop.create_task(send_gc_reward_message(config["igp_gamble"]))
    client.loop.create_task(send_gc_reward_message(config["igp_gamble_2"]))

    users = utilities.get_user_names_from_id()
    for id in users:
        user = await client.fetch_user(id)
        utilities.insert_user_name_into_table(id, user.name)


# Used to have the bot reply to a message when @ or replied to.
async def reply_to(message, thread, bot_response):
    if isinstance(message.channel, discord.Thread):
        await message.channel.send(bot_response)
    else:
        await message.reply(bot_response)


# Bot replies with loser if you @ or reply to it.
async def loser_reply(message, thread):
    try:
        await reply_to(message, thread, "Talking to a bot, major L.")
        await message.channel.send("<:peepoLoser:1268361127344078868>")
        utilities.increment_stat("loser reply")
        logger.info(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{message.author},loser,1')
    except:
        logger.error(f'{datetime.now().strftime("%m/%d/%Y %H:%M:%S")} reply error')
    


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Ignore DMs.
    if message.guild is None:
        return
    
    # Delete server owner's message from the leaderboard channel.
    # No way to prevent the owner from sending messages in Discord itself, so I do it myself.
    if message.channel.id == config["snax_leaderboard"] and message.author.id == config["liam"]:
        await message.delete()
        return


    channel_id = message.channel.id
    user_message = str(message.content)
    # Responds if it receives a reply.
    if message.reference:
        if is_rate_limited(message.author.id):
            print(f"{message.author} Rate limited.")
            return

        try: 
            referenced_message = await message.channel.fetch_message(message.reference.message_id)
            if referenced_message.author == client.user:
                increment_rate_counter(message.author.id)
                await loser_reply(message, discord.Thread)

        except discord.errors.NotFound as e:
                # Exception when creating a new thread and the first response.
                # The bot can't find the first message and sends an error, but still functions normally.
                print(f"Discord not found error: {e}")
                return


    # Responds if it gets @'d in the chat.
    elif client.user in message.mentions:
        if is_rate_limited(message.author.id):
            print(f"{message.author} Rate limited.")
            return

        increment_rate_counter(message.author.id)
        await loser_reply(message, discord.Thread)


    await client.process_commands(message)


client.run(SECRET_KEY)