# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import structlog

from .models import Namespace, TagColorGroup

logger = structlog.get_logger(__name__)


def namespaces() -> list[Namespace]:
    tagstudio_standard = Namespace("tagstudio-standard", "TagStudio Standard")
    tagstudio_pastels = Namespace("tagstudio-pastels", "TagStudio Pastels")
    tagstudio_shades = Namespace("tagstudio-shades", "TagStudio Shades")
    tagstudio_earth_tones = Namespace("tagstudio-earth-tones", "TagStudio Earth Tones")
    tagstudio_grayscale = Namespace("tagstudio-grayscale", "TagStudio Grayscale")
    tagstudio_neon = Namespace("tagstudio-neon", "TagStudio Neon")
    return [
        tagstudio_standard,
        tagstudio_pastels,
        tagstudio_shades,
        tagstudio_earth_tones,
        tagstudio_grayscale,
        tagstudio_neon,
    ]


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


def standard() -> list[TagColorGroup]:
    red = TagColorGroup(
        slug="red",
        namespace="tagstudio-standard",
        name="Red",
        primary="#E22C3C",
    )
    red_orange = TagColorGroup(
        slug="red-orange",
        namespace="tagstudio-standard",
        name="Red Orange",
        primary="#E83726",
    )
    orange = TagColorGroup(
        slug="orange",
        namespace="tagstudio-standard",
        name="Orange",
        primary="#ED6022",
    )
    amber = TagColorGroup(
        slug="amber",
        namespace="tagstudio-standard",
        name="Amber",
        primary="#FA9A2C",
    )
    yellow = TagColorGroup(
        slug="yellow",
        namespace="tagstudio-standard",
        name="Yellow",
        primary="#FFD63D",
    )
    lime = TagColorGroup(
        slug="lime",
        namespace="tagstudio-standard",
        name="Lime",
        primary="#92E649",
    )
    green = TagColorGroup(
        slug="green",
        namespace="tagstudio-standard",
        name="Green",
        primary="#45D649",
    )
    teal = TagColorGroup(
        slug="teal",
        namespace="tagstudio-standard",
        name="Teal",
        primary="#22D589",
    )
    cyan = TagColorGroup(
        slug="cyan",
        namespace="tagstudio-standard",
        name="Cyan",
        primary="#3DDBDB",
    )
    blue = TagColorGroup(
        slug="blue",
        namespace="tagstudio-standard",
        name="Blue",
        primary="#3B87F0",
    )
    indigo = TagColorGroup(
        slug="indigo",
        namespace="tagstudio-standard",
        name="Indigo",
        primary="#874FF5",
    )
    purple = TagColorGroup(
        slug="purple",
        namespace="tagstudio-standard",
        name="Purple",
        primary="#BB4FF0",
    )
    magenta = TagColorGroup(
        slug="magenta",
        namespace="tagstudio-standard",
        name="Magenta",
        primary="#F64680",
    )
    pink = TagColorGroup(
        slug="pink",
        namespace="tagstudio-standard",
        name="Pink",
        primary="#FF62AF",
    )
    return [
        red,
        red_orange,
        orange,
        amber,
        yellow,
        lime,
        green,
        teal,
        cyan,
        blue,
        indigo,
        purple,
        pink,
        magenta,
    ]


def pastels() -> list[TagColorGroup]:
    coral = TagColorGroup(
        slug="coral",
        namespace="tagstudio-pastels",
        name="Coral",
        primary="#F2525F",
    )
    salmon = TagColorGroup(
        slug="salmon",
        namespace="tagstudio-pastels",
        name="Salmon",
        primary="#F66348",
    )
    light_orange = TagColorGroup(
        slug="light-orange",
        namespace="tagstudio-pastels",
        name="Light Orange",
        primary="#FF9450",
    )
    light_amber = TagColorGroup(
        slug="light-amber",
        namespace="tagstudio-pastels",
        name="Light Amber",
        primary="#FFBA57",
    )
    light_yellow = TagColorGroup(
        slug="light-yellow",
        namespace="tagstudio-pastels",
        name="Light Yellow",
        primary="#FFE173",
    )
    light_lime = TagColorGroup(
        slug="light-lime",
        namespace="tagstudio-pastels",
        name="Light Lime",
        primary="#C9FF7A",
    )
    light_green = TagColorGroup(
        slug="light-green",
        namespace="tagstudio-pastels",
        name="Light Green",
        primary="#81FF76",
    )
    mint = TagColorGroup(
        slug="mint",
        namespace="tagstudio-pastels",
        name="Mint",
        primary="#68FFB4",
    )
    sky_blue = TagColorGroup(
        slug="sky-blue",
        namespace="tagstudio-pastels",
        name="Sky Blue",
        primary="#8EFFF4",
    )
    light_blue = TagColorGroup(
        slug="light-blue",
        namespace="tagstudio-pastels",
        name="Light Blue",
        primary="#64C6FF",
    )
    lavender = TagColorGroup(
        slug="lavender",
        namespace="tagstudio-pastels",
        name="Lavender",
        primary="#908AF6",
    )
    lilac = TagColorGroup(
        slug="lilac",
        namespace="tagstudio-pastels",
        name="Lilac",
        primary="#DF95FF",
    )
    light_pink = TagColorGroup(
        slug="light-pink",
        namespace="tagstudio-pastels",
        name="Light Pink",
        primary="#FF87BA",
    )
    return [
        coral,
        salmon,
        light_orange,
        light_amber,
        light_yellow,
        light_lime,
        light_green,
        mint,
        sky_blue,
        light_blue,
        lavender,
        lilac,
        light_pink,
    ]


def shades() -> list[TagColorGroup]:
    burgundy = TagColorGroup(
        slug="burgundy",
        namespace="tagstudio-shades",
        name="Burgundy",
        primary="#6E1C24",
    )
    auburn = TagColorGroup(
        slug="auburn",
        namespace="tagstudio-shades",
        name="Auburn",
        primary="#A13220",
    )
    olive = TagColorGroup(
        slug="olive",
        namespace="tagstudio-shades",
        name="Olive",
        primary="#4C652E",
    )
    dark_teal = TagColorGroup(
        slug="dark-teal",
        namespace="tagstudio-shades",
        name="Dark Teal",
        primary="#1F5E47",
    )
    navy = TagColorGroup(
        slug="navy",
        namespace="tagstudio-shades",
        name="Navy",
        primary="#104B98",
    )
    dark_lavender = TagColorGroup(
        slug="dark_lavender",
        namespace="tagstudio-shades",
        name="Dark Lavender",
        primary="#3D3B6C",
    )
    berry = TagColorGroup(
        slug="berry",
        namespace="tagstudio-shades",
        name="Berry",
        primary="#9F2AA7",
    )
    return [burgundy, auburn, olive, dark_teal, navy, dark_lavender, berry]


def earth_tones() -> list[TagColorGroup]:
    dark_brown = TagColorGroup(
        slug="dark-brown",
        namespace="tagstudio-earth-tones",
        name="Dark Brown",
        primary="#4C2315",
    )
    brown = TagColorGroup(
        slug="brown",
        namespace="tagstudio-earth-tones",
        name="Brown",
        primary="#823216",
    )
    light_brown = TagColorGroup(
        slug="light-brown",
        namespace="tagstudio-earth-tones",
        name="Light Brown",
        primary="#BE5B2D",
    )
    blonde = TagColorGroup(
        slug="blonde",
        namespace="tagstudio-earth-tones",
        name="Blonde",
        primary="#EFC664",
    )
    peach = TagColorGroup(
        slug="peach",
        namespace="tagstudio-earth-tones",
        name="Peach",
        primary="#F1C69C",
    )
    warm_gray = TagColorGroup(
        slug="warm-gray",
        namespace="tagstudio-earth-tones",
        name="Warm Gray",
        primary="#625550",
    )
    cool_gray = TagColorGroup(
        slug="cool-gray",
        namespace="tagstudio-earth-tones",
        name="Cool Gray",
        primary="#515768",
    )
    return [dark_brown, brown, light_brown, blonde, peach, warm_gray, cool_gray]


def grayscale() -> list[TagColorGroup]:
    black = TagColorGroup(
        slug="black",
        namespace="tagstudio-grayscale",
        name="Black",
        primary="#111018",
    )
    dark_gray = TagColorGroup(
        slug="dark-gray",
        namespace="tagstudio-grayscale",
        name="Dark Gray",
        primary="#242424",
    )
    gray = TagColorGroup(
        slug="gray",
        namespace="tagstudio-grayscale",
        name="Gray",
        primary="#53525A",
    )
    light_gray = TagColorGroup(
        slug="light-gray",
        namespace="tagstudio-grayscale",
        name="Light Gray",
        primary="#AAAAAA",
    )
    white = TagColorGroup(
        slug="white",
        namespace="tagstudio-grayscale",
        name="White",
        primary="#F2F1F8",
    )
    return [black, dark_gray, gray, light_gray, white]


def neon() -> list[TagColorGroup]:
    neon_red = TagColorGroup(
        slug="neon-red",
        namespace="tagstudio-neon",
        name="Neon Red",
        primary="#180607",
        secondary="#E22C3C",
        color_border=True,
    )
    neon_red_orange = TagColorGroup(
        slug="neon-red-orange",
        namespace="tagstudio-neon",
        name="Neon Red Orange",
        primary="#220905",
        secondary="#E83726",
        color_border=True,
    )
    neon_orange = TagColorGroup(
        slug="neon-orange",
        namespace="tagstudio-neon",
        name="Neon Orange",
        primary="#1F0D05",
        secondary="#ED6022",
        color_border=True,
    )
    neon_amber = TagColorGroup(
        slug="neon-amber",
        namespace="tagstudio-neon",
        name="Neon Amber",
        primary="#251507",
        secondary="#FA9A2C",
        color_border=True,
    )
    neon_yellow = TagColorGroup(
        slug="neon-yellow",
        namespace="tagstudio-neon",
        name="Neon Yellow",
        primary="#2B1C0B",
        secondary="#FFD63D",
        color_border=True,
    )
    neon_lime = TagColorGroup(
        slug="neon-lime",
        namespace="tagstudio-neon",
        name="Neon Lime",
        primary="#1B220C",
        secondary="#92E649",
        color_border=True,
    )
    neon_green = TagColorGroup(
        slug="neon-green",
        namespace="tagstudio-neon",
        name="Neon Green",
        primary="#091610",
        secondary="#45D649",
        color_border=True,
    )
    neon_teal = TagColorGroup(
        slug="neon-teal",
        namespace="tagstudio-neon",
        name="Neon Teal",
        primary="#09191D",
        secondary="#22D589",
        color_border=True,
    )
    neon_cyan = TagColorGroup(
        slug="neon-cyan",
        namespace="tagstudio-neon",
        name="Neon Cyan",
        primary="#0B191C",
        secondary="#3DDBDB",
        color_border=True,
    )
    neon_blue = TagColorGroup(
        slug="neon-blue",
        namespace="tagstudio-neon",
        name="Neon Blue",
        primary="#09101C",
        secondary="#3B87F0",
        color_border=True,
    )
    neon_indigo = TagColorGroup(
        slug="neon-indigo",
        namespace="tagstudio-neon",
        name="Neon Indigo",
        primary="#150B24",
        secondary="#874FF5",
        color_border=True,
    )
    neon_purple = TagColorGroup(
        slug="neon-purple",
        namespace="tagstudio-neon",
        name="Neon Purple",
        primary="#1E0B26",
        secondary="#BB4FF0",
        color_border=True,
    )
    neon_magenta = TagColorGroup(
        slug="neon-magenta",
        namespace="tagstudio-neon",
        name="Neon Magenta",
        primary="#220A13",
        secondary="#F64680",
        color_border=True,
    )
    neon_pink = TagColorGroup(
        slug="neon-pink",
        namespace="tagstudio-neon",
        name="Neon Pink",
        primary="#210E15",
        secondary="#FF62AF",
        color_border=True,
    )
    neon_white = TagColorGroup(
        slug="neon-white",
        namespace="tagstudio-neon",
        name="Neon White",
        primary="#131315",
        secondary="#F2F1F8",
        color_border=True,
    )
    return [
        neon_red,
        neon_red_orange,
        neon_orange,
        neon_amber,
        neon_yellow,
        neon_lime,
        neon_green,
        neon_teal,
        neon_cyan,
        neon_blue,
        neon_indigo,
        neon_purple,
        neon_pink,
        neon_magenta,
        neon_white,
    ]
