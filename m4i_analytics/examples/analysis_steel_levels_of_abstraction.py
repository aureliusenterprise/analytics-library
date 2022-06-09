# -*- coding: utf-8 -*-
"""
Created on Wed Aug  8 00:02:25 2018

@author: andre
"""
#%%
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.graphs.languages.archimate.metamodel.Concepts import RelationshipType
from m4i_analytics.graphs.GraphUtils import GraphUtils
from m4i_analytics.graphs.languages.archimate.model.ArchimateModel import ArchimateModel, ViewAttribute
from m4i_analytics.graphs.model.Graph import NodeAttribute, EdgeAttribute
from m4i_analytics.m4i.platform.PlatformUtils import PlatformUtils

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import networkx as nx
import pandas as pd
import numpy as np

if __name__ == '__main__':    

    model_options = {
            'projectName': 'steel',
            'projectOwner': 'dev',
            'branchName': 's80',
            'userid': 'dev'
        }
        
    model = ArchimateUtils.load_model_from_repository(**model_options)
    g0 = GraphUtils.toNXGraph(model)
    
    
    #%%
    
    def parse_view_concepts(model):
        views = model.views
        view_concepts = []
        for index, view in views.iterrows():
            view_desc= {'view_name':view['name'], 'view_id':view.id}
            if (view.nodes is not None) and (len(view.nodes)>0):
                res = parse_view_items(view.nodes, view_desc, {}, [], [], None, 0)        
                view_concepts = view_concepts+res
            if (view.connections is not None) and (len(view.connections)>0):
                res = parse_view_items(view.connections, view_desc, {}, [], [], None, 0)        
                view_concepts = view_concepts+res
        df_view_concepts = pd.DataFrame(view_concepts)
        return df_view_concepts
    
        
    def parse_view_items(items, view_desc, levels_, levels_arr, levels_ref, parent,  level_):
        res = []
        for item in items:
            levels_new = levels_.copy()
            item_keys = item.keys()
            id_ = ''
            x=0
            y=0
            w=0
            h=0
            label_=''
            type_=None
            ref=None
            ref_type=None
            source=None
            target=None
            res_new  = {}
            if '@x' in item_keys:
                x = item['@x']
            if '@y' in item_keys:
                y = item['@y']
            if '@w' in item_keys:
                w = item['@w']
            if '@h' in item_keys:
                h = item['@h']
            if '@identifier' in item_keys:
                id_ = item['@identifier']
            if '@elementRef' in item_keys:
                ref = item['@elementRef']
                ref_type='ar3_Element'
            if '@source' in item_keys:
                source = item['@source']
            if '@target' in item_keys:
                target = item['@target']
            if '@RelationshipRef' in item_keys:
                ref = item['@relationshipRef']
                ref_type='ar3_Relationship'
            if '@xsi_type' in item_keys:
                type_ = item['@xsi_type']
            if 'ar3_label' in item_keys:
                label_obj = item['ar3_label'][0]
                label_=label_obj['value']
            if 'ar3_viewRef' in item_keys:
                view_ref = item['ar3_viewRef'][0]
                if '@ref' in view_ref.keys():
                    ref = view_ref['@ref']
                    ref_type='ar3_viewRef'
                ref_type='ar3_view'
            if 'ar3_node' in item_keys:
                item_list = item['ar3_node']
                #list_ = []
                ref_type='ar3_node'
                #print(item_list)
                #for item_ in item_list:
                #    print(item_)
                levels_new['level'+str(level_)] = id_
                levels_arr_new = levels_arr.copy()
                levels_arr_new.append(id_)
                if ref !=None:
                    levels_ref_new = levels_ref.copy()
                    levels_ref_new.append(ref)
                else:
                    levels_ref_new= levels_ref
                part = parse_view_items(item_list, view_desc, levels_new, levels_arr_new, levels_ref_new, ref, level_+1)
                #    if isinstance(part, list):
                #        list_ = list_ + part
                #    else:
                #        list_.append(part)
                res = res+part
            res_new = {'x': x, 'y':y, 'w':w, 'h':h, 'id': id_, 'label':label_, 'type':type_, 'ref':ref, 'ref_type': ref_type, 
                       'levels_id':levels_arr, 'levels_ref':levels_ref, 'parent': parent, 'source':source, 'target':target}
            res_new.update(levels_)
            res_new.update(view_desc)
            res.append(res_new)
        return res
    
    
    #%%
    nodes = model.nodes.copy()
    rels = model.edges.copy()
    views = model.views.copy()
    view_concepts = parse_view_concepts(model)
    
    nodes = nodes[np.logical_not(nodes.type.apply(lambda x: x is None))]
    model.nodes = nodes
    #%%
    # study the original graph
    g0 = GraphUtils.toNXGraph(model)
        
    nx.write_graphml(g0,'g.xml')
    
    # observations:
    # - Junctions are not adding anything to the investigation of layers
    # - node types seem to be equaly relevant than relationship types
    # - close relation to propagation of data in monitoring!
    
    #%%
    # study of a simple propagation mechanism
    # 1. initiate each node related via an aggregation or a composition relationship
    # 2. propagate this annotation to neighbouring nodes where the closest annotation wins
    
    # find the root nodes of aggreation and composition
    agg = rels[rels.type.apply(lambda x: x['typename'] == 'Aggregation')]
    comp = rels[rels.type.apply(lambda x: x['typename'] == 'Composition')]
    
    agg_target = list(agg.target)
    agg_top = agg[agg.source.apply(lambda x: x not in agg_target)]
    agg_top = list(agg_top.source.unique())
    
    agg_nodes = nodes[nodes.id.apply(lambda x: x in agg_top)]
    
    #agg_top2 = agg_top.merge(nodes, how='inner', left_on='source', right_on='id')
    
    comp_target = list(comp.target)
    comp_top = comp[comp.source.apply(lambda x: x not in comp_target)]
    comp_top = list(comp_top.source.unique())
    
    comp_nodes = nodes[nodes.id.apply(lambda x: x in comp_top)]
    
    
    # define the levels per root node by labeling them [C|A]_index_level
    # where index is the index of the root node and level is counting from 0
    anodes = nodes.copy()
    anodes = anodes.reset_index()
    anodes = anodes.set_index('id')
    
    anodes['level_index'] = 'undefined'
    anodes['level'] = 99
    anodes['distance'] = 99
    
    ll = agg_top
    ll_rel = agg
    ll_type= 'A'
    # initialize anodes with top nodes
    for ii in range(0,len(ll)): 
        agg_next = [ll[ii]]
        jj=0
        while len(agg_next)>0:
            anodes.loc[agg_next, 'level_index'] = (ll_type+str(ii))
            anodes.loc[agg_next, 'level'] = jj
            anodes.loc[agg_next, 'distance'] = 0
            jj = jj+1
            agg_next = list(ll_rel[ll_rel.source.apply(lambda x: x in agg_next)].target)
    
    ll = comp_top
    ll_rel = comp
    ll_type = 'C'
    # initialize anodes with top nodes
    for ii in range(0,len(ll)): 
        agg_next = [ll[ii]]
        jj=0
        while len(agg_next)>0:
            anodes.loc[agg_next, 'level_index'] = (ll_type+str(ii))
            anodes.loc[agg_next, 'level'] = jj
            anodes.loc[agg_next, 'distance'] = 0
            jj = jj+1
            agg_next = list(ll_rel[ll_rel.source.apply(lambda x: x in agg_next)].target)
    
    ll_next = list(anodes[anodes.level<99].index)
    visited = list(anodes[anodes.level<99].index)
    distance =1
    while len(ll_next)>0:
        ll_next_new = []
        for ee in ll_next:
            print(ee)
            src = anodes.loc[ee]
            trg = list(rels[rels.source == ee].target)
            trg = [x for x in trg if x not in visited and ((anodes.loc[x].type['aspect']==src.type['aspect'] and anodes.loc[x].type['layer']==src.type['layer']) or (anodes.loc[x].type['layer']=='Other') or (src.type['layer']=='Other')) ]
            anodes.loc[trg, 'level_index'] = src['level_index'] 
            anodes.loc[trg, 'level'] = src['level'] 
            anodes.loc[trg, 'distance'] = distance
            for ff in trg:
                ll_next_new.append(ff)
                visited.append(ff)
        #visited = list(anodes[anodes.level<99].id)
        #ll_next = list(rels[rels.source.apply(lambda x: x in ll_next)].target)
        #ll_next.remove_all(visited)
        ll_next = ll_next_new
        distance = distance + 1
        print(len(ll_next ))
            
    anodes[['index','level','level_index','distance']].to_csv('/Local2/code/analytics-library/m4i_analytics/examples/analytics_steel_levels_of_abstraction_data.csv')
    
    # lessons learned:
    # - limit the relations to use for propagation to a set of relationships like e.g. trigger, access, flow
    #     These are the horizontal order relations.      
    #     I have seen a junction where all outgoing connections and the junction are related to one aggregation
    #     while all source nodes of incoming connections are associated with an other aggregation - based on trigger relations.
    #     This does not make any sense.  
    # - disregard the directionality of the relationship 
    #     Just a thought: addressing potentially missing aggregate relations? Maybe causing confusion?
    #     Have to evaluate the effect.
    # - how to deal with conflicting propagations, i.e. assignments to different aggregations with the same distance, potentially different level?
    #     Current approach: first come, first serve
    #     How many conflicts do we have in the model?
    # - how to combine Aggregations and compositions? How to resolve their conflicts?
    #     How many nodes do we have in the model, which are effected by this?
    # needed a special treatment for junctions!
    
    #%%
    # publish the data to the repository to create a color view
    
    # data format
    #  [{ "id": "id-30281eb0-8819-4a55-80fd-fc05cd5a9cec",
    #	  "data": {"rel_prop2": "this is a test"}   },
    #    { "id": "id-bf074c46-5a51-4d81-9e1b-a66ae9186af6", 
    #      "data": {"ar3_documentation": "relation documentation"}	}]
    
    data = []
    for index, row in anodes.iterrows():
        data.append({'id': index, 'data': {'level': row.level,'level_index': row.level_index, 'distance':row.distance}})
    
    PlatformUtils.upload_model_data(projectOwner='dev', projectName='steel', branchName='MASTER', modelId='TRUNK', conceptData=data)
    
    f = open('/Local2/code/analytics-library/m4i_analytics/examples/analytics_steel_levels_of_abstraction_data.txt', 'w')
    for item in data:
      f.write("%s\n" % item)
    f.close()
      
    #%%
    # list the borders of the different level_index and their combination of levels
    
    mismatch = []
    for index,rel in rels.iterrows():
        try:
            if rel.source in anodes.index and rel.target in anodes.index:
                if anodes.loc[rel.source].level_index!=anodes.loc[rel.target].level_index:
                    #print(rel.index)
                    mismatch.append({'src_level_index': anodes.loc[rel.source].level_index, 'src_level': anodes.loc[rel.source].level,
                             'trg_level_index': anodes.loc[rel.target].level_index, 'trg_level': anodes.loc[rel.target].level})
        except:
            print(rel)
            
    mismatch2 = pd.DataFrame(mismatch)
    
    mismatch_detail = mismatch2.groupby(['src_level_index','src_level','trg_level_index','trg_level']).size()
    mismatch_detail = mismatch_detail.rename('cnt').reset_index()
    
    mismatch_overview = mismatch2.groupby(['src_level_index','trg_level_index']).size()
    mismatch_overview = mismatch_overview.rename('cnt').reset_index()
    
    mismatch_overview_pivot = mismatch_overview.pivot(index='src_level_index', columns='trg_level_index', values='cnt')
    mismatch_overview_pivot = mismatch_overview_pivot.fillna(0)
    
    #%%
    # =============================================================================
    #  I am trying to build an order:
    #  - concepts related via horizontal relations are merged as a tuple
    #  - hierarchical relations are reperesented by an order relation
    # =============================================================================
    
    rels = model.edges
    rel_types = list(rels.type.unique())
    
    cluster = []
    
    jj = 0
    for rel_type in rel_types:
        print(rel_type['typename'])
        #m2 = slice_model(model, [rel_type]) 
        m2 = ArchimateUtils.sliceByEdgeType(model, [rel_type])
        #g2 = derive_model_graph(m2)
        g2 = GraphUtils.toNXGraph(m2)
        #if rel_type in [RelationshipType.SPECIALIZATION]:
        #    g2 = g2.reverse()
        #list(g2.nodes(data=True))
        g3 = g2.to_undirected()
     
        print(nx.is_connected(g3))
        print(nx.number_connected_components(g3)	)
    
    
    #%%
    # slice a model based on a set of relationship types
    # return a new model
        
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
    
    def derive_model_graph(model) :
        G = nx.DiGraph()
    
        elements = model.nodes
        for index, row in elements.iterrows():
            G.add_node(row["id"])
            G.nodes[row["id"]]["type"] = row["type"].tag
            G.nodes[row["id"]]["name"] = row["name"]
            G.nodes[row["id"]]["class"] = 'element'
        relationships = model.edges
        for index, row in relationships.iterrows():
            src = row["source"]
            id_ = row["id"]
            trg = row["target"]
            if src not in G.nodes | trg not in G.nodes:
                raise ValueError('This model has relationships using relationships as start or end node, which is not supported in this graph model')
            else:
                G.add_edge(src,trg, id = id_, type = row["type"].tag, name = row["name"])
        return G 
    
    #%%
    # find groups of concepts belonging together via a specific relation type
    
    rels = model.edges
    rel_types = list(rels.type.unique())
    elems = model.nodes.copy()
    #elems.type = elems.type.apply(lambda x: x['tag'])
    #g0 = derive_model_graph(model)
    
    g0 = GraphUtils.toNXGraph(model)
    
    
    cluster = []
    
    jj = 0
    for rel_type in rel_types:
        print(rel_type)
        m2 = slice_model(model, [rel_type]) 
        #g2= GraphUtils.toNXGraph(m2)
        #g2 = derive_model_graph(m2)
        g2 = GraphUtils.toNXGraph(m2)
        #if rel_type in [RelationshipType.SPECIALIZATION]:
        #    g2 = g2.reverse()
        #list(g2.nodes(data=True))
        g3 = g2.to_undirected()
     
        nx.is_connected(g3)
        print(nx.number_connected_components(g3)	)
    
        #nx.connected_components(g2)
        #largest_cc = max(nx.connected_components(g2), key=len)
        #print(len(largest_cc))
        #elems[rel_type] = 0 # means not assigned to a connected group
        ii = 1
        for c in sorted(nx.connected_components(g3), key=len, reverse=True):
            elems.loc[elems.id.isin(list(c)),rel_type.tag] = ii
            H = g2.subgraph(list(c))
            SG=nx.DiGraph( [ (u,v,d) for u,v,d in H.edges(data=True) if d['type']==rel_type.tag] )
            cluster.append((rel_type.tag, ii, list(c), len(list(c)), nx.is_tree(H), nx.is_arborescence(H), nx.is_arborescence(H.reverse()), nx.is_tree(SG), nx.is_arborescence(SG),nx.is_arborescence(SG.reverse())))
            print(str(len(list(c)))+'|'+str(nx.is_arborescence(H)))
            ii = ii + 1
            for n in list(c):
                g0.node[n][rel_type]=ii
    cluster = pd.DataFrame.from_records(cluster, columns=['relation','id','elems','cnt','isTree','isArborescence','isArborescenceRev','isTree2','isArborescence2','isArborescence2Rev'])
    #nx.write_graphml(g0,'g.xml')
    
    #%%
