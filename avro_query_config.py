output_dir = "/home/lucy_data_to_organise/avro"
geom_field_name = 'geom'
USE_WKB = True
# This is necessary because the pre-binaried data will just come through as a string
# the strategy for geometries is to export WKB: ST_AsBinary will include the SRID, EWKB doesn't work at the hive end when ST_GEOMFOMWKB is called

#selectFields = 'id, name AS eco_name, ST_AsBinary(geom) AS geom, is_marine, source, area'
##selectFields = 'id_no, cell_id, ST_AsBinary(geom) AS geom, intersects, CASE WHEN cell_area IS NULL THEN 0.0 ELSE cell_area END AS cell_area, class, category'
##outputfile = "wgrid_amphibia"
##tableName = "hadoop.will_grid_gridded_amphibia"
##testField = 'id_no'

##selectFields = 'wdpaid, wdpa_pid, cell_id, iucn_cat, iso3, marine, type, ST_AsBinary(geom) AS geom, intersects, CASE WHEN cell_area IS NULL THEN 0.0 ELSE cell_area END AS cell_area'
##outputfile = "wgrid_wdpa"
##tableName = "hadoop.will_grid_gridded_wdpa"
##testField = 'wdpaid'

# NB PA names cause a problem on writing: UTF8. Make sure to fix if necessary
##selectFields = 'wdpaid, wdpa_pid, iucn_cat, iso3, marine, rep_area, type, ST_AsBinary(geom) AS geom'
##outputfile = "wdpa_jun_2016"
##tableName = "pp2016.mv_final_wdpa_relevant_jun2016"
##testField = 'wdpaid'
##whereClause = ""

##selectFields = 'id, ST_AsBinary(geom) AS geom'
##outputfile = "vgrid_2015"
##selectFields = 'id as cell_id, ST_AsBinary(geom) AS geom'
##tableName = "hgrid.h_grid2"
##whereClause = " WHERE is_leaf IS TRUE"
##testField = 'id'

selectFields = 'id_no, presence, origin, seasonal, ST_AsBinary(geom) AS geom'
outputfile = "species_feb_2014"
tableName = "pp2016.temp_feb2014_species_dumped_validated_collected"
whereClause = ""
testField = 'id_no'

### For writing out a JSON schema
##selectFields = "id_no,binomial,rl_update,scientific_name,comm_name,kingdom,phylum,class,order_,family,genus_name,species_name,category,biome_mar,biome_fw,biome_terr,ST_AsText(make_valid_geom) as geometry"
##outputfile = "amphib_subset"
##tableName = "public.lb_experiment_iucn_rl_species_2014_2_no_sens"
##whereClause = " LIMIT 1"
##testField = 'id_no'
### for json, make sure the geom field name is blank so it will be written as text
##geom_field_name = ''
