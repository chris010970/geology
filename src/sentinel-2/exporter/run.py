import os
import sys
import argparse

from exporter import Exporter

sys.path.append( os.path.join( os.path.dirname( sys.path[0]), '../utility' ) )
from fs import getFileList


def getSceneList(args):

    """
    Placeholder
    """

    # assume single scene - else collect list
    scenes = [ args.scene ]
    if args.batch is True:
        scenes = getFileList( args.scene, 'S2*.zip' )

    return scenes


def parseArguments(args=None):

    """
    Placeholder
    """

    # parse command line arguments
    parser = argparse.ArgumentParser(description='sentinel-2 process ard')
    parser.add_argument('scene', action="store")

    # batch processing
    parser.set_defaults(batch=False)
    parser.add_argument('--batch',
                        help='batch',
                        dest='batch', action='store_true' )

    return parser.parse_args(args)


def main():

    """
    Placeholder
    """

    # parse arguments
    args = parseArguments()
    obj = Exporter()

    # for each scene
    scenes = getSceneList( args )
    for scene in scenes:

        # generated cloud-masked geotiffs
        if os.path.exists( scene ):
            obj.getImages( scene )

    return

# execute main
if __name__ == '__main__':
    main()

