import pytest
# This import will FAIL initially because you haven't created the class yet
from tagstudio.core.library.fields import RatingField

def test_rating_initialization():
    """REQ-04a: Verify rating field initializes with correct max stars."""
    # create a 5-star rating system
    rating = RatingField(name="Quality", min_value=1, max_value=5)
    assert rating.max_value == 5
    assert rating.icon_type == "star"  # Default icon should be star

def test_rating_stores_integer():
    """REQ-05a: Verify rating stores values as integers."""
    rating = RatingField(name="Score", min_value=1, max_value=10)
    rating.set_value(4)
    assert rating.value == 4
    assert isinstance(rating.value, int)

def test_rating_handles_floats_by_rounding():
    """REQ-01d/REQ-05: Ensure partial stars are rounded to whole numbers."""
    rating = RatingField(name="Precision", min_value=1, max_value=5)
    # If a user tries to set 3.7, it should probably become 4
    rating.set_value(3.7)
    assert rating.value == 4
    assert isinstance(rating.value, int)

def test_rating_icon_configuration():
    """REQ-04b: Verify custom icons can be set."""
    rating = RatingField(name="Hearts", min_value=1, max_value=3, icon_type="heart")
    assert rating.icon_type == "heart"