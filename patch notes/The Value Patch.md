# **The Skills Patch** - {Date TBA}
*Alternative Name (The Value Patch)*

## **Major notes**

- Data has been moved to a database instead of a json file.
- Because of this, !bank now has a cooldown of 3 seconds.
- **[There are now skill upgrades!](#skill-upgrades)**
- Using Discord UI for the skills menu.
- Leaderboards now use display name instead of username when it can.
	- The IGV server will use the display name from Snax first, then Discord username after.
- [/luck payouts have been adjusted.](#payouts)
- /coinflip now has a default maximum of 2,000, it can be upgraded.
- /coinflip now tells you how many times you’ve hit something in a row.
	- Only when placing a bet, if you don’t do a bet, it won’t track and won’t tell you the streak.
- Bot will send a message at a random interval, the first person to react to it will be rewarded GC. Range from 100 - 1,000 GC.
	- Given 1 hour to react, otherwise it’ll delete itself.
	- A new message shows up after the old message is either gone or reacted to, a range between 30 minutes to 90 minutes.
	- Can upgrade how much you receive from the message.
	- Sends one in the Snax server and the [IGV server](https://discord.gg/mtcwF4NVyb).
		- They’re different instances, so you can double dip.
		- [Join](https://discord.gg/mtcwF4NVyb) if you want to double dip in rewards.
- Bot sends leaderboard updates to the Intergalactic Verse server as well.
	- Also sends the new luckiest message to that server.
	- Not entirely sure if this broke the function, though, I haven’t really tested it.
	- But I assure you, the new luckiest worked prior to this, just no one has been able to beat the 7 roll.

## **Skill Upgrades**

### Coinflip Maximum
- Can be upgraded as many times as you can afford.
- Initial cost: 10,000 GC, each upgrade doubles the cost of the next.
- Each upgrade increases the coinflip maximum you can make by 2x.
- If default is 2,000, level 1 makes it 4,000, level 2 makes it 8,000, etc.

### Coinflip Consecutive Bonus
- Can be upgraded 10 times.
- Initial cost: 20,000 GC, each upgrade increases price by 20,000.
- Each time you level up the skill, you get a 1% increase payout to coinflip if you consecutively land on heads.
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

### Claim Multiplier
- Can be upgraded 9 times.
- Initial cost: 30,000 GC, each upgrade increases price by 30,000.
- Each level increases the amount you receive when claiming the free react reward. ~~Reward = (skill level + 1) * amount.~~ Reward = ((level * 0.5) + 1)
- If the reward would’ve been 200, and your skill level is 1, you will receive ~~400~~ 300 instead.

<sub>Updated to be a 0.5 increase each level instead of 1.</sub>

### Bank Interest
- Can be upgraded 5 times.
- Initial cost: 5M GC, each upgrade costs an additional 5M GC.
- Each upgrade increases the interest you make on your bank by .5% up to 3% weekly, paid out hourly.
- This is actually quite a lot given that it’s compounded interest.
	- Meaning, if you had 1M GC that you left untouched for a week and you had level 5, or 3% interest, by the end of the week you’d have about 1,030,000 GC, profit of 30k.
```
	LEVEL   |  PERCENT WEEKLY
	--------------------------
	  1     | 	0.5%
	  2     |  	1.0%
	  3     |  	1.5%
	  4     |  	2.0%
	  5     |  	3.0%
```


## **Commands**

### **/skills**
- Opens up the skills menu, can see what your current skills are at or upgrade them from the menu.

### **!bank**
- Cooldown adjust from 30s -> 15s -> 3s

### **???**

## **Payouts**

**/luck** payouts have been adjusted

n = the amount you rolled, i.e. how many dots you have.

    n  = 1:  0.0x
	n  = 2:  2.0x
	n  = 3:  3.5x
	n  = 4:  8.0x
	n  = 5: 12.0x
	n >= 6:  0.75 * (4 * n)

	Example: kingstuckey hit a phat 7 roll on 8/7/2024 at 8:05 P.M. CDT.
	.75 * (4 * 7)
	.75 * 28
	= 21x
	Take the 50 flat rate at the time.
	50 * 21 = 1050
	1050 - 50 = 1000 profit.


## **Minor notes**
Moved over to a database, [very nice.](https://www.youtube.com/watch?v=LBduNcf1eQc) Used to use .json files, not very convenient.
Databases are much more efficient and easier to work with. Also fixed a race condition that I had before, whoops.
Honestly, !bank had no reason to be on such a long cooldown, but I kept it at 15 out of spite from 30. But I changed it to 3 seconds, why not.
Cleaned up the main file again by putting all of the meme commands in a separate file.
The main goal of this update was to give some value to GC. Things got inflated really high, vault slowly crept up, once it hit 1M GC, it climbed to 5M then to 8M very fast. 8M to 19M happened in a blink of an eye. At some point, coinflipping 500k had no more meaning than 5k a few days before.
I know that feeling of coinflipping high amounts is fun, which is why I made no limit to the amount of times you can increase the Coinflip Maximum skill, but it does get more and more expensive to upgrade. Think this is one good way to control the value of GC.
Learned how to use Discord UI for menus, which is great for upgrading skills and possibly other things 👀
