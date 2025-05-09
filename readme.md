# General Information

Everyone starts with 10,000 Galactic Coins (GC).

There's a global leaderboard, will most likely use your Discord username.
Leaderboard updates every hour.

Any GC lost from a wager gets 5% of it added, capped at 5k per wager, to the Galactic Coin Vault.

The bot will periodically send out a message where if you react to it, you will receive x Galactic Coins. The message disappears after some time.

## Table of Contents
1. [Commands](#commands)
	1. [/bank](#bank)
	2. [/vault](#vault)
	3. [/give](#give-user-amount)
	4. [/gifted](#gifted)
	5. [/mypets](#mypets)
	6. [/givepet](#give-user-petname)
	7. [/networth](#networth)
	8. [/skills](#skills)
	9. [/coinflip](#coinflip)
	10. [/luck](#luck)
	11. [/luckiest](#luckiest)
	12. [/roll](#roll)
	13. [/ping](#ping)
	14. [/fortune](#fortune)
	15. [/cwar](#cwar)
	16. [/blackjack](#blackjack)
	17. [/pets](#pets)
	18. [/elusive_hunter](#elusive_hunter)
	19. [/slotto](#slotto)
	20. [/games](#games)
	21. [!bankfull](#bankfull)
	22. [!pet](#pet)
	23. [!blackjack](#blackjack-strategy)
2. [Skill Upgrades](#skill-upgrades)
	1. [Wager Maximum](#wager-maximum)
	2. [Coinflip Consecutive Bonus](#coinflip-consecutive-bonus)
	3. [Claim Multiplier](#claim-multiplier)
	4. [Bank Interest](#bank-interest)
	5. [Lucky Charm](#lucky-charm)
	6. [Streak Saver](#streak-saver)
3. [Payouts](#payout)

## Commands

### /bank
Replies with how many Galactic Coins you currently have.

### /vault
Replies with how much GC is in the vault currently.

### /give @user amount
Transfers GC from your account to the person you've mentioned.
Can only give 35% of your balance from an hour ago.
Meaning, if you had 100,000 GC an hour ago, regardless of how much you have now, you can only give up to 35,000 GC.

### /gifted
Tells you how much you've gifted in the last hour.

### /mypets
- Replies with your currently owned pets.

### /givepet @user petname
- Gives the user a pet that you own.
- /givepet @user Quasar Turtle
	- Pet name is not case sensitive.
	- Must spell the pet name correctly, including spaces.

### /networth
- Replies with your networth, as much as it can.
	- Combines spent GC on upgrades, pets, and your current bank.

### /skills
Replies with a menu where you can check your skills and upgrade or see information about a skill.
Check the [Skills section](#skills) for more information on skills.

### /coinflip
Does a coinflip, Heads 49% or Tails 51%.
Can place a wager using your GC, you win only if it lands on heads.
Default wager is 2,000, can be upgraded.
Shows how many times you've landed on heads or tails in a row.
Payout is 2x if placing a wager, can be upgraded.

### /luck
Does a consecutive coinflip where you have a 30% (green) chance to flip again or a 70% chance (red) to stop.
Replies with how many dots you got.
Provides the probability of getting the amount of dots you got.
Can place a wager using your GC. [Payouts](#payout) can be seen below.
If you place a wager and beat the [/luckiest](#/luckiest) roll, you win the contents of the vault. If no wager is placed, you still get the record, but you don't win the vault.
The minimum for this game is 200, has a starting maximum of 20,000 GC, can be upgraded.

### /luckiest
Replies with the first person to get the record /luck roll.

### /roll
By default, does a roll between 1 - 100.

Optional lower and upper bounds.

### /ping
Replies with the latency of the bot.

### /fortune
- Can spend GC to receive your fortune in the form of an [Omikuji.](https://blog.japanwondertravel.com/what-is-omikuji-29421)
    - Options of Cheap, Standard, and Quality.
		- Prices:
			Cheap = 500 GC, or 2% of your balance, whichever ends up being higher.
			Standard = 2,000 GC, or 5% of your balance, whichever ends up being higher.
			Quality = 10,000 GC, or 10% of your balance, whichever ends up being higher.
        - While not guaranteed, more likely to get a bad fortune out of Cheap, a good fortune out of Quality. No weight on Standard.
			- However, Cheap cannot get a Great Blessing and Quality cannot get a Great Bad Fortune.
				- It was unlikely before, but now guaranteed to not happen.
- Rankings in order from best to worst fortunes:
1. Great blessing
2. Middle blessing
3. Small blessing
4. Blessing
5. Future blessing
6. Bad fortune
7. Great bad fortune


- Do the fortunes actually do anything? Who knows?
- Has a 1 hour cooldown from the moment you used the command.
    - Either get a fortune, or wait an hour until you can do it again.

<sub>Spent GC does not get added to the vault.</sub>

### /cwar
- Minimums are 100 GC. Maximum is 25% of your Coinflip Max. Upgradable with Wager Maximum.
    - Increase / decrease by 100, 500, 1_000, 5_000, or 10_000 at a time.
    - Or go straight to max / min bet.
- Standard single deck of cards, shuffled every round.
- Dealer draws a card and the player draws a card, whoever has the higher value card wins the round.
    - Card values from highest to lowest: Ace > King > Queen > Jack
- Payout 2:1 upon winning.
    - Consecutive Coinflip Bonus skill also works in Card War, albeit at half efficiency.
- Payout for a tie if placed is 13:1.
    - A tie side bet takes 50% of your original wager.
    - Example, if original wager is 16,000 GC, tie would be an additional 8,000 GC.
    - A tie bet is active when the Tie button is green.
        - It stays active until you press it again to deactivate it.

### /blackjack
- Standard 3 to 2 Blackjack.
	- [Official Guide + Strategy.](https://www.officialgamerules.org/card-games/blackjack)
	- Only currently has hitting, stand, and doubling down.
		- The rest of the features will slowly roll out as they're done.
- Minimum of 200 GC to play.
- Maximum is 50% of your Coinflip Max.
	- If you're at level 0 for Wager Max, the Max for Blackjack will be 600
- Shoe is shuffled when there is between 30% - 50% of cards remaining.
	- It will let you know when the deck is reshuffled.
	- Changing your wager does not reshuffle the deck!
- Can change shoe size, options being 1, 2, 6, and 8.
	- Changing shoe size gives a new shuffled deck.
- If you use the Quit button, it'll tell you your session results, how many times player, dealer, etc won.
- **Don't get too comfortable with Double Down, it'll be locked to an upgrade later**

### /pets
- Can buy pets!
- Provides a one stop shop for Pets.
- Can see what the current pet on sale is, or check your currently owned pets.
- Current pet on sale changes every new hour.
	- Price of pet changes depending on how rare that particular pet is.
- Doesn't do anything other than for collection, or bragging rights.
- There are some secret pets as well!
- There is a history channel for all pets that have been in rotation.

### /elusive_hunter
- Assigns you the Elusive Hunter role.
- Pings you when a pet with the Elusive modifier shows up.

## /slotto
- A weird mixed game of slots and lottery?
- Minimum of 50 GC to play.
- Same Maximum as Coinflip.
Choose up to 3 numbers between 1-99 or have them randomly assigned to you. Winning numbers will be picked afterwards,
your numbers and the winning numbers must be matching in the same spot in order to receive a payout.

## /games
- Displays currently available games as well as a link to this readme.
- [/blackjack](#blackjack)
- [/coinflip](#coinflip)
- [/cwar](#cwar)
- [/luck](#luck)
- [/roll](#roll)
- [/slotto](#slotto)

### !bankfull
- When doing !bank, it'll round to the nearest tenth. Often, you can have a .001, which would give you a value of .01
- Using this will give you your full amount in case you want to use it all, or in case you're trying to do something and it says you don't have enough.

### !pet
- Replies with the current pet on sale and its price.

### !blackjack strategy
- Replies with Wizard of Odd's blackjack strategy guide.

## Skill Upgrades

### Wager Maximum
- Can be upgraded as many times as you can afford.
- Initial cost: 10,000 GC, each upgrade doubles the cost of the next.
	- First upgrade cost 10,000, level 2 cost 20,000, level 3 cost 40,000.
	- After level 5, the price increases with a new formula.
    	- C(n) = (2 * C(n-1) * (n-1)) * .3
			- `C(n)` represents the cost at level `n`.
			- `C` represents previous cost.
		```
		C(4) = 160,000

		C(5) = (2 * C(5-1)  * (5-1)) * .3
		C(5) = (2 * 160,000 * 4)     * .3
		C(5) = (320,000     * 4)     * .3
		C(5) = (1,280,000)           * .3
		C(5) = 384,000

		C(6) = (2 * C(6-1)  * (6-1)) * .3
		C(6) = (2 * 384,000 * 5)     * .3
		C(6) = (768,000     * 5)     * .3
		C(6) = (3,840,000)           * .3
		C(6) = 1,152,000
		```
		- Level 6 cost 384,000 GC, level 7 cost 1,152,000
- Each upgrade increases the maximum wager for various games.
- Coinflip increases by 2x each upgrade.
	- Card War is 25% of your Coinflip Max.
	- Blackjack is 50% of your Coinflip Max.
- If default is 2,000, level 1 makes it 4,000, level 2 makes it 8,000, etc.

### Coinflip Consecutive Bonus
- Can be upgraded 10 times.
- Initial cost: 20,000 GC, each upgrade increases price by 20,000 until you hit level 5.
	- After level 5, the formula for price is:
		- `C(n) = (2 * C(n-1) * (n-1)) * .2`
- Each time you level up the skill, you get a 1% increase payout to Coinflip if you consecutively win.
	- Half effiency in Card War.
- If the skill is level 1:
	```
	COUNT    |  PAYOUT
	-------------------
	1x Win   |    2.00x
	2x Win   |    2.01x
	3x Win   |    2.02x
	```
- If the skill is level 2:
	```
	COUNT    |  PAYOUT
	-------------------
	1x Win   |    2.00x
	2x Win   |    2.02x
	3x Win   |    2.04x
	```

### Claim Multiplier
- Can be upgraded 10 times.
- Initial cost: 30,000 GC, each upgrade increases price by 30,000.
- Each level increases the amount you receive when claiming the free react reward. Reward = ((skill level * 0.5) + 1) * amount.
- If the reward would’ve been 200, and your skill level is 1, you will receive 300 instead.

### Bank Interest
- Can be upgraded 5 times.
- Initial cost: 5M GC, each upgrade costs an additional 5M GC.
- Each upgrade increases the interest you make on your bank by .5% up to 3% weekly, paid out hourly.
- This is actually quite a lot given that it’s compounded interest.
	- Meaning, if you had 1M GC that you left untouched for a week and you had level 5, or 3% interest, by the end of the week you’d have about 1,030,000 GC, profit of 30k.

### Lucky Charm
- Can be upgraded 5 times.
- Initial cost: 500,000 GC, each upgrade costs double the previous.
- Each level adds a .6% chance to preserve your wager when losing a bet.
    - Up to a total of 3%.

### Streak Saver
- Can be upgraded 5 times.
- Initial cost: 300,000 GC, each upgrade costs double the previous.
- Each level adds a 1% chance to preserve your streak when losing in Card War or Coinflip when your previous was a win.
    - Up to a total of 5%.

<sub>Spent GC on upgrades does not get added to the vault.</sub>

## Payout

### /luck

n = the amount you rolled, i.e. how many dots you have.

    n  = 1:  0.0x
	n  = 2:  2.0x
	n  = 3:  3.5x
	n  = 4:  8.0x
	n  = 5: 12.0x
	n >= 6:  0.75 * (4 * n)

### /coinflip

1:1 on Heads, 0 otherwise.
Can buy upgrades from the Skills menu to increase the payout.
Each upgrade level increases the payout by 1% for each consecutive flip.
You can upgrade the skill a total of 10 times.

For example:

- If the skill is level 1:
	```
	COUNT    |  PAYOUT
	-------------------
	1x Heads |    2.00x
	2x Heads |    2.01x
	3x Heads |    2.02x
	```
- If the skill is level 2:
	```
	COUNT    |  PAYOUT
	-------------------
	1x Heads |    2.00x
	2x Heads |    2.02x
	3x Heads |    2.04x
	```

### /cwar

1:1 when beating the dealer, otherwise 0.
Can buy upgrades from the Skills menu to increase the payout.
Each upgrade level increases the payout by 1% for each consecutive win.
You can upgrade the skill a total of 10 times.

- If the skill is level 1:
	```
	COUNT    |  PAYOUT
	-------------------
	1x Win   |    2.000x
	2x Win   |    2.005x
	3x Win   |    2.010x
	```
- If the skill is level 2:
	```
	COUNT    |  PAYOUT
	-------------------
	1x Win   |    2.000x
	2x Win   |    2.010x
	3x Win   |    2.020x
	```

Can place a Tie side bet. It will take half of your current wager.
If the result ends up being a tie, you get a 13:1 payout.
Example with Tie side bet:

If you wager 10,000 GC, and the dealer wins, you lose 15,000 GC.

If you wager 10,000 GC, and the player wins, you win 5,000 GC.

If you wager 10,000 GC, and the result is a tie, you win 60,000 GC. (Original Tie bet of (5,000 * 13) -5,000) Push on original bet.


### /blackjack

2:1 when beating the dealer, otherwise 0.

Landing a Blackjack, an Ace with a 10 card, you get paid 3 to 2.

If you wager 500 GC, and the result is Blackjack, you win 750 GC. Receiving the amount you put in and an additional half of the wager.


## /slotto

n = the amount you matched.

    n  = 0:      0x
	n  = 1:     15x
	n  = 2:    400x
	n  = 3:  3,500x