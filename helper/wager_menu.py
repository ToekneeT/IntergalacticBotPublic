import discord, logging, functools
# from discord.ext import commands
# from discord import app_commands
from helper import utilities


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


# Increases the current bet by the amount passed.
# Prevents going under the minimum and max.
# Returns a string of the results.
def increase_bet(balance: float, controller, inc_amount: float) -> str:
    result_str: str = f"Balance: {balance:,.2f} GC\nMaximum: {controller.game_state.maximum:,.2f} GC\n"

    if controller.game_state.current_bet + inc_amount > balance and balance < controller.game_state.maximum:
        controller.game_state.current_bet = balance
        result_str += f"Current Wager: {controller.game_state.current_bet:,.2f} GC\n"
        # result_str += "Wager would be over your balance.\n"
        return result_str

    elif controller.game_state.current_bet + inc_amount <= controller.game_state.maximum:
        controller.game_state.current_bet += inc_amount
        result_str += f'Current Wager: {controller.game_state.current_bet:,.2f} GC\n'
        return result_str
    
    else:
        controller.game_state.current_bet = controller.game_state.maximum
        result_str += f'Current Wager: {controller.game_state.current_bet:,.2f} GC\n'
        # result_str += "Wager would be over your maximum.\n"
        return result_str


# Decreases the current bet by the amount passed.
# Prevents going under the minimum and max.
# Returns a string of the results.
def decrease_bet(balance: float, controller, dec_amount: float) -> str:
    result_str: str = f"Balance: {balance:,.2f} GC\nMaximum: {controller.game_state.maximum:,.2f} GC\n"

    if controller.game_state.current_bet - dec_amount >= controller.game_state.minimum:
        controller.game_state.current_bet -= dec_amount
        result_str += f'Current Wager: {controller.game_state.current_bet:,.2f} GC\n'
        return result_str
        
    else:
        controller.game_state.current_bet = controller.game_state.minimum
        result_str += f"Current Wager: {controller.game_state.current_bet:,.2f} GC\n"
        # result_str += "Wager would be under the minimum."
        return result_str


class WagerMenu(discord.ui.View):
    # add game state to this. make the maximum stuff affect the game_state instead of the view.
    def __init__(self, original_user: discord.User, view, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.value = None
        self.original_user = original_user
        self.original_view = view
        self.game_state = view.game_state
    

    @discord.ui.button(label="Increase 100", style=discord.ButtonStyle.primary)
    @original_user_only()
    async def increase_bet_one_hundred(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name=self.original_view.game_name)
        description: str = increase_bet(user_balance, self, 100)

        embed.add_field(name=f'{interaction.user.display_name}', value=description)
        await interaction.response.edit_message(embed=embed)


    @discord.ui.button(label="Increase 500", style=discord.ButtonStyle.primary)
    @original_user_only()
    async def increase_bet_five_hundred(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name=self.original_view.game_name)
        description: str = increase_bet(user_balance, self, 500)

        embed.add_field(name=f'{interaction.user.display_name}', value=description)
        await interaction.response.edit_message(embed=embed)


    @discord.ui.button(label="Increase 1,000", style=discord.ButtonStyle.primary)
    @original_user_only()
    async def increase_bet_one_thousand(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name=self.original_view.game_name)
        description: str = increase_bet(user_balance, self, 1_000)

        embed.add_field(name=f"{interaction.user.display_name}", value=description)
        await interaction.response.edit_message(embed=embed)
    

    @discord.ui.button(label="Increase 5,000", style=discord.ButtonStyle.primary)
    @original_user_only()
    async def increase_bet_five_thousand(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name=self.original_view.game_name)
        description: str = increase_bet(user_balance, self, 5_000)

        embed.add_field(name=f"{interaction.user.display_name}", value=description)
        await interaction.response.edit_message(embed=embed)
    

    @discord.ui.button(label="Increase 10,000", style=discord.ButtonStyle.primary)
    @original_user_only()
    async def increase_bet_ten_thousand(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name=self.original_view.game_name)
        description: str = increase_bet(user_balance, self, 10_000)

        embed.add_field(name=f"{interaction.user.display_name}", value=description)
        await interaction.response.edit_message(embed=embed)
    

    @discord.ui.button(label="Max Bet", style=discord.ButtonStyle.primary)
    @original_user_only()
    async def max_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name=self.original_view.game_name)
        description: str = f'Balance: {user_balance:,.2f} GC\nMaximum: {self.game_state.maximum:,.2f} GC\n'

        if self.game_state.maximum < user_balance:
            self.game_state.current_bet = self.game_state.maximum
        elif user_balance < self.game_state.maximum and user_balance > self.game_state.minimum:
            self.game_state.current_bet = user_balance
        description += f'Current Wager: {self.game_state.current_bet:,.2f} GC\n'

        embed.add_field(name=f"{interaction.user.display_name}", value=description)
        await interaction.response.edit_message(embed=embed)
    

    @discord.ui.button(label="Decrease 100", style=discord.ButtonStyle.secondary)
    @original_user_only()
    async def decrease_bet_one_hundred(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=self.original_view.game_name)
        description: str = decrease_bet(user_balance, self, 100)

        embed.add_field(name=f"{interaction.user.display_name}", value=description)
        await interaction.response.edit_message(embed=embed)
    

    @discord.ui.button(label="Decrease 500", style=discord.ButtonStyle.secondary)
    @original_user_only()
    async def decrease_bet_five_hundred(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=self.original_view.game_name)
        description: str = decrease_bet(user_balance, self, 500)

        embed.add_field(name=f"{interaction.user.display_name}", value=description)
        await interaction.response.edit_message(embed=embed)


    @discord.ui.button(label="Decrease 1,000", style=discord.ButtonStyle.secondary)
    @original_user_only()
    async def decrease_bet_one_thousand(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=self.original_view.game_name)
        description: str = decrease_bet(user_balance, self, 1_000)

        embed.add_field(name=f"{interaction.user.display_name}", value=description)
        await interaction.response.edit_message(embed=embed)


    @discord.ui.button(label="Decrease 5,000", style=discord.ButtonStyle.secondary)
    @original_user_only()
    async def decrease_bet_five_thousand(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=self.original_view.game_name)
        description: str = decrease_bet(user_balance, self, 5_000)

        embed.add_field(name=f"{interaction.user.display_name}", value=description)
        await interaction.response.edit_message(embed=embed)


    @discord.ui.button(label="Decrease 10,000", style=discord.ButtonStyle.secondary)
    @original_user_only()
    async def decrease_bet_ten_thousand(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=self.original_view.game_name)
        description: str = decrease_bet(user_balance, self, 10_000)

        embed.add_field(name=f"{interaction.user.display_name}", value=description)
        await interaction.response.edit_message(embed=embed)


    @discord.ui.button(label="Min Bet", style=discord.ButtonStyle.secondary)
    @original_user_only()
    async def min_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=self.original_view.game_name)
        description: str = f'Balance: {user_balance:,.2f} GC\nMaximum: {self.game_state.maximum:,.2f} GC\nMinimum: {self.game_state.minimum:,.2f} GC\n'

        self.game_state.current_bet = self.game_state.minimum
        description += f'Current Wager: {self.game_state.current_bet:,.2f} GC\n'

        embed.add_field(name=f"{interaction.user.display_name}", value=description)
        await interaction.response.edit_message(embed=embed)
    

    @discord.ui.button(label="Return To Game", style=discord.ButtonStyle.green)
    @original_user_only()
    async def return_to_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id: int = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name=self.original_view.game_name)

        game_description: str = f'Balance: {user_balance:,.2f} GC\nMaximum: {self.game_state.maximum:,.2f} GC\nMinimum: {self.game_state.minimum:,.2f} GC\n'
        game_description += f'Current Wager: {self.game_state.current_bet:,.2f} GC\n'
        game_description += self.original_view.game_description

        embed.add_field(name=f"{interaction.user.display_name}", value=game_description)
        await interaction.response.edit_message(embed=embed, view=self.original_view)