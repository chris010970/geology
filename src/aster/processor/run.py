import os
import sys
import argparse

from processor import Processor

# add utility functions
sys.path.append( os.path.join( os.path.dirname( sys.path[0]), '../utility' ) )
from fs import getPathList
from dp import getDateTime, getTle


def getRootPath( scene ):

    """
    Placeholder
    """

    # get tle
    tle = getTle( scene )
    return scene[ 0: scene.find( tle ) + len( tle ) ]


def getDateList(args):

    """
    Placeholder
    """

    # assume single scene - else collect list
    scenes = [ args.scene ]
    if args.batch is True:
        scenes = getPathList( args.scene, os.path.join( args.scene, '*20*_*' ) )
        
    # create list of datetime folders
    dates = []
    for scene in scenes:

        dt = getDateTime( scene )
        d = dt.strftime( '%Y%m%d')

        if d is not dates :
            dates.append( d )

    # ensure non duplicate list
    return list( set( dates ) ) 


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
    root = getRootPath( args.scene )

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

    # create object and get unique datetimes
    dates = getDateList( args )
    obj = Processor()

    # for each aoi
    for aoi in aois:
        for d in dates:

            pathlist = getPathList( root, '{}*{}_*/{}'.format( root, d, aoi[ 'name' ] ) )
            if len( pathlist ) > 0:

                # execute processing
                out_path = '{}/{}/{}_000000'.format ( root.replace( 'ard', 'products' ), aoi[ 'name' ], d )
                obj.process( pathlist, out_path )

    return

# execute main
if __name__ == '__main__':
    main()

