from game_logic.card import TichuCard


def card_to_filename(card: TichuCard):
    if card.suit:
        return f"{card.suit}_{card.name}.png"
    else:
        return f"{card.name}.png"


def flatten(xss):
    return [x for xs in xss for x in xs]
