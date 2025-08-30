# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


def json_to_sql_color(json_color: str) -> tuple[str | None, str | None]:
    """Convert a color string from a <=9.4 JSON library to a 9.5+ (namespace, slug) tuple."""
    json_color_ = json_color.lower()
    match json_color_:
        case "black":
            return ("tagstudio-grayscale", "black")
        case "dark gray":
            return ("tagstudio-grayscale", "dark-gray")
        case "gray":
            return ("tagstudio-grayscale", "gray")
        case "light gray":
            return ("tagstudio-grayscale", "light-gray")
        case "white":
            return ("tagstudio-grayscale", "white")
        case "light pink":
            return ("tagstudio-pastels", "light-pink")
        case "pink":
            return ("tagstudio-standard", "pink")
        case "magenta":
            return ("tagstudio-standard", "magenta")
        case "red":
            return ("tagstudio-standard", "red")
        case "red orange":
            return ("tagstudio-standard", "red-orange")
        case "salmon":
            return ("tagstudio-pastels", "salmon")
        case "orange":
            return ("tagstudio-standard", "orange")
        case "yellow orange":
            return ("tagstudio-standard", "amber")
        case "yellow":
            return ("tagstudio-standard", "yellow")
        case "mint":
            return ("tagstudio-pastels", "mint")
        case "lime":
            return ("tagstudio-standard", "lime")
        case "light green":
            return ("tagstudio-pastels", "light-green")
        case "green":
            return ("tagstudio-standard", "green")
        case "teal":
            return ("tagstudio-standard", "teal")
        case "cyan":
            return ("tagstudio-standard", "cyan")
        case "light blue":
            return ("tagstudio-pastels", "light-blue")
        case "blue":
            return ("tagstudio-standard", "blue")
        case "blue violet":
            return ("tagstudio-shades", "navy")
        case "violet":
            return ("tagstudio-standard", "indigo")
        case "purple":
            return ("tagstudio-standard", "purple")
        case "peach":
            return ("tagstudio-earth-tones", "peach")
        case "brown":
            return ("tagstudio-earth-tones", "brown")
        case "lavender":
            return ("tagstudio-pastels", "lavender")
        case "blonde":
            return ("tagstudio-earth-tones", "blonde")
        case "auburn":
            return ("tagstudio-shades", "auburn")
        case "light brown":
            return ("tagstudio-earth-tones", "light-brown")
        case "dark brown":
            return ("tagstudio-earth-tones", "dark-brown")
        case "cool gray":
            return ("tagstudio-earth-tones", "cool-gray")
        case "warm gray":
            return ("tagstudio-earth-tones", "warm-gray")
        case "olive":
            return ("tagstudio-shades", "olive")
        case "berry":
            return ("tagstudio-shades", "berry")
        case _:
            return (None, None)
