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
        scenes = getFileList( args.scene, 'AST*.hdf' )

    return scenes


def parseArguments(args=None):

    """
    Placeholder
    """

    # parse command line arguments
    parser = argparse.ArgumentParser(description='aster l1t exporter')
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

        # export hdf sub-datasets to geotiff
        obj.process( scene )

    return

# execute main
if __name__ == '__main__':
    main()


