import os
import re
import numpy as np
from osgeo import gdal, osr
from datetime import datetime


class Exporter:

    def __init__(self ):

        """
        Placeholder
        """

        # dn to reflectance / radiance coefficients
        self._ucc = np.matrix(([[0.676, 1.688, 2.25, 0.0],\
                                [0.708, 1.415, 1.89, 0.0],\
                                [0.423, 0.862, 1.15, 0.0],\
                                [0.1087, 0.2174, 0.2900, 0.2900],\
                                [0.0348, 0.0696, 0.0925, 0.4090],\
                                [0.0313, 0.0625, 0.0830, 0.3900],\
                                [0.0299, 0.0597, 0.0795, 0.3320],\
                                [0.0209, 0.0417, 0.0556, 0.2450],\
                                [0.0159, 0.0318, 0.0424, 0.2650]]))

        # Thome et al. is used, which uses spectral irradiance values from MODTRAN
        # Ordered b1, b2, b3N, b4, b5...b9
        self._irradiance = [1848, 1549, 1114, 225.4, 86.63, 81.85, 74.85, 66.49, 59.85]
        return


    def process( self, scene, out_path=None ):

        """
        Placeholder
        """

        # open file
        in_ds = gdal.Open( scene )
        if in_ds is not None:

            # initialise output path
            raw_path = os.path.dirname( scene )
            if out_path is None:
                out_path = raw_path.replace( 'raw', 'ard' )

            # initialise output path
            if not os.path.exists( out_path ):
                os.makedirs( out_path, 0o755 )

            # extract metadata / subdatasets
            in_sds = in_ds.GetSubDatasets()
            meta = in_ds.GetMetadata()

            # get earth sun distance and solar azimuth
            esd = self.getEarthSunDistance( meta )
            sza = [np.float(x) for x in meta['SOLARDIRECTION'].split(', ')][1]

            # get gain data
            gain = self.getGainData( meta )

            # get utm projection
            utm = self.getUtmProjection( meta )

            # cycle through subdatasets
            for gname in in_sds:

                # locate visible and shortwave ir datasets
                vnir = re.search("(VNIR.*)", gname[ 0 ])
                swir = re.search("(SWIR.*)", gname[ 0 ])
                if vnir or swir:

                    # create tif output name
                    band = gname[ 0 ].split(':')[-1]

                    out_pathname = '{}/{}_{}.tif'.format(out_path, os.path.basename( scene ).split('.hdf')[0], band )
                    out_pathname_rad = '{}_radiance.tif'.format(out_pathname.split('.tif')[0])
                    out_pathname_ref = '{}_reflectance.tif'.format(out_pathname.split('.tif')[0])

                    # open SDS and create array            
                    band_ds = gdal.Open( gname[ 0 ], gdal.GA_ReadOnly)
                    band_data = band_ds.ReadAsArray().astype(np.uint16)
                    
                    # define extent and offset for UTM South zones            
                    if utm[ 'n_s' ] < 0:
                        ul_y = utm[ 'ul' ][0] + 10000000
                        ul_x = utm[ 'ul' ][1]
                    
                        lr_y = utm[ 'lr' ][0] + 10000000
                        lr_x = utm[ 'lr' ][1]
                        
                    # define extent for UTM North zones            
                    else:
                        ul_y = utm[ 'ul' ][0] 
                        ul_x = utm[ 'ul' ][1]
                    
                        lr_y = utm[ 'lr' ][0] 
                        lr_x = utm[ 'lr' ][1]
                
                    # query raster dimensions and calculate raster x & y resolution
                    ncols, nrows = band_data.shape            
                    y_res = -1 * round((max( ul_y, lr_y ) - min( ul_y, lr_y ) ) / ncols )
                    x_res = round((max( ul_x, lr_x ) - min( ul_x, lr_x ) ) / nrows )

                    # define UL x and y coordinates based on spatial resolution
                    ul_yy = ul_y - (y_res/2)
                    ul_xx = ul_x - (x_res/2)

                    #------------------------------------------------------------------------------

                    # start conversions by band (1-9)        
                    if band == 'ImageData1':
                        bn = -1 + 1                
                        # query for gain specified in file metadata (by band)            
                        if gain['01'] == 'HGH':
                            ucc1 = self._ucc[bn, 0] 
                        elif gain['01'] == 'NOR':
                            ucc1 = self._ucc[bn, 1] 
                        else:
                            ucc1 = self._ucc[bn, 2] 
                        
                    if band == 'ImageData2':
                        bn = -1 + 2
                        # query for gain specified in file metadata (by band)            
                        if gain['02'] == 'HGH':
                            ucc1 = self._ucc[bn, 0] 
                        elif gain['02'] == 'NOR':
                            ucc1 = self._ucc[bn, 1] 
                        else:
                            ucc1 = self._ucc[bn, 2] 
                        
                    if band == 'ImageData3N':
                        bn = -1 + 3                
                        # Query for gain specified in file metadata (by band)            
                        if gain['3N'] == 'HGH':
                            ucc1 = self._ucc[bn, 0] 
                        elif gain['3N'] == 'NOR':
                            ucc1 = self._ucc[bn, 1] 
                        else:
                            ucc1 = self._ucc[bn, 2] 
                        
                    if band == 'ImageData4':
                        bn = -1 + 4                
                        # Query for gain specified in file metadata (by band)            
                        if gain['04'] == 'HGH':
                            ucc1 = self._ucc[bn, 0] 
                        elif gain['04'] == 'NOR':
                            ucc1 = self._ucc[bn, 1] 
                        elif gain['04'] == 'LO1':
                            ucc1 = self._ucc[bn, 2] 
                        else:
                            ucc1 = self._ucc[bn, 3] 
                        
                    if band == 'ImageData5':
                        bn = -1 + 5                
                        # Query for gain specified in file metadata (by band)            
                        if gain['05'] == 'HGH':
                            ucc1 = self._ucc[bn, 0] 
                        elif gain['05'] == 'NOR':
                            ucc1 = self._ucc[bn, 1] 
                        elif gain['05'] == 'LO1':
                            ucc1 = self._ucc[bn, 2] 
                        else:
                            ucc1 = self._ucc[bn, 3] 
                        
                    if band == 'ImageData6':
                        bn = -1 + 6                
                        # Query for gain specified in file metadata (by band)            
                        if gain['06'] == 'HGH':
                            ucc1 = self._ucc[bn, 0] 
                        elif gain['06'] == 'NOR':
                            ucc1 = self._ucc[bn, 1] 
                        elif gain['06'] == 'LO1':
                            ucc1 = self._ucc[bn, 2] 
                        else:
                            ucc1 = self._ucc[bn, 3] 
                            
                    if band == 'ImageData7':
                        bn = -1 + 7                
                        # Query for gain specified in file metadata (by band)            
                        if gain['07'] == 'HGH':
                            ucc1 = self._ucc[bn, 0] 
                        elif gain['07'] == 'NOR':
                            ucc1 = self._ucc[bn, 1] 
                        elif gain['07'] == 'LO1':
                            ucc1 = self._ucc[bn, 2] 
                        else:
                            ucc1 = self._ucc[bn, 3] 
                        
                    if band == 'ImageData8':
                        bn = -1 + 8                
                        # Query for gain specified in file metadata (by band)            
                        if gain['08'] == 'HGH':
                            ucc1 = self._ucc[bn, 0] 
                        elif gain['08'] == 'NOR':
                            ucc1 = self._ucc[bn, 1] 
                        elif gain['08'] == 'LO1':
                            ucc1 = self._ucc[bn, 2] 
                        else:
                            ucc1 = self._ucc[bn, 3] 
                            
                    if band == 'ImageData9':
                        bn = -1 + 9                
                        # Query for gain specified in file metadata (by band)            
                        if gain['09'] == 'HGH':
                            ucc1 = self._ucc[bn, 0] 
                        elif gain['09'] == 'NOR':
                            ucc1 = self._ucc[bn, 1] 
                        elif gain['09'] == 'LO1':
                            ucc1 = self._ucc[bn, 2] 
                        else:
                            ucc1 = self._ucc[bn, 3] 

                    #------------------------------------------------------------------------------
                
                    # generate radiance geotiff files
                    driver = gdal.GetDriverByName('GTiff')
                    dn = driver.Create(out_pathname, nrows, ncols, 1, gdal.GDT_UInt16)
                    
                    # define CRS and extent properties
                    srs = osr.SpatialReference()
                    srs.ImportFromEPSG(utm[ 'zone' ] )
                    dn.SetProjection(srs.ExportToWkt())
                    dn.SetGeoTransform((ul_xx, x_res, 0., ul_yy, 0., y_res))
                    
                    # write SDS array to geoTiff
                    outband = dn.GetRasterBand(1)
                    outband.SetNoDataValue(0)
                    outband.WriteArray(band_data)
                    dn = None

                    #------------------------------------------------------------------------------

                    # convert dn to radiance        
                    rad = self.dn2radiance(band_data, ucc1 )
                    rad[rad == self.dn2radiance(0, ucc1)] = 0
                    del band_data

                    # Next, Radiance (w/m2/sr/µm)
                    out_rad = driver.Create(out_pathname_rad, nrows, ncols, 1, gdal.GDT_Float32)
                    
                    # Define output GeoTiff CRS and extent properties
                    out_rad.SetProjection(srs.ExportToWkt())
                    out_rad.SetGeoTransform((ul_xx, x_res, 0., ul_yy, 0., y_res))
                
                    # Write SDS array to output GeoTiff
                    outband = out_rad.GetRasterBand(1)
                    outband.SetNoDataValue(0)
                    outband.WriteArray(rad)
                    out_rad = None

                    #------------------------------------------------------------------------------

                    # Convert radiance to TOA reflectance
                    irradiance = self._irradiance[bn]
                    ref = self.radiance2reflectance(rad, esd, sza, irradiance )
                    del rad

                    # reflectance (w/m2/sr/µm)
                    ref = np.uint16( ref * ( ( 2**16 ) - 1 ) )
                    print ( 'Exporting: {}'.format( out_pathname ) )
                    out_ref = driver.Create(out_pathname_ref, nrows, ncols, 1, gdal.GDT_UInt16)
                
                    # Define output GeoTiff CRS and extent properties
                    out_ref.SetProjection(srs.ExportToWkt())
                    out_ref.SetGeoTransform((ul_xx, x_res, 0., ul_yy, 0., y_res))
                    
                    # Write SDS array to output GeoTiff
                    outband = out_ref.GetRasterBand(1)
                    outband.SetNoDataValue(0)
                    outband.WriteArray(ref)
                    out_ref = None

        return


    def getEarthSunDistance( self, meta ):

        # get aos info
        date = meta['CALENDARDATE']
        dated = datetime.strptime(date, '%Y%m%d')
        day = dated.timetuple()
        doy = day.tm_yday
        
        # calculate Earth-Sun distance    
        return 1.0 - 0.01672 * np.cos(np.radians(0.9856 * (doy - 4)))


    def getGainData( self, meta ):

        # extract meta data
        gain_list = [g for g in meta.keys() if 'GAIN' in g] 
        gain_info = []

        # query gain data for each band
        for f in range(len(gain_list)):
            gain_info1 = meta[gain_list[f]].split(', ')
            gain_info.append(gain_info1)

        return dict(gain_info)


    def getUtmProjection( self, meta ):

        # get upper left and lower right coordinates
        utm = { 'ul' : [np.float(x) for x in meta['UPPERLEFTM'].split(', ')],
                'lr' : [np.float(x) for x in meta['LOWERRIGHTM'].split(', ')] }

        # get hemisphere
        utm[ 'n_s' ] = np.float(meta['NORTHBOUNDINGCOORDINATE'])
        
        # create UTM zone code numbers    
        zone = np.int(meta['UTMZONENUMBER'])

        utm_n = [i+32600 for i in range(60)]
        utm_s = [i+32700 for i in range(60)]
        
        # get utm zone
        if utm[ 'n_s' ] < 0:
            utm[ 'zone' ] = utm_s[zone]
        else:
            utm[ 'zone' ] = utm_n[zone]
            
        return utm
        
    def dn2radiance ( self, x, ucc1) :
        return (x-1.)*ucc1
        
    def radiance2reflectance ( self, rad, esd, sza, irradiance ):
        return (np.pi * rad * (esd * esd)) / (irradiance * np.sin(np.pi * sza / 180.0)) 

