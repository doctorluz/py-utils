###################################### Run-specific configuration ###############################################
# where to write to
output_dir = "/home/lucy_data_to_organise/python/red_list_2016_rasters"
# this is the field that is meaningful to you to name the raster - it need not be unique within the table.
unique_id_field = 'id_no'
# unique_id_field = 'wdpa_pid'

# clause for filtering the results (leave blank if none is needed
# for species Red List data, only certain types of occupancy are important in defining a usable range
whereClause = " presence IN (1,2) AND origin IN (1,2) AND seasonal IN (1,2,3) AND class IS NOT NULL AND class != ''"
# whereClause = ""

# for species Red List data, also need class and category for grouping the output usefully
# leave this blank if you don't need any extra fields
extraFields1 = ",MIN(class) AS class, MIN(rlcategory) AS rlcategory"
extraFields2 = ",foo.class, foo.rlcategory"

# clause for grouping the records into one map. Leave blank if you want one map per database row.
# in this case, we choose one map for each species - wdpa are already individual on parcel
groupByClause = " GROUP BY id_no"
# groupByClause = " GROUP BY wdpa_pid"
# The geometry is selected in order to burn it into the binary raster. Name the geometry field for your table.
geometryFieldName = "geom"
# original data table where the above geometry and other data is stored
# tableName = "public.lb_experiment_iucn_rl_species_2014_2_no_sens"
# tableName = "pp2016.mv_final_wdpa_relevant_jun2016"
tableName = "red_list_2016.v_amr"
# 10 arc seconds...
pixelRes = 0.00277777777777777777777777777778
# 30 arc seconds
# pixelRes = 0.00833333333333333333333333333333
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
overwrite = False
###############################################################################################################
