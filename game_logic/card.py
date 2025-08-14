# game_logic/card.py

class TichuCard:
    def __init__(self, name, suit=None, rank=None, points=0):
        self.name = name  # "2", "A", "Dragon", etc.
        self.suit = suit  # "black", "green", "blue", "red", or None
        self.rank = rank  # 2-14 for standard, custom for specials
        self.points = points  # Used for scoring
        if self.suit:
            self.id = self.name + "_" + self.suit
        else:
            self.id = self.name

    def __repr__(self):
        return f"{self.name} of {self.suit}" if self.suit else self.name

    def __lt__(self, other):
        return self.rank < other.rank


def create_tichu_deck():
    suits = ["spades", "diamonds", "hearts", "clubs"]  # TODO: should be "black", "green", "blue", "red", or None
    names = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    rank_map = {name: i+2 for i, name in enumerate(names)}
    point_map = {"5": 5, "10": 10, "K": 10}

    deck = []

    # Standard cards
    for suit in suits:
        for name in names:
            deck.append(TichuCard(name=name, suit=suit, rank=rank_map[name], points=point_map.get(name, 0)))

    # Special cards
    deck.append(TichuCard("Mah Jong", rank=1, points=0))
    deck.append(TichuCard("Dog", rank=-1, points=0))
    deck.append(TichuCard("Phoenix", rank=0, points=-25))   # special handling
    deck.append(TichuCard("Dragon", rank=15, points=25))   # highest

    return deck


# Test run
if __name__ == "__main__":
    deck = create_tichu_deck()
    print(f"Total cards: {len(deck)}")
    for card in deck:
        print(card)
