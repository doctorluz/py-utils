import sys, json, os
import psycopg2
from db_processing_connect import db_connection_string
from subprocess import Popen
from rasterise_all_at_once_settings import *

try:
    # create connection to database
    conn = psycopg2.connect(db_connection_string)
    # create a cursor object called cur
    cur = conn.cursor()

    # Make a list of unique values of id: going to try and burn them one at a time to go easier on memory
    if whereClause != '':
        strSql = """
        SELECT %s FROM %s WHERE %s;
        """ % (unique_id_field, tableName, whereClause)
    else:
        strSql = """
        SELECT %s FROM %s;
        """ % (unique_id_field, tableName)    
    print (strSql)

    # execute the query
    cur.execute(strSql)
     
    # store the result of the query into Tuple c
    myList = cur.fetchall()

    # Create a command for the blank raster
    if (not os.path.isfile(output_filename) or overwrite is True):

        # create a base binary raster going to the edges of required region, 30 arc-second resolution
        gdal_command = 'gdal_rasterize -co NBITS=1 -co COMPRESS=%s -ot Byte -burn 0 -a_srs %s -tr %s %s -te %d %d %d %d PG:\"%s\" -sql \"SELECT ST_SetSRID(ST_MakePolygon(ST_GeomFromText(\'LINESTRING(%d %d,%d %d, %d %d, %d %d, %d %d)\')), %d);\" %s' % (compressionStrategy, theProj, str(pixelRes), str(pixelRes), llx, lly, urx, ury, db_connection_string, llx,lly,llx,ury,urx,ury,urx,lly,llx,lly,epsg, output_filename)
       
        proc = Popen(gdal_command, shell=True)
        proc.wait()
        if (proc.returncode != 0):
            print proc.returncode      

    ##    #xmin,ymin,xmax,ymax = float(*extent)
    ##    # was trying to cleverly unpack the list here, but it doesn't work

    for theVal in myList:

        theID = theVal[0]
        print (theID)
        
        gdal_command = 'gdal_rasterize -burn 1 '

        if whereClause != '':
            gdal_command += 'PG:\"%s\" -sql \"SELECT %s FROM %s WHERE %s=%d AND %s\" %s' %(db_connection_string, geometryFieldName, tableName, unique_id_field, theID, whereClause, output_filename)
        else:
            gdal_command += 'PG:\"%s\" -sql \"SELECT %s FROM %s WHERE %s=%d\" %s' %(db_connection_string, geometryFieldName, tableName, unique_id_field, theID, output_filename)

        print gdal_command
        proc = Popen(gdal_command, shell=True)
        proc.wait()
        if (proc.returncode != 0):
            print proc.returncode

    # closes the connection
    conn.close()
except () as e:
     print "ERROR"
     print e.strerror
     if conn:
         conn.close()


