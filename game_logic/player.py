# game_logic/tichu_player.py

class TichuPlayer:
    def __init__(self, name, sid=None, team=None):
        self.name = name
        self.team = team  # 'A' or 'B'
        self.hand = []  # List of TichuCard objects
        self.tricks_won = []  # List of cards won in tricks
        self.called_tichu = False
        self.called_grand_tichu = False
        self.finished = False  # True if player is out of cards
        self.sid = sid

    def receive_card(self, card):
        self.hand.append(card)
        self.hand.sort()

    def remove_cards(self, cards):
        for card in cards:
            if card in self.hand:
                self.hand.remove(card)
            else:
                raise ValueError(f"{card} not in hand!")

    def has_card(self, card):
        return card in self.hand

    def get_passable_cards(self):
        """Called at the start of a round to pass 3 cards."""
        # You can replace this with interactive or frontend logic
        return self.hand[:3]  # Default: pass first 3 (for now)

    def add_trick(self, cards):
        self.tricks_won.extend(cards)

    def calculate_points(self):
        return sum(card.points for card in self.tricks_won)

    def reset_for_new_round(self):
        self.hand.clear()
        self.tricks_won.clear()
        self.called_tichu = False
        self.called_grand_tichu = False
        self.finished = False

    def __repr__(self):
        return f"{self.name} (Team {self.team})"

if __name__ == "__main__":
    from card import create_tichu_deck

    p = TichuPlayer("Alice", team="A")
    deck = create_tichu_deck()

    for _ in range(14):
        p.receive_card(deck.pop())

    print(f"{p.name}'s hand:")
    print(p.hand)

    cards_won = [deck.pop(), deck.pop(), deck.pop(), deck.pop(), deck.pop()]
    p.add_trick(cards_won)
    print(f"{p.name}'s trick points: {p.calculate_points()} with cards: {cards_won}")
