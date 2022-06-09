# -*- coding: utf-8 -*-
"""
Created on Wed May  8 12:11:44 2019

@author: andre
"""

#%% 
# Analyze model structures of AgriComp

from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from credentials import user, passwd

model_options = {
                'projectName': 'ShipManagement',
                'projectOwner': 'manonvanrooijen', 
                'branchName': 'SMD Architecture',
                'userid': 'dev', 
                'version': 1622543826890,
                'username': user,
                'password': passwd
            }
model_xin = ArchimateUtils.load_model_from_repository(**model_options)    

nodes_xin = model_xin.nodes
edges_xin = model_xin.edges
views_xin = model_xin.views

#%%
model_options = {
                'projectName': 'ShipManagement',
                'projectOwner': 'manonvanrooijen', 
                'branchName': 'SMD Architecture',
                'userid': 'dev', 
                'version': 1622543097330,
                'username': user,
                'password': passwd
            }
model_xin1 = ArchimateUtils.load_model_from_repository(**model_options)    

nodes_xin1 = model_xin1.nodes
edges_xin1 = model_xin1.edges
views_xin1 = model_xin1.views



#%%
# check a missing id
id_ = "id_512b84b"

row = nodes_xin[nodes_xin['id'].apply(lambda x: id_ in x)]


ArchimateUtils.cion available ommit_model_to_repository_with_conflict_resolution(model, conflict_resolution_template="upload_only", description="commit_test", **model_options)
#%%
model_options = {
                'projectName': 'ShipManagement',
                'projectOwner': 'manonvanrooijen', 
                'branchName': 'SMD Architecture',
                'userid': 'dev', 
                'version': 1622543826890,
                'username': user,
                'password': passwd
            }
model_xin = ArchimateUtils.load_model_from_repository(**model_options)    

nodes_xin = model_xin.nodes
edges_xin = model_xin.edges
views_xin = model_xin.views

1622543826890
#%%
# smd branch input
model_options = {
                'projectName': 'xin_test2',
                'projectOwner': 'dev', 
                'branchName': 'smd branch',
                'userid': 'dev', 
                'username': user,
                'password': passwd
            }
model_dev = ArchimateUtils.load_model_from_repository(**model_options)    

nodes_dev = model_dev.nodes
edges_dev = model_dev.edges
views_dev = model_dev.views

#%%
# marine branch input
model_options = {
                'projectName': 'xin_test2',
                'projectOwner': 'dev', 
                'branchName': 'marine branch',
                'userid': 'dev', 
                'username': user,
                'password': passwd
            }
model_dev2 = ArchimateUtils.load_model_from_repository(**model_options)    

nodes_dev2 = model_dev2.nodes
edges_dev2 = model_dev2.edges
views_dev2 = model_dev2.views

#%%
# merged result
model_options = {
                'projectName': 'xin_test2',
                'projectOwner': 'dev', 
                'branchName': 'smd branch',
                'userid': 'dev', 
                'username': user,
                'password': passwd
            }
model_dev3 = ArchimateUtils.load_model_from_repository(**model_options)    

nodes_dev3 = model_dev3.nodes
edges_dev3 = model_dev3.edges
views_dev3 = model_dev3.views

#%%
# compare ID in both models

nodes_xin1[nodes_xin1['id'].isin(nodes_dev['id'].to_list())]

nodes_xin1[nodes_xin1['id'].isin(nodes_xin['id'].to_list())]

nodes_xin[nodes_xin['id'].isin(nodes_dev2['id'].to_list())]

#%%
nodes_xin[~nodes_xin['id'].isin(nodes_dev3['id'].to_list())]
nodes_dev3[~nodes_dev3['id'].isin(nodes_xin['id'].to_list())]
# merged models do not have a deviation in nodes

edges_xin[~edges_xin['id'].isin(edges_dev3['id'].to_list())]
edges_dev3[~edges_dev3['id'].isin(edges_xin['id'].to_list())]

views_xin[~views_xin['id'].isin(views_dev3['id'].to_list())]
views_dev3[~views_dev3['id'].isin(views_xin['id'].to_list())]

views_xin['nodes']==views_dev3['nodes']

#%%
res = []
for ind, row in views_xin.iterrows():
    # vnodes = views_xin['nodes'].iloc[0]
    vnodes = row['nodes']
    if vnodes!=None:
        if '@elementRef' in vnodes:
            v_node_elem = [node['@elementRef'] for node in vnodes]
            res.append(len(nodes_xin[nodes_xin['id'].isin(v_node_elem)])==len(v_node_elem))
        else:
            res.append(True)
    else:
        AgriCompres.append(True)