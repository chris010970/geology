import os
import re
import sys
import osr

from osgeo import gdal, ogr
from shapely.geometry.polygon import Polygon

# utility functions
sys.path.append( os.path.join( os.path.dirname( sys.path[0]), '../utility' ) )
from fs import getFileList, getFile


class Clipper:

    def __init__( self ):

        """
        Placeholder
        """

        # increase system memory usage
        os.environ['GDAL_CACHEMAX'] = '2048'
        gdal.UseExceptions()

        self._epsg = 28412

        return


    def process( self, scene_path, aois, out_path=None, distance=100 ):

        """
        Placeholder
        """

        aoi_paths = []

        # get exported geotiff list
        files = getFileList( scene_path, '*_B*_*m.tif' )
        for f in files: 

            # open image
            ds = gdal.Open( f )
            if ds is not None:

                # get aoi to image transform
                extent = self.getExtent ( ds )
                coord_tx = self.getCoordinateTransform( ds )

                # for each aoi
                for aoi in aois:

                    # get buffered bounding box coordinates
                    bbox = self.getBoundingBox( aoi[ 'bbox'], coord_tx[ 'aoi_image' ], distance=distance )

                    """
                    ulx, uly, ulz = coord_rx.TransformPoint( bbox[ 'lrx' ], bbox[ 'lry' ] )
                    lrx, lry, lrz = coord_rx.TransformPoint( bbox[ 'ulx' ], bbox[ 'uly' ] )
                    print ( aoi[ 'name' ], ulx, uly, lrx, lry )
                    """

                    if self.overlapsScene( extent, bbox ) is True:

                        # create aoi sub-path
                        aoi_path = os.path.join( scene_path, aoi[ 'name'] + '/' )
                        if not os.path.exists( aoi_path ):
                            os.makedirs(aoi_path, 0o755 )

                        # generate aoi sub-image aligned with bbox
                        aoi_pathname = os.path.join( aoi_path, os.path.basename( f ) )
                        print ( 'Creating AoI image: {}'.format( aoi_pathname ) )

                        # reproject bbox to local utm and fix pixel resolution
                        bbox = self.getBoundingBox( aoi[ 'bbox'], coord_tx[ 'aoi_local' ], distance=distance )
                        res_option = self.getResolution( os.path.basename( f ))

                        # reproject bbox to local utm - setup warp options
                        options = '-t_srs EPSG:{} -tr {} -te {} {} {} {}'. format ( self._epsg, res_option, bbox[ 'ulx'], bbox[ 'lry' ], bbox[ 'lrx' ], bbox[ 'uly'] )

                        gdal.Warp( aoi_pathname, ds, options=options )

                        # resample 20m resolution sub-image to 10m
                        if '20m' in aoi_pathname:

                            print ( 'Creating resampled AoI image: {}'.format( aoi_pathname.replace( '20m', '10m' ) ) )

                            # rerun gdalwarp
                            options = '-t_srs EPSG:{} -tr 10 -10 -te {} {} {} {}'. format ( self._epsg, bbox[ 'ulx'], bbox[ 'lry' ], bbox[ 'lrx' ], bbox[ 'uly'] )
                            gdal.Warp( aoi_pathname.replace( '20m', '10m' ), ds, options=options )

                        # record aoi image location
                        aoi_paths.append ( aoi_path )

        return list( set( aoi_paths ) )


    def getExtent( self, ds ):

        """
        Placeholder
        """

        # create transform
        geo = ds.GetGeoTransform()
        return { 
                    'ulx' : geo[ 0 ],
                    'uly' : geo[ 3 ],
                    'lrx' : geo[ 0 ] + ( ds.RasterXSize * geo[ 1 ] ),
                    'lry' : geo[ 3 ] + ( ds.RasterYSize * geo[ 5 ] )
        }    


    def getCoordinateTransform( self, ds ):

        """
        Placeholder
        """

        # retrieve srs from image
        image = osr.SpatialReference( wkt=ds.GetProjection() )

        # aoi in lat / lon
        aoi = osr.SpatialReference()
        aoi.ImportFromEPSG( 4326 )

        # output in local utm
        local = osr.SpatialReference()
        local.ImportFromEPSG( self._epsg )

        # create transform
        return { 'aoi_image' : osr.CoordinateTransformation( aoi, image ), 
                    'aoi_local' : osr.CoordinateTransformation( aoi, local ) }


    def getBoundingBox( self, aoi, coord_tx, distance=100 ):

        """
        Placeholder
        """

        # sort lat / lon min and max
        lat = [ min ( aoi[ 0 ], aoi[ 2 ] ), max( aoi[ 0 ], aoi[ 2 ] ) ]
        lon = [ min ( aoi[ 1 ], aoi[ 3 ] ), max( aoi[ 1 ], aoi[ 3 ] ) ]

        # transform lat / lon to image crs
        ulx, uly, ulz = coord_tx.TransformPoint( lon[ 0 ], lat[ 1 ] )
        lrx, lry, lrz = coord_tx.TransformPoint( lon[ 1 ], lat[ 0 ] )

        # lock to 20m grid
        ulx = ulx + ( 20.0 - ulx % 20 )
        uly = uly + ( 20.0 - uly % 20 )

        lrx = lrx + ( 20.0 - lrx % 20 )
        lry = lry + ( 20.0 - lry % 20 )

        # return bbox window
        return {
                    'ulx' : ulx - distance, 
                    'uly' : uly + distance, 
                    'lrx' : lrx + distance, 
                    'lry' : lry - distance 
        }


    def overlapsScene( self, extent, bbox ):

        """
        Placeholder
        """

        # create scene extent polygon
        p1 = Polygon( [ ( extent[ 'ulx' ], extent[ 'uly' ] ),
                        ( extent[ 'lrx' ], extent[ 'uly' ] ),
                        ( extent[ 'lrx' ], extent[ 'lry' ] ),
                        ( extent[ 'ulx' ], extent[ 'lry' ] ),
                        ( extent[ 'ulx' ], extent[ 'uly' ] ) ] )
        
        # create aoi polygon
        p2 = Polygon( [ ( bbox[ 'ulx' ], bbox[ 'uly' ] ),
                        ( bbox[ 'lrx' ], bbox[ 'uly' ] ),
                        ( bbox[ 'lrx' ], bbox[ 'lry' ] ),
                        ( bbox[ 'ulx' ], bbox[ 'lry' ] ),
                        ( bbox[ 'ulx' ], bbox[ 'uly' ] ) ] )
        
        return p1.intersects( p2 )


    def getResolution( self, filename ):

        # parse for date time sub directory
        m = re.search( '[0-9]{2}m', filename )
        res = int(re.sub(r'[^\d-]+', '', str(m.group(0) ) ) )

        return '{} {}'.format( res, -res ) 

