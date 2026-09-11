import unittest

from main import Blackjack, BjAction, BjResult, BjState, Deck


class TestBlackjack(unittest.TestCase):
    def make_game(self, cards):
        """Create a round with a predictable deal order.

        Blackjack deals the first two cards to the dealer, the next two
        cards to the player, and then consumes any remaining cards on hits.
        """
        return Blackjack(Deck(cards.copy()))

    def test_initial_deal_gives_two_cards_to_each_hand(self):
        game = self.make_game([2, 3, 4, 5])

        self.assertEqual(game.get_dealer_hand(), [2])
        self.assertEqual(game.get_player_hand(), [4, 5])
        self.assertEqual(game.state, BjState.PLAYER_TURN)
        self.assertIsNone(game.result)

    def test_dealer_hole_card_is_hidden_during_player_turn(self):
        game = self.make_game([2, 3, 4, 5])

        self.assertEqual(game.get_dealer_hand(), [2])

    def test_dealer_hand_is_revealed_after_player_stands(self):
        game = self.make_game([10, 7, 10, 8])

        game.turn(BjAction.STAND)

        self.assertEqual(game.get_dealer_hand(), [10, 7])

    def test_non_busting_hit_keeps_player_turn_active(self):
        game = self.make_game([2, 3, 4, 5, 6])

        result = game.turn(BjAction.HIT)

        self.assertIsNone(result)
        self.assertEqual(game.get_player_hand(), [4, 5, 6])
        self.assertEqual(game.player_hand.score(), 15)
        self.assertEqual(game.state, BjState.PLAYER_TURN)
        self.assertIsNone(game.result)

    def test_player_bust_completes_round(self):
        game = self.make_game([2, 3, 10, 9, 5])

        result = game.turn(BjAction.HIT)

        self.assertEqual(result, BjResult.PLAYER_BUST)
        self.assertEqual(game.result, BjResult.PLAYER_BUST)
        self.assertEqual(game.state, BjState.COMPLETE)
        self.assertEqual(game.player_hand.score(), 24)

    def test_dealer_stands_on_17(self):
        game = self.make_game([10, 7, 10, 6])

        result = game.turn(BjAction.STAND)

        self.assertEqual(result, BjResult.DEALER_WIN)
        self.assertEqual(game.dealer_hand.get(), [10, 7])
        self.assertEqual(game.dealer_hand.score(), 17)
        self.assertEqual(game.state, BjState.COMPLETE)

    def test_dealer_hits_until_reaching_17(self):
        game = self.make_game([2, 3, 10, 6, 4, 8])

        result = game.turn(BjAction.STAND)

        self.assertEqual(result, BjResult.DEALER_WIN)
        self.assertEqual(game.dealer_hand.get(), [2, 3, 4, 8])
        self.assertEqual(game.dealer_hand.score(), 17)
        self.assertEqual(game.state, BjState.COMPLETE)

    def test_dealer_busts_after_player_stands(self):
        game = self.make_game([10, 6, 10, 7, 10])

        result = game.turn(BjAction.STAND)

        self.assertEqual(result, BjResult.DEALER_BUST)
        self.assertEqual(game.dealer_hand.score(), 26)
        self.assertEqual(game.state, BjState.COMPLETE)

    def test_player_wins_when_player_score_is_higher(self):
        game = self.make_game([10, 7, 23, 21])

        result = game.turn(BjAction.STAND)

        self.assertEqual(game.player_hand.score(), 18)
        self.assertEqual(game.dealer_hand.score(), 17)
        self.assertEqual(result, BjResult.PLAYER_WIN)

    def test_dealer_wins_when_dealer_score_is_higher(self):
        game = self.make_game([10, 8, 23, 20])

        result = game.turn(BjAction.STAND)

        self.assertEqual(game.player_hand.score(), 17)
        self.assertEqual(game.dealer_hand.score(), 18)
        self.assertEqual(result, BjResult.DEALER_WIN)

    def test_equal_scores_result_in_tie(self):
        game = self.make_game([10, 7, 23, 20])

        result = game.turn(BjAction.STAND)

        self.assertEqual(game.player_hand.score(), 17)
        self.assertEqual(game.dealer_hand.score(), 17)
        self.assertEqual(result, BjResult.TIE)

    def test_player_natural_blackjack_completes_round(self):
        game = self.make_game([2, 3, 1, 10])

        self.assertEqual(game.result, BjResult.PLAYER_BLACKJACK)
        self.assertEqual(game.state, BjState.COMPLETE)

    def test_both_natural_blackjacks_result_in_tie(self):
        game = self.make_game([1, 10, 14, 23])

        self.assertEqual(game.result, BjResult.TIE)
        self.assertEqual(game.state, BjState.COMPLETE)

    def test_dealer_natural_blackjack_is_resolved_when_dealer_turn_starts(self):
        game = self.make_game([1, 10, 2, 3])

        self.assertEqual(game.state, BjState.PLAYER_TURN)
        self.assertIsNone(game.result)

        result = game.turn(BjAction.STAND)

        self.assertEqual(result, BjResult.DEALER_BLACKJACK)
        self.assertEqual(game.result, BjResult.DEALER_BLACKJACK)
        self.assertEqual(game.state, BjState.COMPLETE)

    def test_three_card_21_is_not_natural_blackjack(self):
        game = self.make_game([4, 5, 7, 3, 1])

        result = game.turn(BjAction.HIT)

        self.assertIsNone(result)
        self.assertEqual(game.player_hand.score(), 21)
        self.assertEqual(len(game.player_hand), 3)
        self.assertEqual(game.state, BjState.PLAYER_TURN)
        self.assertIsNone(game.result)

    def test_dealer_stands_on_soft_17(self):
        game = self.make_game([1, 6, 10, 9])

        result = game.turn(BjAction.STAND)

        self.assertEqual(game.dealer_hand.score(), 17)
        self.assertEqual(game.dealer_hand.get(), [1, 6])
        self.assertEqual(result, BjResult.PLAYER_WIN)

    def test_invalid_action_raises_value_error_during_player_turn(self):
        game = self.make_game([2, 3, 4, 5])

        with self.assertRaises(ValueError):
            game.turn("hit")

    def test_result_is_returned_again_after_round_is_complete(self):
        game = self.make_game([2, 3, 10, 9, 5])

        first_result = game.turn(BjAction.HIT)
        second_result = game.turn(BjAction.STAND)

        self.assertEqual(first_result, BjResult.PLAYER_BUST)
        self.assertEqual(second_result, BjResult.PLAYER_BUST)
        self.assertEqual(game.state, BjState.COMPLETE)

    def test_player_can_stand_on_a_three_card_21(self):
        game = self.make_game([4, 5, 7, 3, 1, 6, 6])

        self.assertIsNone(game.turn(BjAction.HIT))
        result = game.turn(BjAction.STAND)

        self.assertEqual(game.player_hand.score(), 21)
        self.assertEqual(len(game.player_hand), 3)
        self.assertEqual(result, BjResult.PLAYER_WIN)

    def test_player_hit_can_change_an_ace_from_eleven_to_one(self):
        game = self.make_game([2, 3, 1, 5, 10])

        result = game.turn(BjAction.HIT)

        self.assertIsNone(result)
        self.assertEqual(game.player_hand.score(), 16)
        self.assertEqual(game.state, BjState.PLAYER_TURN)

    def test_player_can_bust_after_an_ace_has_been_downgraded(self):
        game = self.make_game([2, 3, 1, 5, 10, 8])

        self.assertIsNone(game.turn(BjAction.HIT))
        result = game.turn(BjAction.HIT)

        self.assertEqual(result, BjResult.PLAYER_BUST)
        self.assertEqual(game.player_hand.score(), 24)
        self.assertEqual(game.state, BjState.COMPLETE)

    def test_player_bust_does_not_make_dealer_play(self):
        game = self.make_game([10, 6, 10, 9, 5, 8])

        result = game.turn(BjAction.HIT)

        self.assertEqual(result, BjResult.PLAYER_BUST)
        self.assertEqual(game.dealer_hand.get(), [10, 6])
        self.assertEqual(game.state, BjState.COMPLETE)

    def test_dealer_stands_on_18_or_higher(self):
        game = self.make_game([10, 8, 10, 7])

        result = game.turn(BjAction.STAND)

        self.assertEqual(result, BjResult.PLAYER_WIN)
        self.assertEqual(game.dealer_hand.get(), [10, 8])
        self.assertEqual(game.dealer_hand.score(), 18)

    def test_dealer_downgrades_ace_while_drawing(self):
        game = self.make_game([1, 5, 10, 9, 10, 2])

        result = game.turn(BjAction.STAND)

        self.assertEqual(game.dealer_hand.get(), [1, 5, 10, 2])
        self.assertEqual(game.dealer_hand.score(), 18)
        self.assertEqual(result, BjResult.PLAYER_WIN)

    def test_dealer_uses_multiple_aces_when_drawing(self):
        game = self.make_game([1, 14, 10, 9, 5])

        result = game.turn(BjAction.STAND)

        self.assertEqual(game.dealer_hand.get(), [1, 14, 5])
        self.assertEqual(game.dealer_hand.score(), 17)
        self.assertEqual(result, BjResult.PLAYER_WIN)

    def test_dealer_reaching_21_after_a_hit_is_not_blackjack(self):
        game = self.make_game([5, 6, 10, 9, 10])

        result = game.turn(BjAction.STAND)

        self.assertEqual(game.dealer_hand.score(), 21)
        self.assertEqual(result, BjResult.DEALER_WIN)
        self.assertNotEqual(result, BjResult.DEALER_BLACKJACK)

    def test_player_blackjack_is_detected_with_each_ten_value_rank(self):
        ace_and_ten_values = [
            (1, 10),
            (1, 11),
            (1, 12),
            (1, 13),
            (14, 23),
            (27, 36),
            (40, 49),
        ]

        for ace, ten_value in ace_and_ten_values:
            with self.subTest(ace=ace, ten_value=ten_value):
                game = self.make_game([2, 3, ace, ten_value])

                self.assertEqual(game.result, BjResult.PLAYER_BLACKJACK)
                self.assertEqual(game.state, BjState.COMPLETE)

    def test_dealer_blackjack_is_detected_with_each_ten_value_rank(self):
        ace_and_ten_values = [
            (1, 10),
            (1, 11),
            (1, 12),
            (1, 13),
            (14, 23),
            (27, 36),
            (40, 49),
        ]

        for ace, ten_value in ace_and_ten_values:
            with self.subTest(ace=ace, ten_value=ten_value):
                game = self.make_game([ace, ten_value, 2, 3])

                self.assertEqual(game.state, BjState.PLAYER_TURN)
                result = game.turn(BjAction.STAND)

                self.assertEqual(result, BjResult.DEALER_BLACKJACK)
                self.assertEqual(game.state, BjState.COMPLETE)

    def test_hit_after_player_blackjack_returns_the_existing_result(self):
        game = self.make_game([2, 3, 1, 10, 5])

        result = game.turn(BjAction.HIT)

        self.assertEqual(result, BjResult.PLAYER_BLACKJACK)
        self.assertEqual(game.player_hand.get(), [1, 10])
        self.assertEqual(game.state, BjState.COMPLETE)

    def test_action_after_normal_completion_returns_the_existing_result(self):
        game = self.make_game([10, 7, 23, 21])

        first_result = game.turn(BjAction.STAND)
        player_cards = game.player_hand.get().copy()
        dealer_cards = game.dealer_hand.get().copy()
        second_result = game.turn(BjAction.HIT)

        self.assertEqual(first_result, BjResult.PLAYER_WIN)
        self.assertEqual(second_result, BjResult.PLAYER_WIN)
        self.assertEqual(game.player_hand.get(), player_cards)
        self.assertEqual(game.dealer_hand.get(), dealer_cards)

    def test_invalid_action_values_are_rejected(self):
        game = self.make_game([2, 3, 4, 5])

        for invalid_action in [None, "hit", 0, BjResult.PLAYER_WIN]:
            with self.subTest(invalid_action=invalid_action):
                with self.assertRaises(ValueError):
                    game.turn(invalid_action)

    def test_insufficient_cards_for_initial_deal_are_rejected(self):
        with self.assertRaises(ValueError):
            self.make_game([2, 3, 4])

    def test_deck_with_exactly_four_cards_can_deal_initial_hands(self):
        game = self.make_game([2, 3, 4, 5])

        self.assertEqual(game.dealer_hand.get(), [2, 3])
        self.assertEqual(game.player_hand.get(), [4, 5])
        self.assertEqual(game.deck.get(), [])
