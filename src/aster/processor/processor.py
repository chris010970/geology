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

        self._products = {   'composite' : [
                                            { 'name' : '3_2_1',     'channels' : [ 3, 2, 1 ] },
                                            { 'name' : '6_4_1',     'channels' : [ 6, 4, 1 ] },
                                            { 'name' : '6_4_3',     'channels' : [ 6, 4, 3 ] },
                                            { 'name' : '4_6_8',     'channels' : [ 4, 6, 8 ] },
                                            { 'name' : '7_2_1',     'channels' : [ 7, 2, 1 ] }
                                            ],
                            'ratio' : [
                                            { 'name' : '4-8_4-2_8-9',     'channels' : [ (4, 8), (4, 2), (8, 9) ] },
                                            { 'name' : '6-8_4-5_2-4',     'channels' : [ (6, 8), (4, 5), (2, 4) ] },
                                            { 'name' : '1-4_3-4_5-2',     'channels' : [ (1, 4), (3, 4), (5, 2) ] },
                                            { 'name' : '4-1_4-5_4-7',     'channels' : [ (4, 1), (4, 5), (4, 7) ] }
                                    ],
                            'pca' : [
                                            { 'name' : 'pca-1_2_3', 'channels' : [ 1, 2, 3, 4, 5, 6, 7, 8, 9 ], 'components' : [ 0, 1, 2 ] },
                                    ] }


        self._channels = [ 'Data1', 'Data2', 'Data3N', 'Data4', 'Data5', 'Data6', 'Data7', 'Data8', 'Data9' ]
        return


    def process( self, aois, out_path ):

        """
        Placeholder
        """

        # generate mosaics
        mosaic_path = os.path.join( out_path, 'mosaic' )
        self.mergeImages( aois, mosaic_path )    

        # get channel images
        dataset = self.getMosaicDataset( mosaic_path, '*_reflectance.tif' )
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

        print ( datasets )

        # create out path
        if not os.path.exists( out_path ):
            os.makedirs( out_path, 0o755 )

        # for each channel
        for channel in self._channels:

            files = []

            # locate corresponding channel file within dataset folders
            for dataset in datasets:
                f = getFile( dataset, '*{}_reflectance.tif'.format ( channel ) )
                if f is not None:
                    files.append ( f )

            # merge into one with warp
            pathname = '{}/{}_reflectance.tif'.format ( out_path, channel )
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
            match = re.search( 'Data[0-9]+', os.path.basename( f ) )
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
            save_rgb( rgb_pathname, img_pc[:,:,:3], stretch=(0.02,0.98) )

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
