import discord, logging, functools, random, datetime, asyncio
from discord.ext import commands
from discord import app_commands
from helper import utilities, wager_menu, card_deck

logger = logging.getLogger()
logging.basicConfig(filename="stats.log", level=logging.INFO)


def get_max(user_id: int):
    wager_max: int = utilities.get_upgrade_level("Wager Maximum", user_id)
    # If your max lvl is 0, then the starting max is 600.
    if wager_max == 0:
        return (600)
    # Each upgrade should double the previous maximum.
    return (2_000 * (2 ** (wager_max))) * .5


# Checks if the hand is blackjack or not.
def is_blackjack(hand) -> bool:
    if hand[0].value == 11 and hand[1].value == 10:
        return True
    if hand[0].value == 10 and hand[1].value == 11:
        return True
    return False


# Deals a card from the deck, returns the value of card.
def deal_card(hand, controller) -> int:
    dealt_card = controller.deck.pop()
    hand.append(dealt_card)
    return dealt_card.value


# Prevents card total greater than 21 due to aces by converting
# the ace value from 11 to 1. Returns the hand total.
def aces(hand, hand_total) -> int:
    count = 0
    while hand_total > 21 and count < len(hand):
        if hand[count].value == 11:
            hand[count].value = 1
            hand_total -= 10
            count += 1
        else:
            count += 1
    return hand_total


def get_hand_value(hand) -> int:
    hand_total = 0
    for card in hand:
        hand_total += card.value
    
    if hand_total > 21:
        aces_hand = aces(hand, hand_total)
        return min(hand_total, aces_hand)
    
    return hand_total


def surrender(dealer_hand) -> bool:
    if (not is_blackjack(dealer_hand)):
        return True
    return False


async def draw_a_single_card(controller, interaction: discord.Interaction, wager: float, log_text: str):
    toggle_double_button(controller, True)
    user_id: int = interaction.user.id
    username: str = interaction.user.name
    display_name: str = interaction.user.display_name
    dealt_card = deal_card(controller.player_hand, controller.game)
    hand_value = get_hand_value(controller.player_hand)
    controller.player_hand_str += f'{controller.player_hand[-1].name} {controller.player_hand[-1].suit} '
    dealer_hand: str = f'Dealer Hand: {controller.dealer_hand[0].name} {controller.dealer_hand[0].suit}   ?\n'
    table: str = ""

    log_text += f"drew {dealt_card} "
    log_text += f"Total: {hand_value} "

    if hand_value > 21:
        table += f"**Bust**\n{controller.dealer_hand_str}\n{controller.player_hand_str}\n"
        table += f"\nDealer Total: {get_hand_value(controller.dealer_hand)}\nPlayer Total: {get_hand_value(controller.player_hand)}\n"
        # Payout here
        output_str: str = utilities.bet_payout(user_id, username, display_name, wager, 0)
        # If the message starts with lucky, don't add it to the losses as it didn't actually count as a loss.
        if not output_str.startswith("Lucky", 1):
            controller.game.player_gc_lost -= wager

        
        table += f"{output_str}\n\nNew Balance: {utilities.get_balance(user_id):,.2f} GC\n"
        controller.embed.set_field_at(index=0, name=f"Game Results\nWager: {controller.game.current_bet:,.2f} GC", value=table)
        controller.embed.color = discord.Color.red()
        toggle_start_buttons(controller, False)
        toggle_menu_buttons(controller, True)
        await interaction.edit_original_response(embed=controller.embed, view=controller)
        # Reset the game values to a new game, minus the deck.
        reset_hands(controller)
        log_text += "Bust!"
        controller.game.dealer_count += 1
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {log_text}')
        await shuffle_cards(controller, interaction)
        return hand_value
    
    table += f"{dealer_hand}{controller.player_hand_str}\n"
    table += f"\nDealer Total: {controller.dealer_hand[0].value}\nPlayer Total: {get_hand_value(controller.player_hand)}\n"
    controller.embed.set_field_at(index=0, name=f"Current Game\nWager: {controller.game.current_bet:,.2f} GC", value=table)
    await interaction.edit_original_response(embed=controller.embed, view=controller)

    logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {log_text}')
    return hand_value


async def player_stands(controller, interaction: discord.Interaction, wager: float, log_text: str=""):
    user_id: int = interaction.user.id
    username: str = interaction.user.name
    display_name: str = interaction.user.display_name
    dealer_draw(controller.dealer_hand, controller.game)
    player_total = get_hand_value(controller.player_hand)
    dealer_total = get_hand_value(controller.dealer_hand)

    log_text += f"{player_total} "
    log_text += f"Dealer total: {dealer_total} "

    await reveal_dealer_cards(controller.player_hand_str, player_total, controller.dealer_hand, interaction, controller)

    table: str = ""
    table += f"{controller.dealer_hand_str}\n{controller.player_hand_str}"
    table += f"\n\nDealer Total: {dealer_total}\nPlayer Total: {player_total}\n"

    if player_total == dealer_total:
        controller.game.push_count += 1
        controller.embed.color = discord.Color.dark_grey()
        log_text += "Push "
        table += "**Push!**\n"
        # Payout here
        output_str: str = utilities.bet_payout(user_id, username, display_name, wager, 1)
    elif (player_total > dealer_total and player_total <= 21) or (dealer_total > 21 and player_total <=21):
        controller.game.player_count += 1
        controller.game.player_gc_win += wager
        controller.embed.color = discord.Color.green()
        log_text += "player win "
        table += "**Player Wins!**\n"
        # Payout here
        output_str: str = utilities.bet_payout(user_id, username, display_name, wager, 2)
    else:
        controller.game.dealer_count += 1
        controller.embed.color = discord.Color.red()
        log_text += "dealer win "
        table += "**Dealer Wins!**\n"
        # Payout here
        output_str: str = utilities.bet_payout(user_id, username, display_name, wager, 0)
        # If the message starts with lucky, don't add it to the losses as it didn't actually count as a loss.
        if not output_str.startswith("Lucky", 1):
            controller.game.player_gc_lost -= wager
    
    table += f"{output_str}\n\nNew Balance: {utilities.get_balance(user_id):,.2f} GC"
    
    controller.embed.set_field_at(index=0, name=f"Game Results\nWager: {controller.game.current_bet:,.2f} GC", value=table)
    await interaction.edit_original_response(embed=controller.embed)
    reset_hands(controller)

    logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {log_text}')
    # await shuffle_cards(controller, interaction)


# Draws cards to the dealer's hand if it's not already 21, or
# if it's less than 17.
# Returns the total card value of dealer's hand.
def dealer_draw(dealer_hand, controller) -> int:
    hand_value = get_hand_value(dealer_hand)
    while hand_value < 17 and hand_value != 21:
        deal_card(dealer_hand, controller)
        hand_value = get_hand_value(dealer_hand)
    
    return get_hand_value(dealer_hand)


async def deal_new_hands(player_hand, dealer_hand, interaction: discord.Interaction, controller):
    user_id: int = interaction.user.id
    username: str = interaction.user.name
    display_name: str = interaction.user.display_name
    toggle_menu_buttons(controller, True)
    await interaction.response.defer()
    await interaction.edit_original_response(view=controller)
    dealer_cards: str = "Dealer Hand: "
    player_cards: str = "Player Hand: "

    table: str = f'{dealer_cards}\n{player_cards}'
    controller.embed.set_field_at(index=0, name=f"Current Game\nWager: {controller.game.current_bet:,.2f} GC", value=table)

    await interaction.edit_original_response(embed=controller.embed)
    await asyncio.sleep(0.5)

    for idx in range(2):
        player_cards += f"{player_hand[idx].name} {player_hand[idx].suit} "
        table = f'{dealer_cards}\n{player_cards}'
        await asyncio.sleep(0.5)
        controller.embed.set_field_at(index=0, name=f"Current Game\nWager: {controller.game.current_bet:,.2f} GC", value=table)
        await interaction.edit_original_response(embed=controller.embed)

        if idx == 0:
            dealer_cards += f"{dealer_hand[idx].name} {dealer_hand[idx].suit} "
        else:
            dealer_cards += f"  ?"
        
        table = f'{dealer_cards}\n{player_cards}'
        await asyncio.sleep(0.5)
        controller.embed.set_field_at(index=0, name=f"Current Game\nWager: {controller.game.current_bet:,.2f} GC", value=table)
        await interaction.edit_original_response(embed=controller.embed)
    
    await asyncio.sleep(0.5)

    table += f"\n\nDealer Total: {dealer_hand[0].value}\nPlayer Total: {get_hand_value(player_hand)}\n"
    if is_blackjack(controller.dealer_hand) and not is_blackjack(controller.player_hand):
        table = f"**Dealer Blackjack!**\n{controller.dealer_hand_str}\n{player_cards}\n"
        table += f"\nDealer Total: {get_hand_value(dealer_hand)}\nPlayer Total: {get_hand_value(player_hand)}\n"
        controller.game.dealer_blackjack_count += 1

        # Payout Here
        output_str: str = utilities.bet_payout(user_id, username, display_name, controller.game.current_bet, 0)
        if not output_str.startswith("Lucky", 1):
            controller.game.dealer_gc_win_blackjack -= controller.game.current_bet

        table += f"{output_str}\n\nNew Balance: {utilities.get_balance(user_id):,.2f} GC\n"
        toggle_start_buttons(controller, False)
        reset_hands(controller)
        await shuffle_cards(controller, interaction)
    elif is_blackjack(controller.player_hand) and not is_blackjack(controller.dealer_hand):
        table = f"**Blackjack!**\n{controller.dealer_hand_str}\n{player_cards}\n"
        table += f"\nDealer Total: {get_hand_value(dealer_hand)}\nPlayer Total: {get_hand_value(player_hand)}\n"
        controller.game.player_blackjack_count += 1
        controller.game.player_gc_win_blackjack += controller.game.current_bet * 1.5

        # Payout Here
        output_str: str = utilities.bet_payout(user_id, username, display_name, controller.game.current_bet, 2.5)
        table += f"{output_str}\n\nNew Balance: {utilities.get_balance(user_id):,.2f} GC\n"
        toggle_start_buttons(controller, False)
        reset_hands(controller)
        await shuffle_cards(controller, interaction)
    elif is_blackjack(controller.player_hand) and is_blackjack(controller.dealer_hand):
        await player_stands(controller, interaction, controller.game.current_bet, "Blackjack Push")
        return
    else:
        toggle_menu_buttons(controller, False)

    controller.embed.set_field_at(index=0, name=f"Current Game\nWager: {controller.game.current_bet:,.2f} GC", value=table)
    await interaction.edit_original_response(embed=controller.embed, view=controller)


async def reveal_dealer_cards(player_cards: str, player_total: int, dealer_hand, interaction: discord.Interaction, controller):
    toggle_menu_buttons(controller, True)
    # await interaction.response.defer()
    await interaction.edit_original_response(view=controller)
    dealer_cards: str = f"Dealer Hand: {controller.dealer_hand[0].name} {controller.dealer_hand[0].suit} "

    await interaction.edit_original_response(embed=controller.embed)
    dealer_total = dealer_hand[0].value
    for idx in range(1, len(dealer_hand)):
        dealer_cards += f"{dealer_hand[idx].name} {dealer_hand[idx].suit} "
        dealer_total += dealer_hand[idx].value
        table = f"{dealer_cards}\n{player_cards}"
        table += f"\n\nDealer Total: {dealer_total}\nPlayer Total: {player_total}\n"
        await asyncio.sleep(0.5)
        controller.embed.set_field_at(index=0, name=f"Current Game\nWager: {controller.game.current_bet:,.2f} GC", value=table)
        await interaction.edit_original_response(embed=controller.embed)
    
    controller.dealer_hand_str = dealer_cards

    # COME BACK HERE
    # 
    # I FORGOT WHY I HAD THIS BUT I'M LEAVING IT IN CASE I REMEMBER
    toggle_start_buttons(controller, False)
    await interaction.edit_original_response(embed=controller.embed, view=controller)
        


def toggle_menu_buttons(menu, switch: bool):
    menu_names: list[str] = ["start", "return", "min_bet", "max_bet", "saved_bet", "inc_fifty_per", "dec_fifty_per"]
    for item in menu.children:
        if isinstance(item, discord.ui.Button) and item.custom_id not in menu_names:
            item.disabled = switch


def toggle_start_buttons(menu, switch: bool):
    menu_names: list[str] = ["start", "return", "min_bet", "max_bet", "saved_bet", "inc_fifty_per", "dec_fifty_per"]
    for item in menu.children:
        if isinstance(item, discord.ui.Button) and (item.custom_id in menu_names):
            item.disabled = switch


def toggle_double_button(menu, switch: bool):
    for item in menu.children:
        if isinstance(item, discord.ui.Button) and item.custom_id == "dd":
            item.disabled = switch


def reset_hands(game):
    game.active_game = False
    game.player_hand.clear()
    game.player_hand_str = ""
    game.dealer_hand.clear()
    game.dealer_hand_str = ""


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


# Changes the deck size and adjusts the game description to show the new deck size.
# Automatically shuffles the new deck.
def deck_size_change(controller, size: int, interaction: discord.Interaction):
    user_id = interaction.user.id
    display_name: str = interaction.user.display_name
    controller.game_state.deck_size = size
    controller.game_state.deck = card_deck.generate_deck_bj(size)
    random.shuffle(controller.game_state.deck)

    user_balance: float = utilities.get_balance(user_id)
    embed = discord.Embed(color=discord.Color.dark_grey())

    game_description: str = f'Balance: {user_balance:,.2f} GC\nMaximum: {controller.game_state.maximum:,.2f} GC\n'
    game_description += f'Current Wager: {controller.game_state.current_bet:,.2f} GC\n'
    game_description += f"Deck Size: {size}\n"
    game_description += controller.game_description

    embed.add_field(name=f"{display_name}", value=game_description)
    return embed


async def shuffle_cards(controller, interaction: discord.Interaction):
    # Reshuffle the deck when the cards remaining are about 30% - 50%.
    if (len(controller.game.deck) / controller.game.initial_size) <= controller.game.reshuffle_point:
        controller.game.deck = card_deck.generate_deck_bj(controller.game.deck_size)
        random.shuffle(controller.game.deck)
        controller.game.reshuffle_point = random.uniform(0.3, 0.5)

        # controller.embed.add_field(name="Deck Reshuffled", value="")
        controller.embed.remove_field(index=2)
        controller.embed.insert_field_at(index=2, name="Deck Shuffled", value="")

        await interaction.edit_original_response(embed=controller.embed)
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {interaction.user.name} Deck shuffled.')



class DeckSizeMenu(discord.ui.View):
    def __init__(self, original_user: discord.User, game_menu, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.original_user = original_user
        self.view = game_menu
    

    @discord.ui.button(label="1", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def deck_size_one(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=deck_size_change(self.view, 1, interaction), view=BlackjackMenu(interaction.user, self.view.game_state))
    

    @discord.ui.button(label="2", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def deck_size_two(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=deck_size_change(self.view, 2, interaction), view=BlackjackMenu(interaction.user, self.view.game_state))
    

    @discord.ui.button(label="6", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def deck_size_six(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=deck_size_change(self.view, 6, interaction), view=BlackjackMenu(interaction.user, self.view.game_state))
    

    @discord.ui.button(label="8", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def deck_size_eight(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=deck_size_change(self.view, 8, interaction), view=BlackjackMenu(interaction.user, self.view.game_state))
    

    @discord.ui.button(label="Return To Game", style=discord.ButtonStyle.green)
    @original_user_only()
    async def return_to_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        display_name: str = interaction.user.display_name
        user_balance: float = utilities.get_balance(user_id)
        embed = discord.Embed(color=discord.Color.dark_grey())
        embed.set_author(name=self.view.game_name)

        game_description: str = f'Balance: {user_balance:,.2f} GC\nMaximum: {self.view.game_state.maximum:,.2f} GC\nMinimum: {200:,.2f} GC\n'
        game_description += f'Current Wager: {self.view.game_state.current_bet:,.2f} GC\n'
        game_description += f"Deck Size: {self.view.game_state.deck_size}\n"
        game_description += self.view.game_description

        embed.add_field(name=f"{display_name}", value=game_description)
        await interaction.response.edit_message(embed=embed, view=BlackjackMenu(interaction.user, self.view.game_state))


class GameState():
    def __init__(self, user_id: int):
        self.maximum: int = get_max(user_id)
        self.current_bet: int = 200
        self.minimum: int = 200
        self.saved_bet: int = 200
        self.dealer_count: int = 0
        self.dealer_blackjack_count: int = 0
        self.player_count: int = 0
        self.player_blackjack_count: int = 0
        self.player_gc_win: float = 0
        self.player_gc_win_blackjack: float = 0
        self.dealer_gc_win_blackjack: float = 0
        self.player_gc_lost: float = 0
        self.push_count: int = 0
        self.deck_size: int = 1
        self.deck = card_deck.generate_deck_bj(self.deck_size)
        self.initial_size = len(self.deck)
        # Ratio from 30% to 50%
        self.reshuffle_point = random.uniform(0.3, 0.5)
        random.shuffle(self.deck)


class BlackjackMenu(discord.ui.View):
    def __init__(self, original_user: discord.User, game_state, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.value = None
        self.original_user = original_user
        self.game_name = "Blackjack"
        self.game_state = game_state

        # self.game_description: str = f"Deck Size: {self.deck_size}\n"
        self.game_description: str = "\nYou play against a dealer both taking turns drawing cards.\n"
        self.game_description += "Whoever gets closer to a hand value of 21 without going over wins.\n"
        self.game_description += "Dealer stands on soft 17.\n"
        self.game_description += "\nFace cards (Jack, Queen, King) are worth 10 points. Ace can be worth 1 or 11 points.\n"
        self.game_description += "\nIf there's an active hand going on, you have 5 minutes to perform an action, otherwise you automatically lose.\n"
    

    @discord.ui.button(label="Play", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def play(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        username: str = interaction.user.name
        display_name: str = interaction.user.display_name
        user_balance: float = utilities.get_balance(user_id)
        
        embed = discord.Embed(color=discord.Color.dark_gray())
        embed.set_author(name=self.game_name)
        description: str = f'Balance: {user_balance:,.2f} GC\nMaximum: {self.game_state.maximum:,.2f} GC\nCurrent Wager: {self.game_state.current_bet:,.2f} GC\n'
        description += self.game_description

        embed.add_field(name=f"{display_name}", value=description)

        if self.game_state.current_bet <= user_balance:
            await interaction.response.edit_message(view=BlackJackGameMenu(interaction.user, self))
        else:
            embed.add_field(name="Game Result", value="Bet is higher than your balance.")
            embed.color = discord.Color.red()
            await interaction.response.edit_message(embed=embed)


    @discord.ui.button(label="Change Deck Size", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def change_deck_size(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=DeckSizeMenu(interaction.user, self))


    @discord.ui.button(label="Change Wager", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def change_wager(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=wager_menu.WagerMenu(interaction.user, self))
    

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.red)
    @original_user_only()
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(color=discord.Color.random())

        player_gc_lost = self.game_state.player_gc_lost
        player_gc_win = self.game_state.player_gc_win
        player_gc_win_blackjack = self.game_state.player_gc_win_blackjack
        dealer_gc_win_blackjack = self.game_state.dealer_gc_win_blackjack
        takeaway = player_gc_lost + player_gc_win + player_gc_win_blackjack + dealer_gc_win_blackjack

        output_text = "```"
        output_text += "{:20} | {:3,} ({:8,.0f} GC)\n".format("Dealer Wins", self.game_state.dealer_count, player_gc_lost)
        output_text += "{:20} | {:3,} ({:8,.0f} GC)\n".format("Dealer Blackjacks", self.game_state.dealer_blackjack_count, dealer_gc_win_blackjack)
        output_text += "{:20} | {:3,} ({:8,.0f} GC)\n".format("Player Wins", self.game_state.player_count, player_gc_win)
        output_text += "{:20} | {:3,} ({:8,.0f} GC)\n".format("Player Blackjacks", self.game_state.player_blackjack_count, player_gc_win_blackjack)
        output_text += "{:20} | {:3,}```".format("Pushes", self.game_state.push_count)
        output_text += f"Takeaway: {takeaway:,.2f} GC\n"

        output_text += f'Come again, {interaction.user.display_name}!'
        embed.add_field(name=f"{self.game_name} Session Results", value=output_text)

        # Disables all buttons.
        utilities.toggle_menu_buttons(self, True)
        await interaction.response.edit_message(embed=embed, view=self)
        self.value = False
        self.stop()


class BlackJackGameMenu(discord.ui.View):
    def __init__(self, original_user: discord.User, bj_view, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.value = None
        self.original_user = original_user
        self.game = bj_view.game_state
        self.bj_view = bj_view
        self.player_hand = [self.game.deck.pop(), self.game.deck.pop()]
        self.dealer_hand = [self.game.deck.pop(), self.game.deck.pop()]
        self.dealer_hand_str: str = f"Dealer Hand: {self.dealer_hand[0].name} {self.dealer_hand[0].suit} {self.dealer_hand[1].name} {self.dealer_hand[1].suit} "
        self.player_hand_str: str = f'Player Hand: {self.player_hand[0].name} {self.player_hand[0].suit} {self.player_hand[1].name} {self.player_hand[1].suit} '
        self.deck_shuffled: str = ""
        self.active_game = False
        self.embed = discord.Embed(color=discord.Color.dark_grey())
        self.embed.add_field(name=f"Current Game\nWager: {self.game.current_bet} GC", value="")


    @discord.ui.button(label="Hit", style=discord.ButtonStyle.grey, disabled=True, custom_id="hit")
    @original_user_only()
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        log_text: str = f"{interaction.user.name} hit "
        await draw_a_single_card(self, interaction, self.game.current_bet, log_text)

    

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.grey, disabled=True, custom_id="stand")
    @original_user_only()
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        log_text: str = f"{interaction.user.name} stood on "
        await player_stands(self, interaction, self.game.current_bet, log_text)
        await shuffle_cards(self, interaction)
            
    
    @discord.ui.button(label="Double Down", style=discord.ButtonStyle.grey, disabled=True, custom_id="dd")
    @original_user_only()
    async def double_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user_id: int = interaction.user.id
        username: str = interaction.user.name
        display_name: str = interaction.user.display_name
        user_balance: float = utilities.get_balance(user_id)

        if (self.game.current_bet * 2) > user_balance:
            embed = discord.Embed(title="Insufficient GC", description=f"You don't have enough GC.\nYour balance: {user_balance:,.2f} GC", color=discord.Color.red())
            await interaction.edit_original_response(embed=embed)
            await asyncio.sleep(3)
            await interaction.edit_original_response(embed=self.embed)
            return
        
        log_text: str = f"{interaction.user.name} double downed "
        player_value = await draw_a_single_card(self, interaction, self.game.current_bet*2, log_text)

        if player_value > 21:
            toggle_start_buttons(self, False)
            return
        
        await player_stands(self, interaction, self.game.current_bet*2)
        await shuffle_cards(self, interaction)

        toggle_start_buttons(self, False)
        
    

    @discord.ui.button(label="Start", style=discord.ButtonStyle.danger, custom_id="start")
    @original_user_only()
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        username: str = interaction.user.name
        user_balance: float = utilities.get_balance(user_id)

        if self.game.current_bet > user_balance:
            self.embed.set_field_at(index=0, name="Insufficient GC", value=f"You don't have enough GC.\nYour balance: {user_balance:,.2f} GC")
            await interaction.response.edit_message(embed=self.embed)
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {username} has insufficient GC to start bj.')
            return
        if not self.active_game:
            utilities.increment_stat("Blackjack rounds")
            log_text: str = f"{username} started a round "
            toggle_start_buttons(self, True)
            self.active_game = True
            embed = discord.Embed(color=discord.Color.dark_grey())
            embed.add_field(name=f"Current Game\nWager: {self.game.current_bet} GC", value="")
            self.embed = embed

            # Have it use a fortune as it affects lucky charm if the user has it.
            lucky_charm = utilities.get_upgrade_level("Lucky Charm", user_id)
            if lucky_charm:
                user_fortune = utilities.get_user_fortune(user_id)
                if user_fortune > 0:
                    utilities.set_user_fortune(user_id, user_fortune-1)
                elif user_fortune < 0:
                    utilities.set_user_fortune(user_id, user_fortune+1)

            if not len(self.player_hand) and not len(self.dealer_hand):
                self.player_hand = [self.game.deck.pop(), self.game.deck.pop()]
                self.dealer_hand = [self.game.deck.pop(), self.game.deck.pop()]
                self.dealer_hand_str: str = f"Dealer Hand: {self.dealer_hand[0].name} {self.dealer_hand[0].suit} {self.dealer_hand[1].name} {self.dealer_hand[1].suit} "
                self.player_hand_str: str = f"Player Hand: {self.player_hand[0].name} {self.player_hand[0].suit} {self.player_hand[1].name} {self.player_hand[1].suit} "

            log_text += f"{self.player_hand_str} "
            log_text += f"{self.dealer_hand_str} "
            await deal_new_hands(self.player_hand, self.dealer_hand, interaction, self)
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {log_text}')
    

    @discord.ui.button(label="Minimum Bet", style=discord.ButtonStyle.primary, custom_id="min_bet")
    @original_user_only()
    async def set_to_minimum(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        username: str = interaction.user.name
        user_balance: float = utilities.get_balance(user_id)

        result_str: str = f"Balance: {user_balance:,.2f} GC\nMaximum: {self.game.maximum:,.2f} GC\nMinimum: {200:,.2f} GC\n"
        if self.game.minimum > user_balance:
            result_str += f"Current Wager: {self.game.current_bet:,.2f} GC\n"
            result_str += "Wager would be over your balance.\n"
        else:
            if self.game.current_bet != self.game.maximum and self.game.current_bet != self.game.minimum:
                self.game.saved_bet = self.game.current_bet
            self.game.current_bet = self.game.minimum
            result_str += f"Current Wager: {self.game.current_bet:,.2f} GC\n"

        if len(self.embed.fields) == 1:
            self.embed.add_field(name="Wager Change", value=result_str)
        else:
            self.embed.set_field_at(index=1, name="Wager Change", value=result_str)
        await interaction.response.edit_message(embed=self.embed)


    @discord.ui.button(label="-50% Bet", style=discord.ButtonStyle.primary, custom_id="dec_fifty_per")
    @original_user_only()
    async def dec_fifty_per(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        username: str = interaction.user.name
        user_balance: float = utilities.get_balance(user_id)

        result_str: str = f"Balance: {user_balance:,.2f} GC\nMaximum: {self.game.maximum:,.2f} GC\nMinimum: {200:,.2f} GC\n"
        new_bet = int(self.game.current_bet * 0.5)
        if new_bet >= self.game.minimum:
            self.game.current_bet = new_bet
        
        result_str += f"Current Wager: {self.game.current_bet:,.2f} GC\n"

        if len(self.embed.fields) == 1:
            self.embed.add_field(name="Wager Change", value=result_str)
        else:
            self.embed.set_field_at(index=1, name="Wager Change", value=result_str)
        await interaction.response.edit_message(embed=self.embed)



    @discord.ui.button(label="Saved Bet", style=discord.ButtonStyle.primary, custom_id="saved_bet")
    @original_user_only()
    async def set_to_saved_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        username: str = interaction.user.name
        user_balance: float = utilities.get_balance(user_id)

        result_str: str = f"Balance: {user_balance:,.2f} GC\nMaximum: {self.game.maximum:,.2f} GC\nMinimum: {200:,.2f} GC\n"
        if self.game.saved_bet > user_balance:
            result_str += f"Current Wager: {self.game.current_bet:,.2f} GC\n"
            result_str += "Wager would be over your balance.\n"
        else:
            previous_saved = self.game.saved_bet
            if self.game.current_bet != self.game.maximum and self.game.current_bet != self.game.minimum and self.game.current_bet != self.game.saved_bet:
                self.game.saved_bet = self.game.current_bet
            self.game.current_bet = previous_saved
            result_str += f"Current Wager: {self.game.current_bet:,.2f} GC\n"

        if len(self.embed.fields) == 1:
            self.embed.add_field(name="Wager Change", value=result_str)
        else:
            self.embed.set_field_at(index=1, name="Wager Change", value=result_str)
        await interaction.response.edit_message(embed=self.embed)


    @discord.ui.button(label="+50% Bet", style=discord.ButtonStyle.primary, custom_id="inc_fifty_per")
    @original_user_only()
    async def inc_fifty_per(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        username: str = interaction.user.name
        user_balance: float = utilities.get_balance(user_id)

        result_str: str = f"Balance: {user_balance:,.2f} GC\nMaximum: {self.game.maximum:,.2f} GC\nMinimum: {200:,.2f} GC\n"
        new_bet = int(self.game.current_bet * 1.5)
        if new_bet > user_balance:
            result_str += f"Current Wager: {self.game.current_bet:,.2f} GC\n"
            result_str += "Wager would be over your balance.\n"
        elif new_bet <= self.game.maximum:
            self.game.current_bet = new_bet
            result_str += f"Current Wager: {self.game.current_bet:,.2f} GC\n"
        else:
            result_str += f"Current Wager: {self.game.current_bet:,.2f} GC\n"

        if len(self.embed.fields) == 1:
            self.embed.add_field(name="Wager Change", value=result_str)
        else:
            self.embed.set_field_at(index=1, name="Wager Change", value=result_str)
        await interaction.response.edit_message(embed=self.embed)


    @discord.ui.button(label="Maximum Bet", style=discord.ButtonStyle.primary, custom_id="max_bet")
    @original_user_only()
    async def set_to_maximum(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        username: str = interaction.user.name
        user_balance: float = utilities.get_balance(user_id)

        result_str: str = f"Balance: {user_balance:,.2f} GC\nMaximum: {self.game.maximum:,.2f} GC\nMinimum: {200:,.2f} GC\n"
        if self.game.maximum > user_balance:
            result_str += f"Current Wager: {self.game.current_bet:,.2f} GC\n"
            result_str += "Wager would be over your balance.\n"
        else:
            if self.game.current_bet != self.game.maximum and self.game.current_bet != self.game.minimum:
                self.game.saved_bet = self.game.current_bet
            self.game.current_bet = self.game.maximum
            result_str += f"Current Wager: {self.game.current_bet:,.2f} GC\n"

        if len(self.embed.fields) == 1:
            self.embed.add_field(name="Wager Change", value=result_str)
        else:
            self.embed.set_field_at(index=1, name="Wager Change", value=result_str)
        await interaction.response.edit_message(embed=self.embed)


    @discord.ui.button(label="Return To Menu", style=discord.ButtonStyle.green, custom_id="return")
    @original_user_only()
    async def return_to_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        display_name: str = interaction.user.display_name
        user_balance: float = utilities.get_balance(user_id)
        embed = discord.Embed(color=discord.Color.dark_grey())
        embed.set_author(name="Blackjack")

        game_description: str = f'Balance: {user_balance:,.2f} GC\nMaximum: {self.game.maximum:,.2f} GC\nMinimum: {200:,.2f} GC\n'
        game_description += f'Current Wager: {self.game.current_bet:,.2f} GC\n'
        game_description += f"Deck Size: {self.game.deck_size}\n"
        game_description += self.bj_view.game_description

        embed.add_field(name=f"{display_name}", value=game_description)
        if self.active_game:
            # Takes the user's GC from the current wager.
            early_leave_result = utilities.bet_payout(self.original_user.id,
                                                self.original_user,
                                                self.original_user.display_name,
                                                self.game.current_bet, 0)
            early_leave_result += f"\n\nNew Balance: {utilities.get_balance(user_id):,.2f} GC"
            embed.add_field(name=f"Game Result", value=early_leave_result)

        await interaction.response.edit_message(embed=embed, view=BlackjackMenu(interaction.user, self.game))


    async def on_timeout(self):
        if self.active_game:
            # Takes the user's GC from the current wager.
            timeout_result = utilities.bet_payout(self.original_user.id,
                                                self.original_user,
                                                self.original_user.display_name,
                                                self.game.current_bet, 0)
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {self.original_user.name} forfeited {self.game.current_bet}')


class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="blackjack", description="A game of Blackjack.")
    @app_commands.guild_only()
    async def blackjack(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        username: str = interaction.user.name
        display_name: str = interaction.user.display_name
        user_balance: float = utilities.get_balance(user_id)
        user_maximum: float = get_max(user_id)
        embed = discord.Embed(color=discord.Color.dark_gray())
        description: str = f"Balance: {user_balance:,.2f} GC\nMaximum: {user_maximum:,.2f} GC\nMinimum: {200:,.2f} GC\nCurrent Wager: {200:,.2f} GC\n"
        description += "Deck Size: 1\n"
        description += "\nYou play against a dealer both taking turns drawing cards.\n"
        description += "Whoever gets closer to a hand value of 21 without going over wins.\n"
        description += "Dealer stands on soft 17.\n"
        description += "\nFace cards (Jack, Queen, King) are worth 10 points. Ace can be worth 1 or 11 points.\n"
        description += "\nIf there's an active hand going on, you have 5 minutes to perform an action, otherwise you automatically lose.\n"
        embed.set_author(name=f'Blackjack')
        embed.add_field(name=f'{display_name}', value=description)

        view = BlackjackMenu(interaction.user, GameState(user_id))
        await interaction.response.send_message(embed=embed, view=view)
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{username},played blackjack,')


async def setup(bot):
    await bot.add_cog(Blackjack(bot))