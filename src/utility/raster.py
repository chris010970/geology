import os
import sys
import numpy as np
import shutil

from osgeo import gdal, osr
from utility import srs


def createCopy( in_pathname, datatype, out_pathname=None,  **kwargs ):

    """
    Placeholder
    """

    out_ds = None

    # get default output name
    if out_pathname is None:
        out_pathname = in_pathname.replace( '.tif', '-copy.tif' )

    # delete existing file if overwrite enabled
    overwrite = kwargs.pop( 'overwrite', False )
    if os.path.exists( out_pathname ) and overwrite is True:
        os.remove( out_pathname )

    # output file does not exist
    if not os.path.exists( out_pathname ):

        # open input file
        in_ds = gdal.Open( in_pathname )
        if in_ds is not None:

            # get band and dimensions
            in_band = in_ds.GetRasterBand( 1 )
            nCols, nRows = in_band.XSize, in_band.YSize

            # create output object - single byte band
            driver = gdal.GetDriverByName("GTiff")
            out_ds = driver.Create( out_pathname, nCols, nRows, 1, datatype, kwargs.pop( 'options', None ) )

            if ( out_ds is not None ):

                out_band = out_ds.GetRasterBand(1)

                # set geotransform / projection as input
                out_ds.SetGeoTransform( in_ds.GetGeoTransform() )  
                out_ds.SetProjection( in_ds.GetProjection() )

                # need nodata value for postgis
                no_data = 2 ** gdal.GetDataTypeSize( datatype ) - 1
                out_band.SetNoDataValue( no_data )

                # get range - either defined or image stats
                data_min = kwargs.pop( 'data_min', None ); 
                data_max = kwargs.pop( 'data_max', None ) 

                if data_min is None or data_max is None:
                    stats = in_band.GetStatistics( True, True )
                    data_min = stats[ 0 ]; data_max = stats[ 1 ]

                # compute linear scale and offset
                out_band.SetScale( ( data_max - data_min  ) / ( no_data - 1 ) )
                out_band.SetOffset( data_min )


        # close input
        in_ds = None

    return out_ds, out_pathname


def fillNoData( pathname, band_index=1, mask_band=None, md=2, si=1, overwrite=False ):

    """
    Placeholder
    """

    res = None

    # open file for updates
    ds = gdal.Open( pathname, gdal.GA_Update )
    if ds is not None:

        # call api function to plug gaps
        res = gdal.FillNodata(  targetBand=ds.GetRasterBand(band_index), 
                                maskBand=mask_band, 
                                maxSearchDist=md, 
                                smoothingIterations=si )

        # close output
        ds.FlushCache() 
        ds = None

    return res


def nanToNoData( pathname, band_index=1 ):

    """
    Placeholder
    """

    # open input file
    ds = gdal.Open( pathname, gdal.GA_Update )
    if ds is not None:

        band = ds.GetRasterBand( band_index )
        nCols, nRows = band.XSize, band.YSize

        no_data = band.GetNoDataValue()

        # for each row
        rowRange = range( nRows )
        for row in rowRange:

            # locate nan values
            data = band.ReadAsArray( 0, row, nCols, 1 )
            idx = np.isnan( data )

            # set nan values to no data
            data[ idx ] = no_data
            band.WriteArray( data, 0, row )

        # flush and close
        ds.FlushCache()
        ds = None

    return


def reproject( in_pathname, out_pathname, warp_options, create_options=None ):

    """
    Placeholder
    """

    # need target srs
    if ( 't_epsg' in warp_options ):

        if ( 'geo' not in warp_options ):
            warp_options = srs.getTransform ( in_pathname, warp_options )

        # open raster
        in_ds = gdal.Open( in_pathname )
        if in_ds is not None:

            # create new image
            driver = gdal.GetDriverByName("GTiff")
            out_ds = driver.Create( out_pathname, warp_options[ 'cols' ], warp_options[ 'rows' ], in_ds.RasterCount, in_ds.GetRasterBand(1).DataType, create_options )

            # generate warp files
            if out_ds is not None:

                # get srs
                t_srs = osr.SpatialReference ()
                t_srs.ImportFromEPSG ( int( warp_options[ 't_epsg' ] ) )

                # set geotransform / projection in target image
                out_ds.SetGeoTransform( warp_options[ 'geo' ] )  
                out_ds.SetProjection( t_srs.ExportToWkt() )

                out_ds.SetDescription( in_ds.GetDescription() )

                # copy no data configuration
                nodata = in_ds.GetRasterBand(1).GetNoDataValue()
                if nodata is not None:
                    out_ds.GetRasterBand(1).SetNoDataValue( nodata )

                # copy description
                description = in_ds.GetRasterBand(1).GetDescription()
                out_ds.GetRasterBand(1).SetDescription( description )

                # compute warp
                res = gdal.ReprojectImage( in_ds, out_ds, in_ds.GetProjection(), out_ds.GetProjection(), gdal.GRA_Bilinear, 0, 0.05, options=[ 'NUM_THREADS=ALL_CPUS'] )

                # flush and close output
                out_ds.FlushCache()
                out_ds = None

    return


def rescale( in_pathname, datatype, out_pathname=None, band_index=1, **kwargs ):

    """
    Placeholder
    """

    # open input file
    in_ds = gdal.Open( in_pathname )
    if in_ds is not None:

        # create copy
        out_ds, out_pathname = createCopy( in_pathname, datatype, out_pathname=out_pathname, **kwargs )
        if out_ds is not None:

            # get bands and dimensions
            in_band = in_ds.GetRasterBand( band_index )
            out_band = out_ds.GetRasterBand( 1 )

            nCols, nRows = in_band.XSize, in_band.YSize

            # get min and max values from scale and offset
            type_max = 2 ** gdal.GetDataTypeSize( datatype ) - 2
            data_min = out_band.GetOffset(); data_max = out_band.GetOffset() + ( type_max * out_band.GetScale() )

            # for each row
            rowRange = range( nRows )
            for row in rowRange:

                # read row and transform
                in_data = in_band.ReadAsArray( 0, row, nCols, 1 )
                idx = ~np.isclose( in_data, in_band.GetNoDataValue() )

                in_data[ idx ] = ( in_data[ idx ] * in_band.GetScale() ) + in_band.GetOffset()

                # compute rescaled data
                out_data = np.zeros( ( 1, nCols ) )
                out_data[ idx ] = np.clip( in_data[ idx ], data_min, data_max )

                out_data[ idx ] = np.round ( ( in_data[ idx ] - out_band.GetOffset() ) / out_band.GetScale() )
                out_data[ ~idx ] = out_band.GetNoDataValue()

                # write array to output
                if datatype == gdal.GDT_UInt16:
                    out_data = np.uint16( out_data )
               
                if datatype == gdal.GDT_Byte:
                    out_data = np.uint8( out_data )

                out_band.WriteArray( out_data, 0, row )

            # close output
            out_ds.FlushCache() 
            out_ds = None

        # close input
        in_ds = None

    return out_pathname


def getScaleOffset( pathname, index=1 ):

    """
    Placeholder
    """

    scale = offset = None

    # open raster
    ds = gdal.Open( pathname )
    if ds is not None:

        # retrieve scale and offset
        scale = ds.GetRasterBand( index ).GetScale()
        offset = ds.GetRasterBand( index ).GetOffset()

        ds = None

    return scale, offset


def getNoDataValue( pathname, index=1 ):

    """
    Placeholder
    """

    value = None

    # open raster
    ds = gdal.Open( pathname )
    if ds is not None:

        # get no data value
        ds.GetRasterBand( index ).GetNoDataValue()
        ds = None

    return value


def setNoDataValue( pathname, value, index=1 ):

    """
    Placeholder
    """

    # open raster
    ds = gdal.Open( pathname, gdal.GA_Update )
    if ds is not None:

        print( pathname )

        # set no data value
        ds.GetRasterBand( index ).SetNoDataValue( value )
        ds.FlushCache()
        ds = None

    return 


def getHistogram( band, nbuckets=1000, percentiles=[1.0, 99.0] ):

    """
    Given a band handle, finds approximate percentile values and provides the
    gdal_translate invocation required to create an 8-bit PNG.
    Works by evaluating a histogram of the original raster with a large number of
    buckets between the raster minimum and maximum, then estimating the
    probability mass and distribution functions before reporting the percentiles
    requested.
    N.B. This technique is very approximate and hasn't been checked for asymptotic
    convergence. Heck, it uses GDAL's `GetHistogram` function in approximate mode,
    so you're getting approximate percentiles using an approximated histogram.
    Optional arguments:
    - `percentiles`: list of percentiles, between 0 and 100 (inclusive).
    - `nbuckets`: the more buckets, the better percentile approximations you get.
    """

    # Use GDAL to find the min and max
    (lo, hi, avg, std) = band.GetStatistics(True, True)

    # Use GDAL to calculate a big histogram
    rawhist = band.GetHistogram(min=lo, max=hi, buckets=nbuckets)
    binEdges = np.linspace(lo, hi, nbuckets+1)

    # Probability mass function. Trapezoidal-integration of this should yield 1.0.
    pmf = rawhist / (np.sum(rawhist) * np.diff(binEdges[:2]))

    # Cumulative probability distribution. Starts at 0, ends at 1.0.
    distribution = np.cumsum(pmf) * np.diff(binEdges[:2])

    # Which histogram buckets are close to the percentiles requested?
    idxs = [np.sum(distribution < p / 100.0) for p in percentiles]

    # These:
    vals = [binEdges[i] for i in idxs]

    # Append 0 and 100% percentiles (min & max)
    percentiles = [0] + percentiles + [100]
    vals = [lo] + vals + [hi]

    return (vals, percentiles)

