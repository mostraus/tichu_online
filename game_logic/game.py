# game_logic/tichu_game.py

import random
from game_logic.card import create_tichu_deck
from game_logic.player import TichuPlayer
from game_logic.combo import Combo
from game_logic.Helpers import card_to_filename, flatten


class TichuGame:
    def __init__(self, players, socketio):
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
        self.socketio = socketio

    def assign_teams(self):
        # Assign teams A and B alternately
        for i, player in enumerate(self.players):
            player.team = 'A' if i % 2 == 0 else 'B'

    def send_hands_to_players(self):
        for p in self.players:
            hand_images = [card_to_filename(card) for card in p.hand]
            self.socketio.emit('update_hand', {'hand': hand_images}, room=p.sid)

    def deal_first_eight(self):
        # Deal 8 cards first (allow Grand Tichu declaration)
        for _ in range(8):
            for p in self.players:
                p.receive_card(self.deck.pop())

        self.send_hands_to_players()
        self.socketio.emit("call_grand_tichu")

    def deal_remaining_cards(self):
        # Deal remaining 6 cards
        for _ in range(6):
            for player in self.players:
                player.receive_card(self.deck.pop())

        for player in self.players:
            print(player.hand)

        self.start_passing_phase()

    def start_passing_phase(self):
        for player in self.players:
            cards_data = [{"id": card.id, "image": "static/cards/" + card_to_filename(card)} for card in player.hand]
            targets = [p.name for p in self.players if p != player]
            self.socketio.emit(
                "start_passing",
                {"cards": cards_data, "targets": targets},
                room=player.sid  # nur an diesen Spieler
            )

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

        self.deal_first_eight()

    def set_starting_player_index(self):
        for i,p in enumerate(self.players):
            for c in p.hand:
                if c.rank == 1:
                    self.turn_index = i

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
        combo_type = combo.identify_combo_type()
        if combo_type == "invalid":
            print("This is not a valid Combo!")
            return False
        else:
            current_player = self.get_current_player()
            if self.wish in [c.name for c in current_player.hand] and self.wish not in [c.name for c in cards_to_play]:
                print("Wish has to be fulfilled!")
                return False
            elif self.current_trick:
                current_combo = self.current_trick[-1]["combo"]
                current_combo_type = current_combo.identify_combo_type()
                if current_combo_type == combo_type:
                    if (current_combo_type in ["pair_sequence", "straight"]) and (len(current_combo.cards) != len(combo.cards)):
                        return False
                    elif combo.rank > current_combo.rank:
                        return True
                    else:
                        return False
                # 4er bomb wins except vs straight bomb, 4er vs 4er is handled above
                if combo_type == "bomb_4kind":
                    if "bomb" not in current_combo_type:
                        return True
                    else:
                        return False
                # straight bomb wins bc straight bomb vs straight bomb is handled above
                if combo_type == "bomb_straight":
                    return True
            else:
                return True

    def get_combo_player(self, combo_obj):
        for item in reversed(self.current_trick):
            if item['combo'] == combo_obj:
                return item['player']

    def calculate_round_points(self):
        round_points = {"A": 0, "B": 0}
        for p in self.players:
            # double win
            if self.finished_players[0].team == self.finished_players[1].team:
                if p.team == self.finished_players[0].team:
                    round_points[p.team] += 100
            # points for cards won
            else:
                points = sum([c.points for c in [trick for trick in p.tricks_won]])
                # last players hand goes to opposing team and their points go to the first player
                if p not in self.finished_players:
                    round_points[self.finished_players[0].team] += points
                    if p.team == "A":
                        round_points["B"] += sum([c.points for c in p.hand])
                    else:
                        round_points["A"] += sum([c.points for c in p.hand])
                else:
                    round_points[p.team] += points
            # points for tichu call
            if p.called_tichu:
                if p == self.finished_players[0]:
                    round_points[p.team] += 100
                else:
                    round_points[p.team] -= 100
            # points for grand tichu call
            if p.called_grand_tichu:
                if p == self.finished_players[0]:
                    round_points[p.team] += 200
                else:
                    round_points[p.team] -= 200
        self.team_scores["A"] += round_points["A"]
        self.team_scores["B"] += round_points["B"]
        return round_points


if __name__ == "__main__":
    game = TichuGame([TichuPlayer(name) for name in ["Alice", "Bob", "Clara", "David"]], None)
    #game.start_new_round()
    game.deck = create_tichu_deck()
    random.shuffle(game.deck)
    game.finished_players += game.players[1:]

    for player in game.players:
        for _ in range(10):
            player.hand.append(game.deck.pop())
        player.add_trick(c for c in player.hand)
        print(player.name, player.team)
        print(player.tricks_won)
    round_points = game.calculate_round_points()
    print(round_points)
