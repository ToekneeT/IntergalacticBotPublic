import discord, logging, functools, datetime, os, re
from discord.ext import commands
from discord import app_commands
from helper import utilities

logger = logging.getLogger()
logging.basicConfig(filename="stats.log", level=logging.INFO)

# TABLE pet
#                      discord_id INTEGER FOREIGN KEY,
#                      pet_name TEXT,
#                      count INTEGER DEFAULT 0,
#                      cost NUMERIC DEFAULT 0,
# Current Pet discord_id = 0


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


class PetMenu(discord.ui.View):
    def __init__(self, original_user: discord.User, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.value = None
        self.original_user = original_user
        self.current_pet: str = utilities.get_current_pet()[0]
        self.pet_price: float = utilities.get_current_pet()[1]
    

    @discord.ui.button(label="Buy", style=discord.ButtonStyle.green)
    @original_user_only()
    async def buy_pet(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        username = interaction.user.name
        balance = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.dark_gray())
        description: str = f"Balance: {balance:,.2f} GC\n"
        description += f"Current Pet: **{self.current_pet}**\n"
        description += f'Pet Price: **{self.pet_price:,} GC**'
        embed.set_author(name=f'Pets')
        embed.add_field(name=f'{interaction.user.display_name}', value=description)

        if balance < self.pet_price:
            embed.color = discord.Color.red()
            output_text: str = "You don't have enough GC to buy this pet."
            embed.add_field(name="Insufficient Funds", value=output_text)
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {interaction.user} could not afford {self.current_pet}')
            await interaction.response.edit_message(embed=embed)
            return
        
        if self.pet_price == 0:
            embed.color = discord.Color.red()
            output_text: str = "You can't buy this."
            embed.add_field(name="Unpurchasable", value=output_text)
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {interaction.user} tried to buy {self.current_pet}')
            await interaction.response.edit_message(embed=embed)
            return

        utilities.update_balance(user_id, -self.pet_price)
        utilities.add_pet_to_user(user_id, self.current_pet, self.pet_price)
        user_balance: float = utilities.get_balance(user_id)
        utilities.add_transaction_to_history(user_id, username, "pet", -self.pet_price, user_balance)
        utilities.update_user_networth(user_id, self.pet_price)
        embed.color = discord.Color.green()
        output_text: str = f"You bought {self.current_pet} for {self.pet_price:,} GC!\n"
        output_text += f"Remaining Balance: {utilities.get_balance(user_id):,.2f} GC"
        embed.add_field(name="New Pet Acquired!", value=output_text)
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {interaction.user} bought {self.current_pet} for {self.pet_price}')

        await interaction.response.edit_message(embed=embed)
    

    @discord.ui.button(label="Current Pet Info", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def current_pet(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        balance = utilities.get_balance(user_id)

        embed = discord.Embed(color=discord.Color.dark_gray())
        description: str = f"Balance: {balance:,.2f} GC\n"
        description += f"Current Pet: **{self.current_pet}**\n"
        description += f'Pet Price: **{self.pet_price:,} GC**\n\n'
        user_pets = utilities.get_user_pets(user_id)
        if self.current_pet not in user_pets:
            description += "You don't have this pet.\n"
        else:
            pet_amount: int = user_pets[self.current_pet][0]
            if pet_amount == 1:
                description += f"You have 1 {self.current_pet}"
            else:
                description += f"You have {pet_amount} {self.current_pet}s"
        embed.set_author(name=f'Pets')
        embed.add_field(name=f'{interaction.user.display_name}', value=description)
        
        await interaction.response.edit_message(embed=embed)
    

    @discord.ui.button(label="My Pets", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def check_pets(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_pets: dict = utilities.get_user_pets(interaction.user.id)
        username = interaction.user.display_name
        user_id = interaction.user.id

        if not len(user_pets):
            output_string: str = f"{username} has no pets."
        else:
            output_string: str = f"```"
            output_string = output_string + '{:22} | {:2}\n'.format("Pet", "Amount")
            output_string = output_string + f'{"-"*40}\n'
            for pet_name in user_pets:
                output_string = output_string + '{:22} | {:2,.0f}\n'.format(pet_name, user_pets[pet_name][0])
            output_string += '```'
        
        if len(output_string) >= 1024:
            output_string = "You have too many pets! Try the /mypets command instead!"

        embed = discord.Embed(color=discord.Color.dark_gray())
        embed.add_field(name=f"{username}'s Pets", value=output_string)
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {interaction.user} checked their pets')

        await interaction.response.edit_message(embed=embed)
    

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.red)
    @original_user_only()
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disables all buttons.
        utilities.toggle_menu_buttons(self, True)
        await interaction.response.edit_message(view=self)
        self.value = False
        self.stop()


class Pet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="pets", description="Pet home portal.")
    @app_commands.guild_only()
    async def pets(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_balance: float = utilities.get_balance(user_id)
        embed = discord.Embed(color=discord.Color.dark_gray())
        description: str = f"Balance: {user_balance:,.2f} GC\n"
        current_pet_info = utilities.get_current_pet()
        user_pets = utilities.get_user_pets(user_id)
        description += f"Current Pet: **{current_pet_info[0]}**\n"
        description += f'Pet Price: **{current_pet_info[1]:,} GC**\n\n'
        if current_pet_info[0] not in user_pets:
            description += "You don't have this pet.\n"
        else:
            pet_amount: int = user_pets[current_pet_info[0]][0]
            if pet_amount == 1:
                description += f"You have 1 {current_pet_info[0]}"
            else:
                description += f"You have {pet_amount} {current_pet_info[0]}s"
        embed.set_author(name=f'Pets')
        embed.add_field(name=f'{interaction.user.display_name}', value=description)

        view = PetMenu(interaction.user)
        await interaction.response.send_message(embed=embed, view=view)
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user},opened the pet menu,')


    @app_commands.command(name="mypets", description="List your pets.")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 1800, key=lambda i: (i.guild.id, i.user.id))
    async def mypets_slash(self, interaction: discord.Interaction):
        name = interaction.user.display_name
        user_id = interaction.user.id

        user_pets: str = utilities.get_user_pets(user_id)
        if not len(user_pets):
            output_string: str = f"{name} has no pets."
        else:
            output_string: str = f"{name}'s Pets\n"
            output_string = output_string + '{:25} | {:2}\n'.format("```Pet", "Amount (Price Per Pet)")
            output_string = output_string + f'{"-"*40}\n'
            for pet_name in user_pets:
                output_string = output_string + '{:22} | {:2,.0f} ({:11,} GC)\n'.format(pet_name, user_pets[pet_name][0], user_pets[pet_name][1])
            output_string += '```'
        
        if len(output_string) <= 2000:
            await interaction.response.send_message(f'{output_string}')
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {interaction.user.name} checked their pets')
            return
        else:
            filename: str = f"{user_id}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                cleaned_output: str = re.sub(r'`', '', output_string)
                f.write(cleaned_output)
            
            await interaction.response.send_message("You have a lot of pets!", file=discord.File(filename))
            os.remove(filename)



    @app_commands.command(name="givepet", description="Give a pet you own to another user.")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 3, key=lambda i: (i.guild.id, i.user.id))
    async def givepet_slash(self, interaction: discord.Interaction, member: discord.Member, pet_name: str):
        name = interaction.user.display_name
        user_id = interaction.user.id

        pet_name = pet_name.title()
        if user_id == member.id:
            return
        if pet_name in ["Golden Dragon", "Sly Tanuki", "Caged Iguana", "Chance Chimera", "Iridescent Mallard"]:
            await interaction.response.send_message(f"You cannot give away the {pet_name}!")
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {interaction.user.name} tried to give away the {pet_name} to {member.name}')
            return
        
        user_pets = utilities.get_user_pets(user_id)
        try:
            pet_cost = user_pets[pet_name][1]
        except:
            await interaction.response.send_message(f"You don't own that pet or it doesn't exist.")
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {interaction.user.name} does not have {pet_name}')
            return
        
        is_remove_pet = utilities.remove_pet_from_user(user_id, pet_name, pet_cost)

        if is_remove_pet:
            utilities.add_pet_to_user(member.id, pet_name, pet_cost)
        else:
            await interaction.response.send_message(f"You don't own that pet or it doesn't exist.")
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {interaction.user.name} failed to give {pet_name} to {member.name}')
            return
        
        await interaction.response.send_message(f'{name} gave {pet_name} to <@{member.id}>.')
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {interaction.user.name} gave {pet_name} to {member.name}')
    

    @commands.command(name="pet")
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def pet(self, ctx: commands.Context):
        current_pet_info: str = utilities.get_current_pet()
        await ctx.send(f'Current Pet: {current_pet_info[0]}\nPrice: {current_pet_info[1]:,} GC')
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {ctx.author} checked the current pet')
    

    # @commands.command(name="mypets")
    # @commands.cooldown(1, 60, commands.BucketType.user)
    # async def mypets(self, ctx: commands.Context):
    #     user_pets: str = utilities.get_user_pets(ctx.author.id)
    #     if not len(user_pets):
    #         output_string: str = f"{ctx.author.display_name} has no pets."
    #     else:
    #         output_string: str = f"{ctx.author.display_name}'s Pets\n"
    #         output_string = output_string + '{:25} | {:2}\n'.format("```Pet", "Amount")
    #         output_string = output_string + f'{"-"*40}\n'
    #         for pet_name in user_pets:
    #             output_string = output_string + '{:22} | {:2,.0f}\n'.format(pet_name, user_pets[pet_name][0])
    #         output_string += '```'

    #     await ctx.send(f'{output_string}')
    #     logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {ctx.author} checked their pets')
    

    # @commands.command(name="givepet")
    # @commands.cooldown(1, 3, commands.BucketType.user)
    # async def givepet(self, ctx: commands.Context, member: discord.Member, *, pet_name: str):
    #     user_id = ctx.author.id
    #     pet_name = pet_name.title()
    #     if user_id == member.id:
    #         return
    #     if pet_name in ["Golden Dragon", "Sly Tanuki", "Caged Iguana"]:
    #         await ctx.send(f"You cannot give away the {pet_name}!")
    #         logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {ctx.author} tried to give away the Golden Dragon to {member.name}')
    #         return
        
    #     user_pets = utilities.get_user_pets(user_id)
    #     try:
    #         pet_cost = user_pets[pet_name][1]
    #     except:
    #         logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {ctx.author} does not have {pet_name}')
    #         return
        
    #     is_remove_pet = utilities.remove_pet_from_user(user_id, pet_name, pet_cost)

    #     if is_remove_pet:
    #         utilities.add_pet_to_user(member.id, pet_name, pet_cost)
    #     else:
    #         await ctx.send(f"You don't own that pet or it doesn't exist.")
    #         logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {ctx.author} failed to give {pet_name} to {member.name}')
    #         return
        
    #     await ctx.send(f'{ctx.author.display_name} gave {pet_name} to {member.display_name}.')
    #     logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} {ctx.author} gave {pet_name} to {member.name}')


async def setup(bot):
    await bot.add_cog(Pet(bot))