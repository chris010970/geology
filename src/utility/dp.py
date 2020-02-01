import os
import re

from datetime import datetime

# parse date time sub-folder name from pathname
def getDateTimeString( pathname ):

    dt = None

    # parse for date time sub directory
    m = re.search( '[0-9]{8}_[0-9]{6}', pathname )
    if m:
        dt = str(m.group(0) )

    return dt

# parse date time from pathname
def getDateTime( pathname ):

    dt = None

    # parse for date time sub directory
    m = re.search( '[0-9]{8}_[0-9]{6}', pathname )
    if m:
        dt = datetime.strptime( str(m.group(0) ), '%Y%m%d_%H%M%S')

    return dt

# parse tle from pathname
def getTle( pathname ):

    tle = None

    # parse for date time sub directory
    m = re.search( '\d{5}', pathname )
    if m:
        tle = str( m.group(0) )

    return tle


