import discord, logging, functools, random, datetime
from discord.ext import commands
from discord import app_commands
from helper import utilities

# stats.db is a database that holds bank information, upgrades, and stats.
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


logger = logging.getLogger()
logging.basicConfig(filename="stats.log", level=logging.INFO)

# {"setting": "data", "user": 129837182, "msg_channel": 1928371}
config = {}
config = utilities.load_config()


def luck_roll() -> int:
    if random.random() < .7:
        return 1
    else:
        return luck_roll() + 1


def convert_roll_to_dot(amt: int) -> str:
    return "🟢" * (amt-1) + "🔴" + f" {(.3**(amt-1)) * .7 * 100:.{amt-1}f}%"


# Payouts for the luck roll.
def luck_payout(n: int) -> int:
    if n == 1:
        return 0
    elif n == 2:
        return 2
    elif n == 3:
        return 3.5
    elif n == 4:
        return 8
    elif n == 5:
        return 12
    else:
        return (1 - .25) * (4 * n)


def get_user_max(user_id: int, max: int):
    coinflip_max: int = utilities.get_upgrade_level("Wager Maximum", user_id)
    if coinflip_max == 0:
        return max
    # Each upgrade should double the previous maximum.
    return max * (2 ** (coinflip_max))


def get_coinflip_bonus_pay(user_id: int) -> float:
    user_coinflip_multiplier = utilities.get_upgrade_level("Coinflip Consecutive Bonus", user_id)
    if user_coinflip_multiplier == 0:
        return 2.0
    coin_count = utilities.get_user_coin_count(user_id)
    bonus = (user_coinflip_multiplier / 100) * coin_count
    return 2.0 + bonus


# Sends out a message if the bet placed is invalid and returns False.
# Only sends out true if there is bet placed and they have enough
async def is_bet(interaction: discord.Interaction, bet: float) -> bool:
    if bet == 0:
        return False
    elif bet < 0:
        await interaction.response.send_message(f'Can\'t place a bet less than 0.')
        return False
    elif bet > utilities.get_balance(interaction.user.id):
        await interaction.response.send_message(f'You don\'t have enough GC.\nYou have {utilities.get_balance(interaction.user.id):,.2f} GC')
        return False
    
    return True


async def new_luckiest(bot, interaction: discord.Interaction, roll_amt: int):
    old_luckiest = config["luckiest"]
    old_luckiest_msg = config["luckiest_msg"]
    config["luckiest"] = str(interaction.user)
    config["luckiest_num"] = roll_amt
    utilities.save_config(config)

    response_message = await interaction.original_response()
    await response_message.pin()
    channel = bot.get_channel(config["snax_text"])
    channel_igv = bot.get_channel(config["igp_gamble"])

    if old_luckiest != str(interaction.user):
        new_winner = await channel.send(
            f'{old_luckiest} has been dethroned! {interaction.user} is the new champ!\n\
{"<a:GoldDice:1269187263116476491>"*(roll_amt-4)} {convert_roll_to_dot(roll_amt)} {"<a:GoldDice:1269187263116476491>"*(roll_amt-4)}')
        new_winner_igv = await channel_igv.send(
            f'{old_luckiest} has been dethroned! {interaction.user} is the new champ!\n\
{"<a:GoldDice:1269187263116476491>"*(roll_amt-4)} {convert_roll_to_dot(roll_amt)} {"<a:GoldDice:1269187263116476491>"*(roll_amt-4)}')
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user},newest champ,{roll_amt}')
    else:
        new_winner = await channel.send(
                f'{interaction.user} has become luckier! {roll_amt} is the new highest!\n\
{"<a:GoldDice:1269187263116476491>"*(roll_amt-4)} {convert_roll_to_dot(roll_amt)} {"<a:GoldDice:1269187263116476491>"*(roll_amt-4)}')
        new_winner_igv = await channel_igv.send(
                f'{interaction.user} has become luckier! {roll_amt} is the new highest!\n\
{"<a:GoldDice:1269187263116476491>"*(roll_amt-4)} {convert_roll_to_dot(roll_amt)} {"<a:GoldDice:1269187263116476491>"*(roll_amt-4)}')
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user},got even higher,{roll_amt}')

    await new_winner.pin()
    await new_winner_igv.pin()
    old_pin = await channel.fetch_message(old_luckiest_msg)
    try:
        await old_pin.unpin()
    except discord.NotFound:
        print("Message not found to unpin")

    config["luckiest_msg"] = new_winner.id
    utilities.save_config(config)


async def vault_winner(interaction: discord.Interaction, bot):
    user_id: int = interaction.user.id
    username: str = interaction.user

    channel_snax = bot.get_channel(config["snax_gamble"])
    channel_igv = bot.get_channel(config["igp_gamble"])
    vault_contents = utilities.get_balance(0)
    utilities.update_balance(0, -vault_contents)
    utilities.update_balance(user_id, vault_contents)
    user_balance: float = utilities.get_balance(user_id)
    utilities.add_transaction_to_history(user_id, username, "vault win", vault_contents, user_balance)
    utilities.add_transaction_to_history(0, "GC Vault", "vault win", -vault_contents, 0)
    # await interaction.channel.send(f'**{interaction.user.display_name}** has claimed the contents of the vault! **{vault_contents:,.2f}** GC has been credited.')
    await channel_snax.send(f'**{interaction.user.display_name}** has claimed the contents of the vault! **{vault_contents:,.2f}** GC has been credited.')
    await channel_igv.send(f'**{interaction.user.display_name}** has claimed the contents of the vault! **{vault_contents:,.2f}** GC has been credited.')
    utilities.increment_stat("Vault Won")


def original_user_only():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            # If someone tries to use the menu that isn't the original invoker, stop and prevent them.
            if interaction.user != self.original_user:
                await interaction.response.send_message("You cannot interact with this menu.", ephemeral=True)
                return
            # If the user is the original user, proceed
            return await func(self, interaction, *args, **kwargs)
        return wrapper
    return decorator


class FortuneMenu(discord.ui.View):
    def __init__(self, original_user: discord.User, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.value = None
        self.original_user = original_user
        self.balance = utilities.get_balance(original_user.id)
        self.fortune_ranking = "\n\n**Fortune Ranking:**\nGreat blessing\nMiddle blessing\nSmall blessing\nBlessing\n"
        self.fortune_ranking += "Future blessing\nBad fortune\nGreat bad fortune\n"

        self.description: str = f"Balance: {self.balance:,.2f} GC\n\
\n<a:omikuji:1277921174357282907> Receive your fortune in the form of an Omikuji. <a:omikuji:1277921174357282907>\n\n"
        self.description += f"Prices:\n"
        self.description += f"Cheap: **{max(self.balance * .02, 500):,.2f} GC**\n"
        self.description += f"Standard: **{max(self.balance * .05, 2000):,.2f} GC**\n"
        self.description += f"Quality: **{max(self.balance * .1, 10000):,.2f} GC**\n\n"
        self.description += "Cheap has a higher chance to roll a bad fortune. Cannot get Great Blessing.\n"
        self.description += "Standard has no weight.\n"
        self.description += "Quality has a higher chance to roll a good fortune. Cannot get Great Bad Fortune."

        self.omikuji = {
            1: ("Great bad fortune", -random.randint(8, 13)),
            2: ("Bad fortune", -random.randint(3, 7)),
            3: ("Future blessing", -random.randint(1, 2)),
            4: ("Blessing", 0),
            5: ("Small blessing", random.randint(1, 2)),
            6: ("Middle blessing", random.randint(3, 7)),
            7: ("Great blessing", random.randint(8, 13))
        }


    @discord.ui.button(label="Cheap", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def fortune_unlucky(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        username: str = interaction.user.name

        # Cost is based on balance of when activated.
        cost: float = self.balance * .02
        # Cost 500 GC, or 2% of the user's balance, whichever one is higher.
        cost = max(cost, 500)
        if utilities.get_balance(self.original_user.id) - cost < 0:
            embed = discord.Embed(color=discord.Color.dark_gray())
            embed.set_author(name=f"{interaction.user.display_name}")
            embed.add_field(name=f"Not enough GC.", value=self.description)
            await interaction.response.edit_message(embed=embed)
            return
        
        # Gets a random fortune between the lowest to the second highest. Cannot get Great Blessing from this.
        # Rolls twice, will get the lower fortune of the two. Example, if you roll 2 and 6, you will get fortune 2.
        omikuji_num = utilities.get_lower_of_two(random.randint(1, len(self.omikuji)-1), random.randint(1, len(self.omikuji)-1))
        fortune_text, fortune = self.omikuji[omikuji_num]
        utilities.set_user_fortune(user_id, fortune)

        embed = discord.Embed(color=discord.Color.light_gray())
        embed.set_author(name=f'{interaction.user.display_name}')
        embed.add_field(name=f'Your Fortune', value=f'{fortune_text + self.fortune_ranking}')
        
        # Disables buttons
        utilities.toggle_menu_buttons(self, True)
        await interaction.response.edit_message(embed=embed, view=self)
        utilities.update_balance(user_id, -cost)
        user_balance: float = utilities.get_balance(user_id)
        utilities.add_transaction_to_history(user_id, username, "fortune unlucky", -cost, user_balance)
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{username},got their fortune,{fortune_text}')
        utilities.increment_stat("fortune cheap")
        utilities.fortune_spent(cost)
        self.value = False
        self.stop()
    

    @discord.ui.button(label="Standard", style=discord.ButtonStyle.blurple)
    @original_user_only()
    async def fortune_regular(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        username: str = interaction.user.name

        # Cost is based on balance of when activated.
        cost: float = self.balance * .05
        # Cost 2000 GC, or 5% of the user's balance, whichever one is higher.
        cost = max(cost, 2000)
        if utilities.get_balance(self.original_user.id) - cost < 0:
            embed = discord.Embed(color=discord.Color.dark_gray())
            embed.set_author(name=f"{interaction.user.display_name}")
            embed.add_field(name=f"Not enough GC.", value=self.description)
            await interaction.response.edit_message(embed=embed)
            return
        
        omikuji_num = random.randint(1, len(self.omikuji))
        fortune_text, fortune = self.omikuji[omikuji_num]
        utilities.set_user_fortune(interaction.user.id, fortune)

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_author(name=f'{interaction.user.display_name}')
        embed.add_field(name=f'Your Fortune', value=f'{fortune_text + self.fortune_ranking}')

        # Disables buttons
        utilities.toggle_menu_buttons(self, True)
        await interaction.response.edit_message(embed=embed, view=self)
        utilities.update_balance(user_id, -cost)
        user_balance: float = utilities.get_balance(user_id)
        utilities.add_transaction_to_history(user_id, username, "fortune standard", -cost, user_balance)
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{username},got their fortune,{fortune_text}')
        utilities.increment_stat("fortune standard")
        utilities.fortune_spent(cost)
        self.value = False
        self.stop()
    

    @discord.ui.button(label="Quality", style=discord.ButtonStyle.red)
    @original_user_only()
    async def fortune_lucky(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        username: str = interaction.user.name

        # Cost is based on balance of when activated.
        cost: float = self.balance * .10
        # Cost 10000 GC, or 10% of the user's balance, whichever one is higher.
        cost = max(cost, 10000)
        if utilities.get_balance(self.original_user.id) - cost < 0:
            embed = discord.Embed(color=discord.Color.dark_gray())
            embed.set_author(name=f"{interaction.user.display_name}")
            embed.add_field(name=f"Not enough GC.", value=self.description)
            await interaction.response.edit_message(embed=embed)
            return
        
        # Gets a random fortune between the second lowest to the highest. Cannot get Great Bad Fortune from this.
        # Rolls twice, will get the higher fortune of the two. Example, if you roll 2 and 6, you will get fortune 6.
        omikuji_num = utilities.get_higher_of_two(random.randint(2, len(self.omikuji)), random.randint(2, len(self.omikuji)))
        fortune_text, fortune = self.omikuji[omikuji_num]
        utilities.set_user_fortune(interaction.user.id, fortune)

        if cost >= 27_000_000 and omikuji_num == 2 and "Sly Tanuki" not in utilities.get_user_pets(interaction.user.id):
            utilities.add_pet_to_user(user_id, "Sly Tanuki", 0)
            await interaction.channel.send(f'🎉 <@{username}> has been awarded the **Sly Tanuki** for getting robbed! 🎉')
            utilities.increment_stat("Sly Tanuki")
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {username} claimed Sly Tanuki')

        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=f'{interaction.user.display_name}')
        embed.add_field(name=f'Your Fortune', value=f'{fortune_text + self.fortune_ranking}')

        # Disables buttons
        utilities.toggle_menu_buttons(self, True)
        await interaction.response.edit_message(embed=embed, view=self)
        utilities.update_balance(user_id, -cost)
        user_balance: float = utilities.get_balance(user_id)
        utilities.add_transaction_to_history(user_id, username, "fortune quality", -cost, user_balance)
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{username},got their fortune,{fortune_text}')
        utilities.increment_stat("fortune quality")
        utilities.fortune_spent(cost)
        self.value = False
        self.stop()


class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # ____________________ Owner Only On Commands ____________________


    # Owner only, credit to someone's bank.
    @commands.command(name="credit")
    @commands.is_owner()
    async def credit(self, ctx: commands.Context, member: discord.Member, amount: float):
        utilities.update_balance(member.id, amount)
        user_balance: float = utilities.get_balance(member.id)
        utilities.add_transaction_to_history(member.id, member.name, "credit", amount, user_balance)
        await ctx.send(f'{amount:,.2f} GC credited to {member.display_name}.\n{user_balance:,.2f} in bank.')
        utilities.increment_stat("!credit")
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{ctx.author},credited {member.name},{amount}')
    

    # Can test the luck command and print out the results of what the chances would be.
    @commands.command(name="showluck")
    @commands.is_owner()
    async def showluck(self, ctx: commands.Context, message: int):
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{ctx.author},!showluck,{message}')
        await ctx.send(convert_roll_to_dot(message))
        utilities.increment_stat("showluck")
    

    @commands.command(name="creditall")
    @commands.is_owner()
    async def creditall(self, ctx: commands.Context, amount: float):
        utilities.update_all_balances(amount)
        utilities.add_transactions_to_history_everyone(amount)
        await ctx.send(f'{amount:,.2f} GC credited to everyone.')
        utilities.increment_stat("!creditall")
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{ctx.author},credited everyone,{amount}')


    # ____________________ End of Owner Only On Commands ____________________
    # ____________________ On Commands ____________________

    @commands.command(name="bank")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def bank(self, ctx: commands.Context):
        await ctx.send(f'{ctx.author.display_name} has {utilities.get_balance(ctx.author.id):,.2f} GC!')
        utilities.increment_stat("!bank")
    

    @bank.error
    async def bank_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'You\'re on cooldown. {error.retry_after:.0f} seconds.\nDo math, you literally used this command a few seconds ago.')
    

    @commands.command(name="bankfull")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def bankfull(self, ctx: commands.Context):
        await ctx.send(f'{ctx.author.display_name} has {utilities.get_balance(ctx.author.id):,} GC!')
        utilities.increment_stat("!bankfull")


    @bankfull.error
    async def bankfull_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'You\'re on cooldown. {error.retry_after:.0f} seconds.\nDo math, you literally used this command a few seconds ago.')
    

    @commands.command(name="networth")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def networth(self, ctx: commands.Context):
        await ctx.send(f"{ctx.author.display_name}'s networth is {utilities.get_user_networth(ctx.author.id):,.2f} GC!")
        utilities.increment_stat("!networth")


    @commands.command(name="firstvault")
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def firstvault(self, ctx: commands.Context):
        await ctx.send('https://imgur.com/zNqDe6g')
    

    # Can transfer GC from one to another.
    @commands.command(name="give")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def give(self, ctx: commands.Context, member: discord.Member, amount: float):
        user_id: int = ctx.author.id
        username: str = ctx.author

        if user_id == member.id:
            return
        curr_balance = utilities.get_balance(user_id)
        transaction_history_amount: float = utilities.get_give_transactions_total_last_hour(user_id)
        thirty_five_percent_balance: float = utilities.get_balance_from_one_hour_ago(user_id) * .35
        if amount <= 0:
            await ctx.send("The amount must be greater than zero.")
            return
        elif curr_balance <= 0:
            await ctx.send(f'{ctx.author.display_name} has no GC to give.')
            await ctx.send("<:peepoLoser:1268361127344078868>")
            return
        elif abs(transaction_history_amount) >= thirty_five_percent_balance or amount > thirty_five_percent_balance:
            remaining: float = thirty_five_percent_balance - abs(transaction_history_amount)
            await ctx.send(f"Can't send more than 35% of your balance from an hour ago. (Allowance: {utilities.truncate_hundredths(remaining):,})")
            return
        elif curr_balance - amount < 0:
            # await ctx.send(f'{ctx.author.display_name} doesn\'t have enough GC to give.')
            # await ctx.send(f'{ctx.author.display_name} has {curr_balance:,.2f} GC!')
            amount = curr_balance

        await ctx.send(f'{ctx.author.display_name} gave {amount:,.2f} GC to {member.display_name}.')

        utilities.update_balance(user_id, -amount)
        utilities.update_balance(member.id, amount)
        user_balance: float = utilities.get_balance(user_id)
        recipient_balance: float = utilities.get_balance(member.id)
        utilities.add_transaction_to_history(user_id, username, "give", -amount, user_balance)
        utilities.add_transaction_to_history(member.id, member.name, "gift", amount, recipient_balance)
        utilities.increment_stat("!give")
    

    # Used to see how much is in the vault currently.
    @commands.command(name="vault")
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def vault(self, ctx: commands.Context):
        await ctx.send(f'Galactic Coin Vault: **{utilities.get_balance(0):,.2f}** GC')
        utilities.increment_stat("!vault")


    # @commands.command(name="max")
    # @commands.cooldown(1, 10, commands.BucketType.user)
    # async def max(self, ctx: commands.Context):
    #     skill_level = utilities.get_upgrade_level("Wager Maximum", ctx.author.id)
    #     coinflip_max = 2_000 * (2 ** (skill_level)) if skill_level > 0 else 2_000
    #     # While slotto is sharing the same as coinflip, it might change in the future.
    #     slotto_max = 2_000 * (2 ** (skill_level)) if skill_level > 0 else 2_000
    #     card_war_max = (2_000 * (2 ** (skill_level))) * .25 if skill_level > 0 else 2_000
    #     bj_max = (2_000 * (2 ** (skill_level))) * .5 if skill_level > 0 else 600
    #     luck_max = 20_000 * (2 ** (skill_level)) if skill_level > 0 else 20_000

    #     output_string: str = f"{ctx.author.display_name}'s Maximums\n```"
    #     output_string += "{:15}: {:12,.0f} GC\n".format("Luck Max", luck_max)
    #     output_string += "{:15}: {:12,.0f} GC\n".format("Coinflip Max", coinflip_max)
    #     output_string += "{:15}: {:12,.0f} GC\n".format("Slotto Max", slotto_max)
    #     output_string += "{:15}: {:12,.0f} GC\n".format("Blackjack Max", bj_max)
    #     output_string += "{:15}: {:12,.0f} GC```".format("Card War Max", card_war_max)        

    #     await ctx.send(output_string)


    @commands.command(name="blackjack")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def blackjack_chart(self, ctx: commands.Context):
        await ctx.send("https://wizardofodds.com/games/blackjack/strategy/calculator/")
        utilities.increment_stat("bj chart")
    

    # ____________________ End of On Commands ____________________
    # ____________________ On Slash Commands ____________________

    @app_commands.command(name="games", description="Available games.")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 3, key=lambda i: (i.guild.id, i.user.id))
    async def games(self, interaction: discord.Interaction):
        output_str: str = f"/blackjack, /coinflip, /cwar, /luck, /roll (make your own game), /slotto\nFor more information: \
https://gist.github.com/ToekneeT/a99a3c3e5db6b6234e62410422d43d8f"
        await interaction.response.send_message(output_str)


    @app_commands.command(name="bank", description="Check your balance.")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 3, key=lambda i: (i.guild.id, i.user.id))
    async def bank_slash(self, interaction: discord.Interaction):
        name = interaction.user.display_name
        user_id = interaction.user.id
        await interaction.response.send_message(f'{name} has {utilities.get_balance(user_id):,.2f} GC!')
        utilities.increment_stat("!bank")


    @app_commands.command(name="networth", description="Check your networth.")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 3, key=lambda i: (i.guild.id, i.user.id))
    async def networth_slash(self, interaction: discord.Interaction):
        name = interaction.user.display_name
        user_id = interaction.user.id
        user_networth: float = utilities.get_user_networth(user_id)

        await interaction.response.send_message(f"{name}'s networth is {user_networth:,.2f} GC!")
        if user_networth >= 1_000_000_000 and "Golden Dragon" not in utilities.get_user_pets(user_id):
            utilities.add_pet_to_user(user_id, "Golden Dragon", 0)
            await interaction.channel.send(f'🎉 <@{user_id}> has been awarded the **Golden Dragon** for reaching a minimum networth of 1 Billion GC! 🎉')
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {interaction.user.name} claimed Golden Dragon')
            utilities.increment_stat("Golden Dragon")
        utilities.increment_stat("!networth")


    @app_commands.command(name="max", description="Check your maximums")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild.id, i.user.id))
    async def max_slash(self, interaction: discord.Interaction):
        name = interaction.user.display_name
        user_id = interaction.user.id

        skill_level = utilities.get_upgrade_level("Wager Maximum", user_id)
        coinflip_max = 2_000 * (2 ** (skill_level)) if skill_level > 0 else 2_000
        # While slotto is sharing the same as coinflip, it might change in the future.
        slotto_max = 2_000 * (2 ** (skill_level)) if skill_level > 0 else 2_000
        card_war_max = (2_000 * (2 ** (skill_level))) * .25 if skill_level > 0 else 2_000
        bj_max = (2_000 * (2 ** (skill_level))) * .5 if skill_level > 0 else 600
        luck_max = 20_000 * (2 ** (skill_level)) if skill_level > 0 else 20_000

        output_string: str = f"{name}'s Maximums\n```"
        output_string += "{:15}: {:12,.0f} GC\n".format("Luck Max", luck_max)
        output_string += "{:15}: {:12,.0f} GC\n".format("Coinflip Max", coinflip_max)
        output_string += "{:15}: {:12,.0f} GC\n".format("Slotto Max", slotto_max)
        output_string += "{:15}: {:12,.0f} GC\n".format("Blackjack Max", bj_max)
        output_string += "{:15}: {:12,.0f} GC```".format("Card War Max", card_war_max)

        await interaction.response.send_message(output_string)


    # Used to see how much is in the vault currently.
    @app_commands.command(name="vault", description="Current amount in the Galactic Coin Vault.")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 30, key=lambda i: (i.guild.id, i.user.id))
    async def vault_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Galactic Coin Vault: **{utilities.get_balance(0):,.2f}** GC')
        utilities.increment_stat("!vault")


    @app_commands.command(name="give", description="Transfer GC from you to another user.")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 3, key=lambda i: (i.guild.id, i.user.id))
    async def give_slash(self, interaction: discord.Interaction, member: discord.Member, amount: float):
        name = interaction.user.display_name
        username = interaction.user.name
        user_id = interaction.user.id

        if user_id == member.id:
            return
        curr_balance: float = utilities.get_balance(user_id)
        transaction_history_amount: float = utilities.get_give_transactions_total_last_hour(user_id)
        thirty_five_percent_balance: float = utilities.get_balance_from_one_hour_ago(user_id) * .35
        if amount <= 0:
            await interaction.response.send_message("The amount must be greater than zero.")
            return
        elif curr_balance <= 0:
            await interaction.response.send_message(f'{name} has no GC to give.')
            await interaction.channel.send("<:peepoLoser:1268361127344078868>")
            return
        elif abs(transaction_history_amount) >= thirty_five_percent_balance or amount > thirty_five_percent_balance:
            remaining: float = thirty_five_percent_balance - abs(transaction_history_amount)
            await interaction.response.send_message(f"Can't send more than 35% of your balance from an hour ago. (Allowance: {utilities.truncate_hundredths(remaining):,} GC)")
            return
        elif curr_balance - amount < 0:
            # await ctx.send(f'{ctx.author.display_name} doesn\'t have enough GC to give.')
            # await ctx.send(f'{ctx.author.display_name} has {curr_balance:,.2f} GC!')
            amount = curr_balance

        # Responds by stating where the GC transfers to and @s the recipient.
        await interaction.response.send_message(f'{name} gave {amount:,.2f} GC to <@{member.id}>.')

        utilities.update_balance(user_id, -amount)
        utilities.update_balance(member.id, amount)
        user_balance: float = utilities.get_balance(user_id)
        recipient_balance: float = utilities.get_balance(member.id)
        utilities.add_transaction_to_history(user_id, username, "give", -amount, user_balance)
        utilities.add_transaction_to_history(member.id, member.name, "gift", amount, recipient_balance)
        utilities.increment_stat("!give")
    

    @app_commands.command(name="gifted", description="How much have you gifted in the last hour.")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 3, key=lambda i: (i.guild.id, i.user.id))
    async def given(self, interaction: discord.Interaction):
        user_id: int = interaction.user.id
        transaction_history_amount: float = utilities.get_give_transactions_total_last_hour(user_id)
        thirty_five_percent_balance: float = utilities.get_balance_from_one_hour_ago(user_id) * .35
        remaining: float = utilities.truncate_hundredths(thirty_five_percent_balance - abs(transaction_history_amount))
        await interaction.response.send_message(f"You've gifted {abs(utilities.truncate_hundredths(transaction_history_amount)):,} GC in the last hour.\nAllowance: {remaining:,} GC.")
        return


    # Does a coin flip, heads or tails.
    @app_commands.command(name="coinflip", description="Flip a coin.")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 2, key=lambda i: (i.guild.id, i.user.id))
    async def coinflip(self, interaction: discord.Interaction, wager: float = 0.0) -> None:
        coin: float = random.random()
        user_id = interaction.user.id
        user: str = str(interaction.user.name)
        display_name: str = str(interaction.user.display_name)
        user_balance = utilities.get_balance(user_id)
        # Get user fortune, if it's negative, higher chance to roll tails.
        # if it's positive, higher chance to roll heads.
        user_fortune = utilities.get_user_fortune(user_id)
        log_text: str = f"OG: {coin} "
        
        output_string: str = ""

        # Checks user skills for maximum bet.
        user_max = get_user_max(user_id, 2_000)
        
        if wager > user_balance and user_balance <= user_max:
            wager = user_balance
        elif wager > user_max:
            # await interaction.response.send_message(f"Your maximum is {user_max:,} GC.")
            # return
            wager = user_max
        
        # Positive fortune is lucky, negative is unlucky.
        if user_fortune > 0:
            coin = utilities.fortune_roll(user_id,
                                          user_fortune,
                                          coin,
                                          random.random(),
                                          favor_high=False)
            log_text += f"fortune affected: {coin} "
        elif user_fortune < 0:
            coin = utilities.fortune_roll(user_id,
                                          user_fortune,
                                          coin,
                                          random.random(),
                                          favor_high=True)
            log_text += f"fortune affected: {coin} "
        
        # Checks if they have the Coinflip Consec skill.
        payout: float = 2 if coin <= .49 else 0
        user_pay_with_bonus = get_coinflip_bonus_pay(user_id) if coin <= .49 else 0
        user_last_coin = utilities.get_user_last_coin(user_id)

        if coin <= .49:
            output_string += f"Heads <a:coinflip:1271989785782784051>"
            log_text += "Heads"
            utilities.increment_stat("Heads")
            if wager > 0 and wager <= user_balance:
                # Track the last coin the user received.
                utilities.set_user_last_coin(user_id, "Heads")
        else:
            output_string += f"Tails <a:coinTails:1271991655502712915>"
            log_text += "Tails"
            utilities.increment_stat("Tails")
            if wager > 0 and wager <= user_balance:
                # Attempts to save the heads streak if the user has the streak saver skill.
                streak_saver: int = utilities.get_upgrade_level("Streak Saver", user_id)
                is_streak_saved: bool = False
                if streak_saver > 0:
                    is_streak_saved = utilities.attempt_streak_save(user_id, streak_saver)

                if is_streak_saved:
                    output_string += "\nStreak Saver activated!"
                else:
                    utilities.set_user_last_coin(user_id, "Tails")
        
        if await is_bet(interaction, wager):
            # Payout is different if they have the Consec skill + they land on heads previously.
            coin_count = utilities.get_user_coin_count(user_id)
            if user_last_coin == "Heads" and payout:

                # Secret pet for getting heads 16 times in a row.
                # Courtesy of toastyboi.
                if coin_count >= 16 and "Iridescent Mallard" not in utilities.get_user_pets(user_id):
                    utilities.add_pet_to_user(user_id, "Iridescent Mallard", 0)
                    await interaction.channel.send(f'🎉 <@{user_id}> has been awarded the **Iridescent Mallard** for reaching a giga heater! 🎉')
                    logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {interaction.user.name} claimed Iridescent Mallard')
                    utilities.increment_stat("Iridescent Mallard")

                if coin_count >= 4:
                    output_string += f'\n<a:heater:1275362788788797482> You\'re on a heater! Heads {coin_count} times in a row! \
<a:heater:1275362788788797482>'
                else:
                    output_string += f'\nYou\'ve hit Heads {coin_count} times in a row!'
                    
                if user_pay_with_bonus > 2.0:
                    # Increase payout rates and let the user know.
                    output_string += f'\nPayout Rate: {user_pay_with_bonus:,.2f}x'
                output_string += utilities.bet_payout(user_id, user, display_name, wager, user_pay_with_bonus)


            else:
                if coin_count >= 4 and user_last_coin == "Tails":
                    output_string += f'\n<a:rigged:1275566471908556821> You\'ve hit Tails {coin_count} times in a row. <a:rigged:1275566471908556821>'
                elif coin_count >= 2 and user_last_coin == "Tails":
                    output_string += f'\nYou\'ve hit Tails {coin_count} times in a row.' 
                output_string += utilities.bet_payout(user_id, user, display_name, wager, payout)
        
        await interaction.response.send_message(output_string)
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},{log_text}')
    

    # Recursive luck command.
    @app_commands.command(name="luck", description="Test your luck.")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 2, key=lambda i: (i.guild.id, i.user.id))
    async def luck(self, interaction: discord.Interaction, wager: float = 0.0):
        roll_amt: int = luck_roll()
        user_id: int = interaction.user.id
        user: str = str(interaction.user.name)
        user_balance: float = utilities.get_balance(interaction.user.id)
        display_name: str = str(interaction.user.display_name)
        user_fortune: int = utilities.get_user_fortune(user_id)
        user_max = get_user_max(user_id, 20_000)
        log_text: str = f"Luck, OG: {roll_amt} "

        output_string = ""

        if wager != 0 and wager < 200:
            await interaction.response.send_message("Minimum 200 GC if placing a bet.")
            return

        if wager > user_balance and user_balance <= user_max:
            wager = user_balance
        elif wager > user_max:
            # await interaction.response.send_message(f"Your maximum is {user_max:,} GC.")
            # return
            wager = user_max
        
        # Positive fortune is lucky, negative is unlucky.
        if user_fortune > 0:
            roll_amt = utilities.fortune_roll(user_id, user_fortune, roll_amt, luck_roll())
            log_text += f"fortune affected: {roll_amt}"
        elif user_fortune < 0:
            roll_amt = utilities.fortune_roll(user_id, user_fortune, roll_amt, luck_roll(), favor_high=False)
            log_text += f"fortune affected: {roll_amt}"

        # If the roll is 5 or higher, special print out with dice.
        if roll_amt >= 5:
                output_string += f'{"<a:GoldDice:1269187263116476491>"*(roll_amt-4)} {convert_roll_to_dot(roll_amt)} {"<a:GoldDice:1269187263116476491>"*(roll_amt-4)}'
        else:
            output_string += f'{convert_roll_to_dot(roll_amt)}'
        
        if await is_bet(interaction, wager):
            output_string += utilities.bet_payout(user_id, user, display_name, wager, luck_payout(roll_amt))
        
        await interaction.response.send_message(output_string)
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},{log_text}')


        # If the roll is higher than the previous highest, it'll pin the new one and unpin the old.
        if roll_amt > config["luckiest_num"]:
            await new_luckiest(self.bot, interaction, roll_amt)
            # Ensures that a wager was placed.
            if wager > 0 and wager <= utilities.get_balance(user_id):
                await vault_winner(interaction, self.bot)

        utilities.increment_stat("luck")
    

    @app_commands.command(name="fortune", description="Get your fortune.")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 3600, key=lambda i: (i.guild.id, i.user.id))
    async def fortune(self, interaction: discord.Interaction):
        user_balance: float = utilities.get_balance(interaction.user.id)
        embed = discord.Embed(color=discord.Color.red())
        description: str = f"Balance: {user_balance:,.2f} GC\n\
\n<a:omikuji:1277921174357282907> Receive your fortune in the form of an Omikuji. <a:omikuji:1277921174357282907>\n\n"
        description += f"Prices:\n"
        description += f"Cheap: **{max(user_balance * .02, 500):,.2f} GC**\n"
        description += f"Standard: **{max(user_balance * .05, 2000):,.2f} GC**\n"
        description += f"Quality: **{max(user_balance * .1, 10000):,.2f} GC**\n\n"
        description += "Cheap has a higher chance to roll a bad fortune. Cannot get Great Blessing.\n"
        description += "Standard has no weight.\n"
        description += "Quality has a higher chance to roll a good fortune. Cannot get Great Bad Fortune."
        embed.set_author(name=f'Fortune')
        embed.add_field(name=f"{interaction.user.display_name}", value=description)
        view = FortuneMenu(interaction.user)
        await interaction.response.send_message(embed=embed, view=view)
    

    @fortune.error
    async def fortune_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.response.send_message(f'You\'re on cooldown. {error.retry_after/60:.0f} minutes.', ephemeral=True)


    # Grabs the person who holds the record for the highest /luck roll.
    @app_commands.command(name="luckiest", description="The luckiest.")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild.id, i.user.id))
    async def luckiest(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f'The luckiest: <a:GoldDice:1269187263116476491> {config["luckiest"]} <a:GoldDice:1269187263116476491> with {config["luckiest_num"]}')
        utilities.increment_stat("luckiest command")
    

    @commands.Cog.listener()
    async def on_slash_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f'This command is on cooldown. Try again after {error.retry_after:.2f} seconds.', ephemeral=True)
            logger.error(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{error},{interaction.user.name},1')
        elif isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("You don't have permissions to do this.", ephemeral=True)
            logger.error(f'{interaction.user.name}\nPermission error: {error}')
        else:
            await interaction.response.send_message(f'{interaction.user.name}\nAn error occurred: {str(error)}.', ephemeral=True)
            logger.error(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{error},{interaction.user.name},1')


async def setup(bot):
    await bot.add_cog(Casino(bot))