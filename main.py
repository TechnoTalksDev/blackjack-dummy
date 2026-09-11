import random
import math
import time
from datetime import timedelta

from enum import Enum
from collections import namedtuple, deque
from itertools import count

import matplotlib
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

#device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
device = torch.device("cpu")  # Force CPU usage for compatibility

class Deck:
    def __init__(self, cards=None, auto_shuffle=False):
        if cards is not None:
            self.cards = cards
        else:
            self.cards = [i for i in range(1, 53)]
            self.shuffle()
        self._discarded = []
        self.auto_shuffle = auto_shuffle

    def get(self):
        return self.cards

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, count: int):
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
                # print("Deck is empty, reshuffling...")
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

    def ace(self):
        for card in self.cards:
            card = ((card - 1) % 13) + 1
            if card == 1:
                return True
        return False
    
    def usable_ace(self):
        total = 0
        aces = 0
        for card in self.cards:
            rank = ((card - 1) % 13) + 1
            if rank == 1:
                aces += 1
                total += 1
            else:
                total += min(rank, 10)
        return aces > 0 and total + 10 <= 21

    def score(self):
        score = 0
        for card in self.cards:
            card = ((card - 1) % 13) + 1
            if card == 1:
                score += 11
            elif card > 10:
                score += 10
            else:
                score += card
        if score > 21:
            for card in self.cards:
                card = ((card - 1) % 13) + 1
                if card == 1:
                    score -= 10
                if score <= 21:
                    break
        return score


def get_hand_value(hand):
    score = 0
    for card in hand:
        card = ((card - 1) % 13) + 1
        if card == 1:
            score += 11
        elif card > 10:
            score += 10
        else:
            score += card
    if score > 21:
        for card in hand:
            card = ((card - 1) % 13) + 1
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

def calculate_reward(result: BjResult):
    """
    rewarded outcomes:
    - PLAYER_WIN
    - DEALER_BUST
    - TIE

    punished outcomes:
    - PLAYER_BUST
    - DEALER_WIN
    - DEALER_BLACKJACK

    rewards:
    - +1 win, -1 loss, 0 push (tie)
    """
    if result == BjResult.PLAYER_WIN or result == BjResult.DEALER_BUST:
        return 1.0
    elif result == BjResult.PLAYER_BUST or result == BjResult.DEALER_WIN:
        return -1.0
    elif result == BjResult.TIE:
        return 0.0
    else:
        return 0.0

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
        elif self.dealer_hand.score() == 21 and self.player_hand.score() != 21:
            self.state = BjState.COMPLETE
            self.result = BjResult.DEALER_BLACKJACK
        elif self.dealer_hand.score() == 21 and self.player_hand.score() == 21:
            self.state = BjState.COMPLETE
            self.result = BjResult.TIE

    def get_player_hand(self):
        return self.player_hand.get()

    def get_data(self):
        """
        Returns a tuple of the following data:
        - player hand score
        - dealer hand score
        - ace in player hand bool
        - ace in dealer hand bool
        """

        return (
            self.player_hand.score(),
            get_hand_value(self.get_dealer_hand()),
            self.player_hand.usable_ace(),
            Hand(self.get_dealer_hand()).ace(),
        )

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

    def turn(self, action: BjAction):
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
    return ", ".join(convert_index_to_card(card) for card in hand)


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
        if action == "h":
            result = game.turn(BjAction.HIT)
            print("Player hand:", convert_hand_to_string(game.get_player_hand()))
            if result == BjResult.PLAYER_BUST:
                print("Player busts! Dealer wins.")
                break
        elif action == "s":
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


Transition = namedtuple("Transition", ("state", "action", "next_state", "reward"))


class ReplayMemory(object):
    def __init__(self, capacity):
        self.memory = deque([], maxlen=capacity)

    def push(self, *args):
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)

class DQN(nn.Module):
    def __init__(self, n_observations, n_actions):
        super(DQN, self).__init__()
        self.layer1 = nn.Linear(n_observations, 128)
        self.layer2 = nn.Linear(128, 128)
        self.layer3 = nn.Linear(128, n_actions)
    
    def forward(self, x):
        x = F.relu(self.layer1(x))
        x = F.relu(self.layer2(x))
        return self.layer3(x)




BATCH_SIZE = 128
GAMMA = 0.99
EPS_START = .9
EPS_END = .01
EPS_DECAY = 3000
TAU = .005
LR = 3e-4

# number of actions: hit or stand
n_actions = len(BjAction)
# number of observations: player hand score, dealer hand score, ace in player hand, ace in dealer hand
n_observations = 4

policy_net = DQN(n_observations, n_actions).to(device)
target_net = DQN(n_observations, n_actions).to(device)
target_net.load_state_dict(policy_net.state_dict())

optimizer = optim.AdamW(policy_net.parameters(), lr=LR, amsgrad=True)
memory = ReplayMemory(10000)

steps_done = 0

def select_action(state):
    global steps_done
    sample = random.random()
    eps_threshold = EPS_END + (EPS_START - EPS_END) * \
        math.exp(-1. * steps_done / EPS_DECAY)
    steps_done += 1
    if sample > eps_threshold:
        with torch.no_grad():
            return policy_net(state).max(1).indices.view(1, 1)
    else:
        random_action = random.choice(list(BjAction)).value
        return torch.tensor([[random_action]], device = device, dtype=torch.long)

def select_greedy_action(state):
    with torch.no_grad():
        return policy_net(state).max(1).indices.view(1, 1)

episode_durations = []
episode_rewards = []
episode_results = []

WIN_RESULTS = {
    BjResult.PLAYER_WIN,
    BjResult.DEALER_BUST,
}

LOSS_RESULTS = {
    BjResult.PLAYER_BUST,
    BjResult.DEALER_WIN,
}

def plot_durations(show_result=False):
    plt.figure(1)
    durations_t = torch.tensor(episode_durations, dtype=torch.float)
    
    if show_result:
        plt.title('Result')
    else:
        plt.clf()
        plt.title('Training...')
    
    plt.xlabel('Episode')
    plt.ylabel('Duration')
    plt.plot(durations_t.numpy())
    
    if len(durations_t) >= 100:
        means = durations_t.unfold(0, 100, 1).mean(1).view(-1)
        means = torch.cat((torch.zeros(99), means))
        plt.plot(means.numpy())
    
    plt.pause(0.001)
    
def plot_win_rate(show_result=False, window=100):
    if not episode_results:
        return
    
    
    win_values = torch.tensor(
        [
            float(result in WIN_RESULTS)
            for result in episode_results
        ],
        dtype=torch.float32
    )
    
    episode_numbers = torch.arange(1, len(win_values)+1, dtype=torch.float32)
    
    cumulative_win_rate = (win_values.cumsum(0) / episode_numbers)
    
    plt.figure(2)
    plt.clf()
    
    if show_result:
        plt.title('Final Win Rate')
    else:
        plt.title('Training Win Rate')
        
    plt.xlabel("Episode")
    plt.ylabel('Win Rate')
    plt.ylim(0.0, 1.0)
    plt.plot(episode_numbers.numpy(), cumulative_win_rate.numpy(), label='Cumulative Win Rate')
    
    if len(win_values) >= window:
        rolling_win_rate = (win_values.unfold(0, window, 1).mean(1))
        
        rolling_episode_numbers = episode_numbers[window-1:]
        
        plt.plot(rolling_episode_numbers.numpy(), rolling_win_rate.numpy(), label=f'Rolling Win Rate (window={window})')
    
    plt.legend()
    plt.pause(0.001)

def print_summary():
    total_episodes = len(episode_results)

    if total_episodes == 0:
        print("No episode statistics available.")
        return

    wins = sum(
        result in WIN_RESULTS
        for result in episode_results
    )

    losses = sum(
        result in LOSS_RESULTS
        for result in episode_results
    )

    ties = sum(
        result == BjResult.TIE
        for result in episode_results
    )

    average_reward = (
        sum(episode_rewards) / len(episode_rewards)
    )

    average_duration = (
        sum(episode_durations) / len(episode_durations)
    )

    print("\nTraining Summary")
    print("----------------")
    print(f"Episodes:          {total_episodes}")
    print(f"Wins:              {wins}")
    print(f"Losses:            {losses}")
    print(f"Ties:              {ties}")
    print(f"Win rate:          {wins / total_episodes:.2%}")
    print(f"Loss rate:         {losses / total_episodes:.2%}")
    print(f"Tie rate:          {ties / total_episodes:.2%}")
    print(f"Average reward:    {average_reward:.3f}")
    print(f"Average duration:  {average_duration:.2f} actions")

def evaluate_bot(num_episodes=1000):
    policy_net.eval()

    results = []
    deck = Deck(auto_shuffle=True)

    for _ in range(num_episodes):
        game = Blackjack(deck)

        # Match training behavior by excluding natural blackjacks.
        while game.state == BjState.COMPLETE:
            game = Blackjack(deck)

        state = torch.tensor(
            game.get_data(),
            device=device,
            dtype=torch.float32,
        ).unsqueeze(0)

        for _ in count():
            action = select_greedy_action(state)
            result = game.turn(BjAction(action.item()))

            if result is not None:
                results.append(result)
                break

            state = torch.tensor(
                [game.get_data()],
                device=device,
                dtype=torch.float32,
            )

    policy_net.train()



    wins = sum(result in WIN_RESULTS for result in results)
    losses = sum(result in LOSS_RESULTS for result in results)
    ties = sum(result == BjResult.TIE for result in results)

    total = len(results)

    print("\nEvaluation Summary")
    print("------------------")
    print(f"Episodes:   {total}")
    print(f"Wins:       {wins}")
    print(f"Losses:     {losses}")
    print(f"Ties:       {ties}")
    print(f"Win rate:   {wins / total:.2%}")
    print(f"Loss rate:  {losses / total:.2%}")
    print(f"Tie rate:   {ties / total:.2%}")

def optimize_model():
    if len(memory) < BATCH_SIZE:
        return
    transitions = memory.sample(BATCH_SIZE)
    batch = Transition(*zip(*transitions))

    non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
                                            batch.next_state)), device=device, dtype=torch.bool)
    non_final_next_states = [s for s in batch.next_state
                                        if s is not None]
    state_batch = torch.cat(batch.state)
    action_batch = torch.cat(batch.action)
    reward_batch = torch.cat(batch.reward)

    state_action_values = policy_net(state_batch).gather(1, action_batch)

    next_state_values = torch.zeros(BATCH_SIZE, device=device)
    
    if non_final_next_states:
        with torch.no_grad():
            next_state_values[non_final_mask] = (target_net(torch.cat(non_final_next_states)).max(1).values)

    expected_state_action_values = (next_state_values * GAMMA) + reward_batch

    criterion = nn.SmoothL1Loss()
    loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))

    optimizer.zero_grad()
    loss.backward()

    torch.nn.utils.clip_grad_value_(policy_net.parameters(), 100)
    optimizer.step()

def train_bot():
    global num_episodes, policy_net, target_net, optimizer, memory, steps_done, episode_durations, episode_rewards, episode_results
    """_summary_

    https://docs.pytorch.org/tutorials/intermediate/reinforcement_q_learning.html

    input nodes:
    - player hand score int
    - dealer hand score int
    - ace in player hand bool
    - ace in dealer hand bool

    additional input nodes that could be added later:
    - number of cards in player hand int
    - number of cards left in deck

    output nodes:
    - hit
    - stand

    rewarded outcomes:
    - PLAYER_WIN
    - DEALER_BUST
    - TIE

    punished outcomes:
    - PLAYER_BUST
    - DEALER_WIN
    - DEALER_BLACKJACK

    rewards:
    - +1 win, -1 loss, 0 push (tie)

    using a Q learning neural network

    """

    deck = Deck(auto_shuffle=True)

    if torch.cuda.is_available():
        print("Using GPU")
        num_episodes = 20000
    else:
        print("Using CPU")
        num_episodes = 50
    
    for i_episode in range(num_episodes):
        
        game = Blackjack(deck)
        while game.state == BjState.COMPLETE:
            game = Blackjack(deck)
        
        state = torch.tensor(game.get_data(), device=device, dtype=torch.float32).unsqueeze(0)
        
        episode_reward = 0.0
        
        for t in count():
            action = select_action(state)
            result = game.turn(BjAction(action.item()))

            if result is not None:
                reward_value = calculate_reward(result)
                next_state = None
            else:
                reward_value = 0.0
                next_state = torch.tensor([game.get_data()], device=device, dtype=torch.float32)

            reward = torch.tensor([reward_value], device=device, dtype=torch.float32)
            
            episode_reward += reward_value
            
            memory.push(state, action, next_state, reward)

            state = next_state

            optimize_model()
            
            target_net_state_dict = target_net.state_dict()
            policy_net_state_dict = policy_net.state_dict()
            
            for key in policy_net_state_dict:
                target_net_state_dict[key] = policy_net_state_dict[key] * TAU + target_net_state_dict[key] * (1 - TAU)
            
            target_net.load_state_dict(target_net_state_dict)
            
            if result is not None:
                episode_rewards.append(episode_reward)
                episode_results.append(result)
                episode_durations.append(t + 1)
                
                wins = sum(result in WIN_RESULTS for result in episode_results)
                rate = wins / len(episode_results)
                
                if (i_episode + 1) % 100 == 0 or i_episode == num_episodes - 1:
                    print(f"Episode {i_episode+1}/{num_episodes} finished after {t+1} actions. Result: {result.name}. Reward: {episode_reward:.2f}. Win rate: {rate:.2%}")
                
                #plot_win_rate() # removed for performance reasons
                break

    print("Training complete")
    print_summary()


def main():
    print("Hello from blackjack-dummy!")
    training_start_time = time.time()
    
    train_bot()
    print(f"Training time: {str(timedelta(seconds=(time.time()-training_start_time)))}")
    
    evaluation_start_time = time.time()
    evaluate_bot(num_episodes=1000)
    print(f"Evaluation time: {str(timedelta(seconds=(time.time()-evaluation_start_time)))}")
    
    plot_win_rate(show_result=True)
    
    plt.ioff()
    plt.show()


if __name__ == "__main__":
    main()
