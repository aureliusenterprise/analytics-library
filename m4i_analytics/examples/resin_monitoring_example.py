# -*- coding: utf-8 -*-
"""
Created on Mon Aug 20 21:58:12 2018

@author: andre
"""
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.model_extractor.ResinExtractor import ResinExtractor

if __name__ == '__main__':

    model_options = {
        'projectOwner': 'dev',
        'projectName': 'test_resin_1125',
        }

    username ='delphi_admin' 
    password = 'Delphi!123' 

    res = ResinExtractor.extract_resin_model(username, password)
    model = res['model']
    data = res['data']

    # set a name which is common for all branches
    model.name = 'monitoring model'

    # upload the model to the repository
    res2 = ArchimateUtils.commit_model_to_repository(model, branchName='MASTER', userid='dev', description='monitoring model', **model_options)
