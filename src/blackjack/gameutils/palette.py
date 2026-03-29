"""Swappable color palette system for terminal UI.

Each palette defines semantic color roles (chrome, highlight, win, loss, etc.)
using 256-color ANSI codes. The active palette is a module-level global that
display functions read at render time.
"""


class Palette:
    def __init__(self, name, label, chrome, highlight, win, loss, neutral, card_red, card_back):
        self.name = name
        self.label = label
        self.chrome = f"\033[38;5;{chrome}m"
        self.highlight = f"\033[38;5;{highlight}m"
        self.win = f"\033[38;5;{win}m"
        self.loss = f"\033[38;5;{loss}m"
        self.neutral = f"\033[38;5;{neutral}m"
        self.card_red = f"\033[38;5;{card_red}m"
        self.card_back = f"\033[38;5;{card_back}m"
        self.dim = "\033[2m"
        self.reset = "\033[0m"


WARM_FELT = Palette("warm-felt", "Warm Felt",
                     chrome=180, highlight=223, win=114, loss=203,
                     neutral=222, card_red=203, card_back=60)

ART_DECO = Palette("art-deco", "Art Deco",
                    chrome=214, highlight=230, win=35, loss=161,
                    neutral=187, card_red=161, card_back=236)

MIDNIGHT = Palette("midnight", "Midnight",
                    chrome=146, highlight=117, win=115, loss=175,
                    neutral=188, card_red=175, card_back=60)

PALETTES = [WARM_FELT, ART_DECO, MIDNIGHT]
PALETTE_MAP = {p.name: p for p in PALETTES}
DEFAULT_PALETTE = WARM_FELT

# Module-level active palette — mutable global.
active = DEFAULT_PALETTE


def set_palette(name):
    """Switch the active palette by name."""
    global active
    active = PALETTE_MAP[name]
