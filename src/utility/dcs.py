import numpy as np
import cv2
import pdb

def dstretch( bgr, targetMean=np.asarray([ 120.0, 120.0, 120.0 ]), targetSigma=np.asarray([ 50.0, 50.0, 50.0 ] ) ):

    targetMean=None; targetSigma=None

    # generate destretch CIE L*a*b image
    lab = cv2.cvtColor( bgr, cv2.COLOR_BGR2Lab) 
    lab32f = dcs_transform( lab, targetMean, targetSigma )

    # rescale to byte
    bands = []
    for idx in range( lab32f.shape[-1] ):
        bands.append( convertToByte( lab32f[ :,:,idx] ) )

    # rescale to byte and convert to rgb colour space
    lab8u = np.dstack( bands )
    lab2bgr = cv2.cvtColor( lab8u, cv2.COLOR_Lab2BGR ) 

    # dstretch rgb data
    bgr32f = dcs_transform( bgr, targetMean, targetSigma )

    bands = []
    for idx in range( bgr32f.shape[-1] ):
        bands.append( convertToByte( bgr32f[ :,:,idx] ) )

    bgr8u = np.dstack( bands )

    return bgr8u, lab8u


def dcs_transform( img, targetMean, targetSigma ):


    # flatten to 2d
    data = img.reshape( -1, img.shape[-1] )

    # compute mean and stddev of input
    dataMu, dataSigma = cv2.meanStdDev(img)

    # compute pca
    mean = np.empty((0))
    mean, eigenvectors, eigenvalues =  cv2.PCACompute2( data, mean )

    # scaling matrix (Sc)
    eigDataSigma = np.sqrt( eigenvalues )
    scale = np.diagflat(1/eigDataSigma)

    # stretching matrix (St)
    # if targetSigma is empty, set sigma of transformed data equal to that of original data
    if targetSigma is None:
        stretch = np.diagflat( dataSigma )
    else:
        stretch = np.diagflat( targetSigma )

    # stretching matrix (St)
    repMu = cv2.repeat( dataMu.T, data.shape[0], 1)
    zmudata = cv2.subtract(data.astype( float ), repMu )

    if targetMean is not None:
        repMu = np.tile( targetMean.T, (data.shape[0], 1 ) )

    # compute pca transformation
    transformed = zmudata @ ( eigenvectors.T @ scale @  eigenvectors @ stretch )
    transformed = np.add( transformed, repMu )

    return transformed.reshape( img.shape )


def convertToByte( data_16, p_min=0.02, p_max=0.98, bins=4096 ):

    """
    Placeholder
    """

    # find valid data
    mask = np.where( data_16 != 0 ) 

    # compute cumulative distribution
    hist, bin_edges = np.histogram( data_16[ mask ], bins=bins, density=True)
    cdf = np.cumsum( hist * np.diff(bin_edges) )

    # get dn values corresponding to min / max probability
    min_value = bin_edges[ np.argmax(cdf>p_min) ]
    max_value = bin_edges[ np.argmax(cdf>p_max) ]

    # scale between 1 to 255
    scale = ( max_value - min_value ) / 254.0
    data = np.copy( data_16 ).astype( float )

    # clip between 1 to 255
    data[ mask ] = np.round ( ( data_16[ mask ] - min_value ) / scale ) + 1
    data[ mask ] = data[mask].clip( min = 1.0, max=255.0 )
    
    return data.astype( np.uint8 )
