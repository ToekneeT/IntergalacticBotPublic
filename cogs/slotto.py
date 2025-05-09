import discord, logging, random, datetime, asyncio
from discord.ext import commands
from discord import app_commands
from helper import utilities

logger = logging.getLogger()
logging.basicConfig(filename="stats.log", level=logging.INFO)


#================================================================================== Adjust ==================================================================================
# Same maximum as Coinflip
def get_max(user_id: int) -> int:
    wager_max: int = utilities.get_upgrade_level("Wager Maximum", user_id)
    return (2_000 * (2 ** (wager_max)))


def get_dealer_numbers() -> list[int, int, int]:
    return [random.randint(1, 99), random.randint(1, 99), random.randint(1, 99)]


# If the user is fortune affected, reroll the dealer's numbers based on what fortune they have.
def fortune_roll_dealer(user_fortune: int, user_id: int, player_numbers: list[int, int, int], dealer_numbers: list[int, int, int]) -> list[int, int, int]:
    log_message: str = f"Original dealer's: {dealer_numbers} "
    # Use a fortune.
    # Rerolls the dealer's numbers based on fortune.
    # If good fortune, reroll all numbers that aren't equal to the player's.
    # Opposite if bad fortune.
    if user_fortune > 0:
        utilities.set_user_fortune(user_id, user_fortune-1)
        for idx in range(3):
            if player_numbers[idx] != dealer_numbers[idx]:
                dealer_numbers[idx] = random.randint(1, 99)
    elif user_fortune < 0:
        utilities.set_user_fortune(user_id, user_fortune+1)
        for idx in range(3):
            if player_numbers[idx] == dealer_numbers[idx]:
                dealer_numbers[idx] = random.randint(1, 99)

    log_message += f"Fortune Affected dealer's: {dealer_numbers}"
    logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")}, {log_message}')
    return dealer_numbers


def matching_numbers(player_numbers, dealer_numbers, username) -> int:
    matching: int = 0
    log_message_player: str = "Player's: "
    log_message_dealer: str = "Dealer's: "
    for idx in range(3):
        log_message_player += f"{player_numbers[idx]}, "
        log_message_dealer += f"{dealer_numbers[idx]}, "
        if player_numbers[idx] == dealer_numbers[idx]:
            matching += 1
    
    logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")}, {username}, {log_message_player}\n{log_message_dealer}')
    return matching


payouts = {
    0: 0,
    1: 21,
    2: 401,
    3: 3_501,
}


class Slotto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="slotto", description="A round of Slotto.")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 4, key=lambda i: (i.guild.id, i.user.id))
    async def slotto(self, interaction: discord.Interaction, wager: float, first: int = 0, second: int = 0, third: int = 0):
        if wager <= 0 or wager < 50:
            await interaction.response.send_message("Must put a wager greater than 50 GC.")
            return
        # Can't randomize the numbers in the parameters as it'll just run once the bot starts
        # thereby giving the players the exact same numbers every single time unless they choose to change them.
        # So I give them all an initial value of something that can't be achieved, and then randomize them from there.
        if first == 0:
            first = random.randint(1, 99)
        if second == 0:
            second = random.randint(1, 99)
        if third == 0:
            third = random.randint(1, 99)
        # Exit early, numbers can only be in a range between 1 and 99.
        if first < 1 or first > 99:
            await interaction.response.send_message("Numbers can only be between 1 and 99. (First Number)", ephemeral=True)
            return
        elif second < 1 or second > 99:
            await interaction.response.send_message("Numbers can only be between 1 and 99. (Second Number)", ephemeral=True)
            return
        elif third < 1 or third > 99:
            await interaction.response.send_message("Numbers can only be between 1 and 99. (Third Number)", ephemeral=True)
            return

        user_id = interaction.user.id
        username: str = interaction.user.name
        display_name: str = interaction.user.display_name
        user_balance: float = utilities.get_balance(user_id)
        user_maximum: float = get_max(user_id)

        if wager > user_balance and user_balance <= user_maximum:
            wager = user_balance
        elif wager > user_maximum:
            wager = user_maximum

        player_numbers: list[int, int, int] = [first, second, third]
        dealer_numbers: list[int, int, int] = get_dealer_numbers()

        user_fortune = utilities.get_user_fortune(user_id)
        # As long as the user is fortune affected, it runs.
        if user_fortune:
            dealer_numbers = fortune_roll_dealer(user_fortune, user_id, player_numbers, dealer_numbers)

        round_results: int = matching_numbers(player_numbers, dealer_numbers, username)
        payout_results: str = utilities.bet_payout(user_id, username, display_name, wager, payouts[round_results])

        output_str: str = f"{display_name}'s numbers: **{first:02}**, **{second:02}**, **{third:02}**\nWinning numbers: ..."
        await interaction.response.send_message(output_str)
        output_str = output_str[:-3]
        for idx in range(3):
            await asyncio.sleep(0.5)
            if idx != 2:
                output_str += f"**{dealer_numbers[idx]:02}**, "
            else:
                output_str += f"**{dealer_numbers[idx]:02}**"
            await interaction.edit_original_response(content=output_str)

        await asyncio.sleep(0.5)
        output_str += f"\nMatched: **{round_results}** numbers"
        output_str += payout_results
        await interaction.edit_original_response(content=f'\n{output_str}')
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{username},played slotto,')

        utilities.increment_stat("slotto")

async def setup(bot):
    await bot.add_cog(Slotto(bot))