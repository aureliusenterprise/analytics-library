# -*- coding: utf-8 -*-
"""
Created on Wed Nov  7 16:30:22 2018

@author: andre
"""
#%%
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
import pandas as pd

if __name__ == '__main__': 
    
    res = ArchimateUtils.commit_model_to_repository(sup_model, branchName='MASTER', userid='dev', description='initial model', projectName='test9993', projectOwner='dev')
    
    #%%
    model = sup_model
    model = resin_model
    nodes = model.nodes
    edges = model.edges
    views = model.views
    org = model.organizations
    data = sup_data
    
    #%%
    import pandas as pd
    model = sup_model
    nodes = model.nodes
    edges = model.edges
    views = model.views
    org = model.organizations
    
    remarks = []
    agg = nodes.groupby(by='id').size().rename('cnt').reset_index()
    agg = agg[agg.cnt>1]
    if len(agg)>0:
        remarks.extend([{'label': 'duplicate node id','ref': row['id']} for index,row in agg.iterrows() ])
    nids = list(set(nodes.id))
    
    agg = edges.groupby(by='id').size().rename('cnt').reset_index()
    agg = agg[agg.cnt>1]
    if len(agg)>0:
        remarks.extend([{'label': 'duplicate edge id', 'ref': row['id']} for index,row in agg.iterrows() ])
    eids = list(set(edges.id))
    
    agg = views.groupby(by='id').size().rename('cnt').reset_index()
    agg = agg[agg.cnt>1]
    if len(agg)>0:
        remarks.extend([{'label': 'duplicate view id','ref': row['id']} for index,row in agg.iterrows() ])
    vids = list(set(views.id))
    
    r = edges[edges.id.apply(lambda x: x in nids)]
    if len(r)>0:
        remarks.extend([{'label': 'duplicate id in nodes and relations', 'ref': row['id']} for index,row in r.iterrows() ])
    
    r = views[views.id.apply(lambda x: x in nids)]
    if len(r)>0:
        remarks.extend([{'label': 'duplicate id in views and nodes', 'ref': row['id']} for index,row in r.iterrows() ])
    
    r = views[views.id.apply(lambda x: x in eids)]
    if len(r)>0:
        remarks.extend([{'label': 'duplicate id in views and relations', 'ref': row['id']} for index,row in r.iterrows() ])
    
    all_ids = list(set(nids).union(eids).union(vids))
    
    r = edges[edges.source.apply(lambda x: x not in nids)]
    if len(r)>0:
        remarks.extend([{'label': 'missing source node reference in relation', 'ref': row['id']} for index,row in r.iterrows() ])
        
    r = edges[edges.target.apply(lambda x: x not in nids)]
    if len(r)>0:
        remarks.extend([{'label': 'missing target node reference in relation', 'ref': row['id']} for index,row in r.iterrows() ])
    
    #row = views.iloc[0]
    for index, row in views.iterrows():
        vn = pd.DataFrame(row['nodes'] )
        ve = pd.DataFrame(row['connections'] )
        if len(vn)>0:
            # check for duplicates in ids
            agg = vn.groupby(by='@identifier').size().rename('cnt').reset_index()
            agg = agg[agg.cnt>1]
            if len(agg)>0:
                remarks.extend([{'label': 'duplicate node identifier in view %s with id' % row['name'], 'ref':row2['@identifier']} for index2,row2 in agg.iterrows() ])
            vn_ids = list(set(vn['@identifier']))
            r = vn[vn[ '@identifier'].apply(lambda x: x in all_ids)]
            if len(r)>0:
                remarks.extend([{'label': 'duplicate id in view nodes and other concepts in view %s' % row['name'], 'ref':row2['@identifier']} for index2,row2 in r.iterrows() ])
            all_ids = list(set(all_ids).union(set(vn_ids)))
        
            # check @elementRef
            r = vn[vn['@elementRef'].apply(lambda x: x not in nids)]
            if len(r)>0:
                remarks.extend([{'label': 'wrong element reference in view %s' %  row['name'], 'ref':row2['@identifier']} for index2,row2 in r.iterrows() ])
    
        if len(ve)>0:    
            agg = ve.groupby(by='@identifier').size().rename('cnt').reset_index()
            agg = agg[agg.cnt>1]
            if len(agg)>0:
                remarks.extend([{'label': 'duplicate edge identifier in view %s with id' % row['name'], 'ref':row2['@identifier']} for index2,row2 in agg.iterrows() ])
            ve_ids = list(set(vn['@identifier']))
            r = ve[ve['@identifier'].apply(lambda x: x in all_ids)]
            if len(r)>0:
                remarks.extend([{'label': 'duplicate id in relations with other ids in view %s' % row['name'], 'ref':row2['@identifier']} for index2,row2 in r.iterrows() ])
            all_ids = list(set(all_ids).union(set(ve_ids)))
            
            # check references inside the view: @source @target
            r = ve[ve['@source'].apply(lambda x: x not in vn_ids)]
            if len(r)>0:
                remarks.extend([{'label': 'wrong source reference in view %s' %  row['name'], 'ref':row2['@identifier']} for index2,row2 in r.iterrows() ])
            r = ve[ve['@target'].apply(lambda x: x not in vn_ids)]
            if len(r)>0:
                remarks.extend([{'label': 'wrong target reference in view %s' %  row['name'], 'ref':row2['@identifier']} for index2,row2 in r.iterrows() ])
            
            # check @relationshipRef
            r = ve[ve['@relationshipRef'].apply(lambda x: x not in eids)]
            if len(r)>0:
                remarks.extend([{'label': 'wrong relationship reference in view %s' %  row['name'], 'ref':row2['@identifier']} for index2,row2 in r.iterrows() ])
            
        
    
    remarks
    df = pd.DataFrame(remarks)
