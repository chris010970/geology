import os
import sys
import argparse
import shutil

from osgeo import gdal, ogr
from zipfile import ZipFile

sys.path.append( os.path.join( os.path.dirname( sys.path[0]), '../utility' ) )
from fs import getFileList, getFile
from srs import getEpsgCode
import ogr2ogr

class Exporter:

    # images to export
    images_10m = [ '*B02_10m.jp2', '*B03_10m.jp2', '*B04_10m.jp2', '*B08_10m.jp2' ]
    images_20m = [ '*B05_20m.jp2', '*B06_20m.jp2', '*B07_20m.jp2', '*B11_20m.jp2', '*B12_20m.jp2' ]
    images_60m = [ '*B01_60m.jp2', '*B09_60m.jp2' ]

    def __init__(self ):

        """
        Placeholder
        """

        # increase system memory usage
        os.environ['GDAL_CACHEMAX'] = '2048'
        gdal.UseExceptions()

        return


    def getImages( self, scene, out_path=None, overwrite=False ):

        """
        Placeholder
        """

        # initialise output path
        raw_path = os.path.dirname( scene )
        if out_path is None:
            out_path = raw_path.replace( 'raw', 'ard' )

        # postpone export if path exists and no overwrite
        if not os.path.exists( out_path ) or overwrite:

            # extract SAFE zip into tmp folder
            with ZipFile( scene, 'r' ) as zipObj:
                zipObj.extractall( os.path.join( raw_path, 'tmp/' ) )

            # initialise output path
            if not os.path.exists( out_path ):
                os.makedirs( out_path, 0o755 )

            # get cloud mask
            mask_pathname = self.getCloudMask( raw_path, out_path )

            # export to geotiff
            self.exportToGeoTiff( raw_path, out_path, self.images_60m, mask=mask_pathname )
            self.exportToGeoTiff( raw_path, out_path, self.images_20m, mask=mask_pathname )
            self.exportToGeoTiff( raw_path, out_path, self.images_10m, mask=mask_pathname )

            # remove decompressed sub-directory
            shutil.rmtree( os.path.join( raw_path, 'tmp/' ) )

        else:
            # report export bypass
            print ( 'Path exists - ignoring... {}'.format( out_path ) )

        return out_path


    def getCloudMask( self, raw_path, out_path ):

        """
        Placeholder
        """

        mask_pathname = None 

        # find gml
        gml = getFile( raw_path, '*CLOUDS*.gml' )
        if gml is not None:

            # projection not parsed correctly from l2a gml - retrieve from scene raster
            scene = getFile( raw_path, '*B02_10m.jp2' )
            if scene is not None:
                epsg = getEpsgCode( scene )

                # generate shape file using raster epsg
                shp = os.path.join( out_path, 'clouds.shp' )
                if ogr2ogr.main( [ "", "-f", "ESRI Shapefile", "-a_srs", 'EPSG:' + epsg, shp, gml ] ) is True:
                    mask_pathname = shp

        return mask_pathname


    def exportToGeoTiff( self, scene_path, out_path, images, mask=None ):

        """
        Placeholder
        """

        def createCopy( src, out_path ):

            """
            Placeholder
            """

            # open jp2 image            
            in_ds = gdal.Open( src  )
            driver = gdal.GetDriverByName( 'GTiff' )

            # recreate as geotiff
            pathname = out_path + '/' + os.path.splitext( os.path.basename( src ) )[0] + '.tif' 
            out_ds = driver.CreateCopy( pathname, in_ds, options=[ 'TILED=YES', 'COMPRESS=DEFLATE', 'INTERLEAVE=PIXEL', 'BLOCKXSIZE=256', 'BLOCKYSIZE=256', 'NBITS=16', 'NUM_THREADS=2' ] )

            # close datasets
            out_ds = None
            in_ds = None
            
            return pathname

        # open cloud mask 
        mask_ds = None
        if mask is not None and os.path.isfile( mask ):
            mask_ds  = gdal.OpenEx( mask, gdal.OF_VECTOR ) 

        # for each entry in list
        for image in images:

            # find file 
            src = getFile( scene_path, image )
            if src is not None:

                # create geotiff copy
                print ( 'Exporting to geotiff: {}'.format( src ) )            
                pathname = createCopy( src, out_path )

                scene_ds = gdal.Open( pathname, gdal.GA_Update )
                if scene_ds is not None:

                    # burn cloud polygons into image as no data
                    scene_ds.GetRasterBand( 1 ).SetNoDataValue( 0 )
                    if mask_ds is not None:
                        gdal.Rasterize( scene_ds, mask_ds, bands = [1], burnValues = [0] )

                    scene_ds = None 

                print ( 'OK!' ) 

            else:

                # burn cloud polygons into image as no data
                print ( 'Unable to locate file {} in path: {}'.format( image, scene_path ) )            

        return

