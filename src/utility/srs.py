
import osr
import gdal
import math

def getTransform( in_pathname, options ):

    """
    Placeholder
    """

    # need target srs
    transform = options
    if ( 't_epsg' in options ):

        # open raster
        ds = gdal.Open( in_pathname )
        if ds is not None:

            # get spatial reference systems    
            s_prj = ds.GetProjection()
            s_srs = osr.SpatialReference( wkt = s_prj )

            t_srs = osr.SpatialReference ()
            t_srs.ImportFromEPSG ( int( options[ 't_epsg' ] ) )

            # compute bounding box coordinates in target srs
            s_geo = ds.GetGeoTransform ()
            tx = osr.CoordinateTransformation ( s_srs, t_srs )

            x_size = ds.RasterXSize
            y_size = ds.RasterYSize

            (ulx, uly, ulz ) = tx.TransformPoint( s_geo[0],  s_geo[3])
            (lrx, lry, lrz ) = tx.TransformPoint( s_geo[0] + s_geo[1] * x_size, \
                                                  s_geo[3] + s_geo[5] * y_size )

            # define pixel resolution
            if 'res_x' in options and 'res_y' in options and options[ 'res_x' ] is not None and options[ 'res_y' ] is not None:
                res_x = int( options[ 'res_x' ] )
                res_y = int( options[ 'res_y' ] )
            else:
                res_x = s_geo[ 1 ]
                res_y = s_geo[ 5 ]

            # align with grid
            ulx = math.floor( ulx / res_x ) * res_x; uly = math.floor( uly / res_y ) * res_y 
            lrx = math.ceil( lrx / res_x ) * res_x; lry = math.ceil( lry / res_y ) * res_y

            # compute dimensions of reprojected image
            transform [ 'cols' ] = int( (lrx - ulx) / res_x )
            transform [ 'rows' ] = int( (lry - uly) / res_y )

            # define target warp parameters
            transform [ 'geo' ] = ( ulx, res_x, s_geo[2], uly, s_geo[4], res_y )
            ds = None


    return transform


def getEpsgCode( pathname ):

    """
    Placeholder
    """

    code = None

    # open raster file
    ds = gdal.Open( pathname )
    if ds is not None:

        # retrieve projection from dataset
        prj = ds.GetProjection()
        srs = osr.SpatialReference(wkt=prj)

        srs.AutoIdentifyEPSG()
        code = srs.GetAuthorityCode(None)

    return code


