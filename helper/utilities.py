import json, time, sqlite3, datetime, random, logging, discord

logger = logging.getLogger()
logging.basicConfig(filename="stats.log", level=logging.INFO)

# Tables:
# GC Vault discord_id = 0
# Current Pet discord_id = 0
# 
# TABLE users
#                      discord_id INTEGER PRIMARY KEY,
#                      balance NUMERIC DEFAULT 10000
# 
# TABLE stats
#                      stat_name TEXT,
#                      count INTEGER
# 
# TABLE upgrades
#                      user_id INTEGER FOREIGN KEY,
#                      upgrade_name TEXT,
#                      upgrade_level INTEGER
# 
# TABLE old_balance
#                      discord_id INTEGER FOREIGN KEY,
#                      balance NUMERIC DEFAULT 10000
# 
# TABLE last_coin
#                      discord_id INTEGER FOREIGN KEY,
#                      coin TEXT,
#                      count INTEGER
# 
# TABLE cwar_result
#                      discord_id INTEGER FOREIGN KEY,
#                      winner TEXT,
#                      count INTEGER DEFAULT 0,
#
# TABLE pet
#                      discord_id INTEGER FOREIGN KEY,
#                      pet_name TEXT,
#                      count INTEGER DEFAULT 0,
#                      cost NUMERIC DEFAULT 0,
# 
# TABLE fortune
#                      discord_id INTEGER FOREIGN KEY,
#                      count NUMERIC,
# 
# TABLE user_networth
#                      discord_id INTEGER FOREIGN KEY,
#                      networth NUMERIC,
# 
# TABLE transactions
#                      discord_id INTEGER FOREIGN KEY,
#                      username TEXT,
#                      type TEXT,
#                      transaction_amount NUMERIC,
#                      balance NUMERIC,
#                      created_at DATETIME DEFAULT CURRENT_TIMESTAMP

def load_config() -> dict:
    try:
        with open("config.json") as f:
            config_data = json.load(f)
        return config_data
    except FileNotFoundError as e:
        print(e)


def save_config(config_file: dict) -> None:
    try:
        with open("config.json", "w") as f:
            json.dump(config_file, f)
    except FileNotFoundError:
        with open(f'bank_{int(time.time())}.json') as f:
            json.dump(config_file, f)


def append_ledger(expense: str) -> None:
    try:
        with open("ledger.csv", "a") as f:
            f.write(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{expense}\n')
    except FileNotFoundError:
        with open(f'ledger_{int(time.time())}.text') as f:
            f.write(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{expense}\n')


def get_db_connection():
    conn = sqlite3.connect('stats.db')
    conn.execute('PRAGMA journal_mode = WAL;')
    conn.execute('PRAGMA foreign_keys = ON;')
    conn.commit()
    return conn


# Truncates or removes any number after the hundedths position
# by multiplying it by 100, turning it into an int, thereby removing the
# rest of the numbers, and then dividing it by 100.
def truncate_hundredths(num: float) -> float:
    num = int(num * 100)
    return num / 100


# Creates all the tables needed at startup.
def create_tables_if_not_exist() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
                   discord_id INTEGER PRIMARY KEY,
                   balance NUMERIC DEFAULT 10000)
    ''')

    cursor.execute('''
        SELECT balance
        FROM users
        WHERE discord_id = 0
    ''')

    vault = cursor.fetchone()
    if vault is None:
        cursor.execute('''
        INSERT INTO users (discord_id, balance)
        VALUES (0, 0)
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS upgrades (
        user_id INTEGER,
        upgrade_name TEXT,
        upgrade_level INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(discord_id))
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fortune (
        discord_id INTEGER,
        count INTEGER DEFAULT 0,
        FOREIGN KEY (discord_id) REFERENCES users(discord_id))
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_networth (
        discord_id INTEGER,
        networth NUMERIC,
        FOREIGN KEY (discord_id) REFERENCES users(discord_id))
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
        stat_name TEXT,
        count INTEGER)
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS old_balance (
        id INTEGER PRIMARY KEY,
        discord_id INTEGER,
        name TEXT,
        balance NUMERIC DEFAULT 10000)
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS last_coin (
        discord_id INTEGER,
        coin TEXT,
        count INTEGER DEFAULT 0,
        FOREIGN KEY (discord_id) REFERENCES users(discord_id))
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cwar_result (
        discord_id INTEGER,
        winner TEXT,
        count INTEGER DEFAULT 0,
        FOREIGN KEY (discord_id) REFERENCES users(discord_id))
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
        discord_id INTEGER,
        username TEXT,
        type TEXT,
        transaction_amount NUMERIC,
        balance NUMERIC,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (discord_id) REFERENCES users(discord_id))
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pet (
        discord_id INTEGER,
        pet_name TEXT,
        count INTEGER DEFAULT 0,
        cost NUMERIC DEFAULT 0,
        FOREIGN KEY (discord_id) REFERENCES users(discord_id))
    ''')

    # Defaults the pet to N/A if the table was just created.
    cursor.execute('''
        SELECT discord_id FROM pet WHERE discord_id = 0
    ''')
    pet_shop = cursor.fetchone()
    if pet_shop is None:
        cursor.execute('''
            INSERT OR IGNORE INTO pet (discord_id, pet_name, count, cost)
            VALUES (?, ?, ?, ?)
        ''', (0, "N/A", 0, 0))
    

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_name (
        discord_id INTEGER,
        username TEXT,
        FOREIGN KEY (discord_id) REFERENCES users(discord_id))
    ''')

    cursor.execute('SELECT username FROM user_name WHERE discord_id = 0')
    vault_name = cursor.fetchone()
    if vault_name is None:
        cursor.execute('INSERT INTO user_name (discord_id, username) VALUES (?, ?)', (0, "GC Vault"))

    conn.commit()
    conn.close()
    return


def get_balance(user_id: int) -> float:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT users.balance
        FROM users
        WHERE users.discord_id = ?
    ''', (user_id,))

    user = cursor.fetchone()

    # Checks if the user exists, otherwise make them a default
    # balance of 10,000
    if user is None:
        cursor.execute('''
        INSERT INTO users (discord_id, balance)
        VALUES (?, ?)
    ''', (user_id, 10_000))
        curr_balance = 10_000
        conn.commit()

    else:
        curr_balance = user[0]

    conn.close()

    return truncate_hundredths(curr_balance)


def update_balance(user_id: int, credit: float) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    curr_balance = get_balance(user_id)

    curr_balance += credit

    cursor.execute('''
        UPDATE users
        SET balance = ?
        WHERE discord_id = ?
    ''', (curr_balance, user_id))

    conn.commit()
    conn.close()


def update_all_balances(credit: float) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users
        SET balance = balance + ?
        WHERE discord_id != ?
    ''', (credit, 0))

    conn.commit()
    conn.close()


def store_previous_balance() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS old_balance')
    conn.commit()

    cursor.execute('CREATE TABLE old_balance AS SELECT * FROM users')

    conn.commit()
    conn.close()


def get_old_balance(user_id: int) -> float:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT balance
        FROM old_balance
        WHERE discord_id = ?
    ''', (user_id,))

    user = cursor.fetchone()

    # Checks if the user exists, otherwise make them a default
    # balance of 10,000
    if user is None:
        cursor.execute('''
        INSERT INTO old_balance (discord_id, balance)
        VALUES (?, ?)
    ''', (user_id, 10_000))
        curr_balance = 10_000
        conn.commit()

    else:
        curr_balance = user[0]

    conn.close()

    return curr_balance


def get_users_sorted_by_balance(ascending=False) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()

    order = "ASC" if ascending else "DESC"

    cursor.execute(f'''
        SELECT discord_id, balance FROM users
        WHERE discord_id != ?
        ORDER BY balance {order}
        LIMIT 10
    ''', (0,))

    sorted_users = cursor.fetchall()

    conn.close()

    return sorted_users


def get_stat(stat: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT count
        FROM stats
        WHERE stat_name = ?
    ''', (stat,))
    stat_count = cursor.fetchone()

    # Checks if the user exists, otherwise make them a default
    # balance of 10,000
    if stat_count is None:
        cursor.execute('''
        INSERT INTO stats (stat_name, count)
        VALUES (?, ?)
    ''', (stat, 1))
        count = 1
        conn.commit()

    else:
        count = stat_count[0]

    conn.close()

    return count


def get_all_stats() -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM stats')
    rows = cursor.fetchall()
    data = {}

    for row in rows:
        stat_name = row[0]
        count = row[1]
        data[stat_name] = count
    
    return data


def increment_stat(stat: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT count
        FROM stats
        where stat_name = ?
    ''', (stat,))
    stat_count = cursor.fetchone()

    if stat_count is None:
        cursor.execute('''
            INSERT INTO stats (stat_name, count)
            VALUES (?, ?)
        ''', (stat, 0))
        count = 0
    else:
        count = stat_count[0]

    new_count = count + 1

    cursor.execute('''
        UPDATE stats
        SET count = ?
        WHERE stat_name = ?
    ''', (new_count, stat))

    conn.commit()
    conn.close()


def get_upgrade_level(skill: str, user_id: int) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT upgrade_level
        FROM upgrades
        WHERE upgrade_name = ? AND user_id = ?
    ''', (skill, user_id))

    skill_level = cursor.fetchone()

    if skill_level is None:
        cursor.execute('''
            INSERT INTO upgrades (user_id, upgrade_name, upgrade_level)
            VALUES (?, ?, ?)
        ''', (user_id, skill, 0))
        level = 0
        conn.commit()

    else:
        level = skill_level[0]
    
    conn.close()
    return level


def get_user_upgrades(user_id: int) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT upgrade_name, upgrade_level
        FROM upgrades
        WHERE user_id = ?
    ''', (user_id,))

    upgrades = cursor.fetchall()

    conn.close()

    return upgrades


def increment_upgrade(skill: str, user_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    curr_level = get_upgrade_level(skill, user_id)
    curr_level += 1

    cursor.execute('''
        UPDATE upgrades
        SET upgrade_level = ?
        WHERE user_id = ? AND upgrade_name = ?
    ''', (curr_level, user_id, skill))

    conn.commit()
    conn.close()


def set_upgrade(skill: str, user_id: int, new_level: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    get_upgrade_level(skill, user_id)

    cursor.execute('''
        UPDATE upgrades
        SET upgrade_level = ?
        WHERE user_id = ? AND upgrade_name = ?
    ''', (new_level, user_id, skill))

    conn.commit()
    conn.close()


def get_user_last_coin(user_id: int) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT coin
        FROM last_coin
        WHERE discord_id = ?
    ''', (user_id,))

    coin = cursor.fetchone()

    if coin is None:
        cursor.execute('''
            INSERT INTO last_coin (discord_id, coin, count)
            VALUES (?, ?, ?)
        ''', (user_id, "Tails", 0))
        last_coin = "Tails"
        conn.commit()

    else:
        last_coin = coin[0]
    
    conn.commit()
    conn.close()
    return last_coin


def set_user_last_coin(user_id: int, coin: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    last_coin = get_user_last_coin(user_id)
    if last_coin == coin:
        cursor.execute('''
            UPDATE last_coin
            SET count = count + 1
            WHERE discord_id = ?
        ''', (user_id,))
    else:
        cursor.execute('''
            UPDATE last_coin
            SET coin = ?, count = ?
            WHERE discord_id = ?
        ''', (coin, 1, user_id))

    conn.commit()
    conn.close()


def get_user_coin_count(user_id: int) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()

    get_user_last_coin(user_id)

    cursor.execute('''
        SELECT count
        FROM last_coin
        WHERE discord_id = ?
    ''', (user_id,))
    
    count = cursor.fetchone()[0]

    conn.close()
    return count


def get_user_last_cwar_result(user_id: int) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT winner
        FROM cwar_result
        WHERE discord_id = ?
    ''', (user_id,))

    result = cursor.fetchone()

    if result is None:
        cursor.execute('''
            INSERT INTO cwar_result (discord_id, winner, count)
            VALUES (?, ?, ?)
        ''', (user_id, "Dealer", 0))
        last_winner = "Dealer"
        conn.commit()

    else:
        last_winner = result[0]
    
    conn.commit()
    conn.close()
    return last_winner


def set_user_last_cwar_result(user_id: int, winner: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    last_winner = get_user_last_cwar_result(user_id)
    if last_winner == winner:
        cursor.execute('''
            UPDATE cwar_result
            SET count = count + 1
            WHERE discord_id = ?
        ''', (user_id,))
    else:
        cursor.execute('''
            UPDATE cwar_result
            SET winner = ?, count = ?
            WHERE discord_id = ?
        ''', (winner, 1, user_id))

    conn.commit()
    conn.close()


def get_user_cwar_win_count(user_id: int) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()

    get_user_last_cwar_result(user_id)

    cursor.execute('''
        SELECT count
        FROM cwar_result
        WHERE discord_id = ?
    ''', (user_id,))
    
    count = cursor.fetchone()[0]

    conn.close()
    return count


def get_all_bank_interest() -> list:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id, upgrade_level
        FROM upgrades
        WHERE upgrade_name = ? AND upgrade_level > 0
    ''', ("Bank Interest",))

    users = cursor.fetchall()
    conn.close()

    return users


def get_user_fortune(user_id: int) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT count
        FROM fortune
        WHERE discord_id = ?
    ''', (user_id,))

    fortune_count = cursor.fetchone()

    if fortune_count is None:
        cursor.execute('''
            INSERT INTO fortune (discord_id, count)
            VALUES (?, ?)
        ''', (user_id, 0))
        fortune = 0
        conn.commit()

    else:
        fortune = fortune_count[0]

    conn.close()

    return fortune


def set_user_fortune(user_id: int, count: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    curr_fortune = get_user_fortune(user_id)
    cursor.execute('''
        UPDATE fortune
        SET count = ?
        WHERE discord_id = ?
    ''', (count, user_id))

    conn.commit()
    conn.close()


def get_higher_of_two(num_one: float, num_two: float) -> float:
    if num_one >= num_two:
        return num_one
    return num_two


def fortune_spent(cost: float) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT count
        FROM stats
        where stat_name = ?
    ''', ("paid fortune",))
    stat_count = cursor.fetchone()

    if stat_count is None:
        cursor.execute('''
            INSERT INTO stats (stat_name, count)
            VALUES (?, ?)
        ''', ("paid fortune", 0))
        count = 0
    else:
        count = stat_count[0]

    cursor.execute('''
        UPDATE stats
        SET count = count + ?
        WHERE stat_name = ?
    ''', (cost, "paid fortune"))

    conn.commit()
    conn.close()


def get_lower_of_two(num_one: float, num_two: float) -> float:
    if num_one >= num_two:
        return num_two
    return num_one


# Does the fortune roll, occasionally the better roll is a lower number, example being chance to not lose your wager.
# Or the way coinflip is setup, heads is the lower value.
# Sometimes, fortune shouldn't be used, such as chance to not lose your wager, which would make it so you lose two
# Fortunes for losing once.
def fortune_roll(user_id: int, fortune_count: int, num_one: int, num_two: int, favor_high: bool = True, use_fortune: bool = True):
    new_result = None
    if favor_high:
        new_result = get_higher_of_two(num_one, num_two)
    else:
        new_result = get_lower_of_two(num_one, num_two)
    
    if use_fortune and fortune_count > 0:
        fortune_count -= 1
        set_user_fortune(user_id, fortune_count)
    elif use_fortune and fortune_count < 0:
        fortune_count += 1
        set_user_fortune(user_id, fortune_count)
    
    return new_result


def bet_payout(user_id: int, user: str, display_name: str, bet: float, rate: float) -> str:
    # In the rare case that the user has less than the bet amount, it'll use what they do have.
    # The user's balance *shouldn't* be less than the bet amount, but there's a chance that it could
    # happen and be abused in Blackjack.
    bet = min(bet, get_balance(user_id))
    pay = round(bet * rate, 2)
    # Grabs the current level the user has.
    lucky_charm_level: int = get_upgrade_level("Lucky Charm", user_id)
    # Percentages are based on each level, increasing by .6% each upgrade, for a max of 3%.
    lucky_charm_dict: dict = {
        0: 0,
        1: .006,
        2: .012,
        3: .018,
        4: .024,
        5: .03,
    }
    lucky_charm: float = lucky_charm_dict[lucky_charm_level]

    # Push, meaning nothing happens.
    # Should only happen when the rate == 1.
    if pay == bet:
        return f'\n**Push!**\nOriginal wager: {bet:,.2f} GC\nPayout to {display_name}: {bet:,.2f} GC'
    # If pay is 0, then the rate means 0, total loss.
    elif pay == 0:
        # Each level of Lucky Charm adds a 1% chance to not lose your bet.
        if lucky_charm > 0:
            user_fortune = get_user_fortune(user_id)
            preserve_chance: float = random.random()
            log_text: str = f'OG: {preserve_chance} '

            # Positive fortune is lucky, negative is unlucky.
            if user_fortune > 0:
                preserve_chance = fortune_roll(user_id,
                                                        user_fortune,
                                                        preserve_chance,
                                                        random.random(),
                                                        favor_high=False,
                                                        use_fortune=False)
                log_text += f"fortune affected: {preserve_chance}"
            elif user_fortune < 0:
                preserve_chance = fortune_roll(user_id,
                                                        user_fortune,
                                                        preserve_chance,
                                                        random.random(),
                                                        favor_high=True,
                                                        use_fortune=False)
                log_text += f"fortune affected: {preserve_chance}"
            if preserve_chance <= lucky_charm:
                logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{user},lucky charm activated,{log_text}')
                return f'\nLucky Charm prevented loss.\nOriginal wager: {bet:,.2f} GC\nPayout to {display_name}: {bet:,.2f} GC'
            logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")},{user},lucky charm missed,{log_text}')
        
        # 5% of losses go into the vault, 95% goes into the void. Max added to vault from one bet is 5,000.
        vault_contribution: float = bet * .05 if bet * .05 < 5_000 else 5_000
        update_balance(0, vault_contribution)
        update_balance(user_id, -bet)
        user_balance: float = get_balance(user_id)
        vault_balance: float = get_balance(0)
        add_transaction_to_history(user_id, user, "gamble", -bet, user_balance)
        add_transaction_to_history(0, "GC Vault", "gamble", vault_contribution, vault_balance)
    elif pay > bet:
        update_balance(user_id, (pay - bet))
        user_balance: float = get_balance(user_id)
        add_transaction_to_history(user_id, user, "gamble", (pay - bet), user_balance)
    elif pay > 0 and pay < bet:
        # Might need to double check this when there's half pay / surrender.
        # Might also need to check the vault contribution here seeing as it's different from the full amount now.
        update_balance(user_id, -pay)
        update_balance(0, pay)
        user_balance: float = get_balance(user_id)
        vault_balance: float = get_balance(0)
        add_transaction_to_history(user_id, user, "gamble", -pay, user_balance)
        add_transaction_to_history(0, "GC Vault", "gamble", pay, vault_balance)
    return f'\nOriginal wager: {bet:,.2f} GC\nPayout to {display_name}: {bet * rate:,.2f} GC'


def get_current_pet() -> tuple[str, float]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT pet_name, cost
        FROM pet
        WHERE discord_id = ?
    ''', (0,))

    current_pet = cursor.fetchone()

    conn.close()

    return (current_pet[0], current_pet[1])


def set_current_pet(name: str, pet_price: int) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()

    get_current_pet()

    # Cost of pet on sale is stored in the cost of "discord_id" 0.
    cursor.execute('''
        UPDATE pet
        SET pet_name = ?, cost = ?
        WHERE discord_id = ?
    ''', (name, pet_price, 0))

    conn.commit()
    conn.close()


def change_current_pet() -> str:
    # List of pets
    with open('pets/adjectives.txt') as file:
        adjectives: list[str] = file.read().splitlines()

    with open('pets/nouns.txt') as file:
        nouns: list[str] = file.read().splitlines()

    # Indexing, minus one as the array is between 0 and length - 1.
    adj_length: int = len(adjectives)-1
    noun_length: int = len(nouns)-1

    # Rolls twice, gets the lower value as the adjective and noun.
    # Making certain adjectives and pets more rare.
    adj_idx: int = get_lower_of_two(random.randint(0, adj_length), random.randint(0, adj_length))
    noun_idx: int = get_lower_of_two(random.randint(0, noun_length), random.randint(0, noun_length))

    # Price of pet changes depending on the adjective and noun.
    # pet_price: float = (((adj_idx + 1) * 40_000) + ((noun_idx + 1) * 100_000)) * 100
    pet_price: float = (adj_idx + 1) * ((noun_idx + 1) * 100_000)
    set_current_pet(f'{adjectives[adj_idx]} {nouns[noun_idx]}', pet_price)


def get_user_pets(user_id: int) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT pet_name, count, cost
        FROM pet
        WHERE discord_id = ? AND count != 0
    ''', (user_id,))

    pets = cursor.fetchall()
    if pets is None:
        return []
    
    pets_dict = {row[0]: (row[1], row[2]) for row in pets}

    conn.close()
    return pets_dict


def add_pet_to_user(user_id: int, pet_name: str, cost: float) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    pet_name = pet_name.title()
    user_pets: dict = get_user_pets(user_id)
    # If the user doesn't already own this pet.
    if pet_name not in user_pets:
        cursor.execute('''
            INSERT INTO pet (discord_id, pet_name, count, cost)
            VALUES (?, ?, ?, ?)
        ''', (user_id, pet_name, 1, cost))
        conn.commit()
    # user does own pet, increment the counter.
    else:
        cursor.execute('''
            UPDATE pet
            SET count = count + 1, cost = ?
            WHERE discord_id = ? AND pet_name = ?
        ''', (cost, user_id, pet_name))

    conn.commit()
    conn.close()
    update_user_networth(user_id, cost)


def remove_pet_from_user(user_id: int, pet_name: str, cost: float) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    pet_name = pet_name.title()
    user_pets: dict = get_user_pets(user_id)
    if pet_name not in user_pets:
        conn.close()
        return False

    cursor.execute('''
        UPDATE pet
        SET count = count - 1
        WHERE discord_id = ? AND pet_name = ? AND count > 0
    ''', (user_id, pet_name))

    conn.commit()
    conn.close()

    update_user_networth(user_id, -cost)

    return True


def get_user_networth(user_id: int) -> float:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT networth
        FROM user_networth
        WHERE discord_id = ?
    ''', (user_id,))

    user = cursor.fetchone()

    # Checks if the user exists, otherwise make it 0.
    if user is None:
        cursor.execute('''
        INSERT INTO user_networth (discord_id, networth)
        VALUES (?, ?)
    ''', (user_id, 0))
        networth = 0
        conn.commit()

    else:
        networth = user[0]

    conn.close()

    return networth + get_balance(user_id)


def update_user_networth(user_id: int, amount: float) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    get_user_networth(user_id)

    cursor.execute('''
        UPDATE user_networth
        SET networth = networth + ?
        WHERE discord_id = ?
    ''', (amount, user_id))

    conn.commit()
    conn.close()


def attempt_streak_save(user_id, streak_saver) -> bool:
    user_fortune = get_user_fortune(user_id)
    preserve_chance: float = random.random()
    log_text: str = f'OG: {preserve_chance} '

    # Positive fortune is lucky, negative is unlucky.
    if user_fortune > 0:
        preserve_chance = fortune_roll(user_id,
                                                user_fortune,
                                                preserve_chance,
                                                random.random(),
                                                favor_high=False,
                                                use_fortune=False)
        log_text += f"fortune affected: {preserve_chance}"
    elif user_fortune < 0:
        preserve_chance = fortune_roll(user_id,
                                                user_fortune,
                                                preserve_chance,
                                                random.random(),
                                                favor_high=True,
                                                use_fortune=False)
        log_text += f"fortune affected: {preserve_chance}"
    if preserve_chance <= streak_saver / 100.0:
        logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} streak saver activated {log_text}')
        return True
    logger.info(f'{datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")} streak saver missed {log_text}')
    return False


def toggle_menu_buttons(menu, switch: bool):
    for item in menu.children:
        if isinstance(item, discord.ui.Button):
            item.disabled = switch


def add_transaction_to_history(user_id: int, username: str, type: str, amt: float, balance: float) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO transactions (discord_id, username, type, transaction_amount, balance) VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, type, amt, balance))
    conn.commit()
    conn.close()


def add_transactions_to_history_everyone(credit: float) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO transactions (discord_id, username, type, transaction_amount, balance) VALUES (?, ?, ?, ?, ?)
    ''', (0, "EVERYONE", "give all", credit, credit))

    conn.commit()
    conn.close()


def get_give_transactions_total_last_hour(user_id: int) -> tuple[int, float]:
    conn = get_db_connection()
    cursor = conn.cursor()

    one_hour_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    one_hour_ago_str: str = one_hour_ago.strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        SELECT SUM(transaction_amount) FROM transactions
        WHERE discord_id = ?
        AND type = ?
        AND created_at > ?
    ''', (user_id, "give", one_hour_ago_str))

    transactions = cursor.fetchone()
    conn.close()

    return transactions[0] if transactions[0] is not None else 0


def get_balance_from_one_hour_ago(user_id: int) -> float:
    conn = get_db_connection()
    cursor = conn.cursor()

    one_hour_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    one_hour_ago_str: str = one_hour_ago.strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        SELECT balance FROM transactions
        WHERE discord_id = ?
        AND type = ?
        AND created_at > ?
        ORDER BY created_at ASC
        LIMIT 1
    ''', (user_id, "give", one_hour_ago_str))

    transactions = cursor.fetchone()
    conn.close()

    return transactions[0] if transactions is not None else get_balance(user_id)


def get_user_names_from_id() -> list[int]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT discord_id FROM users WHERE discord_id != 0')
    usernames = cursor.fetchall()
    user_ids: list[int] = []
    for entry in usernames:
        user_ids.append(entry[0])
    
    conn.close()
    return user_ids


def insert_user_name_into_table(discord_id: int, username: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM user_name WHERE discord_id = ?', (discord_id,))
    user_id = cursor.fetchone()
    if user_id is None:
        cursor.execute('INSERT INTO user_name (discord_id, username) VALUES (?, ?)', (discord_id, username))
    elif user_id[1] != username:
        cursor.execute("UPDATE user_name SET username = ? WHERE discord_id = ?", (username, discord_id))
    
    conn.commit()
    conn.close()