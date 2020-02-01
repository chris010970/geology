import os
import sys
import requests
import xmltodict

from netrc import netrc
from datetime import datetime
from bs4 import BeautifulSoup
from shapely.geometry.polygon import Polygon


class Downloader:

    def __init__(self, root_path='/data/raw/tau-ken/25994' ):

        """
        Placeholder
        """

        # get root + authentication url
        self._root_url = "https://e4ftl01.cr.usgs.gov/ASTER_B/ASTT/AST_L1T.003"
        self._urs = 'urs.earthdata.nasa.gov' 

        # resolve earthdata authentication
        self._netrcDir = os.path.expanduser("~/.netrc")
        self._root_path = root_path

        return


    def process ( self, args, bbox ):

        """
        Placeholder
        """

        # convert strings to epoch times
        start_epoch = datetime.strptime( args.start_date, '%d/%m/%Y' ).timestamp()
        end_epoch = datetime.strptime( args.end_date, '%d/%m/%Y' ).timestamp()

        # get aoi polygon
        aoi = Polygon( [ ( bbox[ 'ulx' ], bbox[ 'uly' ] ),
            ( bbox[ 'lrx' ], bbox[ 'uly' ] ),
            ( bbox[ 'lrx' ], bbox[ 'lry' ] ),
            ( bbox[ 'ulx' ], bbox[ 'lry' ] ),
            ( bbox[ 'ulx' ], bbox[ 'uly' ] ) ] )

        # between start and end dates
        epoch = start_epoch
        while epoch < end_epoch:

            # construct subfolder names
            current_date = datetime.fromtimestamp(epoch)
            sub_folder = current_date.strftime("%Y.%m.%d")

            # get metadata file list from remote directory
            url = '{}/{}/'.format ( self._root_url, sub_folder )
            meta_files = self.getRemoteFileList( url, '.xml' )

            print('Scraping: {}'.format( url ) )
            for f in meta_files:

                # parse hour from remote filename
                tokens = os.path.basename(f).split('_' )
                aos_time = int( tokens[2][-6:-4] )

                # apply constraint
                if aos_time >= args.start_hour and aos_time <= args.end_hour:

                    # read remote meta data into dict
                    doc = self.readRemoteMetaFile( f ) 
                    if doc is not None:

                        # get boundary polygon
                        cov = self.getSceneCoverage( doc )
                        if cov.intersects( aoi ):

                            # create raw folder
                            raw_folder = os.path.join( self._root_path, current_date.strftime("%Y%m%d") + '_' + tokens[2][-6: ] )
                            if not os.path.exists( raw_folder ):
                                os.makedirs( raw_folder, 0o755 )

                            # write meta to file
                            with open( os.path.join( raw_folder, os.path.basename( f ) ), 'w+' ) as meta:
                                meta.write( xmltodict.unparse( doc, pretty=True ))

                            # write dataset to file
                            dataset = os.path.basename(f).replace( '.hdf.xml', '.hdf' )
                            url = os.path.join( os.path.dirname( f ), dataset )

                            self.getDataset( url, os.path.join( raw_folder, dataset ) )

            # move onto next day
            epoch += 60 * 60 * 24

        return


    def getRemoteFileList( self, url, ext ):

        """
        Placeholder
        """

        # parse html listing
        page = requests.get(    url, 
                                stream=True, 
                                auth=(netrc(self._netrcDir).authenticators(self._urs)[0], 
                                        netrc(self._netrcDir).authenticators(self._urs)[2])).text

        soup = BeautifulSoup( page, 'html.parser' )
        return [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]


    def readRemoteMetaFile( self, f ):

        """
        Placeholder
        """

        # retrieve remote meta file
        content = requests.get( f, stream=True, 
            auth=(netrc(self._netrcDir).authenticators(self._urs)[0], netrc(self._netrcDir).authenticators(self._urs)[2])).text

        # load meta xml into dict
        return xmltodict.parse( content )


    def getSceneCoverage( self, doc ):

        """
        Placeholder
        """

        # parse boundary points from xml
        container = doc[ 'GranuleMetaDataFile' ][ 'GranuleURMetaData' ][ 'SpatialDomainContainer' ][ 'HorizontalSpatialDomainContainer' ]

        extent = []
        for schema in container[ 'GPolygon' ][ 'Boundary' ][ 'Point' ]:
            extent.append( { 'lon' : float( schema[ 'PointLongitude' ] ), 
                            'lat' : float( schema[ 'PointLatitude' ] ) } )

        # return polygon
        return Polygon( [ ( extent[ 0 ][ 'lon' ], extent[ 0 ][ 'lat' ] ),
                    ( extent[ 1 ][ 'lon' ], extent[ 1 ][ 'lat' ] ),
                    ( extent[ 2 ][ 'lon' ], extent[ 2 ][ 'lat' ] ),
                    ( extent[ 3 ][ 'lon' ], extent[ 3 ][ 'lat' ] ),
                    ( extent[ 0 ][ 'lon' ], extent[ 0 ][ 'lat' ] ) ] )
                    

    def getDataset( self, url, local_pathname ):

        """
        Placeholder
        """

        # submit request and download file
        print('Downloading file: {} -> {}'.format(url, os.path.dirname( local_pathname )))
        with requests.get( url, stream=True, auth=(netrc(self._netrcDir).authenticators(self._urs)[0], 
                                    netrc(self._netrcDir).authenticators(self._urs)[2])) as response:

            # status ok
            if response.status_code == 200:

                response.raw.decode_content = True
                content = response.raw

                # write content to file in chunks
                with open( local_pathname, 'wb') as d:
                    while True:
                        chunk = content.read(16 * 1024)
                        if not chunk:
                            break
                        d.write(chunk)

                # report success
                print('Downloaded OK!' )
            else:
                
                # error returned from server
                print('Download Error {}'.format(response.status_code ) )

        return

