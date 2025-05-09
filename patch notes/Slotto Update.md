# **Slotto Update** - February 28th, 2025

<sub>Notes include some of the small updates that happened between this one and the [Blackjack and Friends update.](https://gist.github.com/ToekneeT/cfd745bd46cfb3a9c14a57149dcc8adb)</sub>

## **Major notes**
- [Slotto!](#slotto)
	- Invoked with /slotto
	- A weird mixed game of slots and lottery?
- Small balance changes.
	- Lucky Charm now has a maximum of 3% chance to preserve.
	- Streak Saver is cheaper, starting at 300,000 GC.
- Elusive Hunter role (Only in Intergalactic Lounge)
- Soft limit on how much you can `/give` away.
	- Can only give away 35% of your balance from an hour ago.
		- Meaning, if you had 100,000 GC one hour ago, you can give away up to 35,000 GC.
			- If you had 100,000 GC an hour ago, but currently have 30,000 GC, you can give it all away.
	- [/gifted](#gifted)
		- Checks how much you've gifted in the last hour and your allowance.
- Card War Maximum is now 25% of Coinflip's (down from 100%).
- Blackjack Maximum is now 50% of Coinflip's (up from 25%).
- [/games](#games)

## **Skill Upgrades**

### **Streak Saver**
- Now has an initial cost of 300,000 GC, doubling each time.
	- Previously had an initial cost of 500,000 GC.

### **Lucky Charm**
- Now only gives .6% each upgrade, to a maximum of 3% at level 5.
	- Previously 1% each upgrade, to a maximum of 5% at level 5.

## **Commands**

### **/slotto**
- A weird mixed game of slots and lottery?
- Minimum of 50 GC to play.
- Same Maximum as Coinflip.
Choose up to 3 numbers between 1-99 or have them randomly assigned to you. Winning numbers will be picked afterwards,
your numbers and the winning numbers must be matching in the same spot in order to receive a payout.

- Payouts are based on how many numbers you matched. They have to be in the same position as well.
	```
	Player:  01, 27, 88
	Winning: 27, 01, 88
	Matched: 1
	```
	The above scenario would only have a matched number of 1 since 88 are both in the same position.

	```
	n = the amount you matched.

    n  = 0:      0x
	n  = 1:     20x
	n  = 2:    400x
	n  = 3:  3,500x
	```

### **/gifted**
- Shows you how much GC you've gifted or given away in the last hour.
- Shows you your allowance (how much you can give away).

### **/games**
- Displays which games are available to play and links to the readme for more information.

### **!blackjack**
- Provides a link to Wizard of Odds's blackjack strategy calculator.


## **Minor notes**
A very old relic of before the times this bot was moved to a database, I was storing all transactions in a csv file; however, I finally moved 
the transactions to the database. Hostly in order to check how much someone has given away in the last hour to set a limit on how much you can give away.
But what is really cool is that I made a Web UI to view the transactions that have been made and can query certain things.
Oh, also at some point, I dockerized the bot.