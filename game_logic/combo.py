class Combo:
    def __init__(self, cards, gamemanager):
        self.cards = cards
        self.phoenix = any(card.name.lower() == "phoenix" for card in cards)
        self.contains_dragon = any(card.name.lower() == "dragon" for card in cards)
        self.phoenix_straight_max = False
        self.gamemanager = gamemanager
        self.type = self.identify_combo_type()
        self.rank = self.get_rank()  # Used for comparisons

    def identify_combo_type(self):
        cards = self.cards
        counts = {}

        for card in cards:
            value = card.name
            counts[value] = counts.get(value, 0) + 1

        unique_counts = list(counts.values())

        # === SINGLE and DOG===
        if len(cards) == 1:
            if cards[0].name.lower() == "dog":
                return "dog"
            return "single"

        # === PAIR ===
        if len(cards) == 2:
            if unique_counts == [2]:
                return "pair"
            if self.phoenix and len(counts) == 2:
                return "pair"

        # === TRIPLE ===
        if len(cards) == 3:
            if unique_counts == [3]:
                return "triple"
            if self.phoenix and len(counts) == 2:
                return "triple"

        # === FULL HOUSE ===
        if len(cards) == 5:
            if sorted(unique_counts) == [2, 3]:
                return "full_house"
            if self.phoenix and (sorted(unique_counts) == [1, 2, 2] or sorted(unique_counts) == [1, 1, 3]):
                return "full_house"

        # === FOUR-OF-A-KIND BOMB ===
        if len(cards) == 4 and unique_counts == [4]:
            return "bomb_4kind"

        # === STRAIGHT and STRAIGHT BOMB ===
        if len(cards) >= 5 and self.is_straight(cards):
            same_suit = all(card.suit == cards[0].suit for card in cards)
            if same_suit:
                return "bomb_straight"
            else:
                return "straight"

        return "invalid"

    def is_straight(self, cards):
        try:
            values = [card.rank for card in cards]
        except ValueError:
            print("ValueError!")
            return False

        values = sorted(set(values))
        needed_length = len(cards)

        if len(values) == len(cards) and self.phoenix is False:
            # No Phoenix: standard straight
            return all(values[i+1] == values[i] + 1 for i in range(len(values)-1))

        if self.phoenix and len(values) == needed_length:
            # Phoenix: try all possible places to insert a wildcard to create a straight
            values = values[1:]     # drop phoenix from values (bc has value 0)
            for i in range(min(values), max(values) + 2):
                trial = sorted(values + [i])
                if all(trial[j + 1] == trial[j] + 1 for j in range(len(trial) - 1)):
                    if i == max(values) + 1:
                        self.phoenix_straight_max = True
                    return True

        return False

    def get_rank(self):
        if self.type == "single":
            if self.phoenix:
                if self.gamemanager.current_trick:
                    prev_rank = self.gamemanager.current_trick[-1]["combo"].rank
                    rank = min(prev_rank + 0.5, 14.5)
                    print(prev_rank, rank)
                    return rank
                else:
                    return 1.5
            return self.cards[0].rank
        if self.type in ["pair", "triple"]:
            if self.cards[0].name.lower() != "phoenix":
                return self.cards[0].rank
            else:
                return self.cards[1].rank
        elif self.type == "bomb_4kind":
            return self.cards[0].rank
        elif self.type == "full_house":
            counts = {}
            for c in self.cards:
                counts[c.rank] = counts.get(c.rank, 0) + 1
            temp_max_val = 0
            for rank, count in counts.items():
                if count == 3:
                    return rank
                if self.phoenix and count == 2:
                    temp_max_val = max(temp_max_val, rank)
            return temp_max_val
        elif self.type == "straight" or self.type == "bomb_straight":
            if self.phoenix_straight_max:
                return 100 * len(self.cards) + max(c.rank for c in self.cards) + 1
            return 100 * len(self.cards) + max(c.rank for c in self.cards)
        return -1  # Invalid combos

    def __repr__(self):
        if self.type in ["single", "pair", "triple", "bomb_4kind", "full_house"]:
            out = f"{self.type} of {self.rank}s"
        elif self.type in ["straight", "bomb_straight"]:
            out = f"{str(self.rank)[0]}er {self.type} to {self.rank % 100}"
        else:
            out = self.type
        return out
