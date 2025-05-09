# **Blackjack and Friends** - September 30th, 2024

## **Major notes**
- There was a great reset on September 12th, 2024.
	- Too many changes, inflation too high.
	- General consensus from players was to reset.
- [Blackjack!](#blackjack)
	- Invoked with /blackjack
	- Not fully featured, will slowly roll out as the features get added!
		- Has hitting, stand, and double down.
			- Things are subject to change. (DD will be locked behind an upgrade.)
- [Pets!](#pets)
	- Can buy pets!
		- Current pet on sale changes every new hour.
		- Price of pet changes depending on how rare that particular pet is.
	- Doesn't do anything other than for collection, or bragging rights.
	- There are some secret pets as well!
- Vault contribution is now 10% of losses and capped at 30k GC per wager to attempt to reduce inflation.
- [Price of Wager Maximum](#wager-maximum) is higher after level 5.
- [Price of Coinflip Consecutive Bonus](#coinflip-consecutive-bonus) is higher after level 5.
- Lucky Charm price now increases by double the previous level.
- Fortune changes:
	- Options of Cheap, Standard, and Quality.
		- Previous 500, 2000, 10000
	- Prices:
		Cheap = 500 GC, or 2% of your balance, whichever ends up being higher.
		Standard = 2,000 GC, or 5% of your balance, whichever ends up being higher.
		Quality = 10,000 GC, or 10% of your balance, whichever ends up being higher.
	- Cheap cannot get a Great Blessing and Quality cannot get a Great Bad Fortune.
		- It was unlikely before, but now guaranteed to not happen.
- /luck now has a maximum starting at 20,000 GC. Each Wager Maximum also increases it by 2x.
- /luck now has a minimum of 200 GC, up from 50 GC.
- [!bankfull](#bankfull) command.
- [!networth](#networth) command.
- Card War now tells you the session results when you press Quit.
- Skills menu no longer only visible to you.

## **Skill Upgrades**

### **Streak Saver**
- Can be upgraded 5 times.
- Initial cost: 500,000 GC, each upgrade costs double the previous.
- Each level adds a 1% chance to preserve your streak when losing in Card War or Coinflip when your previous was a win.
    - Up to a total of 5%.

### **Wager Maximum**
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

### **Coinflip Consecutive Bonus**
- `C(n) = (2 * C(n-1) * (n-1)) * .2`
- Same formula as Wager Maximum, just takes 20% instead of 30%.

### **Lucky Charm**
- Price now cost double the previous upgrade cost.

## **Commands**

### **/blackjack**
- Standard 3 to 2 Blackjack.
	- [Official Guide + Strategy.](https://www.officialgamerules.org/card-games/blackjack)
	- Only currently has hitting, stand, and doubling down.
		- The rest of the features will slowly roll out as they're done.
- Minimum of 200 GC to play.
- Maximum is 25% of your Coinflip Max.
	- If you're at level 0 for Wager Max, the Max for Blackjack will be 600
- Shoe is shuffled when there is between 30% - 50% of cards remaining.
	- It will let you know when the deck is reshuffled.
	- Changing your wager does not reshuffle the deck!
- Can change shoe size, options being 1, 2, 6, and 8.
	- Changing shoe size gives a new shuffled deck.
- If you use the Quit button, it'll tell you your session results, how many times player, dealer, etc won.
- **Don't get too comfortable with Double Down, it'll be locked to an upgrade later**

### **/pets**
- Provides a one stop shop for Pets.
- Can see what the current pet on sale is, or check your currently owned pets.

### **!pet**
- Replies with the current pet on sale and its price.

### **!mypets**
- Replies with your currently owned pets.

### **!givepet @user petname**
- Gives the user a pet that you own.
- !givepet @user Quasar Turtle
	- Pet name is not case sensitive.
	- Must spell the pet name correctly, including spaces.

### **!bankfull**
- When doing !bank, it'll round to the nearest tenth. Often, you can have a .001, which would give you a value of .01
- Using this will give you your full amount in case you want to use it all, or in case you're trying to do something and it says you don't have enough.

### **!networth**
- Replies with your networth, as much as it can.
	- Prior to this update, any Galactic Coins spent on upgrades was not added to your networth.
	- Only new upgrades and now pets that are purchased will be added your networth.
	- Combines spent GC on upgrades, pets, and your current bank.


## **Minor notes**
- Made all buttons go gray when you hit Quit in every menu.
I created a blackjack program a few years ago so that I could learn how to count cards.
Well, I never ended up using it for that, I made it, got most of the functions working, and then almost never played it.
With this, I'm hoping more people can enjoy it, while also maybe learning to count cards themselves.
I'm sure if you get good at counting cards, single shoe will be a decent Galactic Coin earner.