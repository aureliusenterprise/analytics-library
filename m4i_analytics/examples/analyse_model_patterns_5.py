# -*- coding: utf-8 -*-
"""
Created on Sun Jun 10 22:53:25 2018

@author: andre
"""
#%%
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.graphs.languages.archimate.metamodel.Concepts import ElementType, RelationshipType, Aspect,Layer
from m4i_analytics.graphs.GraphUtils import GraphUtils
from m4i_analytics.graphs.languages.archimate.model.ArchimateModel import ArchimateModel, ViewAttribute
from m4i_analytics.graphs.model.Graph import NodeAttribute, EdgeAttribute
from m4i_analytics.graphs.visualisations.GraphPlotter import GraphPlotter 

from math import log, pi
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

from bokeh.plotting import figure 
from datetime import date
from random import randint

from bokeh.io import output_file, show
from bokeh.layouts import widgetbox
from bokeh.models import ColumnDataSource, LinearColorMapper, ColorBar, Title, Legend
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn
from bokeh.layouts import gridplot,layout
from bokeh.models.widgets import Div
from bokeh.transform import transform
from bokeh.palettes import Greys256, PuBu, Plasma256, GnBu3, OrRd3,Category20, Plasma, linear_palette

if __name__ == '__main__':    

    #%%
    CUT_OFF = 3 # each pattern must be supported by at least 3 instances
    model_options = {
                    'projectName': 'Archisurance', 
                    'projectOwner': 'dev', 
                    'branchName': 'MASTER', 
                    'userid': 'test_user'
                }
    model = ArchimateUtils.load_model_from_repository(**model_options)    
    
    #%%
    rels = model.edges
    nodes = model.nodes
    
    rels = rels.merge(nodes, how='left', left_on='source', right_on='id')
    rels = rels[['id_x', 'type_x', 'source','target','type_y']]
    rels.columns = ['rel_id','rel_type', 'source','target', 'src_type']
    rels = rels.merge(nodes, how='left', left_on='target', right_on='id')
    rels = rels[['rel_id','rel_type', 'source','target', 'src_type', 'type']]
    rels.columns = ['rel_id','rel_type', 'source','target', 'src_type','trg_type']
    
    rels.rel_type = rels.rel_type.apply(lambda x: x['typename'])
    rels.src_type = rels.src_type.apply(lambda x: x['typename'])
    rels.trg_type = rels.trg_type.apply(lambda x: x['typename'])
    
    rels_agg = rels.groupby(['rel_type','src_type','trg_type']).apply(lambda x: list(x['rel_id'])).rename('set_').reset_index()
    rels_agg['cnt'] = rels_agg.set_.apply(lambda x: len(x))
    
    # apply cut off
    rels_agg = rels_agg[rels_agg.cnt>=CUT_OFF]
    
    #rules0 = []
    constr0 = []
    opt0 = ''
    bin0 = 'bin '
    for index, row in rels_agg.iterrows():
        ii=0
        rel_ids = row['set_']
        for rel_id in rel_ids:
            opt0 = opt0+' + m'+str(index)+'_'+str(ii)
            constr0.append((rel_id, 'm'+str(index)+'_'+str(ii)))
            #rules0.append('m'+str(index)+' <= 1;')
            bin0 = bin0+'m'+str(index)+'_'+str(ii)+','
            ii = ii+1
    bin0 = bin0[0:-1]+';'
    
    #constr = rels.index.to_series().apply(lambda x: 'm'+str(x))
    constr = pd.DataFrame(constr0, columns=['rel_id','constr_str'])
    
    rels2 = rels.merge(rels, how='inner', left_on='target', right_on='source')
    rels2.columns = ['rel_id1', 'rel_type1', 'source1', 'target1', 'src_type1',
           'trg_type1', 'rel_id2', 'rel_type2', 'source2', 'target2',
           'src_type2', 'trg_type2']
    
    rels2_agg = rels2.groupby(['rel_type1','src_type1','rel_type2','src_type2','trg_type2']).apply(lambda x: list(x['rel_id1']+'|'+x['rel_id2'])).rename('set_').reset_index()
    rels2_agg['cnt'] = rels2_agg.set_.apply(lambda x: len(x))
    
    # remove patterns which are a multiple of themselves
    rels2_agg = rels2_agg[np.logical_or(
                np.logical_or(rels2_agg.rel_type1!=rels2_agg.rel_type2, rels2_agg.src_type2!=rels2_agg.trg_type2)
                ,rels2_agg.src_type1!=rels2_agg.src_type2) ]
    
    # apply cut off
    rels2_agg = rels2_agg[rels2_agg.cnt>= CUT_OFF]
    
    rules2 = []
    constr2 = []
    opt2 = ''
    bin2 = 'bin '
    for index, row in rels2_agg.iterrows():
        rel_ids = row['set_']
        ii = 0
        for rel_id in rel_ids:
            str_arr = rel_id.split('|')
            opt2 = opt2+' + 2 p'+str(index)+'_'+str(ii)+'_0 + 2 p'+str(index)+'_'+str(ii)+'_1'
            constr2.append((str_arr[0], 'p'+str(index)+'_'+str(ii)+'_0'))
            constr2.append((str_arr[1], 'p'+str(index)+'_'+str(ii)+'_1'))
            rules2.append('p'+str(index)+'_'+str(ii)+'_0'+' - p'+str(index)+'_'+str(ii)+'_1 = 0;')
            #rules2.append('p'+str(index)+' <= 1;')
            bin2 = bin2+'p'+str(index)+'_'+str(ii)+'_0'+',p'+str(index)+'_'+str(ii)+'_1,'
            ii = ii + 1
    bin2 = bin2[0:-1]+';'
    #constr = rels.index.to_series().apply(lambda x: 'p'+str(x) if )
    
    constr2df = pd.DataFrame(constr2, columns=['rel_id','constr_str'])
    constr2df = constr2df.groupby(by='rel_id').apply(lambda x: ' + '.join(x['constr_str'])).rename('constr_str2').reset_index()
    constr = constr.merge(constr2df, how='left', on='rel_id')
    constr.loc[constr.constr_str2.notnull(),'constr_str'] = constr[constr.constr_str2.notnull()].apply(lambda x: 
                                        x['constr_str'] + ' + ' + x['constr_str2'],axis=1)
    
    #%%
    # write to an LPsolver file
    
    f= open("archisurance_cluster2.lp","w")
    f.write('\nmax: '+opt0[2:])
    f.write('\n      '+opt2+' ;')
    f.write('\n ')
    f.write('\n/* constraints per relation */')
    f.write('\n/* each relation can only belong to a single pattern */')
    for index,row in constr.iterrows():
        f.write('\n'+row['constr_str']+' = 1; /* '+str(row['rel_id'])+' */')
    f.write('\n ')
    f.write('\n/* constraints per pattern */')
    f.write('\n/* all relations belonging to a single pattern must be included */')
    for row in rules2:
        f.write('\n'+row)
    f.write('\n ')
    f.write('\n/* define all variables as binary */')
    f.write('\n'+bin0)
    f.write('\n'+bin2)
    f.close()
    
    #%%
    # execute the logical program
    
    #%%
    # process the analytics result
    
    result = pd.read_csv('archisurance_cluster2.lp.csv',sep=';')
    result = result[result.Variables.notnull()]
    
    positive = list(result.apply(lambda x: [x['result'], x['Variables'][0]]+ x['Variables'][1:].split('_') , axis=1))
    positivedf = pd.DataFrame(positive, columns=['result','letter','pattern','instance','rel_index'])
    positivedf.pattern = positivedf.pattern.apply(lambda x: int(float(x)))
    
    positivedf = positivedf[positivedf.result==1]
    #pos_agg = positivedf.groupby(by=['letter', 'pattern']).apply(lambda x: '|'.join(set(x['instance']))).rename('inst').reset_index()
    pos_agg = positivedf.groupby(by=['letter', 'pattern']).apply(lambda x: len(set(x['instance']))).rename('inst_cnt').reset_index()
    
    pos_agg2 = pos_agg[pos_agg.letter=='p']
    mapping2 = rels2_agg.merge(pos_agg2, how='left', left_index=True, right_on='pattern')
    
    mapping2.inst_cnt = mapping2.inst_cnt.fillna(0)
    mapping2['ratio'] = mapping2.inst_cnt / mapping2.cnt
    mapping2['pattern_str'] = mapping2.src_type1+'-'+mapping2.rel_type1+'-'+mapping2.src_type2+'-'+mapping2.rel_type2+'-'+mapping2.trg_type2
    
    map2_aggP = mapping2[['pattern_str','cnt','inst_cnt']]
    map2_aggP = map2_aggP.fillna(0)
    map2_aggP = map2_aggP.sort_values(by='pattern_str', ascending=True)
    #map2_aggP = map2_aggP.reset_index()
    columns = list(map2_aggP.columns[1:])
    columns_new = ['pattern_str']
    ii=1
    for c in map2_aggP.columns[1:]:
        columns_new.append('c'+str(ii))
        ii=ii+1
    map2_aggP.columns = columns_new
    
    p = figure(y_range=list(map2_aggP.pattern_str), plot_height=400, plot_width=1024, 
               title="Possible vs actual frequency of model pattern",
               toolbar_location=None)
    
    p.hbar_stack(list(columns_new[1:]), y='pattern_str', height=0.9, color=['green','blue'], 
                 source=ColumnDataSource(map2_aggP), legend=["%s " % x for x in columns])
    
    p.y_range.range_padding = 0.01
    p.ygrid.grid_line_color = None
    p.legend.location = "top_left"
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    #p.legend.orientation = "horizontal"
    #p.legend.location=(300,0)
    
    new_legend = p.legend[0]
    p.legend[0].plot = None
    p.add_layout(new_legend, 'right')
    show(p)
    
    
    
    #%%
    df = pd.DataFrame(list(rels2.rel_id1)+list(rels2.rel_id2), columns=['rel_id'])
    df = df.groupby(by='rel_id').size().rename('cnt').reset_index()
    df_agg = df.groupby(by='cnt').size().rename('freq').reset_index()
    df_agg.plot.bar('cnt','freq')