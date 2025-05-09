import discord, logging, datetime, functools
from discord.ext import commands
from discord import app_commands
from helper import utilities

logger = logging.getLogger()
logging.basicConfig(filename="stats.log", level=logging.INFO)


# SKILL KEY
#     Wager Maximum
#     Claim Multiplier
#     Bank Interest
#     Coinflip Consecutive Bonus
#     Lucky Charm
#


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


def get_skills(user_id: int) -> str:
    skills: list = utilities.get_user_upgrades(user_id)
    if skills:
        all_skills: str = "{:33} | {:5}\n".format("```Skill", "Level")
        all_skills += f"{"-"*40}\n"
        for skill_name, skill_level in skills:
            all_skills += "{:30} | {:5}\n".format(skill_name, skill_level)
        
        all_skills += "```"
    else:
        all_skills = "```Do Something First To Update Your Skills```"
    return all_skills


class SkillsMenu(discord.ui.View):
    def __init__(self, original_user: discord.User, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.original_user = original_user
        self.value = None
     

    @discord.ui.button(label="Upgrade Skills", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def upgrade_skills(self, interaction: discord.Integration, button: discord.ui.Button):
        await interaction.response.edit_message(content="", view=UpgradeSkillsMenu(interaction.user))


    @discord.ui.button(label="Quit", style=discord.ButtonStyle.red)
    @original_user_only()
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disables buttons
        utilities.toggle_menu_buttons(self, True)
        await interaction.response.edit_message(view=self)
        self.value = False
        self.stop()


def get_wager_max_cost(skill_level: int, cost: float) -> float:
    for level in range(1, skill_level + 1):
        if level >= 5:
            cost = (cost * 2 * (level - 1)) * .3
        else:
            cost *= 2
    return cost


def get_skill_cost_multiply_per_level(skill_level: int, cost: float) -> float:
    return cost * (skill_level + 1)


def get_skill_cost_double_per_level(skill_level: int, cost: float) -> float:
    for level in range(1, skill_level + 1):
        cost *= 2
    return cost


def get_consec_skill_cost(skill_level: int, cost: float) -> float:
    if skill_level >= 5:
        cost = 100_000
        for level in range(5, skill_level + 1):
            cost = (cost * 2 * (level - 1)) * .2
    else:
        cost = cost * (skill_level + 1)
    return cost


def get_upgrade_skill_text(skill_name: str, skill_level: int, cost: float, additional_text: str = "") -> str:
    output_text: str = ''
    output_text += f'{skill_name} Current Level: {skill_level}\n'
    output_text += f'Cost to upgrade to level {skill_level+1}: **{cost:,.2f} GC**\n'
    output_text += "\n" + additional_text
    return output_text


class UpgradeSkillsMenu(discord.ui.View):
    def __init__(self, original_user: discord.User, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.value = None
        self.original_user = original_user


    @discord.ui.button(label="Wager Maximum", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def upgrade_coinflip_max(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name=f'Wager Maximum')
        user_id: int = interaction.user.id
        skill_level: int = utilities.get_upgrade_level("Wager Maximum", user_id)
        current_max = 2_000 * (2 ** (skill_level)) if skill_level > 0 else 2_000
        bj_max = (2_000 * (2 ** (skill_level))) * .25 if skill_level > 0 else 600
        luck_max = 20_000 * (2 ** (skill_level)) if skill_level > 0 else 20_000
        upgrade_cost = get_wager_max_cost(skill_level, 10_000)
        additional_text: str = f"Each upgrade increases your wager maximum for various games. \
Coinflip and Card War share the same max, doubling each time.\nCurrent Coinflip / Card War maximum = {current_max:,.0f} GC \n\
Current Blackjack maximum = {bj_max:,.0f} GC\nCurrent Luck maximum: {luck_max:,.0f} GC\n\nMax level = \u221E"
        output_text: str = get_upgrade_skill_text("Wager Maximum", skill_level, upgrade_cost, additional_text)
        user_balance: float = utilities.get_balance(user_id)

        embed.add_field(name=f'Balance: {user_balance:,.2f} GC', value=output_text)
        await interaction.response.edit_message(content="Wager Maximum", embed=embed, view=UpgradeChoice(interaction.user))
    

    @discord.ui.button(label="Coinflip Consecutive Bonus", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def upgrade_coinflip_multiplier(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name=f'Coinflip Consecutive Bonus')
        user_id = interaction.user.id
        skill_level = utilities.get_upgrade_level("Coinflip Consecutive Bonus", user_id)
        if skill_level == 10:
            embed.add_field(name=f"Max Level.", value="You've hit the max level for Coinflip Consecutive Bonus.")
            await interaction.response.edit_message(embed=embed, view=SkillsMenu(interaction.user))
            return
        upgrade_cost = get_consec_skill_cost(skill_level, 20_000)
        additional_text: str = "Each upgrade increases the pay amount of Coinflip if you land a consecutive win by 1%. \
Half efficiency in Card War. \
\nFor example, if you win one time, you get paid 2x, if you win again, you get paid 2.01x. If you win \
for a third time, the payout is 2.02x.\nNow, if the skill level is 2, the payout should be 2%, so 2.02x, 2.04x, etc.\n\n\
Max level = 10"
        output_text = get_upgrade_skill_text("Coinflip Consecutive Bonus", skill_level, upgrade_cost, additional_text)
        user_balance = utilities.get_balance(user_id)

        embed.add_field(name=f'Balance: {user_balance:,.2f} GC.', value=output_text)
        await interaction.response.edit_message(content="Coinflip Consecutive Bonus", embed=embed, view=UpgradeChoice(interaction.user))


    @discord.ui.button(label="Claim Multiplier", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def upgrade_claim_multiplier(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name=f'Claim Multiplier')
        user_id = interaction.user.id
        skill_level = utilities.get_upgrade_level("Claim Multiplier", user_id)
        if skill_level == 10:
            embed.add_field(name=f"Max Level.", value="You've hit the max level for Claim Multiplier.")
            await interaction.response.edit_message(embed=embed, view=SkillsMenu(interaction.user))
            return
        upgrade_cost = get_skill_cost_multiply_per_level(skill_level, 30_000)
        additional_text: str = "Each upgrade level increases the amount you receive from claiming the react reward by 0.5x. \
Reward = Amount * ((Skill Level * 0.5) + 1).\n\nMax level = 10"
        output_text = get_upgrade_skill_text("Claim Multiplier", skill_level, upgrade_cost, additional_text)
        user_balance = utilities.get_balance(user_id)

        embed.add_field(name=f'Balance: {user_balance:,.2f} GC', value=output_text)
        await interaction.response.edit_message(content="Claim Multiplier", embed=embed, view=UpgradeChoice(interaction.user))

    
    @discord.ui.button(label="Bank Interest", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def upgrade_bank_interest(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name=f'Bank Interest')
        user_id = interaction.user.id
        skill_level = utilities.get_upgrade_level("Bank Interest", user_id)
        if skill_level == 5:
            embed.add_field(name=f"Max Level.", value="You've hit max level for Bank Interest.")
            await interaction.response.edit_message(embed=embed, view=SkillsMenu(interaction.user))
            return
        upgrade_cost = (skill_level + 1) * 5_000_000
        additional_text: str = "Slowly gain interest on your bank, paid out every hour. \
Each upgrade increases your weekly interest by .5%, except level 4 -> 5 goes from 2% to 3%.\nLevel 1 = .5%\n\
Level 2 = 1%\nLevel 3 = 1.5%\nLevel 4 = 2%\nLevel 5 = 3%\n\nMax level = 5"
        output_text = get_upgrade_skill_text("Bank Interest", skill_level, upgrade_cost, additional_text)
        user_balance = utilities.get_balance(user_id)

        embed.add_field(name=f'Balance: {user_balance:,.2f} GC', value=output_text)
        await interaction.response.edit_message(content="Bank Interest", embed=embed, view=UpgradeChoice(interaction.user))
    

    @discord.ui.button(label="Lucky Charm", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def upgrade_lucky_charm(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name=f'Lucky Charm')
        user_id: int = interaction.user.id
        skill_level: int = utilities.get_upgrade_level("Lucky Charm", user_id)
        if skill_level == 5:
            embed.add_field(name=f"Max Level.", value="You've hit max level for Lucky Charm.")
            await interaction.response.edit_message(embed=embed, view=SkillsMenu(interaction.user))
            return
        upgrade_cost: float = get_skill_cost_double_per_level(skill_level, 500_000)
        additional_text: str = f"Each level adds a .6% chance to preserve your wager when losing a bet. 3% chance to preserve at max.\n\nMax level = 5"
        output_text: str = get_upgrade_skill_text("Lucky Charm", skill_level, upgrade_cost, additional_text)
        user_balance: float = utilities.get_balance(user_id)

        embed.add_field(name=f'Balance: {user_balance:,.2f} GC', value=output_text)
        await interaction.response.edit_message(content="Lucky Charm", embed=embed, view=UpgradeChoice(interaction.user))
    

    @discord.ui.button(label="Streak Saver", style=discord.ButtonStyle.grey)
    @original_user_only()
    async def upgrade_streak_saver(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name=f'Streak Saver')
        user_id: int = interaction.user.id
        skill_level: int = utilities.get_upgrade_level("Streak Saver", user_id)
        if skill_level == 5:
            embed.add_field(name=f"Max Level.", value="You've hit max level for Streak Saver.")
            await interaction.response.edit_message(embed=embed, view=SkillsMenu(interaction.user))
            return
        upgrade_cost: float = get_skill_cost_double_per_level(skill_level, 300_000)
        additional_text: str = f"Each level adds a 1% chance to preserve your streak when losing in Coinflip or Card War.\n\nMax level = 5"
        output_text: str = get_upgrade_skill_text("Streak Saver", skill_level, upgrade_cost, additional_text)
        user_balance: float = utilities.get_balance(user_id)

        embed.add_field(name=f'Balance: {user_balance:,.2f} GC', value=output_text)
        await interaction.response.edit_message(content="Streak Saver", embed=embed, view=UpgradeChoice(interaction.user))


    @discord.ui.button(label="Return To Main Menu", style=discord.ButtonStyle.blurple)
    @original_user_only()
    async def return_to_main_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name=f'List of your skills.')
        user_skills = get_skills(interaction.user.id)
        user_balance = utilities.get_balance(interaction.user.id)

        embed.add_field(name=f"Balance: {user_balance:,.2f} GC", value=user_skills)
        await interaction.response.edit_message(embed=embed, view=SkillsMenu(interaction.user))


    @discord.ui.button(label="Quit", style=discord.ButtonStyle.red)
    @original_user_only()
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disables buttons
        utilities.toggle_menu_buttons(self, True)
        await interaction.response.edit_message(view=self)
        self.value = False
        self.stop()


def attempt_upgrade(skill_name: str, user_id: int, username: str, balance: float, cost: float):
    if balance >= cost:
        utilities.increment_upgrade(skill_name, user_id)
        utilities.update_balance(user_id, -cost)
        utilities.append_ledger(f'{username},{-cost},{utilities.get_balance(user_id)}')
        utilities.update_user_networth(user_id, cost)
        return "Skill Upgraded."
    else:
        return "Not enough GC."


class UpgradeChoice(discord.ui.View):
    def __init__(self, original_user: discord.User, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.value = None
        self.original_user = original_user
    

    @discord.ui.button(label="Upgrade", style=discord.ButtonStyle.green)
    @original_user_only()
    async def upgrade(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name=f'List of your skills.')
        user_id = interaction.user.id
        user_balance = utilities.get_balance(user_id)

        previous_message = interaction.message.content

        if previous_message == "Wager Maximum":
            skill_level = utilities.get_upgrade_level("Wager Maximum", user_id)
            upgrade_cost = get_wager_max_cost(skill_level, 10_000)
            
            content = attempt_upgrade("Wager Maximum", user_id, interaction.user.name, user_balance, upgrade_cost)
            user_skills = get_skills(user_id)
            embed.add_field(name=f"Balance: {utilities.get_balance(user_id):,.2f} GC", value=user_skills)
            await interaction.response.edit_message(content=content, embed=embed, view=UpgradeSkillsMenu(interaction.user))
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},upgraded {previous_message},{skill_level+1}')
            return

        elif previous_message == "Claim Multiplier" or previous_message == "Coinflip Consecutive Bonus":
            skill_level = utilities.get_upgrade_level(previous_message, user_id)
            if previous_message == "Claim Multiplier":
                upgrade_cost = get_skill_cost_multiply_per_level(skill_level, 30_000)
            else:
                upgrade_cost = get_consec_skill_cost(skill_level, 20_000)

            content = attempt_upgrade(previous_message, user_id, interaction.user.name, user_balance, upgrade_cost)
            user_skills = get_skills(user_id)
            embed.add_field(name=f"Balance: {utilities.get_balance(user_id):,.2f} GC", value=user_skills)
            await interaction.response.edit_message(content=content, embed=embed, view=UpgradeSkillsMenu(interaction.user))
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},upgraded {previous_message},{skill_level+1}')
            return

        elif previous_message == "Bank Interest":
            skill_level = utilities.get_upgrade_level(previous_message, user_id)
            upgrade_cost = get_skill_cost_multiply_per_level(skill_level, 5_000_000)

            content = attempt_upgrade("Bank Interest", user_id, interaction.user.name, user_balance, upgrade_cost)
            user_skills = get_skills(user_id)
            embed.add_field(name=f"Balance: {utilities.get_balance(user_id):,.2f} GC", value=user_skills)
            await interaction.response.edit_message(content=content, embed=embed, view=UpgradeSkillsMenu(interaction.user))
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},upgraded {previous_message},{skill_level+1}')
            return
        
        elif previous_message == "Lucky Charm":
            skill_level = utilities.get_upgrade_level(previous_message, user_id)
            upgrade_cost = get_skill_cost_double_per_level(skill_level, 500_000)

            content = attempt_upgrade(previous_message, user_id, interaction.user.name, user_balance, upgrade_cost)
            user_skills = get_skills(user_id)
            embed.add_field(name=f"Balance: {utilities.get_balance(user_id):,.2f} GC", value=user_skills)
            await interaction.response.edit_message(content=content, embed=embed, view=UpgradeSkillsMenu(interaction.user))
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},upgraded {previous_message},{skill_level+1}')
            return
        
        elif previous_message == "Streak Saver":
            skill_level = utilities.get_upgrade_level(previous_message, user_id)
            upgrade_cost = get_skill_cost_double_per_level(skill_level, 300_000)

            content = attempt_upgrade(previous_message, user_id, interaction.user.name, user_balance, upgrade_cost)
            user_skills = get_skills(user_id)
            embed.add_field(name=f"Balance: {utilities.get_balance(user_id):,.2f} GC", value=user_skills)
            await interaction.response.edit_message(content=content, embed=embed, view=UpgradeSkillsMenu(interaction.user))
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},upgraded {previous_message},{skill_level+1}')
            return
        
        else:
            user_skills = get_skills(user_id)
            embed.add_field(name=f"Balance: {user_balance:,.2f} GC", value=user_skills)
            await interaction.response.edit_message(content="Not enough GC.", embed=embed, view=UpgradeSkillsMenu(interaction.user))
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},too broke to upgrade,')
            return
    

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    @original_user_only()
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name=f'List of your skills.')
        user_skills = get_skills(interaction.user.id)
        user_balance = utilities.get_balance(interaction.user.id)

        embed.add_field(name=f"Balance: {user_balance:,.2f} GC", value=user_skills)
        await interaction.response.edit_message(content="No Upgrade.", embed=embed, view=UpgradeSkillsMenu(interaction.user))
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},chose not to level,')


class Upgrades(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    

    # ____________________ Owner Only On Commands ____________________


    @commands.command(name="setupgrade")
    @commands.is_owner()
    async def setupgrade(self, ctx: commands.Context, member: discord.Member, upgrade_name: str, level: int):
        utilities.set_upgrade(upgrade_name, member.id, level)
        await ctx.send(f'{upgrade_name} is now level {level} for {member.display_name}.')
        logger.info(
            f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{ctx.author},set {upgrade_name} of {member.name},{level}')


    # ____________________ End of Owner Only On Commands ____________________
    # ____________________ On Commands ____________________






    # ____________________ End of On Commands ____________________
    # ____________________ On Slash Commands ____________________


    @app_commands.command(name="skills", description="Check your skills.")
    @app_commands.guild_only()
    async def skills(self, interaction: discord.Interaction):
        view = SkillsMenu(interaction.user)
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name=f'List of your skills.')
        user_skills = get_skills(interaction.user.id)
        user_balance = utilities.get_balance(interaction.user.id)

        embed.add_field(name=f"Balance: {user_balance:,.2f} GC", value=user_skills)
        await interaction.response.send_message(embed=embed, view=view)
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{interaction.user.name},accessed skills,')

        


async def setup(bot):
    await bot.add_cog(Upgrades(bot))