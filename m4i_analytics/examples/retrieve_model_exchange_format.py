# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 21:27:10 2019

@author: andre
"""

from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.m4i.platform.PlatformApi import PlatformApi

model_options = {
    'projectName': 'dev__test35',
    'branchName': 'cgi demo',
    'userid': 'dev'
}

model_options2 = {
    'projectName': 'test24',
    'projectOwner': 'dev',
    'branchName': 'color model',
    'userid': 'dev'
}

auth_options = {
    'username': 'dev',
    'password': 'xxxxxx'
}

# Retrieve a model from the repository
model = ArchimateUtils.load_model_from_repository(
    **model_options, **auth_options)

xml =  PlatformApi.retrieve_model(**model_options,  **auth_options,contentType="xml")
f= open("cgi_demo_model.xml","wb")
f.write(xml)
f.close()