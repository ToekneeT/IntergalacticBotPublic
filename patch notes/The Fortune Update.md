# **The Fortune Update** - August 30th, 2024

## **Major notes**
- 90% of lost bets are now added to the vault instead of 100%.
- New [Fortune command.](#fortune)
- New Skill: [Lucky Charm.](#lucky-charm)
- Claim Multiplier skill now goes to level 10 instead of 9.
- Payout rate text now shows up below how many times you've landed on a coin.
- New game: [Card War](#cwar)
    - /cwar
    - Basically another 50/50 game.
    - Check [payout](#payout) for more information.
- Coinflip Maximum has been renamed to Wager Maximum.


## **Skill Upgrades**

### **Lucky Charm**
- Can be upgraded 5 times.
- ~~Every upgrade cost 100,000 1,000,000 GC regardless of which level you're buying.~~
- Initial cost: 500,000 GC, each upgrade costs an additional 500,000 GC.
- Each level adds a 1% chance to preserve your wager when losing a bet.
    - Up to a total of 5%.

### **Claim Multiplier**
- Max level 10 instead of 9.
- Should be able to get up to 6x claim multiplier.

### **Coinflip Consecutive Bonus**
- Works with Card War.

### **Coinflip Maximum**
- Works with Card War.
- Renamed to Wager Maximum.

## **Commands**

### **/fortune**
- Can spend GC to receive your fortune in the form of an [Omikuji.](https://blog.japanwondertravel.com/what-is-omikuji-29421)
    - Options of 500 GC, 2_000 GC, and 10_000 GC.
        - While not guaranteed, more likely to get a bad fortune out of 500, a good fortune out of 10,000. No weight on 2,000.
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

### **/cwar**
- Minimums are 100 GC. Maximum shares the same max as Coinflip. Upgradable with Wager Maximum.
    - Increase / decrease by 100, 500, 1_000, 5_000, or 10_000 at a time.
    - Or go straight to max / min bet.
- Standard single deck of cards, shuffled every round.
- Dealer draws a card and the player draws a card, whoever has the higher value card wins the round.
    - Card values from highest to lowest: Ace > King > Queen > Jack
- Payout 2:1 upon winning.
    - Consecutive Coinflip Bonus skill also works in Card War.
- Payout for a tie if placed is 13:1.
    - A tie side bet takes 50% of your original wager.
    - Example, if original wager is 16,000 GC, tie would be an additional 8,000 GC.
    - A tie bet is active when the Tie button is green.
        - It stays active until you press it again to deactivate it.


### **!firstvault**
- On August 22nd, 2024, whiffy11 won the first vault, totaling 20,298,259.19 GC.
    - Had to get an 8 roll, which is a 0.0153% chance.
- To commemorate this moment, this command was created that sends a screenshot of the leaderboard update after winning the vault.


## Payout

### /cwar

2x payout if you have a higher card than the dealer. 0x, otherwise.
Can buy upgrades from the Skills menu to increase the payout.
Each upgrade level increases the payout by 1% for each consecutive win.
You can upgrade the skill a total of 10 times.

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

Can place a Tie side bet. It will take half of your current wager.
If the result ends up being a tie, you get a 13:1 payout.
Example with Tie side bet:

If you wager 10,000 GC, and the dealer wins, you lose 15,000 GC.

If you wager 10,000 GC, and the player wins, you win 5,000 GC.

If you wager 10,000 GC, and the result is a tie, you win 60,000 GC. (Original Tie bet of (5,000 * 13) -5,000) Push on original bet.


## **Minor notes**
While mostly space themed and reference filled, I've added some bot related status messages to show up.

Did some more database optimizations. When I was first setting them up, I didn't have a full idea on how I wanted to set things up. Due to that, there were some columns that weren't used, and foreign keys that weren't being utilized when they should. Should be all fine and dandy now.

I decided to have Card War share the same maximum as Coinflip since they're both basically 50/50 games.
The amount you bet is kinda limited by the menu, not entirely sure if there's another way around it.

Renamed Coinflip Maximum to Wager Maximum as the skill will probably be used for other games.