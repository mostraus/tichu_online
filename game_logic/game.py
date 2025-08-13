# game_logic/tichu_game.py

import random
from game_logic.card import create_tichu_deck
from game_logic.player import TichuPlayer
from game_logic.combo import Combo


class TichuGame:
    def __init__(self, players):
        assert len(players) == 4, "Tichu requires exactly 4 players."
        self.players = players
        self.assign_teams()
        self.deck = []
        self.pile = []  # center pile of played cards
        self.turn_index = 0
        self.round_number = 1
        self.finished_players = []
        self.current_trick = []     # ist ein dict mit [{"combo": Combo, "player": Player}]
        self.waiting_for_wish = False
        self.wish = None
        self.waiting_for_dragon_choice = False
        self.dragon_winner = None
        self.dragon_possible_recipients = None
        self.team_scores = {"A": 0, "B": 0}
        self.pass_count = 0

    def assign_teams(self):
        # Assign teams A and B alternately
        for i, player in enumerate(self.players):
            player.team = 'A' if i % 2 == 0 else 'B'

    def start_new_round(self):
        # reset game
        self.pass_count = 0
        self.current_trick = []
        self.finished_players = []
        self.deck = create_tichu_deck()
        # reset deck
        random.shuffle(self.deck)
        for player in self.players:
            player.reset_for_new_round()

        # Deal 8 cards first (allow Grand Tichu declaration)
        for _ in range(8):
            for player in self.players:
                player.receive_card(self.deck.pop())

        # (Frontend will allow Grand Tichu calls here)

        # Deal remaining 6 cards
        for _ in range(6):
            for player in self.players:
                player.receive_card(self.deck.pop())

        for player in self.players:
            print(player.hand)

        self.set_starting_player_index()

        # # TODO: (Frontend will allow passing here)
        # You can call self.pass_cards() if logic is implemented

    def set_starting_player_index(self):
        for i,p in enumerate(self.players):
            for c in p.hand:
                print(c.rank)
                if c.rank == 1:
                    print("mah jong found")
                    self.turn_index = i

    def pass_cards(self, pass_dict):
        """
        Expects dict like:
        {
            "Alice": [card1, card2, card3],
            "Bob": [cardA, cardB, cardC],
            ...
        }
        Each player passes 3 cards in order:
        - left (to player on their left)
        - across
        - right
        """
        # Index map for left, across, right
        num_players = len(self.players)
        left = lambda i: (i + 1) % num_players
        across = lambda i: (i + 2) % num_players
        right = lambda i: (i + 3) % num_players

        # Resolve passing
        for i, player in enumerate(self.players):
            cards = pass_dict[player.name]
            if len(cards) != 3:
                raise ValueError(f"{player.name} must pass exactly 3 cards.")
            player.remove_cards(cards)

            self.players[left(i)].receive_card(cards[0])
            self.players[across(i)].receive_card(cards[1])
            self.players[right(i)].receive_card(cards[2])

    def get_current_player(self):
        return self.players[self.turn_index]

    def advance_turn(self):
        if len(self.finished_players) >= len(self.players) - 1:
            return  # Runde ist praktisch vorbei

        while True:
            self.turn_index = (self.turn_index + 1) % len(self.players)
            if self.players[self.turn_index] not in self.finished_players:
                break

    def is_round_over(self):
        return len(self.finished_players) == 3

    def __repr__(self):
        return f"TichuGame(Round {self.round_number})"

    def valid_play(self, cards_to_play):
        combo = Combo(cards_to_play, self)
        if combo.identify_combo_type() == "invalid":
            print("This is not a valid Combo!")
            return False
        else:
            current_player = self.get_current_player()
            if self.wish in [c.name for c in current_player.hand] and self.wish not in [c.name for c in cards_to_play]:
                print("Wish has to be fulfilled!")
                return False
            elif self.current_trick:
                current_combo = self.current_trick[-1]["combo"]
                if combo.rank > current_combo.rank:
                    return True
                else:
                    return False
            else:
                return True

    def get_combo_player(self, combo_obj):
        for item in reversed(self.current_trick):
            if item['combo'] == combo_obj:
                return item['player']

    def calculate_round_points(self):
        round_points = {"A": 0, "B": 0}
        for p in self.players:
            points = sum([c.points for c in p.tricks_won])
            # last players hand goes to first player and their points go to the opposing team
            if p not in self.finished_players:
                round_points[self.finished_players[0].team] += sum([c.points for c in p.hand])
                if p.team == "A":
                    round_points["B"] += points
                else:
                    round_points["A"] += points
            else:
                round_points[p.team] += points
        self.team_scores["A"] += round_points["A"]
        self.team_scores["B"] += round_points["B"]
        return round_points


if __name__ == "__main__":
    game = TichuGame(["Alice", "Bob", "Clara", "David"])
    game.start_new_round()
    for player in game.players:
        print(f"{player.name} ({player.team}): {len(player.hand)} cards")
