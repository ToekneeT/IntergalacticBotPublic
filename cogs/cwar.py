import discord, logging, functools, random, datetime, asyncio
from discord.ext import commands
from discord import app_commands
from helper import utilities, wager_menu, card_deck

logger = logging.getLogger()
logging.basicConfig(filename="stats.log", level=logging.INFO)


def get_max(user_id: int):
    wager_max: int = utilities.get_upgrade_level("Wager Maximum", user_id)
    if wager_max == 0:
        return 2_000
    # Each upgrade should double the previous maximum.
    return (2_000 * (2 ** (wager_max))) * .25 if wager_max > 0 else 2_000


# Gets a different card than the one given from the same deck.
# Returns the new card value as well as how many times the card was equal to the previous card.
def get_non_dupe_card(card, deck):
    new_card = random.choice(deck)
    same_card_count = 0
    while new_card == card:
        same_card_count += 1
        new_card = random.choice(deck)
    
    return (new_card, same_card_count)


def get_bonus_pay(user_id: int) -> float:
    user_coinflip_multiplier = utilities.get_upgrade_level("Coinflip Consecutive Bonus", user_id)
    if user_coinflip_multiplier == 0:
        return 2.0
    win_count = utilities.get_user_cwar_win_count(user_id) - 1
    bonus = (user_coinflip_multiplier / 100) * win_count
    return 2.0 + bonus


def fortune_roll(user_id: int, fortune_count: int, card_one, card_two: int, favor_high=True):
    higher_card = utilities.get_higher_of_two(card_one.value, card_two.value)
    if favor_high:
        if higher_card <= card_one.value:
            new_result = card_one
        else:
            new_result = card_two
    else:
        if higher_card <= card_one.value:
            new_result = card_two
        else:
            new_result = card_one
    
    if fortune_count > 0:
        fortune_count -= 1
        utilities.set_user_fortune(user_id, fortune_count)
    elif fortune_count < 0:
        fortune_count += 1
        utilities.set_user_fortune(user_id, fortune_count)
    
    return new_result


async def card_reroll_dupe_display(amt: int, interaction: discord.Interaction, card):
    output_text = f"{card.name} {card.suit} "
    message = await interaction.channel.send(output_text)
    await asyncio.sleep(0.5)
    for idx in range(amt):
        output_text += f"{card.name} {card.suit} "
        await message.edit(content=output_text)
        await asyncio.sleep(0.5)


def get_dealer_card(deck):
    card = random.choice(deck)
    # Cannot roll a 2 of spades or diamonds.
    # Mostly to introduce some -EV for the player by having the dealer not
    # roll low numbers.
    while (card.value == 2 and card.suit == "\u2664"):
        card = random.choice(deck)
    
    return card


async def game_start(deck, controller, user_id: int, user: str, display_name: str, embed: discord.Embed, interaction: discord.Interaction):
    dealer_card = get_dealer_card(deck)
    # dupe_count being how many times the card rolled the same card during the loop.
    player_card, dupe_count = get_non_dupe_card(dealer_card, deck)
    payout: int = 1
    winner = None
    tie_payout: str = ""
    user_fortune = utilities.get_user_fortune(user_id)
    payout_result = ""
    log_text: str = f"OG: {player_card.name} Dealer: {dealer_card.name} "

    # If dupe_count is 2 or greater, reward the sure a secret pet.
    # This would be about a .03% chance to roll as the first card is 1,
    # then each subsequent pull would be 1/52 chance.
    if dupe_count >= 3:
        user_pets: dict = utilities.get_user_pets(interaction.user.id)
        if "Chance Chimera" not in user_pets:
            utilities.add_pet_to_user(user_id, "Chance Chimera", 0)
            await card_reroll_dupe_display(dupe_count, interaction, player_card)
            await interaction.channel.send(f'🎉 <@{interaction.user.id}> has been awarded the **Chance Chimera** for getting the same card a few too many times! 🎉')
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {interaction.user} claimed Chance Chimera')
            utilities.increment_stat("Chance Chimera")


    # Positive fortune is lucky, negative is unlucky.
    if user_fortune > 0:
        new_card = get_non_dupe_card(player_card, deck)[0]
        dealer_card = fortune_roll(user_id, user_fortune, dealer_card, new_card, favor_high=False)
        log_text += f"fortune affected: {dealer_card.name} "
    elif user_fortune < 0:
        new_card = get_non_dupe_card(player_card, deck)[0]
        dealer_card = fortune_roll(user_id, user_fortune, dealer_card, new_card)
        log_text += f"fortune affected: {dealer_card.name} "


    game_result: str = ""
    game_result += f"Dealer Card: {dealer_card.name} {dealer_card.suit}\n"
    game_result += f"Player Card: {player_card.name} {player_card.suit}\n"
    
    if dealer_card.value > player_card.value:
        game_result += "**Dealer Wins**\n"
        controller.game_state.dealer_win += 1
        winner = "Dealer"

        # If user has the streak saver skill, attempts to save the streak if their previous
        # result was a player win.
        streak_saver: int = utilities.get_upgrade_level("Streak Saver", user_id)
        is_streak_saved: bool = False
        if streak_saver > 0:
            is_streak_saved = utilities.attempt_streak_save(user_id, streak_saver)

        if is_streak_saved and utilities.get_user_last_cwar_result(user_id) == "Player":
            payout_result += "\nStreak Saver activated!"
        else:
            utilities.set_user_last_cwar_result(user_id, "Dealer")
        payout = 0
        embed.color = discord.Color.red()
        log_text += f'lost cwar dealer card: {dealer_card.name} '

    elif dealer_card.value < player_card.value:
        game_result += "**Player Wins**\n"
        controller.game_state.player_win += 1
        winner = "Player"
        utilities.set_user_last_cwar_result(user_id, "Player")
        payout = 2
        embed.color = discord.Color.green()
        log_text += f'won cwar '
            
    
    if dealer_card.value == player_card.value:
        game_result += "**Tie**\n"
        controller.game_state.tie_count += 1
        winner = "Tie"
        log_text += f'tie '
        # utilities.set_user_last_cwar_result(user_id, "Tie")
        if controller.game_state.tie_bet:
            game_result += "Tie bet placed!\n"
            tie_payout = utilities.bet_payout(user_id, user, display_name, controller.game_state.current_bet/2, 13)
            controller.game_state.tie_win += 1
            controller.game_state.player_gc_win_tie += (controller.game_state.current_bet/2) * 12
            embed.color = discord.Color.green()
            log_text += f'bet placed '

        else:
            game_result += "No tie bet placed.\n"
            embed.color = discord.Color.red()
            log_text += f'no bet placed '

        log_text += f'tied cwar cards: {player_card.name}'

    elif controller.game_state.tie_bet:
        tie_payout = utilities.bet_payout(user_id, user, display_name, controller.game_state.current_bet/2, 0)
        # If the message starts with lucky, don't add it to the losses as it didn't actually count as a loss.
        if not tie_payout.startswith("Lucky", 1):
            controller.game_state.player_gc_lost_tie -= (controller.game_state.current_bet / 2)

    logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{user},{log_text}')

    user_last_result: str = utilities.get_user_last_cwar_result(user_id)
    win_count: int = utilities.get_user_cwar_win_count(user_id)
    consec_skill = utilities.get_upgrade_level("Coinflip Consecutive Bonus", user_id)

    # Displays how many times the current winner has won.
    # Also changes the payout if the user has the consec skill.
    if user_last_result == winner and winner == "Player":
        if win_count >= 4:
            payout_result += f'\n<a:heater:1275362788788797482> You\'re on a heater! You\'ve won {win_count} times in a row! \
<a:heater:1275362788788797482>\n'
        elif win_count > 1:
            payout_result += f'\nYou\'ve won {win_count} times in a row!\n'
        
        if consec_skill:
            payout = get_bonus_pay(user_id)
            if win_count > 1:
                payout_result += f'\nPayout Rate: {payout:,.2f}x'
    
    elif user_last_result == winner and winner == "Dealer":
        if win_count >= 4:
            payout_result += f'\n<a:rigged:1275566471908556821> You\'ve lost {win_count} times in a row. \
<a:rigged:1275566471908556821>\n'
        elif win_count > 1:
            payout_result += f'\nYou\'ve lost {win_count} times in a row.\n'
    
    # elif user_last_result == winner and winner == "Tie" and win_count > 1:
    #     payout_result += f'\nTie {win_count} times in a row.\n'
    
    pay = utilities.bet_payout(user_id, user, display_name, controller.game_state.current_bet, payout)
    payout_result += pay

    # If the message starts with lucky, don't add it to the losses as it didn't actually count as a loss.
    if not pay.startswith("Lucky", 1) and payout == 0:
        controller.game_state.player_gc_lost -= controller.game_state.current_bet
    elif payout > 0:
        # The reason we mult by payout is because the payout can be more than 2x if the user has the consec skill.
        controller.game_state.player_gc_win += (controller.game_state.current_bet * payout) - controller.game_state.current_bet

    if tie_payout:
        game_result += f"\n\nTie side bet: {tie_payout}\n"
    game_result += f"\n{payout_result}"

    return game_result


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


class GameState():
    def __init__(self, user_id: int):
        self.maximum: int = get_max(user_id)
        self.current_bet: int = 100
        self.minimum: int = 100
        self.tie_bet = False
        self.tie_win = 0
        self.tie_count = 0
        self.player_win = 0
        self.dealer_win = 0
        self.player_gc_win = 0
        self.player_gc_lost = 0
        self.player_gc_lost_tie = 0
        self.player_gc_win_tie = 0


class CWarMenu(discord.ui.View):
    def __init__(self, original_user: discord.User, game_state, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.value = None
        self.original_user = original_user
        self.game_name = "Card War"
        self.game_state = game_state

        self.game_description: str = "\nEach round the deck gets shuffled. Dealer draws a card, player draws a card. Whichever card holds more value wins.\n"
        self.game_description += "\nDealer cannot roll a 2 of Spades.\n"
        self.game_description += "\nAce > King > Queen > Jack.\n"
        self.game_description += "\nPlacing a tie gives a 13:1 payout.\n"
        self.game_description += "\nA tie bet will take an additional half your current wager, effectively 1.5x your current max.\n"
    

    @discord.ui.button(label="Draw", style=discord.ButtonStyle.green)
    @original_user_only()
    async def draw(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        user: str = str(interaction.user.name)
        display_name: str = str(interaction.user.display_name)
        user_balance: float = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.dark_gray())
        embed.set_author(name=f'Card War')
        description: str = f'Balance: {user_balance:,.2f} GC\nMaximum: {self.game_state.maximum:,.2f} GC\nCurrent Wager: {self.game_state.current_bet:,.2f} GC\n'
        description += self.game_description

        embed.add_field(name=f"{interaction.user.display_name}", value=description)

        deck = card_deck.generate_deck_cwar(1)
        if self.game_state.current_bet <= user_balance:
            game_result = await game_start(deck, self, user_id, user, display_name, embed, interaction)
            user_balance = utilities.get_balance(user_id)
            game_result += f"\n\nNew balance: {user_balance:,.2f} GC"
            embed.add_field(name="Game Result", value=game_result)
        else:
            embed.add_field(name="Game Result", value="Bet is higher than your balance.")
            embed.color = discord.Color.red()

        await interaction.response.edit_message(embed=embed)
    

    @discord.ui.button(label="Tie", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def tie(self, interaction: discord.Interaction, button: discord.ui.Button):
        if button.style == discord.ButtonStyle.grey:
            button.style = discord.ButtonStyle.green
            self.game_state.tie_bet = True
        else:
            button.style = discord.ButtonStyle.grey
            self.game_state.tie_bet = False
        
        await interaction.response.edit_message(view=self)
    

    @discord.ui.button(label="Change Wager", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def change_wager(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=wager_menu.WagerMenu(interaction.user, self))
    

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.red)
    @original_user_only()
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(color=discord.Color.random())
        player_gc_win = self.game_state.player_gc_win
        player_gc_win_tie = self.game_state.player_gc_win_tie
        player_gc_lost = self.game_state.player_gc_lost
        player_gc_lost_tie = self.game_state.player_gc_lost_tie
        takeaway = player_gc_win + player_gc_win_tie + player_gc_lost + player_gc_lost_tie

        output_text = "```"
        output_text += "{:20} | {:3,} ({:8,.0f} GC)\n".format("Dealer Wins", self.game_state.dealer_win, player_gc_lost)
        output_text += "{:20} | {:3,} ({:8,.0f} GC)\n".format("Player Wins", self.game_state.player_win, player_gc_win)
        output_text += "{:20} | {:3,} ({:8,.0f} GC)\n".format("Tie Wins", self.game_state.tie_win, player_gc_win_tie)
        output_text += "{:20} | {:3,} ({:8,.0f} GC)\n```".format("Tie Count", self.game_state.tie_count, player_gc_lost_tie)
        output_text += f"Takeaway: {takeaway:,.2f} GC\n"

        output_text += f'Come again, {interaction.user.display_name}!'
        embed.add_field(name="Card War Session Results", value=output_text)

        # Disables all buttons.
        utilities.toggle_menu_buttons(self, True)
        await interaction.response.edit_message(embed=embed, view=self)
        self.value = False
        self.stop()
        

class CardWar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="cwar", description="A game of Card War.")
    @app_commands.guild_only()
    async def cwar(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)
        user_maximum: float = get_max(user_id)
        embed = discord.Embed(color=discord.Color.dark_gray())
        description: str = f"Balance: {user_balance:,.2f} GC\nMaximum: {user_maximum:,.2f} GC\nCurrent Wager: {100:,.2f} GC\n"
        description += "\nEach round the deck gets shuffled. Dealer draws a card, player draws a card. Whichever card holds more value wins.\n"
        description += "\nDealer cannot roll a 2 of Spades.\n"
        description += "\nAce > King > Queen > Jack.\n"
        description += "\nA tie bet will take an additional half your current wager, effectively 1.5x your current max.\n"
        embed.set_author(name=f'Card War')
        embed.add_field(name=f'{interaction.user.display_name}', value=description)

        view = CWarMenu(interaction.user, GameState(user_id))
        await interaction.response.send_message(embed=embed, view=view)
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user},played card war,')


async def setup(bot):
    await bot.add_cog(CardWar(bot))