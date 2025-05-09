# **The Degen Update** - August 9th, 2024
## **Major notes**

### Currency is now announced: Galactic Coin (GC).
- Has been running in the background since sometime Monday, August 5th, 2024.
	- Everyone starts with 10,000 GC.
- Every /luck roll took a flat 50 GC.
	- [See payouts for current /luck payout.](#payouts)
- Every /coinflip took a flat 100 GC.
	- [See payouts for current /coinflip payout.](#payouts)
- **You can now wager your GC with /coinflip and /luck.**
	- Can still play for free and have it act just like it has been by not putting any wager.
- New commands that come with currency.
	- See Commands for more information.
- Every time you lost a wager in either /coinflip or /luck, it got added to the Galactic Coin Vault. You can win the GC Vault content by getting a new record on /luck, however, you must place a wager in order to win. If you get a new record without placing a wager, you just made it harder for everyone else to win.
- **There is currently no way to get Galactic Coins without either gambling for them, having someone transfer you some, or claiming the vault. Be wise with your bets.**
- **(UPDATE)** /luck now has a 50 GC minimum.

### A leaderboard that gets updated every hour sorted by person with most to least Galactic Coins, as well as how much is in the Vault.
- Time shown in CDT.
Luckiest should be fixed, again. I did some more testing on my own, and it should be working as intended now. But there could always be something missing or wrong, but who knows, guess we’ll find out whenever someone beats kingstuckey.


## **Commands**

### **!bank** -> 30s cooldown per user.
Shows you your total currency, currently.

### **!give @user amount** -> 3s cooldown per user.
Give or transfer GC from your bank to another user.

	Example usage:
	!give @Toeknee 420.69

Nothing prevents you from making personal bets using this command.
“I bet you 500 GC I’ll /roll higher than you.”

### **!vault** -> 30s cooldown global.
Shows you the content of the vault currently.


## **Payouts**

### **/luck** payouts have been adjusted

n = the amount you rolled, i.e. how many dots you have.


	n = 1: 0x
	n = 2: 2x
	n = 3: 3.5x
	n >= 4: .75 * (4 * n)


	Example: kingstuckey hit a phat 7 roll on 8/7/2024 at 8:05 P.M. CDT.
	.75 * (4 * 7)
	.75 * 28
	= 21x
	Take the 50 flat rate at the time.
	50 * 21 = 1050
	1050 - 50 = 1000 profit.


### **/coinflip**
Just a 2:1 payout.
You win if it lands on heads (49%), you lose if it lands on tails (51%).


## **Minor notes**
I didn’t expect this bot to go as hard as it has. Because of that, all the code was in one file. As I added more and more commands, the file got very long and I started getting lost in the weeds. Well, I’m happy to announce that I refactored the codebase and now things are in separate files and much easier to read and scale. Meaning, adding new features should be much easier than it has been before.

Also, this is a huge milestone for me, because typically, I just restart entire projects instead of refactoring them. Think it just shows that I’ve come a long way since the base code was already pretty well setup, so refactoring wasn’t as hard as it could’ve been.

Anyway, new features will be coming, but I might need to focus on other parts of the backend before I start adding new things, but we’ll see!

