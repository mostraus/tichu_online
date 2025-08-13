from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from game_logic.player import TichuPlayer
from game_logic.game import TichuGame
from game_logic.card import TichuCard
from game_logic.combo import Combo
import traceback

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tichu-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

players = []
sid_to_player = {}
sid_order = []
game = None


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('join')
def handle_join(data):
    global game
    name = data['name']
    sid = request.sid
    print(f"{name} joined with SID: {sid}")

    if sid in sid_to_player:
        return

    player = TichuPlayer(name, sid)
    players.append(player)
    sid_to_player[sid] = player
    print(sid_to_player)
    sid_order.append(sid)

    socketio.emit('game_message', {'message': f"{name} has joined."})

    if len(players) == 4:
        start_game()


def start_game():
    global game
    game = TichuGame(players)
    game.start_new_round()

    # Send initial hands to each player
    send_hands_to_players()

    socketio.emit('game_message', {'message': "All cards have been dealt. Begin passing phase."})

    # TODO: initiate pass phase

    current_player = game.get_current_player()
    for player in game.players:
        sid = player.sid
        socketio.emit("turn_update", {
            "current": current_player.name,
            "you": player.name
        }, room=sid)


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    player = sid_to_player.get(sid)
    if player:
        print(f"{player.name} disconnected.")
        players.remove(player)
        del sid_to_player[sid]
        sid_order.remove(sid)
        socketio.emit('game_message', {'message': f"{player.name} has left the game."})


def send_hands_to_players():
    global game
    for player in game.players:
        hand_images = [card_to_filename(card) for card in player.hand]
        socketio.emit('update_hand', {'hand': hand_images}, room=player.sid)


def card_to_filename(card: TichuCard):
    if card.suit:
        return f"{card.suit}_{card.name}.png"
    else:
        return f"{card.name}.png"


@socketio.on('play_card')
def handle_play_card(data):
    sid = request.sid
    player = sid_to_player.get(sid)
    if not player:
        emit('error_message', {'message': 'Player not found.'})
        return
    if game.get_current_player() != player:
        emit('error_message', {'message': "Not your turn!"})
        return

    if player in game.finished_players:
        emit('error_message', {'message': "You are finished already!"})
        game.advance_turn()
        return

    game.pass_count = 0  # sobald jemand spielt, werden Pässe zurückgesetzt

    card_filenames = data.get('cards', [])
    try:
        cards = filenames_to_cards(card_filenames, player.hand)

        if not game.valid_play(cards):
            emit('error_message', {'message': 'Invalid play!'})
            return

        if any(c.name.lower() == "mah jong" for c in cards):
            game.waiting_for_wish = True
            socketio.emit("ask_wish", room=player.sid)

        if any(c.name.lower() == "dog" for c in cards):
            partner = [p for p in game.players if p.team == player.team and p != player][0]
            # game.turn_index = game.players.index(partner)
            game.advance_turn()
            game.advance_turn()
            # TODO: das muss noch ordentlich implementiert werden
            socketio.emit('game_message', {'message': f"{player.name} plays the Dog! Turn goes to {partner.name}."})
            player.remove_cards(cards)
            current = game.get_current_player()
            socketio.emit('turn_update', {'current': current.name, "you": player.name}, room=sid)
            return

        player.remove_cards(cards)
        game.current_trick.append({'combo': Combo(cards, game), 'player': player})
        if len(player.hand) == 0:
            game.finished_players.append(player)
            if len(game.finished_players) >= len(game.players) - 1:
                round_points = game.calculate_round_points()
                socketio.emit('round_over', {"scores": game.team_scores, "round_points": round_points})
                return

        # Broadcast the played cards to all
        image_filenames = [card_to_filename(c) for c in cards]
        socketio.emit('last_played', {'cards': image_filenames})
        if len(cards) == 1 and cards[0].name.lower() == "phoenix":
            rank = game.current_trick[-1]["combo"].rank
            socketio.emit('game_message', {'message': f"Phoenix was played as single with rank: {rank}"})

        send_hands_to_players()  # Update everyone’s hand
        game.advance_turn()
        current = game.get_current_player()
        for player in game.players:
            sid = player.sid
            socketio.emit('turn_update', {'current': current.name, "you": player.name}, room=sid)

    except Exception as e:
        traceback.print_exc()
        emit('error_message', {'message': str(e)})


def filenames_to_cards(filenames, hand):
    matched_cards = []
    for filename in filenames:
        name = filename.replace(".png", "")
        if "_" in name:
            suit, card_name = name.split("_")
        else:
            suit = None
            card_name = name
        # Suche passende Karte im Hand-Objekt
        for card in hand:
            if card.name == card_name and card.suit == suit:
                matched_cards.append(card)
                break
        else:
            raise ValueError(f"Card {filename} not found in hand.")
    return matched_cards


@socketio.on('pass')
def handle_pass():
    global game

    sid = request.sid
    player = sid_to_player.get(sid)
    if not player:
        emit('error_message', {'message': 'Player not found.'})
        return

    if game.get_current_player() != player:
        emit('error_message', {'message': "Not your turn!"})
        return

    if not game or not game.current_trick:
        emit('error_message', {'message': 'Nothing to pass on yet.'})
        return

    game.pass_count += 1
    socketio.emit('game_message', {'message': f"{player.name} has passed."})

    if game.pass_count >= 4:
        # Trick endet, letzter Spieler gewinnt
        winning_combo = game.current_trick[-1]["combo"]
        winner = game.current_trick[-1]["player"]
        socketio.emit('game_message', {'message': f"{winner.name} wins the trick with {winning_combo}."})

        if winning_combo.contains_dragon:
            game.dragon_possible_recipients = [p.name for p in game.players if p.team != winner.team]
            game.waiting_for_dragon_choice = True
            game.dragon_winner = winner
            socketio.emit("choose_dragon_recipient", {"recipients": game.dragon_possible_recipients}, room=winner.sid)
            return
        else:
            winner.add_trick([card for card in [trick["combo"].cards for trick in game.current_trick]])
        game.current_trick = []
        game.pass_count = 0

        game.turn_index = game.players.index(winner)  # Winner spielt weiter
        socketio.emit('turn_message', {'message': f"{winner.name} starts next trick."})
    else:
        game.advance_turn()
        current = game.get_current_player()
        for player in game.players:
            sid = player.sid
            socketio.emit('turn_update', {'current': current.name, "you": player.name}, room=sid)


@socketio.on('wish_card')
def handle_wish(data):
    wish = data['wish']
    if wish == "None":
        game.waiting_for_wish = False
        socketio.emit('game_message', {'message': "Nothing was wished for."})
        return
    game.wish = wish
    game.waiting_for_wish = False
    socketio.emit('game_message', {'message': f"Wish for {data['wish']}."})


@socketio.on('dragon_recipient_selected')
def handle_dragon_recipient_selected(data):
    recipient_name = data.get('recipient')
    winner = getattr(game, 'dragon_winner', None)
    if not winner:
        return

    recipient = next((p for p in game.dragon_possible_recipients if p == recipient_name), None)     # p is the name
    if not recipient:
        emit('error_message', {'message': 'Invalid recipient'})
        return

    # Stich geben
    for p in game.players:
        if p.name == recipient_name:
            p.add_trick(
                [card for trick in game.current_trick for card in trick["combo"].cards]
            )
            socketio.emit('game_message', {'message': f"{winner.name} gives the Dragon trick to {p.name}."})

    # Aufräumen
    game.waiting_for_dragon_choice = False
    game.dragon_winner = None
    game.dragon_possible_recipients = None

    # Nächste Runde starten
    game.current_trick = []
    game.pass_count = 0
    game.turn_index = game.players.index(winner)  # Winner spielt weiter
    socketio.emit('turn_message', {'message': f"{winner.name} starts next trick."})


ready_players = set()


@socketio.on("ready_for_next_round")
def handle_ready():
    sid = request.sid
    player = sid_to_player[sid]
    ready_players.add(player)

    if len(ready_players) == len(game.players):
        ready_players.clear()
        game.start_new_round()
        send_hands_to_players()
        socketio.emit("game_message", {"message": f"Runde {game.round_number} beginnt!"})


if __name__ == '__main__':
    socketio.run(app, host='localhost', port=5000)
