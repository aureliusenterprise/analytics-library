# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 23:38:30 2018

@author: andre
"""

#%%
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.graphs.model.Graph import EdgeAttribute, NodeAttribute
from m4i_analytics.m4i.platform.PlatformUtils import PlatformUtils
from m4i_analytics.graphs.visualisations.GraphPlotter import Layout
from m4i_analytics.graphs.GraphComplexity import GraphComplexity
from m4i_analytics.graphs.GraphUtils import GraphUtils
import pydotplus as ptp
import pandas as pd
import numpy as np
from m4i_analytics.graphs.languages.archimate.model.ArchimateModel import ArchimateModel
from m4i_analytics.graphs.languages.archimate.metamodel.Concepts import ElementType, RelationshipType
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.graphs.visualisations.GraphPlotter import Layout

if __name__ == '__main__': 
    
    ' To load your own model from the repository make the changes indicated by the comments below: '
    model_options = {
            'projectName': 'steel',  # change to your project name
            'projectOwner': 'dev',     # change to the user name of the owner of the project
            'branchName': 's80',
            'userid': 'dev',              # change to your user name
            'withData': 'true',
    }
    
    #model = ArchimateUtils.load_model_from_repository(**model_options)
    
    
    #%%
    df = pd.read_csv('C:/Users/thijs/Downloads/datamodel.csv', sep=';')
    prevC = ''
    prevT = ''
    for index, row in df.iterrows():
        if row['column']!= row['column'] or len(str(row['column']))<2 :
            row['column'] = prevC
        prevC = row['column']
        if prevT != row.table: 
            prevC=''
            prevT= row['table']
        if row.description!=row.description:
            row.description = ''
    
    df2 = df.groupby(by=['table','column']).apply(lambda x: ', '.join(x.description)).rename('description').reset_index()
    
    #%%
    # Add top level elements for tables and columns
    org_elem = ['database table','database table column']
    org_rel = ['database_table column']
    elems = [{'id':'database table', 'name':'database table', 'type': ElementType.DATA_OBJECT},
            {'id':'database table column', 'name':'database table column', 'type': ElementType.DATA_OBJECT}]
        
    # A table is a set of columns, so add an aggregation relationship between table and column
    rels = [{'id':'database_table column', 'type': RelationshipType.AGGREGATION, 'source': 'database table' ,'target': 'database table column', 'name':''}]
    #, columns=['id', 'name', 'type', 'label', 'source', 'target'])
    nodes = []
    edges = []
    data = []
    view = []
    prev_tab_name = ''
    for index, row in df2.iterrows():
        table_name = row['table']
        column_name = row['column']
        # First, create a node representing the table
        if table_name!=prev_tab_name:
            if len(nodes)>0:
                elems.extend(nodes)
                rels.extend(edges)
                view.append({'nodes': [node['id'] for node in nodes], 'edges': [edge['id'] for edge in edges], 'name':prev_tab_name})
            nodes = [{'id':table_name, 'name':table_name, 'type': ElementType.DATA_OBJECT, 'label': table_name}]
            org_elem.append(table_name)
            edges = [{'id':'database_table_'+table_name, 'type': RelationshipType.SPECIALIZATION, 'source': table_name ,'target': 'database table', 'name': '', 'label': ''}]
            org_rel.append('database_table_'+table_name)
            prev_tab_name = table_name
        name = '{0}.{1}'.format(table_name, column_name)
        nodes.append({'id':name, 'name':name, 'type': ElementType.DATA_OBJECT, 'label':name})    
        org_elem.append(name)    
        edges.append({'id': 'r_'+name,  'type': RelationshipType.AGGREGATION, 'source': table_name ,'target': name, 'name': '', 'label': ''})          
        edges.append({'id':'database_table column_'+name, 'type': RelationshipType.SPECIALIZATION, 'source': name ,'target': 'database table column', 'name': '', 'label': '' })
        org_rel.append('r_'+name)
        org_rel.append('database_table column_'+name)
    if len(nodes)>0:
        elems.extend(nodes)
        rels.extend(edges)
        view.append({'nodes': [node['id'] for node in nodes], 'edges': [edge['id'] for edge in edges], 'name':table_name})
        
        
    # END LOOP
    # Add the generated concepts to the model organization
    
    #%%
    df_elems = pd.DataFrame(elems, columns=['id', 'name', 'type', 'label'])    
    df_rels = pd.DataFrame(rels, columns=['id', 'name', 'type', 'label', 'source', 'target'])
        
    model = ArchimateModel('generated data model', df_elems, df_rels, defaultAttributeMapping=True)
    model.putNodeAttributeMapping(NodeAttribute.LABEL, model.getNodeAttributeMapping(NodeAttribute.NAME))
    model.putEdgeAttributeMapping(EdgeAttribute.LABEL, model.getEdgeAttributeMapping(EdgeAttribute.NAME))  
    
    print(view)
    
    views = ([ArchimateUtils.generate_view(
                model
               , name=view_['name']
               , layout=Layout.HIERARCHICAL
               , nodes=list(view_['nodes'])
               , edges=list(view_['edges']))
            for view_ in view])
    
    model.organize();
    
    
    nodes = model.nodes
    nodes = nodes[np.logical_not(nodes.type.isnull())]
    #nodes2 = nodes[nodes.type == ]
    model.nodes = nodes
    
    output_path = 'C:/Users/thijs/Desktop/csv_model.json'
    with open(output_path, 'w') as output:
        output.write(ArchimateUtils.to_JSON(model))
    # END WITH
        
    data = [{'id': row['table']+'.'+row['column'], 'data':{'ar3_documentation': row['description']}} for index, row in df2.iterrows()] 
    PlatformUtils.upload_model_data(fullProjectName='test786234239',branchName='MASTER', modelId='TRUNK', conceptData=data)
    