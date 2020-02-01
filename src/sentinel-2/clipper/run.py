import os
import sys
import argparse

from clipper import Clipper

sys.path.append( os.path.join( os.path.dirname( sys.path[0]), '../utility' ) )
from fs import getPathList
from dp import getDateTimeString

def getSceneList(args):

    """
    Placeholder
    """

    # assume single scene - else collect list
    pathlist = [ args.scene ]
    if args.batch is True:
        pathlist = getPathList( args.scene, os.path.join( args.scene, '*20*_*' ) )

    # get path list
    scenes = []
    for path in pathlist:

        dt = getDateTimeString( path )
        scenes.append ( path[ 0 : path.find( dt ) + len(dt) ] )

    return list( set ( scenes ) )


def parseArguments(args=None):

    """
    Placeholder
    """

    # parse command line arguments
    parser = argparse.ArgumentParser(description='sentinel-2 processor')
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

    # define aois
    aois = [ 
        {   'name' : 'shokpar',
            'bbox' : [ 43.1547, 74.8458, 43.1692, 74.8853 ]
        },
        {   'name' : 'gargarinskoye',
            'bbox' : [ 43.3863, 74.6333, 43.4083, 74.6741 ]
        },
        {   'name' : 'alaygyr',
            'bbox' : [ 49.0279, 74.4044, 49.0446, 74.4551 ]
        },
        {   'name' : 'kairakty',
            'bbox' : [ 48.6708, 73.2317, 48.7014, 73.2972 ]
        } 
        ]

    # for each scene
    scenes = getSceneList( args )
    for scene in scenes:

        # create aoi sub-images
        obj = Clipper()
        obj.process( scene, aois, distance=10000 )

    return

# execute main
if __name__ == '__main__':
    main()

