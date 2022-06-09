# -*- coding: utf-8 -*-
"""
Created on Wed May  8 12:11:44 2019

@author: andre
"""

#%% 
# Analyze model structures of AgriComp

from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils

model_options = {
                'projectName': 'model check',
                'projectOwner': 'dev', 
                'branchName': 'archisurance 3',
                'userid': 'dev', 
                'username': '<your username>',
                'password': '<your password>'
            }
model = ArchimateUtils.load_model_from_repository(**model_options)    

nodes = model.nodes
edges = model.edges
views = model.views

ArchimateUtils.commit_model_to_repository_with_conflict_resolution(model, conflict_resolution_template="upload_only", description="commit_test", **model_options)