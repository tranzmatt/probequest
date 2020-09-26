"""
Main module.
"""

from argparse import ArgumentParser, FileType
from os import geteuid
from sys import exit as sys_exit
from time import sleep

from . import __version__ as VERSION
from .config import Config, Mode
from .ui.pnl import PNLViewer
from .ui.raw import RawProbeRequestViewer


def get_arg_parser():
    """
    Returns the argument parser.
    """

    arg_parser = ArgumentParser(
        description="Toolkit for Playing with Wi-Fi Probe Requests"
    )
    arg_parser.add_argument(
        "--debug", action="store_true",
        dest="debug",
        help="debug mode"
    )
    arg_parser.add_argument(
        "--fake", action="store_true",
        dest="fake",
        help="display only fake ESSIDs")
    arg_parser.add_argument(
        "-i", "--interface",
        required=True,
        dest="interface",
        help="wireless interface to use (must be in monitor mode)"
    )
    arg_parser.add_argument(
        "--ignore-case", action="store_true",
        dest="ignore_case",
        help="ignore case distinctions in the regex pattern (default: false)"
    )
    arg_parser.add_argument(
        "--mode",
        type=Mode, choices=Mode.__members__.values(),
        dest="mode",
        help="set the mode to use"
    )
    arg_parser.add_argument(
        "-o", "--output",
        type=FileType("a"),
        dest="output_file",
        help="output file to save the captured data (CSV format)"
    )
    arg_parser.add_argument("--version", action="version", version=VERSION)
    arg_parser.set_defaults(debug=False)
    arg_parser.set_defaults(fake=False)
    arg_parser.set_defaults(ignore_case=False)
    arg_parser.set_defaults(mode=Mode.RAW)

    essid_arguments = arg_parser.add_mutually_exclusive_group()
    essid_arguments.add_argument(
        "-e", "--essid",
        nargs="+",
        dest="essid_filters",
        help="ESSID of the APs to filter (space-separated list)"
    )
    essid_arguments.add_argument(
        "-r", "--regex",
        dest="essid_regex",
        help="regex to filter the ESSIDs"
    )

    station_arguments = arg_parser.add_mutually_exclusive_group()
    station_arguments.add_argument(
        "--exclude",
        nargs="+",
        dest="mac_exclusions",
        help="MAC addresses of the stations to exclude (space-separated list)"
    )
    station_arguments.add_argument(
        "-s", "--station",
        nargs="+",
        dest="mac_filters",
        help="MAC addresses of the stations to filter (space-separated list)"
    )

    return arg_parser


def main():
    """
    Entry point of the command-line tool.
    """

    config = Config()
    get_arg_parser().parse_args(namespace=config)

    if not geteuid() == 0:
        sys_exit("[!] You must be root")

    # Default mode.
    if config.mode == Mode.RAW:
        try:
            print("[*] Start sniffing probe requests...")
            raw_viewer = RawProbeRequestViewer(config)
            raw_viewer.start()

            while True:
                sleep(100)
        except OSError:
            raw_viewer.stop()
            sys_exit(
                "[!] Interface {interface} doesn't exist".format(
                    interface=config.interface
                )
            )
        except KeyboardInterrupt:
            print("[*] Stopping the threads...")
            raw_viewer.stop()
            print("[*] Bye!")
    elif config.mode == Mode.PNL:
        try:
            pnl_viewer = PNLViewer(config)
            pnl_viewer.main()
        except OSError:
            sys_exit(
                "[!] Interface {interface} doesn't exist".format(
                    interface=config.interface
                )
            )
        except KeyboardInterrupt:
            pnl_viewer.sniffer.stop()
    else:
        sys_exit("[x] Invalid mode")
