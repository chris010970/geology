import os
import re
import sys
import shutil
import numpy as np

from osgeo import gdal, ogr
from spectral import principal_components, imshow, save_rgb

sys.path.append( os.path.join( os.path.dirname( sys.path[0]), '../utility' ) )
from fs import getFileList, getFile
from ps import execute

class Processor:


    def __init__(self ):

        """
        Placeholder
        """

        # increase system memory usage
        os.environ['GDAL_CACHEMAX'] = '2048'
        gdal.UseExceptions()

        # product definitions
        self._products = {   'composite' : [
                                            { 'name' : '4_3_2',     'channels' : [ 4, 3, 2 ] },
                                            { 'name' : '8_4_3',     'channels' : [ 8, 4, 3 ] }, 
                                            { 'name' : '11_8_4',    'channels' : [ 11, 8, 4 ] },
                                            { 'name' : '11_12_2',   'channels' : [ 11, 12, 2 ] },
                                            { 'name' : '11_12_4',   'channels' : [ 11, 12, 4 ] },
                                            { 'name' : '12_4_2',    'channels' : [ 12, 4, 2 ] },
                                            { 'name' : '12_8_3',    'channels' : [ 12, 8, 3 ] },
                                            { 'name' : '12_11_2',   'channels' : [ 12, 11, 2 ] } 
                                    ],
                            'ratio' : [
                                            { 'name' : '3-2_4-3_11-12',     'channels' : [ (3, 2), (4, 3), (11, 12) ] },
                                            { 'name' : '4-3_4-2_11-12',     'channels' : [ (4, 3), (4, 2), (11, 12) ] },
                                            { 'name' : '4-3_11-2_12-4',     'channels' : [ (4, 3), (11, 2), (12, 4) ] },
                                            { 'name' : '4-8_12-11_3-4',     'channels' : [ (4, 8), (12, 11), (3, 4) ] },
                                            { 'name' : '11-4_4-2_11-12',     'channels' : [ (11, 4), (4, 2), (11, 12) ] }
                                    ],
                            'pca' : [
                                            { 'name' : 'pca-11_12_2', 'channels' : [ 11, 12, 2 ], 'components' : [ 0, 1, 2 ] },
                                            { 'name' : 'pca-11_12_4', 'channels' : [ 11, 12, 4 ], 'components' : [ 0, 1, 2 ] },
                                            { 'name' : 'pca-salehi',  'channels' : [ 2, 3, 4, 5, 6, 7, 11, 12 ], 'components' : [ 3, 7, 4 ] } 
                                    ] }

        self._channels = [ 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B11', 'B12' ]

        return


    def process( self, aois, out_path ):

        """
        Placeholder
        """

        # generate mosaics
        mosaic_path = os.path.join( out_path, 'mosaic' )
        self.mergeImages( aois, mosaic_path )    

        # get channel images
        dataset = self.getMosaicDataset( mosaic_path, 'B*_10m.tif' )
        if len ( dataset[ 'channels' ] ) == len( self._channels ):

            # generate false colour composite images
            self.generateCompositeProducts( dataset, out_path )

            # generate false colour composite images
            self.generateRatioProducts( dataset, out_path )

            # generate pca composite images
            self.generatePrincipalComponentProducts( dataset, out_path )

        return


    def mergeImages( self, datasets, out_path ):

        """
        Placeholder
        """

        # create out path
        if not os.path.exists( out_path ):
            os.makedirs( out_path, 0o755 )

        # for each channel
        for channel in self._channels:

            files = []

            # locate corresponding channel file within dataset folders
            for dataset in datasets:
                f = getFile( dataset, '*{}_10m.tif'.format ( channel ) )
                if f is not None:
                    files.append ( f )

            # merge into one with warp
            pathname = '{}/{}_10m.tif'.format ( out_path, channel )
            gdal.Warp( pathname, files )
                
        return


    def getMosaicDataset( self, path, search ):

        """
        Placeholder
        """

        # return package
        dataset = { 'srs' : None, 'channels' : [] }
        
        # load band data into list
        files = sorted( getFileList( path, search ) )
        for f in files:

            # get band index
            match = re.search( 'B[0-9]{2}', f )
            if match:

                # load geotiff
                ds = gdal.Open( f )
                if ds is not None:  

                    # get srs attributes
                    if dataset[ 'srs' ] is None:
                        dataset[ 'srs' ] = { 'geo' : ds.GetGeoTransform(),
                                                'prj' : ds.GetProjection() }

                    # create dictionary entry
                    dataset[ 'channels' ].append( 
                            {   'index' :  int( ''.join( filter( str.isdigit, match.group(0) ) ) ),
                                'data' : ds.GetRasterBand(1).ReadAsArray(),
                            } 
                        )

        return dataset


    def generateCompositeProducts( self, dataset, out_path ):

        """
        Placeholder
        """

        # create product path
        product_path = os.path.join( out_path, 'composite' )
        if not os.path.exists( product_path ):
            os.makedirs( product_path, 0o755 )

        # get channel images pertaining to product
        print ( 'Creating composite products: {}'.format( product_path ) )
        for product in self._products[ 'composite' ]:

            rgb = []
            for index in product[ 'channels' ]:
                rgb.append( self.getChannelData( dataset, index ) )

            # save rgb image
            rgb_pathname = os.path.join( product_path, product[ 'name' ] + '.jpg' )
            save_rgb( rgb_pathname, np.dstack( rgb ), stretch=(0.02,0.98) )

            # save decorrelation stretch version of rgb image
            dcs_pathname = rgb_pathname.replace( '.jpg', '-dcs.jpg' )
            execute( os.path.join( os.path.dirname( sys.path[0]), '../bin/dstretch' ),
                        [ rgb_pathname, dcs_pathname ] )

            # copy dcs image into geotiff
            self.writeGeoImage( dcs_pathname, dataset[ 'srs' ] )                    

        return


    def generateRatioProducts( self, dataset, out_path ):

        """
        Placeholder
        """

        # create product path
        product_path = os.path.join( out_path, 'ratio' )
        if not os.path.exists( product_path ):
            os.makedirs( product_path, 0o755 )

        # get channel images pertaining to product
        print ( 'Creating ratio products: {}'.format( product_path ) )
        for product in self._products[ 'ratio' ]:

            rgb = []
            for index in product[ 'channels' ]:

                c1 = self.getChannelData( dataset, index[ 0 ] )
                c2 = self.getChannelData( dataset, index[ 1 ] )

                rgb.append( c1 / c2 )

            # save rgb image
            rgb_pathname = os.path.join( product_path, product[ 'name' ] + '.jpg' )
            save_rgb( rgb_pathname, np.dstack( rgb ), stretch=(0.02,0.98) )

            # save decorrelation stretch version of rgb image
            dcs_pathname = rgb_pathname.replace( '.jpg', '-dcs.jpg' )
            execute( os.path.join( os.path.dirname( sys.path[0]), '../bin/dstretch' ),
                        [ rgb_pathname, dcs_pathname ] )

            # copy dcs image into geotiff
            self.writeGeoImage( dcs_pathname, dataset[ 'srs' ] )                    

        return


    def generatePrincipalComponentProducts( self, dataset, out_path ):

        """
        Placeholder
        """

        # create product path
        product_path = os.path.join( out_path, 'pca' )
        if not os.path.exists( product_path ):
            os.makedirs( product_path, 0o755 )

        # get channel images pertaining to product
        print ( 'Creating principal component products: {}'.format( product_path ) )
        for product in self._products[ 'pca' ]:

            channels = []
            for index in product[ 'channels' ]:
                channels.append( self.getChannelData( dataset, index ) )

            img = np.dstack( channels )

            # compute pca transformation
            pc = principal_components( img )
            img_pc = pc.transform( img )

            # save rgb image
            rgb_pathname = os.path.join( product_path, product[ 'name' ] + '.jpg' )
            save_rgb( rgb_pathname, img_pc[:,:,:3], stretch=(0.05,0.95) )

            # save decorrelation stretch version of rgb image
            dcs_pathname = rgb_pathname.replace( '.jpg', '-dcs.jpg' )
            execute( os.path.join( os.path.dirname( sys.path[0]), '../bin/dstretch' ),
                        [ rgb_pathname, dcs_pathname ] )

            # copy dcs image into geotiff
            self.writeGeoImage( dcs_pathname, dataset[ 'srs' ] )                    

        return


    def getChannelData( self, dataset, index ):

        """
        Placeholder
        """

        # return data associated with channel index
        data = None
        for channel in dataset[ 'channels' ]:

            if channel[ 'index' ] == index:
                data = channel[ 'data' ]

        return data


    def writeGeoImage( self, pathname, srs ):

        """
        Placeholder
        """

        # load geotiff
        in_ds = gdal.Open( pathname )
        if in_ds is not None:  

            # get driver and create copy
            driver = gdal.GetDriverByName( 'GTiff' )
            out_ds = driver.CreateCopy( os.path.splitext( pathname )[ 0 ] + '.tif', in_ds, options=[ 'TILED=YES', 'COMPRESS=DEFLATE'] ) 
            if out_ds is not None:

                out_ds.SetGeoTransform( srs[ 'geo'] )
                out_ds.SetProjection( srs[ 'prj'] )

                out_ds = None

        return

