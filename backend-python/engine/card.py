"""
Card class for Texas Hold'em poker game representation.
"""

from enum import Enum
from typing import Union


class Suit(Enum):
    """Playing card suits."""
    SPADES = '♠'
    HEARTS = '♥'
    DIAMONDS = '♦'
    CLUBS = '♣'
    
    def __str__(self):
        return self.value


class Rank(Enum):
    """Playing card ranks with their numeric values for comparison."""
    TWO = (2, '2')
    THREE = (3, '3')
    FOUR = (4, '4')
    FIVE = (5, '5')
    SIX = (6, '6')
    SEVEN = (7, '7')
    EIGHT = (8, '8')
    NINE = (9, '9')
    TEN = (10, '10')
    JACK = (11, 'J')
    QUEEN = (12, 'Q')
    KING = (13, 'K')
    ACE = (14, 'A')
    
    def __init__(self, numeric_value: int, symbol: str):
        """Initialize rank with numeric value and symbol."""
        # Store as tuple elements - value is reserved by Enum
        self._numeric_value = numeric_value
        self._symbol = symbol
    
    @property
    def numeric_value(self) -> int:
        """Get the numeric value of the rank (2-14)."""
        return self._numeric_value
    
    @property
    def symbol(self) -> str:
        """Get the symbol representation of the rank."""
        return self._symbol
    
    def __str__(self):
        return self._symbol
    
    @classmethod
    def from_string(cls, rank_str: str) -> 'Rank':
        """Create a Rank from a string representation."""
        rank_str = rank_str.upper().strip()
        rank_map = {
            '2': cls.TWO, '3': cls.THREE, '4': cls.FOUR, '5': cls.FIVE,
            '6': cls.SIX, '7': cls.SEVEN, '8': cls.EIGHT, '9': cls.NINE,
            '10': cls.TEN, 'T': cls.TEN,
            'J': cls.JACK, 'JACK': cls.JACK,
            'Q': cls.QUEEN, 'QUEEN': cls.QUEEN,
            'K': cls.KING, 'KING': cls.KING,
            'A': cls.ACE, 'ACE': cls.ACE
        }
        if rank_str not in rank_map:
            raise ValueError(f"Invalid rank string: {rank_str}")
        return rank_map[rank_str]
    
    @classmethod
    def from_value(cls, value: int) -> 'Rank':
        """Create a Rank from a numeric value (2-14)."""
        for rank in cls:
            if rank.numeric_value == value:
                return rank
        raise ValueError(f"Invalid rank value: {value}. Must be between 2 and 14.")


class Card:
    """
    Represents a single playing card for Texas Hold'em.
    
    Attributes:
        rank: The rank of the card (2-10, J, Q, K, A)
        suit: The suit of the card (Spades, Hearts, Diamonds, Clubs)
    
    Examples:
        >>> card = Card(Rank.ACE, Suit.SPADES)
        >>> card.get_rank_value()
        14
        >>> str(card)
        'A♠'
        >>> card2 = Card.from_string('K♥')
        >>> card2.get_rank_value()
        13
    """
    
    def __init__(self, rank: Union[Rank, str], suit: Union[Suit, str]):
        """
        Initialize a Card with rank and suit.
        
        Args:
            rank: Rank enum or string representation (2-10, J, Q, K, A)
            suit: Suit enum or string representation (S, H, D, C only)
        
        Raises:
            ValueError: If rank or suit is invalid
            TypeError: If rank or suit types are invalid
        """
        # Validate and convert rank
        if isinstance(rank, str):
            self._rank = Rank.from_string(rank)
        elif isinstance(rank, Rank):
            self._rank = rank
        else:
            raise TypeError(f"Rank must be Rank enum or string, got {type(rank)}")
        
        # Validate and convert suit
        if isinstance(suit, str):
            self._suit = self._parse_suit_string(suit)
        elif isinstance(suit, Suit):
            self._suit = suit
        else:
            raise TypeError(f"Suit must be Suit enum or string, got {type(suit)}")
    
    @staticmethod
    def _parse_suit_string(suit_str: str) -> Suit:
        """
        Parse a suit string into a Suit enum.
        Only accepts single letter format: S, H, D, C (case-insensitive).
        """
        suit_str = suit_str.upper().strip()
        suit_map = {
            'S': Suit.SPADES,
            'H': Suit.HEARTS,
            'D': Suit.DIAMONDS,
            'C': Suit.CLUBS
        }
        if suit_str not in suit_map:
            raise ValueError(f"Invalid suit string: {suit_str}. Must be one of: S, H, D, C")
        return suit_map[suit_str]
    
    @classmethod
    def from_string(cls, card_str: str) -> 'Card':
        """
        Create a Card from a string representation.
        Only accepts standard format: rank + suit letter (e.g., 'As', 'Kh', '2d', '10c').
        Unicode symbols are not accepted as input (only for display).
        
        Args:
            card_str: String in format 'As', 'Kh', '2d', '10c' (case-insensitive)
        
        Raises:
            ValueError: If format is invalid or contains unicode symbols
        
        Examples:
            >>> Card.from_string('As')
            Card(Rank.ACE, Suit.SPADES)
            >>> Card.from_string('Kh')
            Card(Rank.KING, Suit.HEARTS)
        """
        card_str = card_str.strip()
        if len(card_str) < 2:
            raise ValueError(f"Card string too short: {card_str}")
        
        # Check for unicode symbols - not allowed in input
        if card_str[-1] in '♠♥♦♣':
            raise ValueError(f"Unicode symbols not allowed in input. Use standard format: rank + letter (S, H, D, C). Got: {card_str}")
        
        # Standard format: rank + suit letter (S, H, D, C)
        rank_str = card_str[:-1]
        suit_str = card_str[-1]
        
        # Validate suit is a single letter
        if suit_str.upper() not in ['S', 'H', 'D', 'C']:
            raise ValueError(f"Invalid suit letter: {suit_str}. Must be one of: S, H, D, C")
        
        return cls(rank_str, suit_str)
    
    def get_rank_value(self) -> int:
        """
        Get the numeric value of the card's rank.
        
        Returns:
            Integer value: 2-10 for number cards, 11=J, 12=Q, 13=K, 14=A
        """
        return self._rank.numeric_value
    
    @property
    def rank(self) -> Rank:
        """Get the rank enum."""
        return self._rank
    
    @property
    def suit(self) -> Suit:
        """Get the suit enum."""
        return self._suit
    
    def __str__(self) -> str:
        """String representation: e.g., 'A♠', 'K♥', '2♦'"""
        return f"{self._rank}{self._suit}"
    
    def __repr__(self) -> str:
        """Developer representation: e.g., Card(Rank.ACE, Suit.SPADES)"""
        return f"Card(Rank.{self._rank.name}, Suit.{self._suit.name})"
    
    def __eq__(self, other) -> bool:
        """Two cards are equal if they have the same rank and suit."""
        if not isinstance(other, Card):
            return NotImplemented
        return self._rank == other._rank and self._suit == other._suit
    
    def __hash__(self) -> int:
        """Hash based on rank and suit for use in sets and dicts."""
        return hash((self._rank, self._suit))
    
    def __lt__(self, other) -> bool:
        """
        Compare cards by rank value (suit doesn't matter for ordering).
        For same rank, order by suit (Spades < Hearts < Diamonds < Clubs).
        """
        if not isinstance(other, Card):
            return NotImplemented
        if self._rank.numeric_value != other._rank.numeric_value:
            return self._rank.numeric_value < other._rank.numeric_value
        # Same rank, compare by suit
        suit_order = {Suit.SPADES: 0, Suit.HEARTS: 1, Suit.DIAMONDS: 2, Suit.CLUBS: 3}
        return suit_order[self._suit] < suit_order[other._suit]
    
    def __le__(self, other) -> bool:
        """Less than or equal comparison."""
        return self == other or self < other
    
    def __gt__(self, other) -> bool:
        """Greater than comparison."""
        if not isinstance(other, Card):
            return NotImplemented
        return not self <= other
    
    def __ge__(self, other) -> bool:
        """Greater than or equal comparison."""
        return self == other or self > other


def create_hand(card1: Union[Card, str], card2: Union[Card, str]) -> tuple[Card, Card]:
    """
    Create a 2-card Texas Hold'em hand.
    
    Args:
        card1: First card (Card instance or string like 'As', 'Kh')
        card2: Second card (Card instance or string like 'As', 'Kh')
    
    Returns:
        Tuple of two Card objects
    
    Raises:
        ValueError: If cards are the same (duplicate)
    
    Examples:
        >>> hand = create_hand('As', 'Kh')
        >>> len(hand)
        2
        >>> hand = create_hand(Card(Rank.ACE, Suit.SPADES), 'K♥')
    """
    # Convert strings to Card objects if needed
    if isinstance(card1, str):
        card1 = Card.from_string(card1)
    if isinstance(card2, str):
        card2 = Card.from_string(card2)
    
    if not isinstance(card1, Card):
        raise TypeError(f"card1 must be Card or string, got {type(card1)}")
    if not isinstance(card2, Card):
        raise TypeError(f"card2 must be Card or string, got {type(card2)}")
    
    # Check for duplicates
    if card1 == card2:
        raise ValueError(f"Cannot create hand with duplicate card: {card1}")
    
    return (card1, card2)


if __name__ == "__main__":
    """
    Test case that accepts terminal input for creating cards and a 2-card hand.
    
    Usage:
        python card.py
        # Then enter card strings when prompted (e.g., 'As', 'Kh', '2d', '10c')
    """
    print("Texas Hold'em Card Test")
    print("=" * 40)
    print("Enter card strings in format: rank + suit letter")
    print("Format: As, Kh, 2d, 10c (S=Spades, H=Hearts, D=Diamonds, C=Clubs)")
    print("Note: Unicode symbols (♠♥♦♣) are for display only, not input")
    print()
    
    try:
        # Get first card from terminal input
        card1_input = input("Enter first card: ").strip()
        card1 = Card.from_string(card1_input)
        print(f"✓ Card 1 created: {card1} (Rank value: {card1.get_rank_value()})")
        print()
        
        # Get second card from terminal input
        card2_input = input("Enter second card: ").strip()
        card2 = Card.from_string(card2_input)
        print(f"✓ Card 2 created: {card2} (Rank value: {card2.get_rank_value()})")
        print()
        
        # Create the hand
        hand = create_hand(card1, card2)
        print("=" * 40)
        print("Hand created successfully!")
        print(f"Card 1: {hand[0]} (repr: {repr(hand[0])})")
        print(f"Card 2: {hand[1]} (repr: {repr(hand[1])})")
        print()
        
        # Display additional information
        print("Card Details:")
        print(f"  Card 1 - Rank: {hand[0].rank.name}, Suit: {hand[0].suit.name}, Value: {hand[0].get_rank_value()}")
        print(f"  Card 2 - Rank: {hand[1].rank.name}, Suit: {hand[1].suit.name}, Value: {hand[1].get_rank_value()}")
        print()
        
        # Test comparison
        if hand[0] < hand[1]:
            print(f"Card ordering: {hand[0]} < {hand[1]}")
        elif hand[0] > hand[1]:
            print(f"Card ordering: {hand[0]} > {hand[1]}")
        else:
            print(f"Cards have same rank: {hand[0]} == {hand[1]}")
        
    except ValueError as e:
        print(f"❌ Error: {e}")
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

