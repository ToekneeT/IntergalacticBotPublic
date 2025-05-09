

class Card:
    def __init__(self, suit, name, value):
        self.suit = suit
        self.name = name  # Name of card, i.e. Ace, King, Queen, etc.
        self.value = value  # Numerical value.


suits = ["Spades", "Hearts", "Clubs", "Diamonds"]

suit_value = {
    "Spades": "\u2664",
    "Hearts": "\u2661",
    "Clubs": "\u2667",
    "Diamonds": "\u2662"}

cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "K", "Q"]

card_value_bj = {
    "A": 11,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "K": 10,
    "Q": 10}


card_value_cwar = {
    "A": 14,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 11,
    "K": 12,
    "Q": 13}


# def generate_deck(suits, suit_value, cards, card_value, size):
#     deck = []
#     for i in range(int(size)):
#         for suit in suits:
#             for card in cards:
#                 deck.append(Card(suit_value[suit], card, card_value[card]))

#     return deck

def generate_deck_bj(size):
    deck = []
    for idx in range(int(size)):
        for suit in suits:
            for card in cards:
                deck.append(Card(suit_value[suit], card, card_value_bj[card]))

    return deck


def generate_deck_cwar(size):
    deck = []
    for idx in range(int(size)):
        for suit in suits:
            for card in cards:
                deck.append(Card(suit_value[suit], card, card_value_cwar[card]))

    return deck