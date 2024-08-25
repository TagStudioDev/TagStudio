# Parse arguments.
import argparse

class Args(argparse.Namespace):
    open: str
    config_file: str
    debug: bool
    ui: str
    ci: bool

parser = argparse.ArgumentParser()
parser.add_argument(
    "-o",
    "--open",
    dest="open",
    type=str,
    help="Path to a TagStudio Library folder to open on start.",
)
parser.add_argument(
    "-c",
    "--config-file",
    dest="config_file",
    type=str,
    help="Path to a TagStudio .ini or .plist config file to use.",
)

# parser.add_argument('--browse', dest='browse', action='store_true',
#                     help='Jumps to entry browsing on startup.')
# parser.add_argument('--external_preview', dest='external_preview', action='store_true',
#                     help='Outputs current preview thumbnail to a live-updating file.')
parser.add_argument(
    "--debug",
    dest="debug",
    action="store_true",
    help="Reveals additional internal data useful for debugging.",
)
parser.add_argument(
    "--ui",
    dest="ui",
    type=str,
    help="User interface option for TagStudio. Options: qt, cli (Default: qt)",
)
parser.add_argument(
    "--ci",
    action=argparse.BooleanOptionalAction,
    help="Exit the application after checking it starts without any problem. Meant for CI check.",
)
