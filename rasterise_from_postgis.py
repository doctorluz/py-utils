import sys, json, os
import psycopg2
from db_connect import db_connection_string
from subprocess import Popen

###################################### Run-specific configuration ###############################################
# where to write to
output_dir = "/home/lucy_data_to_organise/python/species_raster_ccit"
# this is the field that is meaningful to you to name the raster - it need not be unique within the table.
unique_id_field = 'id_no'
# clause for filtering the results (leave blank if none is needed
# for species Red List data, only certain types of occupancy are important in defining a usable range
# whereClause = " WHERE presence IN (1,2) AND origin IN (1,2) AND seasonal IN (1,2,3)"
whereClause = " WHERE presence IN (1,2) AND origin IN (1,2) AND seasonal IN (1,2,3)"
# clause for grouping the records into one map. Leave blank if you want one map per database row.
# in this case, we choose one map for each species
groupByClause = " GROUP BY id_no"
# The geometry is selected in order to burn it into the binary raster. Name the geometry field for your table.
geometryFieldName = "wkb_geometry"
# original data table where the above geometry and other data is stored
tableName = "public.lb_experiment_iucn_rl_species_2014_2_no_sens"
# 10 arc seconds...
#pixelRes = 0.00277777777777777777777777777778
# 30 arc seconds
pixelRes = 0.00833333333333333333333333333333
# Corner coordinates : currently they are constrained to be integers because of some string work later on
# used in a query to get a plain rectangle covering the whole bounds
llx=-180
lly=-90
urx=180
ury=90
# Projection data for the output rasters
epsg=4326
theProj = 'EPSG:%d' % epsg
# Compression technique (e.g., LZW). For binary maps, choose a Huffman approach
compressionStrategy = 'CCITTRLE'
# pixel threshold for burning all pixels - i.e., if the extent is less than this on one direction
pixelThresh = 6
# should we overwrite existing files?
overwrite = True
###############################################################################################################

try:
    # create connection to database
    conn = psycopg2.connect(db_connection_string)
    # create a cursor object called cur
    cur = conn.cursor()

    # Make a list of unique values of id - at the same time, get the extent of the relevant geometries for each species
    strSql = """
    SELECT foo.%s, ST_XMIN(foo.extent) AS xmin, ST_YMIN(foo.extent) AS ymin, ST_XMAX(foo.extent) AS xmax, ST_YMAX(foo.extent) AS ymax FROM
    (SELECT %s, ST_Extent(%s) as extent FROM %s%s%s) AS foo;
    """ % (unique_id_field, unique_id_field, geometryFieldName, tableName, whereClause, groupByClause)
    
    # print (strSql)

    # execute the query
    cur.execute(strSql)
     
    # store the result of the query into Tuple c
    myList = cur.fetchall()

    # Create a command for a blank raster
    blankfile_name = os.path.join(output_dir,'blank.tif')

    # create a base binary raster going to the edges of required region, 30 arc-second resolution
    gdal_command = 'gdal_rasterize -co NBITS=1 -co COMPRESS=%s -ot Byte -burn 0 -a_srs %s -tr %s %s -te %d %d %d %d PG:\"%s\" -sql \"SELECT ST_SetSRID(ST_MakePolygon(ST_GeomFromText(\'LINESTRING(%d %d,%d %d, %d %d, %d %d, %d %d)\')), %d);\" %s' % (compressionStrategy, theProj, str(pixelRes), str(pixelRes), llx, lly, urx, ury, db_connection_string, llx,lly,llx,ury,urx,ury,urx,lly,llx,lly,epsg, blankfile_name)
   
##    proc = Popen(gdal_command, shell=True)
##    proc.wait()
##    if (proc.returncode != 0):
##        print proc.returncode      

    ##    #xmin,ymin,xmax,ymax = float(*extent)
    ##    # was trying to cleverly unpack the list here, but it doesn't work

    for theID, xmin, ymin, xmax, ymax in myList:

        outputfile_name = os.path.join(output_dir, '%d.tif' % theID)
        
        if (not os.path.isfile(outputfile_name) or overwrite is True):
            
            # check the extent of the features - if very small, make sure that all touched pixels get burned
            # TODO - update this so that it takes into account area and perimeter.

            burnall = False
            xdim = (xmax-xmin)/pixelRes
            ydim = (ymax-ymin)/pixelRes
            if xdim <pixelThresh or ydim <pixelThresh:
                burnall = True
                print "for species %d, the extent is %.2f x %.2f - will burn all pixels" % (theID, xdim, ydim)
                
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

            # clip the base raster to the appropriate coordinates
            gdal_command = 'gdal_translate -co NBITS=1 -co COMPRESS=%s -ot Byte -projwin %f %f %f %f %s %s' % (compressionStrategy, xmin, ymax, xmax, ymin, blankfile_name, outputfile_name)

            #print gdal_command

##            os.remove(outputfile_name)
##            proc = Popen(gdal_command, shell=True)
##            proc.wait()
##            if (proc.returncode != 0):
##                print proc.returncode
##            # os.system('gdalinfo ' + outputfile_name)   
##
##            if burnall: # use the 'all touched' option
##                gdal_command = 'gdal_rasterize -at -burn 1 PG:\"%s\" -sql \"SELECT %s FROM %s%s AND %s=%d \" %s' %(db_connection_string, geometryFieldName, tableName, whereClause, unique_id_field, theID, outputfile_name)
##            else:
##                gdal_command = 'gdal_rasterize -burn 1 PG:\"%s\" -sql \"SELECT %s FROM %s%s AND %s=%d \" %s' %(db_connection_string, geometryFieldName, tableName, whereClause, unique_id_field, theID, outputfile_name)
##            print gdal_command
##            proc = Popen(gdal_command, shell=True)
##            proc.wait()
##            if (proc.returncode != 0):
##                print proc.returncode

    # closes the connection
    conn.close()
except () as e:
     print "ERROR"
     print e.strerror
     if conn:
         conn.close()


