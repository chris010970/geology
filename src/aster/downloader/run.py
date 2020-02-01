import os
import sys
import argparse

from downloader import Downloader

def parseArguments(args=None):

    """
    Placeholder
    """

    # parse command line arguments
    parser = argparse.ArgumentParser(description='aster download ard')
    parser.add_argument('start_date', action="store")
    parser.add_argument('end_date', action="store")

    parser.add_argument('-ts', '--start_hour', action="store")
    parser.add_argument('-te', '--end_hour', action="store")

    return parser.parse_args(args)


def main():

    """
    Placeholder
    """

    # parse arguments
    args = parseArguments()
    obj = Downloader()

    # handcraft additional args
    args.start_hour = 5; args.end_hour = 7
    bbox = { 
                'ulx' : 73.3,
                'uly' : 50.5,
                'lrx' : 75.3,
                'lry' : 48.5,
        }

    obj.process( args, bbox )

    return

# execute main
if __name__ == '__main__':
    main()

