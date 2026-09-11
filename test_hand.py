import unittest
from main import Hand


class TestHand(unittest.TestCase):
    def test_basic_score(self):
        hand = Hand([10, 7])
        self.assertEqual(hand.score(), 17)

    def test_ace_can_be_eleven(self):
        hand = Hand([1, 9])
        self.assertEqual(hand.score(), 20)

    def test_ace_can_be_one_when_hand_would_bust(self):
        hand = Hand([1, 9, 5])
        self.assertEqual(hand.score(), 15)

    def test_multiple_aces_use_the_best_valid_values(self):
        hand = Hand([1, 14, 9])
        self.assertEqual(hand.score(), 21)

    def test_face_cards_are_worth_ten(self):
        hand = Hand([11, 12, 13])
        self.assertEqual(hand.score(), 30)

    def test_bust_score_is_greater_than_21(self):
        hand = Hand([10, 7, 6])
        self.assertGreater(hand.score(), 21)

    def test_add_card(self):
        hand = Hand([10, 7])
        hand.add(2)
        self.assertEqual(hand.get(), [10, 7, 2])
        self.assertEqual(hand.score(), 19)

    def test_clear_hand(self):
        hand = Hand([10, 7])
        hand.clear()
        self.assertEqual(hand.get(), [])
        self.assertEqual(hand.score(), 0)
if __name__ == '__main__':
    unittest.main()