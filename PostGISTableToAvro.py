import sys, json, os
import psycopg2
import avro
import avro.schema
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter, SchemaResolutionException
from datetime import date
from db_connect import db_connection_string
from avro_query_config import *

# the strategy for geometries is to export WKB: the above will include the SRID, EWKB doesn't work at the hive end when ST_GEOMFOMWKB is called
#selectFields = 'id, name AS eco_name, ST_AsBinary(geom) AS geom, is_marine, source, area'

try:
    print "Checking whether files exist"
    # if files exist, delete them
    avro_file = os.path.join(output_dir,outputfile + ".avro")
    avsc_file = os.path.join(output_dir,outputfile + ".avsc")
    if os.path.isfile(avro_file):
        os.remove(avro_file)
    if os.path.isfile(avsc_file):
        os.remove(avsc_file)

    print "Connecting to database"
    # create connection to PostGIS database
    conn = psycopg2.connect(db_connection_string)

    # create a cursor object called cur
    cur = conn.cursor()

    # Get all rows, but at first just to investigate the schema
    strSql = "SELECT %s FROM %s%s" % (selectFields, tableName, whereClause)
    # print strSql
    # execute the query
    cur.execute(strSql)

    schema = cur.description
    # store the result of the query into a tuple 

    ## VERY IMPORTANT!!!!! how to get the numeric type codes needed for the piece below
    ##SELECT n.nspname as "Schema",
    ##t.oid,
    ##  pg_catalog.format_type(t.oid, NULL) AS "Name",
    ##  pg_catalog.obj_description(t.oid, 'pg_type') as "Description"
    ##FROM pg_catalog.pg_type t
    ##     LEFT JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
    ##WHERE (t.typrelid = 0 OR (SELECT c.relkind = 'c' FROM pg_catalog.pg_class c WHERE c.oid = t.typrelid))
    ##  AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_type el WHERE el.oid = t.typelem AND el.typarray = t.oid)
    ##  AND pg_catalog.pg_type_is_visible(t.oid)
    ##ORDER BY 1, 2;

    # and...

    ## Avro schemas are defined using JSON. Schemas are composed of primitive types
    ## (null, boolean, int, long, float, double, bytes, and string)
    ## and complex types (record, enum, array, map, union, and fixed) TODO complex types!

    fieldsArray = []
    for item in schema:
        
        if item.name == geom_field_name:
            fieldType = 'bytes'
        elif item.type_code in [26]: # OID
            fieldType = 'long'
        elif item.type_code in [16]: # boolean
            fieldType = 'boolean'
        elif item.type_code in [21]: # smallint
            fieldType = 'int'
        elif item.type_code in [20,23]: # bigint, integer
            fieldType = 'long'
        elif item.type_code in [700]: # real
            fieldType = 'float'
        elif item.type_code in [701, 1700]: # double precision, real
            fieldType = 'double'
        elif item.type_code in [25, 1042,1043,18,17]: # text, character, character varying, "char", bytea
            fieldType = 'string'
        elif item.type_code in [17]: # bytea
            fieldType = 'bytes'
        elif item.type_code == 16392: # geometry
    # also have 600=point, 603=box,604=polygon,718=circle,707074035=geometry, 707074050=box3d, 707074054=box2d, 707074555=geography. 707074719=raster     
    # actually, for now I will do the conversion to WKB within PostGIS using views, rather than converting geometries in python or re-querying - see top line of this 'if'
            if USE_WKB:
                fieldType = 'bytes'
            else:
                fieldType = 'string'
        elif item.type_code in [1082, 1083, 1114, 1184, 1266]: #date, time w/o zone, timestamp w/o zone, timestamp with zone, time with zone
            fieldType = 'string'
        else:
            print ("problem mapping field type %d" % item.type_code)

        if item.null_ok:
            fieldsArray.append({"name": item.name, "type": [fieldType, "null"]})
        else:
            fieldsArray.append({"name": item.name, "type": fieldType})
        
    # create the schema from the fields
    schemajson = {"type": "record", "name": outputfile, "fields": fieldsArray }
    schemajsonstr = json.dumps(schemajson, None)
    f = open(avsc_file, "w")
    f.write(schemajsonstr)
    f.close()

    schema = avro.schema.parse(schemajsonstr)
    print "Schema written to " + avsc_file

    # open a writer to write the data
    writer = DataFileWriter(open(avro_file, "wb"), DatumWriter(), schema, "deflate")
     
    # get the count
    total = cur.rowcount
     
    # iterate through the records and write the data

    count = 0
    row = cur.fetchone()
    while row:
        print "Processing row number " + str(count) + " of " + str(total)   
        data = {}
        fieldcounter = -1
        for field in row:
           
            fieldcounter +=1
            fn = (fieldsArray[fieldcounter].get('name'))
            
            if fn == geom_field_name:
                data[fn] = bytes(field)
            else:
                data[fn] = field
       
        writer.append(data)
        row = cur.fetchone()
        count = count + 1

    writer.close()
    print "Data written to " + avro_file
    # Test that the file has been properly written...
    print "\nChecking file.."
    reader = DataFileReader(open(avro_file, "rb"), DatumReader())
    ##for record in reader:
    ##    print record[testField]
    reader.close()
    print "Finished" 
    conn.close()
    
except () as e:
     print "ERROR"
     print e.strerror
     if conn:
         conn.close()
