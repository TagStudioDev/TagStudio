class NumericField: # Assuming this is the base structure
    def __init__(self, name, **kwargs):
        self.name = name
        self.value = None

class SliderField(NumericField): # Emma/Sumeya's logic
    def __init__(self, name, min_value=0, max_value=100, **kwargs):
        super().__init__(name, **kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def set_value(self, val):
        self.value = val

# Adjust the import path if SliderField is in a different file
from tagstudio.core.library.fields import SliderField 


class RatingField(SliderField):
    """
    REQ-04, REQ-05: add a specialized SliderField for ratings.
    Ensure values are integers and can be used to display custom icon types
    """

    
    def __init__(self, name, min_value=1, max_value=5, icon_type="star", **kwargs):
        # REQ-04: Initialize with a default icon_type (e.g., "star")
        super().__init__(name=name, min_value=min_value, max_value=max_value, **kwargs)
        self.icon_type = icon_type

    def set_value(self, val):
        """
        REQ-05a: Override setter to ensure rating is always an integer.
        Uses round() to handle float inputs (e.g., 4.7 becomes 5).
        """
        if val is not None:
            val = int(round(float(val)))
        super().set_value(val)