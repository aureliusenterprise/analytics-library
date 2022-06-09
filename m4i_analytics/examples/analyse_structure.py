# -*- coding: utf-8 -*-
"""
Created on Mon May 28 16:08:56 2018

@author: andre
"""

from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.graphs.languages.archimate.metamodel.Concepts import ElementType, RelationshipType, Aspect,Layer
from m4i_analytics.graphs.GraphUtils import GraphUtils
from m4i_analytics.graphs.languages.archimate.model.ArchimateModel import ArchimateModel, ViewAttribute
from m4i_analytics.graphs.model.Graph import NodeAttribute, EdgeAttribute

from math import log
import pandas as pd
import scipy.stats
import numpy as np
from m4i_analytics.m4i.platform.PlatformApi import PlatformApi
from m4i_analytics.m4i.platform.model.ModelProvenance import OperationEnum
from m4i_analytics.m4i.platform.model.ModelQuery import ModelQuery
from m4i_analytics.m4i.platform.model.ModelQueryDifResult import ModelQueryDifResult
from m4i_analytics.m4i.portal.PortalApi import PortalApi 
from m4i_analytics.m4i.portal.DBUtils import DBUtils, InsertBehavior
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import networkx as nx


# slice a model based on a set of relationship types
# return a new model
# WILL NEED THIS AS A CONVENIENCE FUNCTION    
def slice_model(model, rel_types) :
    relationships = model.edges
    rels = relationships[relationships.type.isin(rel_types)]
    elem_ids = list(rels.source.unique()) + list(rels.target.unique())
    elements = model.nodes
    elems = elements[elements.id.isin(elem_ids)]
    organizations = model.organizations
    orgs = organizations[organizations.idRef.isin(elem_ids)]
    result=  ArchimateModel(**{
            "name": model.name+' slice for '+str(rel_types),
            "nodes": elems,
            "edges": rels,
            "views": pd.DataFrame(columns=['id','name','type','connections','nodes','properties']),
            "organizations": orgs
        })
    result.putNodeAttributeMapping(NodeAttribute.ID, "id")
    result.putNodeAttributeMapping(NodeAttribute.TYPE, "type")
    result.putNodeAttributeMapping(NodeAttribute.NAME, "name")
    result.putNodeAttributeMapping(NodeAttribute.LABEL, "label")
    
    result.putEdgeAttributeMapping(EdgeAttribute.ID, "id")
    result.putEdgeAttributeMapping(EdgeAttribute.TYPE, "type")
    result.putEdgeAttributeMapping(EdgeAttribute.NAME, "name")
    result.putEdgeAttributeMapping(EdgeAttribute.LABEL, "label")
    result.putEdgeAttributeMapping(EdgeAttribute.SOURCE, "source")
    result.putEdgeAttributeMapping(EdgeAttribute.TARGET, "target")
    
    result.putViewAttributeMapping(ViewAttribute.ID, "id")
    result.putViewAttributeMapping(ViewAttribute.NAME, "name")
    result.putViewAttributeMapping(ViewAttribute.TYPE, "type")
    result.putViewAttributeMapping(ViewAttribute.CONNECTIONS, "connections")
    result.putViewAttributeMapping(ViewAttribute.NODES, "nodes")
    result.putViewAttributeMapping(ViewAttribute.PROPERTIES, "properties")

    return result
# end of function slice_model

if __name__ == '__main__':    
    
    # Analyze model structures of AgriComp
    model_options = {
                    'projectName': 'AgriCOmp', 
                    'projectOwner': 'dev', 
                    'branchName': 'MASTER', 
                    'userid': 'test_user'
                }
    
    model = ArchimateUtils.load_model_from_repository(**model_options)    
    
    # find groups of concepts belonging together via a specific relation type
    rels = model.edges
    rel_types = list(rels.type.unique())
    elems = model.nodes
    
    for rel_type in rel_types:
        print(rel_type)
        m2 = slice_model(model, [rel_type]) 
        g2= GraphUtils.toNXGraph(m2)
        g2 = g2.to_undirected()
     
        nx.is_connected(g2)
        print(nx.number_connected_components(g2)	)
    
