import sys, json, os
import psycopg2
from db_processing_connect import db_connection_string
from subprocess import Popen
from rasterise_with_buffer_settings import *

try:
    # create connection to database
    conn = psycopg2.connect(db_connection_string)
    # create a cursor object called cur
    cur = conn.cursor()

    # Make a list of unique values of id - at the same time, get the extent of the relevant geometries for each species

    if whereClause != '':
        strSql = """
        SELECT foo.%s, ST_XMIN(foo.extent) AS xmin, ST_YMIN(foo.extent) AS ymin, ST_XMAX(foo.extent) AS xmax, ST_YMAX(foo.extent) AS ymax FROM
        (SELECT %s, ST_Extent(%s) as extent FROM %s WHERE %s%s) AS foo;
        """ % (unique_id_field, unique_id_field, geometryFieldName, bufferTableName, whereClause, groupByClause)
    else:
        strSql = """
        SELECT foo.%s, ST_XMIN(foo.extent) AS xmin, ST_YMIN(foo.extent) AS ymin, ST_XMAX(foo.extent) AS xmax, ST_YMAX(foo.extent) AS ymax FROM
        (SELECT %s, ST_Extent(%s) as extent FROM %s%s) AS foo;
        """ % (unique_id_field, unique_id_field, geometryFieldName, bufferTableName, groupByClause)
    
    print (strSql)

    # execute the query
    cur.execute(strSql)
     
    # store the result of the query into Tuple c
    myList = cur.fetchall()

    try:
        os.makedirs(output_dir)
    except OSError:
        if os.path.exists(output_dir):
            # We are nearly safe
            pass
        else:
            # There was an error on creation, so make sure we know about it
            raise
    
    # Create a command for a blank raster
    blankfile_name = os.path.join(output_dir,'blank.tif')
    if (not os.path.isfile(blankfile_name) or overwrite is True):

        # create a base binary raster going to the edges of required region, 30 arc-second resolution
        gdal_command = 'gdal_rasterize%s -co NBITS=2 -co COMPRESS=%s -ot Byte -burn 0 -a_srs %s -tr %s %s -te %d %d %d %d PG:\"%s\" -sql \"SELECT ST_SetSRID(ST_MakePolygon(ST_GeomFromText(\'LINESTRING(%d %d,%d %d, %d %d, %d %d, %d %d)\')), %d);\" %s' % (bigTiff, compressionStrategy, theProj, str(pixelRes), str(pixelRes), llx, lly, urx, ury, db_connection_string, llx,lly,llx,ury,urx,ury,urx,lly,llx,lly,epsg, blankfile_name)
        print(gdal_command)
        
        proc = Popen(gdal_command, shell=True)
        proc.wait()
        if (proc.returncode != 0):
            print proc.returncode      

    ##    #xmin,ymin,xmax,ymax = float(*extent)
    ##    # was trying to cleverly unpack the list here, but it doesn't work

    # for theID, xmin, ymin, xmax, ymax, theClass, theCat in myList:
    for theID, xmin, ymin, xmax, ymax in myList:
        
        outputfile_name = os.path.join(output_dir, '%s%d.tif' % (filenamePrefix, theID))

        print theID
        if (not os.path.isfile(outputfile_name) or overwrite is True):
            
            # check the extent of the features - if very small, make sure that all touched pixels get burned
            # TODO - update this so that it takes into account area and perimeter.

            burnall = False
            xdim = (xmax-xmin)/pixelRes
            ydim = (ymax-ymin)/pixelRes
            if xdim <pixelThresh or ydim <pixelThresh:
                burnall = True
                print "for polygon %d, the extent is %.2f x %.2f - will burn all pixels" % (theID, xdim, ydim)
                
        ##    # round the coordinates so that the pixels will always snap to an exact grid
            xmin = xmin - (xmin % pixelRes)
            if xmin < llx:
                xmin = llx
            ymin = ymin - (ymin % pixelRes)
            if ymin < lly:
                ymin = lly
            xmax = xmax + (pixelRes -(xmax % pixelRes))
            if xmax > urx:
                xmax = urx
            ymax = ymax + (pixelRes -(ymax % pixelRes))
            if ymax > ury:
                ymax = ury

            print ("%f, %f, %f, %f" % (xmin, ymin, xmax, ymax))
            
            # clip the base raster to the appropriate coordinates
            gdal_command = 'gdal_translate%s -co NBITS=2 -co COMPRESS=%s -ot Byte -projwin %f %f %f %f %s %s' % (bigTiff, compressionStrategy, xmin, ymax, xmax, ymin, blankfile_name, outputfile_name)

            print gdal_command
            if (os.path.isfile(outputfile_name) and overwrite is True):
                os.remove(outputfile_name)
                
            proc = Popen(gdal_command, shell=True)
            proc.wait()
            if (proc.returncode != 0):
                print proc.returncode

            # os.system('chmod 775 ' + outputfile_name)
            
            # burn the buffers - value of 1
            if burnall: # use the 'all touched' option
                gdal_command = 'gdal_rasterize -at -burn 1 '
            else:
                gdal_command = 'gdal_rasterize -burn 1 ' 

            if whereClause != '':
                gdal_command += 'PG:\"%s\" -sql \"SELECT %s FROM %s WHERE %s=%d AND %s\" %s' %(db_connection_string, geometryFieldName, bufferTableName, unique_id_field, theID, whereClause, outputfile_name)
            else:
                gdal_command += 'PG:\"%s\" -sql \"SELECT %s FROM %s WHERE %s=%d\" %s' %(db_connection_string, geometryFieldName, bufferTableName, unique_id_field, theID, outputfile_name)

            print gdal_command
            proc = Popen(gdal_command, shell=True)
            proc.wait()
            if (proc.returncode != 0):
                print proc.returncode

##            datafile = gdal.Open(outputfile_name)
##            geoinformation = datafile.GetGeoTransform()
##            topLeftX = geoinformation[0]
##            topLeftY = geoinformation[3]

##            print "Top left X: " + str(topLeftX)
##            print "Top left Y: " + str(topLeftY)

            # burn the original polygons - value of 2
            # check the size to see whether to burn all pixels
           
            strSql = """
            SELECT ST_XMIN(foo.extent) AS xmin, ST_YMIN(foo.extent) AS ymin, ST_XMAX(foo.extent) AS xmax, ST_YMAX(foo.extent) AS ymax FROM
            (SELECT %s, ST_Extent(%s) as extent FROM %s WHERE %s = %d%s) AS foo;
            """ % (unique_id_field, geometryFieldName, tableName, unique_id_field, theID, groupByClause)
            
            # print (strSql)

            # os.system('gdalinfo ' + outputfile_name)

            # execute the query
            cur.execute(strSql)
             
            # store the result of the query into Tuple c
            xmin, ymin, xmax, ymax = cur.fetchone()
            burnall = False
            xdim = (xmax-xmin)/pixelRes
            ydim = (ymax-ymin)/pixelRes
            
            if xdim <pixelThresh or ydim <pixelThresh:
                burnall = True
                print "for polygon %d, the extent is %.2f x %.2f - will burn all pixels" % (theID, xdim, ydim)
                
            if burnall: # use the 'all touched' option
                gdal_command = 'gdal_rasterize -at -burn 2 ' 

            else:
                gdal_command = 'gdal_rasterize -burn 2 ' 

            if whereClause != '':
                gdal_command += 'PG:\"%s\" -sql \"SELECT %s FROM %s WHERE %s=%d AND %s\" %s' %(db_connection_string, geometryFieldName, tableName, unique_id_field, theID, whereClause, outputfile_name)
            else:
                gdal_command += 'PG:\"%s\" -sql \"SELECT %s FROM %s WHERE %s=%d\" %s' %(db_connection_string, geometryFieldName, tableName, unique_id_field, theID, outputfile_name)

            print gdal_command
            proc = Popen(gdal_command, shell=True)
            proc.wait()
            if (proc.returncode != 0):
                print proc.returncode

##            datafile = gdal.Open(outputfile_name)
##            geoinformation = datafile.GetGeoTransform()
##            topLeftX = geoinformation[0]
##            topLeftY = geoinformation[3]
##
##            print "Top left X: " + str(topLeftX)
##            print "Top left Y: " + str(topLeftY)

    # closes the connection
    conn.close()
except () as e:
     print "ERROR"
     print e.strerror
     if conn:
         conn.close()


