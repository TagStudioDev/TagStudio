from src.core.library.alchemy.models import Color, ColorNamespace
from src.core.palette import ColorType

def get_hex_color(color: Color, color_type: ColorType) -> str:
    #TODO: everything
    if color_type == ColorType.PRIMARY:
        return color.hex_value
    elif color_type == ColorType.TEXT:
        return color.hex_value
    elif color_type == ColorType.BORDER:
        return color.hex_value
    elif color_type == ColorType.LIGHT_ACCENT:
        return color.hex_value
    elif color_type == ColorType.DARK_ACCENT:
        return color.hex_value