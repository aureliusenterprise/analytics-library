from __future__ import unicode_literals

from pandas import DataFrame
from sqlalchemy import create_engine, MetaData, Table, select

from m4i_analytics.graphs.model.Graph import EdgeAttribute, NodeAttribute
from m4i_analytics.graphs.languages.archimate.model.ArchimateModel import ArchimateModel, ViewAttribute
from m4i_analytics.graphs.languages.archimate.metamodel.Concepts import ElementType, RelationshipType
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.m4i.portal.model.superset.slices.SliceFactory import SliceFactory
from m4i_analytics.graphs.visualisations.GraphPlotter import Layout

import json
from datetime import datetime

def getConnection(db):
    engine = create_engine(db, echo=False)
    return engine
# END getConnection

def getTableData(con, metadata, tablename):
    table = Table(tablename, metadata, autoload=True, autoload_with=con)   
    return con.execute(select([table])).fetchall()
# END getTableData

def formatTableName(db_name, schema_name, table_name):
    return '{0}.{1}{2}'.format(db_name, ('%s.' % schema_name)*bool(schema_name), table_name)
# END formatTableName

def getDBName(url):
    return url.split('/')[-1]
# END getDBName

def generate_superset_model(db_url):
        
    script_name = 'superset model generator'
        
    con = getConnection(db_url)
    metadata = MetaData()
    metadata.reflect(bind=con, views=True)
            
    # Content Tables
    slices = getTableData(con, metadata, 'slices')
    slice_types = list(set([slice[8] for slice in slices]))
    dashboards = getTableData(con, metadata, 'dashboards')
    tables = getTableData(con, metadata, 'tables')
    metrics = getTableData(con, metadata, 'sql_metrics')
    users = getTableData(con, metadata, 'ab_user')
    table_columns = getTableData(con, metadata, 'table_columns')
    databases = getTableData(con, metadata, 'dbs')
        
    # Mapping Tables
    dashboard_slices = getTableData(con, metadata, 'dashboard_slices')
    dashboard_users = getTableData(con, metadata, 'dashboard_user')
    slice_users = getTableData(con, metadata, 'slice_user')
        
    def getSliceColumns(slice_id):
        result = []
        
        matching_slices = [slice for slice in slices if slice[2] == slice_id]
        
        if len(matching_slices) > 0:
            
            params = dict(matching_slices[0])
            params['db_con'] = con
            params['db_metadata'] = metadata
            
            slice = SliceFactory().create(matching_slices[0][8], **params)
            
            if slice is not None:                
                result = slice.directColumnDependencies()
        
        return result    
    # END getUsedColumns
    
    def getTableName(table_id):
        result = ''
        if table_id is not None:
            table = [table for table in tables if table[2] == table_id][0]       
            result = formatTableName(getDBName([db[4] for db in databases if db[2] == table[6]][0]), table[14], table[3])
        return result
    # END getTableName
    
    def getDashboardFilteredValuesPerColumn(dashboard_id):
        
        dashboard = next((d for d in dashboards if d[2] == dashboard_id))
        
        metadata = dashboard[10]
        
        result = {}
        if metadata:
            
            json_metadata = json.loads(metadata)
            if json_metadata.get('default_filters'):
                
                filter_settings = json.loads(json_metadata['default_filters'])
                
                for slice_id in filter_settings.keys():
                    
                    column_name_mapping = {}
                                        
                    for column_id in getSliceColumns(slice_id):
                        column = next((col for col in table_columns if col[2] == column_id))
                        column_name_mapping[column[4]] = column_id
                    # END LOOP
                    
                    filter_columns = filter_settings[slice_id].keys()
                    for column_name in filter_columns:
                        value = filter_settings[slice_id][column_name]
                        if type(value) is not list:
                            value = [value]
                        results = result.get(column_name_mapping.get(column_name))
                        if results:
                            results.extend(value)
                        else:
                            result[column_name_mapping.get(column_name)] = value
                    # END LOOP
                # END LOOP  
        return result
    # END getDashboardFilteredValuesPerColumn
        
    # Add the nodes to the model first    
    abstract_nodes = [{'id':'slicetype', 'name':'visualization type', 'type': ElementType.BUSINESS_INTERFACE},                       
        {'id':'dashboard', 'name':'dashboard', 'type': ElementType.BUSINESS_INTERFACE},
        {'id':'table', 'name':'table', 'type': ElementType.DATA_OBJECT},
        {'id':'metric', 'name':'metric', 'type': ElementType.DATA_OBJECT},
        {'id':'user', 'name':'user', 'type': ElementType.BUSINESS_ACTOR},
        {'id':'column', 'name':'column', 'type': ElementType.DATA_OBJECT}]
    
    dashboard_nodes = [{'id':'dashboard-%s' % dashboard[2], 'name':dashboard[3], 'type': ElementType.BUSINESS_INTERFACE} for dashboard in dashboards]
    
    slice_nodes = [{'id':'slice-%s' % slice[2], 'name':slice[3], 'type': ElementType.BUSINESS_INTERFACE} for slice in slices]
    
    table_nodes = [{'id':getTableName(table[2]), 'name': getTableName(table[2]), 'type': ElementType.DATA_OBJECT} for table in tables]
    
    def fmt_user(a,b,c):
        return{'id':'user-{}'.format(a), 'name':'{0} {1}'.format(b, c), 'type': ElementType.BUSINESS_ACTOR}
    # END fmt_user
    
    nodes = abstract_nodes 
    nodes += dashboard_nodes
    nodes += slice_nodes
    nodes += table_nodes
    nodes += [{'id':'slicetype-%s' % index, 'name':slicetype, 'type': ElementType.BUSINESS_INTERFACE} for index, slicetype in enumerate(slice_types)]
    nodes += [{'id':'column-%s' % column[2], 'name':column[4], 'type': ElementType.DATA_OBJECT} for column in table_columns]
    nodes += [{'id':'metric-%s' % metric[2], 'name':metric[3], 'type': ElementType.DATA_OBJECT} for metric in metrics]
    nodes += [fmt_user(user[0], user[1], user[2]) for user in users]
        
    edges = ([{'id':'dashboardslice-%s' % dashboard_slice[0], 'type': RelationshipType.AGGREGATION, 'source': 'dashboard-%s' % dashboard_slice[1] ,'target': 'slice-%s' % dashboard_slice[2], 'name': ''} for dashboard_slice in dashboard_slices]
        + [{'id':'typeofslice-%s' % slice[2], 'type': RelationshipType.SPECIALIZATION, 'source': 'slice-%s' % slice[2], 'target': 'slicetype-%s' % slice_types.index(slice[8]), 'name': ''} for slice in slices]
        + [{'id':'dashboarduser-%s' % dashboard_user[0], 'type': RelationshipType.ASSIGNMENT, 'source': 'dashboard-%s' % dashboard_user[1] ,'target': 'user-%s' % dashboard_user[2], 'name': ''} for dashboard_user in dashboard_users]
        + [{'id':'sliceuser-%s' % slice_user[0], 'type': RelationshipType.ASSIGNMENT, 'source': 'user-%s' % slice_user[1], 'target': 'slice-%s' % slice_user[2], 'name': ''} for slice_user in slice_users]
        + [{'id':'tableslice-%s' % slice[2], 'type': RelationshipType.ACCESS, 'source': 'slice-%s' % slice[2], 'target': getTableName(slice[13]), 'name': ''} for slice in slices]
        + [{'id':'tablemetric-%s' % metric[2], 'type': RelationshipType.AGGREGATION, 'source': getTableName(metric[6]) ,'target': 'metric-%s' % metric[2], 'name': ''} for metric in metrics]
        + [{'id':'tablecolumn-%s' % column[2], 'type': RelationshipType.COMPOSITION, 'source': getTableName(column[3]) ,'target': 'column-%s' % column[2], 'name': ''} for column in table_columns]
        + [{'id':'slicecolumn-{0}-{1}'.format(slice[2], column), 'type': RelationshipType.ACCESS, 'source': 'slice-%s' % slice[2], 'target': 'column-%s' % column, 'name': ''} for slice in slices for column in getSliceColumns(slice[2])]
        + [{'id':'abstractslicetype-%s' % index, 'type': RelationshipType.SPECIALIZATION, 'source': 'slicetype-%s' % index, 'target': 'slicetype', 'name': ''} for index, slicetype in enumerate(slice_types)]
        + [{'id':'abstractdashboard-%s' % dashboard[2], 'type': RelationshipType.SPECIALIZATION, 'source': 'dashboard-%s' % dashboard[2], 'target': 'dashboard', 'name': ''} for dashboard in dashboards]
        + [{'id':'abstracttable-%s' % table[2], 'type': RelationshipType.SPECIALIZATION, 'source': getTableName(table[2]), 'target': 'table', 'name': ''} for table in tables]
        + [{'id':'abstractmetric-%s' % metric[2], 'type': RelationshipType.SPECIALIZATION, 'source': 'metric-%s' % metric[2], 'target': 'metric', 'name': ''} for metric in metrics]
        + [{'id':'abstractuser-%s' % user[0], 'type': RelationshipType.SPECIALIZATION, 'source': 'user-%s' % user[0], 'target': 'user', 'name': ''} for user in users]
        + [{'id':'abstractcolumn-%s' % column[2], 'type': RelationshipType.SPECIALIZATION, 'source': 'column-%s' % column[2], 'target': 'column', 'name': ''} for column in table_columns])
        #+ [{'id':'databasetable-%s' % table[2], 'type': RelationshipType.ASSOCIATION, 'source': getTableName(table[2]), 'target': formatTableName(getDBName(next(db for db in databases if db[2] == table[6])[4]), table[14], table[3]), 'name': ''} for table in tables])
        #+ [{'id':'databasecolumn-%s' % column[2], 'type': RelationshipType.ASSOCIATION, 'source': 'column-%s' % column[2], 'target': formatTableName(getDBName(next(db for db in databases if db[2] == next(table for table in tables if table[2] == column[3])[6])[4]), next(table for table in tables if table[2] == column[3])[14], next(table for table in tables if table[2] == column[3])[3]) + '.' + column[4], 'name': ''} for column in table_columns])
    
    for dashboard in dashboards:
        
        filteredColumnValues = getDashboardFilteredValuesPerColumn(dashboard[2])
        for column_id in filteredColumnValues.keys():
            
            filtervalues = [{'id': 'filtervalue-{0}-{1}-{2}'.format(dashboard[2], column_id, value), 'name': value, 'type': ElementType.BUSINESS_OBJECT } for value in filteredColumnValues[column_id]]
            dashboardfiltervalues = [{'id': 'dashboardfiltervalue-%s' % filtervalue['id'], 'type': RelationshipType.ACCESS, 'source': 'dashboard-%s' % dashboard[2], 'target': filtervalue['id'], 'name': ''} for filtervalue in filtervalues]
            nodes.extend(filtervalues)
            edges.extend(dashboardfiltervalues) 
            
            if column_id:
                columnfiltervalues = [{'id': 'columnfiltervalue-%s' % filtervalue['id'], 'type': RelationshipType.ASSOCIATION, 'source': 'column-%s' % column_id, 'target': filtervalue['id'], 'name': ''} for filtervalue in filtervalues]
                edges.extend(columnfiltervalues)            
        # END LOOP
    # END LOOP
        
    # Add the generated rows to dataframes
    elems = DataFrame(nodes, columns=['id', 'name', 'type', 'label'])    
    rels = DataFrame(edges, columns=['id', 'name', 'type', 'label', 'source', 'target'])
    
    # Initialize the model
    model = ArchimateModel('generated superset model', elems, rels, defaultAttributeMapping=True)
    model.putNodeAttributeMapping(NodeAttribute.LABEL, model.getNodeAttributeMapping(NodeAttribute.NAME))
    model.putEdgeAttributeMapping(EdgeAttribute.LABEL, model.getEdgeAttributeMapping(EdgeAttribute.NAME))  
    
    model.organize()    
        
    # The generate view function automatically adds the view to the model and organization
    views = ([ArchimateUtils.generate_view(
            model
           , name=dashboard['name']
           , layout=Layout.HIERARCHICAL
           , nodes=list(set([node for edge in model.edges.to_dict(orient='records') if edge['source'] == dashboard['id'] or edge['target'] == dashboard['id'] 
               for node in [edge['source'], edge['target']]]))
           , path=['Views', 'Generated superset dashboards']) 
        for dashboard in dashboard_nodes])
        
    views.extend([ArchimateUtils.generate_view(
            model
           , name=slice_node['name']
           , layout=Layout.HIERARCHICAL
           , nodes=list(set(['dashboard'] + [node for edge in model.edges.to_dict(orient='records') if edge['source'] == slice_node['id'] or edge['target'] == slice_node['id'] 
               for node in [edge['source'], edge['target']]]))
           , path=['Views', 'Generated superset slices']) 
        for slice_node in slice_nodes])
    
    views.extend([ArchimateUtils.generate_view(
            model
           , name=table['name']
           , layout=Layout.HIERARCHICAL
           , nodes=list(set([node for edge in model.edges.to_dict(orient='records') if edge['source'] == table['id'] or edge['target'] == table['id'] 
               for node in [edge['source'], edge['target']]]))
           , path=['Views', 'Generated superset tables']) 
        for table in table_nodes])
                
    concept_metadata = [{
            'id': concept['id']
            , 'data': {
                'original_id': concept['id']
                , 'created_on': (datetime.now() - datetime.utcfromtimestamp(0)).total_seconds() * 1000.0
                , 'created_by': script_name
                }
            } for concept in (nodes + edges)]
            
    view_metadata = [{
        'id': view[model.getViewAttributeMapping(ViewAttribute.ID)]
        , 'data': {
            'original_id': view[model.getViewAttributeMapping(ViewAttribute.ID)]
            , 'created_on': (datetime.now() - datetime.utcfromtimestamp(0)).total_seconds() * 1000.0
            , 'created_by': script_name
            }
        } for view in views]
            
    return {'model': model,
            'data': concept_metadata + view_metadata}
    
# END generate_superset_model    
