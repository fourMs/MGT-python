import argparse
import os
import sys
from musicalgestures._utils import unwrap_str

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Play video in a separate process')
    parser.add_argument('command', metavar='command', type=str, help='command')
    args = parser.parse_args()
    os.system(unwrap_str(args.command))