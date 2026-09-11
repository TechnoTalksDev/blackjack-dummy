import random
from enum import Enum

class Deck:
    def __init__(self, cards=None, auto_shuffle=False):
        if cards is not None:
            self.cards = cards
        else:
            self.cards = [i for i in range(1, 53)]
            self.shuffle()
        self._discarded = []
        
    def get(self):
        return self.cards
    def shuffle(self):
        random.shuffle(self.cards)
    def deal(self, count:int):
        cards = []
        try:
            for _ in range(count):
                card = self.cards[0]
                self.cards.pop(0)
                self._discarded.append(card)
                cards.append(card)
            return cards
        except IndexError:
            if self.auto_shuffle:
                print("Deck is empty, reshuffling...")
                self.cards = self._discarded
                self._discarded = []
                self.shuffle()
                return self.deal(count)
            else:
                return None



class Hand:
    def __init__(self, cards):
        self.cards = cards
    def __len__(self):
        return len(self.cards)
    def get(self):
        return self.cards
    def set(self, cards):
        self.cards = cards
    def add(self, card):
        self.cards.append(card)
    def clear(self):
        self.cards = []
    def score(self):
        score = 0 
        for card in self.cards:
            card = ((card-1) % 13) + 1
            if card == 1:
                score += 11
            elif card > 10:
                score += 10
            else:
                score += card
        if score > 21:
            for card in self.cards:
                card = ((card-1) % 13) + 1
                if card == 1:
                    score -= 10
                if score <= 21:
                    break
        return score

class BjResult(Enum):
    PLAYER_BUST = 0
    DEALER_BUST = 1
    PLAYER_WIN = 2
    DEALER_WIN = 3
    PLAYER_BLACKJACK = 4
    DEALER_BLACKJACK = 5
    TIE = 6
    
class BjState(Enum):
    PLAYER_TURN = 1
    DEALER_TURN = 2
    COMPLETE = 3

class BjAction(Enum):
    HIT = 0
    STAND = 1

class Blackjack:
    def __init__(self, deck: Deck):
        self.deck = deck
        self.dealer_hand = Hand([])
        self.player_hand = Hand([])
        self.state = BjState.PLAYER_TURN
        self.result = None
        self._deal()
    
    def _deal(self):
        self.dealer_hand.set(self.deck.deal(2))
        self.player_hand.set(self.deck.deal(2))
        if self.player_hand.score() == 21 and self.dealer_hand.score() != 21:
            self.state = BjState.COMPLETE
            self.result = BjResult.PLAYER_BLACKJACK
        elif self.dealer_hand.score() == 21 and self.player_hand.score() == 21:
            self.state = BjState.COMPLETE
            self.result = BjResult.TIE
    
    def get_player_hand(self):
        return self.player_hand.get()
    
    def get_dealer_hand(self):
        if self.state == BjState.PLAYER_TURN:
            return [self.dealer_hand.get()[0]]
        else:
            return self.dealer_hand.get()
    def _dealer_turn(self):
        if self.dealer_hand.score() == 21:
            self.state = BjState.COMPLETE
            self.result = BjResult.DEALER_BLACKJACK
            return self.result
        while self.dealer_hand.score() < 17:
            self.dealer_hand.add(self.deck.deal(1)[0])
        self.state = BjState.COMPLETE
        if self.dealer_hand.score() > 21:
            self.result = BjResult.DEALER_BUST
            return self.result
        elif self.player_hand.score() > self.dealer_hand.score():
            self.result = BjResult.PLAYER_WIN
            return self.result
        elif self.player_hand.score() < self.dealer_hand.score():
            self.result = BjResult.DEALER_WIN
            return self.result
        else:
            self.result = BjResult.TIE
            return self.result
    
    def turn(self, action:BjAction):
        if self.state == BjState.PLAYER_TURN:
            if action == BjAction.HIT:
                self.player_hand.add(self.deck.deal(1)[0])
                if self.player_hand.score() > 21:
                    self.state = BjState.COMPLETE
                    self.result = BjResult.PLAYER_BUST
                    return self.result
            elif action == BjAction.STAND:
                self.state = BjState.DEALER_TURN
                return self._dealer_turn()
            else:
                raise ValueError("Invalid BjAction")
        elif self.state == BjState.DEALER_TURN:
            return self._dealer_turn()
        else:
            return self.result
        
    
suits = ["Spades", "Diamonds", "Clubs", "Hearts"]
ranks = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]
        
        
def convert_index_to_card(index, show_suits=False):
    suit = (index - 1) // 13
    rank = (index - 1) % 13 + 1
    
    if show_suits:
        final = f"{ranks[rank - 1]} of {suits[suit]}"
    else:
        final = f"{ranks[rank - 1]}"
    return final

def convert_hand_to_string(hand):    
    return ', '.join(convert_index_to_card(card) for card in hand)
   
def human_game():
    deck = Deck()
    game = Blackjack(deck)
    
    print("Dealer hand:", convert_hand_to_string(game.get_dealer_hand()))
    print("Player hand:", convert_hand_to_string(game.get_player_hand()))
    
    if game.result == BjResult.PLAYER_BLACKJACK:
        print("Player has blackjack! Player wins!")

    if game.result == BjResult.DEALER_BLACKJACK:
        print("Dealer has blackjack! Dealer wins!")

    while game.state != BjState.COMPLETE:
        action = input("Enter 'h' to hit or 's' to stand: ")
        if action == 'h':
            result = game.turn(BjAction.HIT)
            print("Player hand:", convert_hand_to_string(game.get_player_hand()))
            if result == BjResult.PLAYER_BUST:
                print("Player busts! Dealer wins.")
                break
        elif action == 's':
            result = game.turn(BjAction.STAND)
            print("Dealer hand:", convert_hand_to_string(game.get_dealer_hand()))
            if result == BjResult.DEALER_BUST:
                print("Dealer busts! Player wins.")
                break
            elif result == BjResult.PLAYER_WIN:
                print("Player wins!")
                break
            elif result == BjResult.DEALER_WIN:
                print("Dealer wins!")
                break
            elif result == BjResult.PLAYER_BLACKJACK:
                print("Player has blackjack! Player wins!")
                break
            elif result == BjResult.DEALER_BLACKJACK:
                print("Dealer has blackjack! Dealer wins!")
                break
            elif result == BjResult.TIE:
                print("It's a tie!")
                break
        else:
            print("Invalid input. Please enter 'h' or 's'.")        

def train_bot():
    """_summary_
    
    https://docs.pytorch.org/tutorials/intermediate/reinforcement_q_learning.html
    
    """
    
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    deck = Deck(auto_shuffle=True)  
    while True:
        pass

def main():
    print("Hello from blackjack-dummy!")

    # human_game()
    
    train_bot()

        


if __name__ == "__main__":
    main()
