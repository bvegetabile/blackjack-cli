from blackjack.gameutils.deckofcards import DeckOfCards


def test_single_deck_has_52_cards():
    deck = DeckOfCards()
    assert len(deck.cards) == 52


def test_double_deck_has_104_cards():
    deck = DeckOfCards(ndecks=2)
    assert len(deck.cards) == 104


def test_get_card_removes_from_deck():
    deck = DeckOfCards()
    card = deck.get_card()
    assert len(deck.cards) == 51
    assert len(deck.used_cards) == 1
    assert deck.used_cards[0] == card


def test_get_card_from_bottom():
    deck = DeckOfCards()
    last_card = deck.cards[-1]
    card = deck.get_card(from_top=False)
    assert card == last_card


def test_shuffle_changes_order():
    deck1 = DeckOfCards()
    original_order = list(deck1.cards)
    deck1.shuffle()
    # Extremely unlikely to remain identical after shuffle
    assert deck1.cards != original_order


def test_all_unique_cards_in_single_deck():
    deck = DeckOfCards()
    card_strs = [str(c) for c in deck.cards]
    assert len(set(card_strs)) == 52
