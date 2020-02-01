import os
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


    def process( self, scene_path, aois, out_path=None, distance=100, ext='*_reflectance.tif' ):

        """
        Placeholder
        """

        aoi_paths = []

        # get exported geotiff list
        files = getFileList( scene_path, ext )
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
                    if self.overlapsScene( extent, bbox ) is True:

                        # create aoi sub-path
                        aoi_path = os.path.join( scene_path, aoi[ 'name'] + '/' )
                        if not os.path.exists( aoi_path ):
                            os.makedirs(aoi_path, 0o755 )

                        # generate aoi sub-image aligned with bbox
                        aoi_pathname = os.path.join( aoi_path, os.path.basename( f ) )
                        print ( 'Creating AoI image: {}'.format( aoi_pathname ) )

                        # reproject bbox to local utm - setup warp options
                        bbox = self.getBoundingBox( aoi[ 'bbox'], coord_tx[ 'aoi_local' ], distance=distance )
                        options = '-t_srs EPSG:{} -tr 15 -15 -te {} {} {} {}'. format ( self._epsg, bbox[ 'ulx'], bbox[ 'lry' ], bbox[ 'lrx' ], bbox[ 'uly'] )

                        gdal.Warp( aoi_pathname, ds, options=options )

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

        # lock to 30m grid
        ulx = ulx + ( 30.0 - ulx % 30 )
        uly = uly + ( 30.0 - uly % 30 )

        lrx = lrx + ( 30.0 - lrx % 30 )
        lry = lry + ( 30.0 - lry % 30 )

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

