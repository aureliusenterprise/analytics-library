# -*- coding: utf-8 -*-
"""
Created on Tue May 29 14:36:07 2018

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

#%%

def analyze_model(model_options, auth_options):
    
    #%%
    def get_data(model):
        ################################
        # basic statistics
        ################################
        elems = model.nodes.copy()
        rels = model.edges.copy()
        views = model.views
        
        # number of nodes and relations per type, tag, aspect, class and layer
        elems['tag'] = elems.type.apply(lambda x:x['tag'])
        elems['layer'] = elems.type.apply(lambda x:x['layer'])
        elems['aspect'] = elems.type.apply(lambda x:x['aspect'])
        elems = elems.drop(columns = ['type'] )
        
        rels['tag'] = rels.type.apply(lambda x:x['tag'])
        rels['relcls'] = rels.type.apply(lambda x:x['relcls'])
        rels = rels.drop(columns = ['type'] )
        
        # in and out degree
        datar = rels.groupby(by=['source']).size()
        datar = datar.reset_index()
        datar.columns= ['source', 'out_degree']
        datab = rels[rels.is_bidirectional==True].target
        if len(datab) > 0:
            datab.reset_index()
            datab.columns=['source','out_degree']
            datar = pd.concat([datar,datab])
        elems = elems.merge(datar, how='left', left_on='id', right_on='source')
        elems = elems.drop(columns = ['source'] )
        rels = rels.merge(datar, how='left', left_on='id', right_on='source')
        rels = rels.drop(columns = ['source_y'] )
    
        datar = rels.groupby(by=['target']).size()
        datar = datar.reset_index()
        datar.columns= ['target', 'in_degree']
        datab = rels[rels.is_bidirectional==True].target
        if len(datab) > 0:
            datab.reset_index()
            datab.columns=['target','in_degree']
            datar = pd.concat([datar,datab])
        elems = elems.merge(datar, how='left', left_on='id', right_on='target')
        elems = elems.drop(columns = ['target'] )
        rels = rels.merge(datar, how='left', left_on='id', right_on='target')
        rels = rels.drop(columns = ['target_y'] )
    
        # calculate aggregates    
        data = elems.groupby(by=['tag','layer','aspect']).agg({'in_degree': ['min', 'sum', 'count', 'max'], 'out_degree': ['min', 'sum', 'count', 'max'], 'id': 'count'})
        data = data.fillna(0)
        data = data.reset_index()
        data.columns = ['tag','layer','aspect', 'in_degree_min', 'in_degree_sum', 'in_degree_cnt', 'in_degree_max', 'out_degree_min', 'out_degree_sum', 'out_degree_cnt', 'out_degree_max', 'cnt']
        data['type'] = 'element'
        
        data2 = rels.groupby(by=['tag','relcls']).agg({'in_degree': ['min', 'sum', 'count', 'max'], 'out_degree': ['min', 'sum', 'count', 'max'], 'id': 'count'})
        data2 = data2.fillna(0)
        data2 = data2.reset_index()
        data2.columns = ['tag','relcls', 'in_degree_min', 'in_degree_sum', 'in_degree_cnt', 'in_degree_max', 'out_degree_min', 'out_degree_sum', 'out_degree_cnt', 'out_degree_max', 'cnt']
        data2['type'] = 'relationship'
        data2['layer'] = 'relationships'
        
        data = pd.concat([data, data2])
        return data
    
    def parse_view_concepts(model):
        views = model.views
        org=model.organizations
        views = views.merge(org, how='left', left_on='id', right_on='idRef')
        def mapping(x):
            if x==x:
                return '|'+str(x)
            else:
                return ''
        views['path'] = views[[x for x in list(views.columns) if 'level' in x ]].apply(lambda x: ''.join(x.map(mapping))[1:] , axis=1)
        view_concepts = []
        for index, view in views.iterrows():
            view_desc= {'view_name':view['path']+'|'+view['name'], 'view_id':view.id}
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
                label_obj = item['ar3_label']
                if isinstance(label_obj,list):
                    label_obj =label_obj[0]
                label_=label_obj['value']
            if 'ar3_viewRef' in item_keys:
                view_ref = item['ar3_viewRef']
                if isinstance(view_ref,list):
                    view_ref =view_ref[0]
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
    model = ArchimateUtils.load_model_from_repository(**model_options, **auth_options)    
    
    dataSummary = get_data(model)
    
    
    #%%
    # generic setup of the output
    playout = []
    TOOLS = "pan,wheel_zoom,box_zoom,reset,save"
    output_file("analysis__%s__%s.html" % (model_options['projectName'].replace('|','_'),model_options['projectOwner']), title='Analysis of model %s of %s' % (model_options['projectName'],model_options['projectOwner']))
    
    div1 = Div(text="""<H1>Analysis of model <i>"""+model.name+
               """</i></H1><p>In the following different metrics are applied to assess the model and to provide some insights on a technical level. 
               In a second step recommendations will be provided on how to improve the model. The analysis is structured by investigating the following aspects of the model:</p>
               <ul><li><a href="#elements">Elements</a></li>
               <li><a href="#relationships">Relationships</a></li>
               <li><a href="#connectivity">Connectivity</a></li>
               <li><a href="#views">Views</a></li>
               </ul>""",
    width=640, height=200)
    playout.append([widgetbox(div1)])
    
    ########################
    # analyszing elements
    ########################
    
    # histogram of layer and aspect
    dataAgg = dataSummary.groupby(by=['aspect','layer']).size() 
    dataAgg = dataAgg.reset_index()
    dataAgg.columns = ['aspect','layer', 'cnt']
    
    dataP = dataAgg.pivot(index='layer', columns='aspect', values='cnt')
    dataP = dataP.fillna(0)
    
    print('Elements')
    print('========')
    #%matplotlib inline  
    #import seaborn as sns
    #plt.figure(figsize=(6,3))
    #sns.heatmap(dataP,cmap="RdYlGn", center = 0)
    #plt.show()
    
    dataT= dataP.stack().rename("cnt").reset_index()
    
    div3 = Div(text="""<H2 id="elements">Elements</H2><p>The model contains """+str(len(model.nodes))+
               """ elements. The distribution over Archimate layers and aspects is depicted below.</p>""",
               width=640, height=50)
    playout.append([widgetbox(div3)])
    
    data = dataSummary[dataSummary.type=='element']
    
    bar1 = figure(toolbar_location='right', tools=TOOLS, title='Absolute frequency of elements',
                    plot_width=640, plot_height=400,x_range=list(data.tag.drop_duplicates()))
    bar1.vbar(x=list(data.tag), width=0.8, bottom=0, top=list(data.cnt))
    bar1.xaxis.major_label_orientation = pi/2
    playout.append([bar1])
    
    
    source = ColumnDataSource(dict(aspect=dataT.aspect, layer=dataT.layer, cnt=dataT.cnt))
    opts = dict(x='aspect', y='layer', line_color=None, source=source)
    
    mapper = LinearColorMapper(palette=list(reversed(PuBu[max(dataT.cnt)-min(dataT.cnt)+1])), low=dataP.values.min(), high=dataP.values.max()+1)
    hm1 = figure(toolbar_location='right', tools=TOOLS, title='Absolute frequency of elements per Archimate Layer and Aspect',
                   x_range=list(dataT.aspect.drop_duplicates()), y_range=list(dataT.layer.drop_duplicates()),
                    plot_width=640, plot_height=300)
    hm1color_bar = ColorBar(color_mapper=mapper, location=(0, 0))
    hm1.rect(
            x='aspect', y='layer', 
            fill_color={'field': 'cnt', 'transform': mapper}, line_color=None,
            source=source, width=1, height=1
        )
    hm1.add_layout(hm1color_bar, 'right')
    hm1.xaxis.major_label_orientation = pi/2
    
    playout.append([hm1])    
    
    ########################
    # analyszing relationships
    ########################
    data = model.nodes
    data = data[['id','type']]
    data = pd.concat([data,model.edges[['id','type']]])
    
    trans = model.edges.merge(data, how='left', left_on='source', right_on='id')
    #trans = data.merge(model.edges, how='left', left_on='id', right_on='source')
    trans = trans[['source','type_y','target','type_x']]
    trans.columns=['source','src_type','target','rel_type']
    trans = trans[np.logical_and(np.logical_not(trans.src_type.isnull()), trans.src_type==trans.src_type)]
        
    # associate the relevant elements
    data = trans.merge(data, how='left', left_on='target', right_on='id')
    data = data[['src_type','rel_type','type']]
    data.columns=['src_type','rel_type','trg_type']
    data = data[np.logical_and(np.logical_not(data.rel_type.isnull()), data.rel_type==data.rel_type)]
    data = data[np.logical_and(np.logical_not(data.trg_type.isnull()), data.trg_type==data.trg_type)]
    
    data.src_type = data.src_type.apply(lambda x: x['tag'])
    data.trg_type = data.trg_type.apply(lambda x: x['tag'])
    data.rel_type = data.rel_type.apply(lambda x: x['tag'])
    
    dataAgg = data.groupby(by=['src_type','trg_type','rel_type']).size() 
    dataAgg = dataAgg.reset_index()
    dataAgg = dataAgg[['src_type','trg_type','rel_type']]
    dataAgg2 = dataAgg.groupby(by=['src_type','trg_type']).apply(lambda x: list(x.rel_type))
    dataAgg2 = dataAgg2.reset_index()
    dataAgg2.columns = ['src_type','trg_type','list']
    dataAgg2['cnt'] = dataAgg2.list.apply(lambda x: len(x))
    
    dev = dataAgg2[dataAgg2.cnt>1]
    
    dataP = dataAgg2.pivot(index='src_type', columns='trg_type', values='cnt')
    dataP = dataP.fillna(0)
    dataT= dataP.stack().rename("cnt").reset_index()
    
    div4 = Div(text="""<H2 id="relationships">Relationships</H2><p>The model contains """+str(len(model.edges))+
               """ relationships. The number of relationship types connecting a source element to target element
               is depicted below.</p>""",
               width=640, height=70)
    playout.append([widgetbox(div4)])
    
    data = dataSummary[dataSummary.type=='relationship']
    
    bar2 = figure(toolbar_location='right', tools=TOOLS, title='Absolute frequency of relationships',
                    plot_width=640, plot_height=400,x_range=list(data.tag.drop_duplicates()))
    bar2.vbar(x=list(data.tag), width=0.5, bottom=0, top=list(data.cnt))
    bar2.xaxis.major_label_orientation = pi/2
    playout.append([bar2])
    
    source = ColumnDataSource(dict(src_type=dataT.src_type, trg_type=dataT.trg_type, cnt=dataT.cnt))
    opts = dict(x='src_type', y='trg_type', line_color=None, source=source)
    
    mapper = LinearColorMapper(palette=list(reversed(PuBu[max(dataT.cnt)-min(dataT.cnt)+1])), low=dataP.values.min(), high=dataP.values.max()+1)
    hm2 = figure(toolbar_location=None, tools='', title='Distinct count of relationship types connecting a source and target element type',
                   x_range=list(dataT.src_type.drop_duplicates()), y_range=list(dataT.trg_type.drop_duplicates()),
                    plot_width=640, plot_height=500)
    hm2color_bar = ColorBar(color_mapper=mapper, location=(0, 0))
    hm2.rect(
            x='src_type', y='trg_type', 
            fill_color={'field': 'cnt', 'transform': mapper}, line_color=None,
            source=source, width=1, height=1
        )
    hm2.xaxis.major_label_orientation = pi/2
    hm2.add_layout(hm2color_bar, 'right')
    
    playout.append([hm2])
    
    #import seaborn as sns
    #plt.figure()
    #sns.heatmap(dataP,cmap="RdYlGn", center = 0)
    #plt.show()
    
    if len(dev)>0:
        div5 = Div(text="""<p>The model contains """+str(len(dev))+
               """ source and target element types, which are not uniquely mapped with a specific relationshiptype,
               but are connected via several relationship types. The relationship types and the number or relationship types
               being involved are depicted below for each source and target element type combination.</p>""",
               width=640, height=70)
        playout.append([widgetbox(div5)])
        dataTable2 = dict(
            src_type=dev.src_type,
            trg_type=dev.trg_type,
            list = dev.list,
            cnt=dev.cnt
            )
        source2 = ColumnDataSource(dataTable2)
    
        columns2 = [
            TableColumn(field="src_type", title="Source Type"),
            TableColumn(field="trg_type", title="Target Type"),
            TableColumn(field="list", title="Relationship Types"),
            TableColumn(field="cnt", title="#Type"),
            ]
        data_table2 = DataTable(source=source2, columns=columns2, width=640, height=280)
        playout.append([widgetbox(data_table2)])
    else:
        div5 = Div(text="""<p>The model contains a unique mapping for connecting a source element to target element.
               That is there is no risk of inconsistencies of relationship usage or a vialotion of model patterns.</p>""",
               width=640, height=70)
        playout.append([widgetbox(div5)])
    
    ######################
    # Analyzing connectivity
    ######################
    # identify isolates
    gmodel= GraphUtils.toNXGraph(model)
    isolates = list(nx.isolates(gmodel))
    names = []
    types_=[]
    gnodes = model.nodes
    gnodes = gnodes.set_index('id')
    print('Connectivity')
    print('============')
    print('total of '+str(len(isolates))+' concepts without any relations')
    for n in isolates:
        if n in list(gnodes.index):
            print(gnodes.loc[n]['name']+' ('+gnodes.loc[n]['type']['tag']+')')
            names.append(gnodes.loc[n]['name'])
            types_.append(gnodes.loc[n]['type']['tag'])
    print()
    print()
    
    div2 = Div(text="""<H2 id="connectivity">Connectivity</H2><p>The way the concepts are related via relationships is depicted in the following two graphs. To understand the graphs
               it is necessary to understand in and out degree. In degree of a concept describes how many relationships having the concept as a target.
               Out degree of a concept is calculated by counting the relationships having the concept as a source.</p>
               <p>The first graph shows the histogram of the in and out degree. In this diagram the number of concepts having a certain in or out degree are depicted.
               In this graph it is not possible to see what the out degree of nodes that have an in degree of 3. This correlation of in and out
               degree is visualized in the second graph, where the color represents the number of concepts that have these particular in and out degrees.</p>
               <p>Interesting part os the second graph are concepts with high in or out degrees since they apparently are highly connected in the graph, which makes it worth 
               checking whether this makes sense from a modeling context. Examples for highly connected concepts are e.g. plateaus.</p>
               <p>Unconnected elements have an in and out degree of zero, thus the number of concepts is visible in the second graph at the coordinates zero and zero.</p>""",
              width=640, height=300)
    playout.append([widgetbox(div2)])
    
    #gmodel = gmodel.to_directed()
    in_degrees = gmodel.in_degree() # dictionary node:degree
    in_values = sorted(set(in_degrees))
    df_in_values = pd.DataFrame(in_values)
    df_in_values.columns = ['id','in_degree']
    df_hist_in = df_in_values.groupby(by='in_degree').size()
    
    out_degrees = gmodel.out_degree() # dictionary node:degree
    out_values = sorted(set(out_degrees))
    df_out_values = pd.DataFrame(out_values)
    df_out_values.columns = ['id','out_degree']
    df_hist_out = df_out_values.groupby(by='out_degree').size()
   
    df_degrees = df_out_values.merge(df_in_values, on='id', how='outer')
    df_degrees2 = df_degrees.groupby(by=['out_degree','in_degree']).size().rename('cnt')
    df_degrees2 = df_degrees2.reset_index()
    #df_degrees2.columns=['out_degree','in_degree','cnt']
    
    source = ColumnDataSource(df_degrees2)
    mapper = LinearColorMapper(palette=list(reversed(Plasma256)), low=0, high=df_degrees2.cnt.max()+1)
   
    p2 = figure(tools=TOOLS, title='Absolute frequency of elements with a specific in degree respectively out degree',
                plot_width=640, plot_height=300)
    p2.line(x=df_hist_in.index, y=df_hist_in, line_color='red',legend="in degree")
    p2.line(x=df_hist_out.index, y=df_hist_out, line_color='blue', legend="out degree")
    p2.xaxis.axis_label = 'frequency'
    p2.yaxis.axis_label = 'degree'
    
    p = figure(tools=TOOLS, title='Absolute frequency of elements with a specific in and outdegree',
               plot_width=640, plot_height=300)
    p.scatter(x='in_degree', y='out_degree', radius=0.3,
              color={'field': 'cnt', 'transform': mapper}, fill_alpha=0.6,
              line_color=None, source=source)
    pcolor_bar = ColorBar(color_mapper=mapper, location=(0, 0))
    p.add_layout(pcolor_bar, 'right')
    p.xaxis.axis_label = 'in degree'
    p.yaxis.axis_label = 'out degree'
    
    playout.append([p2])
    playout.append([p])

    
    if len(isolates)>0:
        div2 = Div(text="""<p>There are """+str(len(isolates))+
               """ elements, which are are not connected to any relationship.</p>""",
               width=640, height=30)
        playout.append([widgetbox(div2)])
        dataTable = dict(
            names=names,
            types=types_,
            )
        source = ColumnDataSource(dataTable)
    
        columns = [
            TableColumn(field="names", title="Name"),
            TableColumn(field="types", title="Type"),
            ]
        data_table1 = DataTable(source=source, columns=columns, width=640, height=280)
        playout.append([widgetbox(data_table1)])
    else:
        div2 = Div(text="""<p>There are no elements, which are are not connected to any relationship.</p>""",
               width=640, height=30)
        playout.append([widgetbox(div2)])
    
    ids_in_75 = df_in_values[df_in_values.in_degree>np.percentile(df_in_values.in_degree, 75)]
    names = []
    types_=[]
    degree=[]
    for index,row in ids_in_75.iterrows():
        names.append(gmodel.node[row.id]['name'])
        types_.append(gmodel.node[row.id]['type_tag'])
        degree.append(row.in_degree)
    div2 = Div(text="""<p>There are """+str(len(ids_in_75))+
               """ elements, which have an in degree above the 75 percentile of all in degrees, i.e. """+str(np.percentile(df_in_values.in_degree, 75))+""".</p>""",
               width=640, height=30)
    playout.append([widgetbox(div2)])
    dataTable = dict(
            names=names,
            types=types_,
            degree=degree,
            )
    source = ColumnDataSource(dataTable)
    
    columns = [
            TableColumn(field="names", title="Name"),
            TableColumn(field="types", title="Type"),
            TableColumn(field="degree", title="In Degree"),
            ]
    data_table1 = DataTable(source=source, columns=columns, width=640, height=280)
    playout.append([widgetbox(data_table1)])
    
    ids_out_75 = df_out_values[df_out_values.out_degree>np.percentile(df_out_values.out_degree, 75)]
    names = []
    types_=[]
    degree=[]
    for index,row in ids_out_75.iterrows():
        names.append(gmodel.node[row.id]['name'])
        types_.append(gmodel.node[row.id]['type_tag'])
        degree.append(row.out_degree)
    div2 = Div(text="""<p>There are """+str(len(ids_in_75))+
               """ elements, which have an out degree above the 75 percentile of all out degrees, i.e. """+str(np.percentile(df_in_values.in_degree, 75))+""".</p>""",
               width=640, height=30)
    playout.append([widgetbox(div2)])
    dataTable = dict(
            names=names,
            types=types_,
            degree=degree,
            )
    source = ColumnDataSource(dataTable)
    
    columns = [
            TableColumn(field="names", title="Name"),
            TableColumn(field="types", title="Type"),
            TableColumn(field="degree", title="Out Degree"),
            ]
    data_table1 = DataTable(source=source, columns=columns, width=640, height=280)
    playout.append([widgetbox(data_table1)])

    ########################
    # views
    ########################
    #playout=[]
    print('Views')
    print('============')
    print('total of '+str(len(model.views))+' views in the model')
    
    div2 = Div(text="""<H2 id="views">Views</H2><p>The model contains """+str(len(model.views))+""" views.</p><p> In the graph below 
               you can see the number of relationships, elements and references to other views contained in each view. Further, the 
               purely graphical elements in the view are represented (ar3_Container element). Graphical elements are notes and group concepts, which are only contained in the 
               view, but are not concepts in the model, i.e. they do not have a semantic meaning described in the ArchiMate standard. 
               Using these graphical elements can help to make a point for a discussion, but should not carry model semantics. The ar3_Label elements are 
               pointers to a view, thus a symbol representing a view is placed inside another view. This mechanism is often used to provide an
               overview page of the model.</p>""",
              width=640, height=180)
    playout.append([widgetbox(div2)])
    
    view_concepts = parse_view_concepts(model)
    views_agg = view_concepts.groupby(by=['view_name', 'type']).size().rename('cnt').reset_index()
       
    views_aggP = views_agg.pivot(index='view_name', columns='type', values='cnt')
    views_aggP = views_aggP.fillna(0)
    views_aggP = views_aggP.reset_index()
    columns = list(views_aggP.columns[1:])
    columns_new = ['view_name']
    ii=1
    for c in views_aggP.columns[1:]:
        columns_new.append('c'+str(ii))
        ii=ii+1
    views_aggP.columns = columns_new
    #views_aggT= views_aggP.stack().rename("cnt").reset_index()
    
    p = figure(y_range=list(views_aggP.view_name), plot_height=40+15*len(views_aggP), plot_width=640, 
               title="Distribution of view concepts per view",
               toolbar_location=None)
    
    p.hbar_stack(list(columns_new[1:]), y='view_name', height=0.9, color=Category20[max(3,len(columns))][0:len(columns)], 
                 source=ColumnDataSource(views_aggP), legend=["%s " % x for x in columns])
    
    p.y_range.range_padding = 0.1
    p.ygrid.grid_line_color = None
    p.legend.location = "top_left"
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    #p.legend.orientation = "horizontal"
    #p.legend.location=(300,0)
    
    new_legend = p.legend[0]
    #p.legend[0].plot = None
    p.add_layout(new_legend, 'right')
    
    playout.append([p])
    
    div25 = Div(text="""<p>The following figure show the absolute frequency of elements that occure n times in a view.
                If an element is not showing up in any view this may indicate that there might be a view missing.
                Further, the elements used in most views are apparently most important for the model.</p>""",
              width=640)
    playout.append([widgetbox(div25)])
    
    data = view_concepts[view_concepts.type == 'ar3_Element']
    #data = data[data.levels_ref.apply(lambda x: len(x))>0]
    data = data[data.ref_type == 'ar3_Element']
    data = data[['parent','levels_ref','ref','view_name','view_id','id']]
    
    # histogram of the number of views an element is used in
    h22 = data.groupby(by='ref').size().rename('cnt').reset_index()
    #h22['cnt'] = h22.cnt.apply(lambda x: str(x))
    hnodes = model.nodes[['id', 'label', 'type']]
    h23 = hnodes.merge(h22, left_on='id', right_on='ref')
    h23['typename'] = h23.type.apply(lambda x: x['typename'])
    
    h26=h23.groupby(by='cnt').size().rename('freq').reset_index()
    h26['cnt'] = h26.cnt.apply(lambda x: str(x))
    bar26 = figure(toolbar_location='right', tools=TOOLS, title='Absolute frequency of elements used in x views',
                    plot_width=640, plot_height=300,x_range=list(h26.cnt.drop_duplicates()))
    bar26.vbar(x=list(h26.cnt), width=0.5, bottom=0, top=list(h26.freq))
    playout.append([bar26])
    
    # detailed list of the 75% percentile of most occurring elements
    if len(h23)>0:
        h25 = h23[h23.cnt>np.percentile(h23.cnt, 75)]
        
        div25 = Div(text="""<p>The list below shows the 75 percentile of the elements used in more than """+str(np.percentile(h23.cnt, 75))+""". </p>""",
                  width=640)
        playout.append([widgetbox(div25)])
        dataTable = dict(
                label=h25.label,
                typename=h25.typename,
                cnt=h25.cnt,
                )
        source = ColumnDataSource(dataTable)
        
        columns = [
                TableColumn(field="label", title="Element Label"),
                TableColumn(field="typename", title="Type"),
                TableColumn(field="cnt", title="Count"),
                ]
        data_table25 = DataTable(source=source, columns=columns, width=640, height=280)
        playout.append([widgetbox(data_table25)])

    
        # detailed list of elements not occurring in any view
        h24 = h23[h23.ref.isnull()]
        
        if len(h24)==0:
            div24 = Div(text="""<p>There is no element which is not included in any view.</p>""",
                  width=640, height=20)
            playout.append([widgetbox(div24)])
        else:
            div24 = Div(text="""<p>There are """+str(len(h24))+""" 
                        element which are not included in any view. The respective elements are listed below.</p>""",
                  width=640, height=20)
            playout.append([widgetbox(div24)])
            dataTable = dict(
                label=h24.label,
                typename=h24.typename,
                cnt=h24.cnt,
                )
            source = ColumnDataSource(dataTable)
        
            columns = [
                TableColumn(field="label", title="Element Label"),
                TableColumn(field="typename", title="Type"),
                TableColumn(field="cnt", title="Count"),
                ]
            data_table24 = DataTable(source=source, columns=columns, width=640, height=280)
            playout.append([widgetbox(data_table24)])
        
    # check whether graphical elements nesting concepts are also related to some concepts and relations in the model
    
    div2 = Div(text="""<h3>Purely Graphical Elements</h3><p>As stated above purely graphical elements are notes and groups, which are
               only contained in the view and are not part of the model. They are used to highlight certain aspects of a view.</p>
               <p>The risk is that these elements imply a certain semantics, which is potentially not explicated in the model.
               This is in particular the case when elements are nested inside a grpahical element, implying that all elements nested 
               in the graphical have something in common. In the following graph, the aim is to identify the commonality of the elements
               nested in a graphical notation.</p></p>""",
              width=640, height=200)
    playout.append([widgetbox(div2)])    
    
    nodes = model.nodes
    
    data = view_concepts[np.logical_and(view_concepts.ref.isnull(), view_concepts.source.isnull())]
    #    data = data[data.levels_id.apply(lambda x: len(x))>0]
    
    if len(data)==0:
        div134 = Div(text="""<p>The provided model does not contain Purely Graphical Elements</p>""",
              width=640, height=50)
        playout.append([widgetbox(div134)])
    else:
        # check nesting of elements in graphical elements 
        data['ref_cnt'] = data.levels_ref.apply(lambda x: len(x))
        data['level_id_cnt'] = data.levels_id.apply(lambda x: len(x))
        
        data44 = data[data.apply(lambda x: x['ref_cnt']!=x['level_id_cnt'], axis=1)]
        data45 = []
        t = data44.apply(lambda x: [data45.append((x.name, nn)) for nn in x['levels_id']], axis=1)
        data45 = pd.DataFrame(data45, columns=['ind','id'])
        data45 = data45.merge(view_concepts, how='left', on='id')
        data45 = data45[data45.type!='ar3_Element']
        data45 = data45[['ind','id','label','type']]
        data45.columns = ['ind','graph_elem_id','graph_elem_label','graph_elem_type']
        data46 = data44.merge(data45, how='left', right_on='ind', left_index=True)
        data46 = data46[['ind','graph_elem_id','graph_elem_label','graph_elem_type', 'view_name', 'ref','ref_type']]
        data47 = data46.groupby(['graph_elem_id','graph_elem_label','graph_elem_type', 'view_name']).apply(lambda x: list(x.ref)).rename('cluster').reset_index()
        
        nxg = GraphUtils.toNXGraph(model)
        #nxg = nxg.to_directed()
        for (n,d) in nxg.nodes(data=True):
            del d["type_name"]
            del d["type_tag"]
            del d["type_aspect"]
            del d["type_layer"]
        for (e1,e2,d) in nxg.edges(data=True):
            del d["type_name"]
            del d["type_tag"]
            del d["type_aspect"]
            del d["type_shorthand"]
        
        if len(data47)>0:
            ii = 0
            data47['connected'] = data47.cluster.apply(lambda x: 'ok' if nx.is_weakly_connected(nxg.subgraph(x)) else 'not ok')
            #for cluster in list(data47.cluster):
            #    g=nxg.subgraph(cluster)
            #    plt.figure()
            #    nx.draw(g)
            #    plt.show()
            #    #nx.write_graphml(g, 'cluster_'+str(ii)+'.gml')
            #    ii = ii+1
            
            data47 = data47.groupby(by=['view_name','connected']).size().rename('cnt').reset_index()
            # reason for the incomplete nesting could be that elements are not related to further nested elements which is addressed in the following part
            data47P = data47.pivot(index='view_name', columns='connected', values='cnt')
            data47P = data47P.fillna(0)
            data47P = data47P.reset_index()
            columns = list(data47P.columns[1:])
            if len(columns)<2:
                if 'ok' in columns:
                    data47P['not ok'] = 0
                    data47P = data47P[['view_name','not ok','ok']]
                if 'not ok' in columns:
                    data47P['ok'] = 0
                    data47P = data47P[['view_name','not ok','ok']]
                columns = list(data47P.columns[1:])
            columns_new = ['view_name']
            columns_legend = []
            ii=1
            for c in data47P.columns[1:]:
                columns_new.append('c%s' % str(ii))
                columns_legend.append('%s'% c)
                ii=ii+1
            data47P.columns = columns_new
            
            
            p = figure(y_range=list(data47P.view_name), plot_height=40+15*len(data47P), plot_width=640, 
                       title="Distribution of nested relations in views also contained in model per view",
                       toolbar_location=None)
            #data47P2 = data47P[columns_new[1:]]
            p.hbar_stack(list(columns_new[1:]), y='view_name', height=0.9, color=['orange', 'green'], 
                         source=ColumnDataSource(data47P), legend=["%s " % x for x in columns_legend])
            
            p.y_range.range_padding = 0.1
            p.ygrid.grid_line_color = None
            p.legend.location = "top_left"
            p.axis.minor_tick_line_color = None
            p.outline_line_color = None
            new_legend = p.legend[0]
            #p.legend[0].plot = None
            p.add_layout(new_legend, 'right')
            
            playout.append([p])

    
    # check whether nested elements have that nesting also in the model
    #playout =[]
    data = view_concepts[view_concepts.type == 'ar3_Element']
    data = data[data.levels_ref.apply(lambda x: len(x))>0]
    data = data[data.ref_type == 'ar3_Element']
    data = data[['parent','levels_ref','ref','view_name','view_id','id']]
    
    if len(data)==0:
        div135 = Div(text="""<p>The provided model does not contain nested elements in views.</p>""",
              width=640, height=50)
        playout.append([widgetbox(div135)])
    else:
        rows=[]
        t= data.apply(lambda row: [rows.append({'ref':row['ref'], 'levels_ref':nn}) for nn in row['levels_ref']], axis=1)
        data1=pd.DataFrame(rows)
        data2 = data.merge(data1, how='left', on='ref')
        data2 = data2[['parent','levels_ref_y','ref','view_name','view_id','id']]
        data2.columns=['parent','levels_ref','ref','view_name','view_id','id']
        data2 = data2.drop_duplicates()
        
        data4 = data2.merge(model.edges, how='left', left_on='ref', right_on='source')
        data4 = data4[['levels_ref','ref','view_name','view_id','id_x','target']]
        data4.columns = ['levels_ref','ref','view_name','view_id','id','rel']
         
        data3 = data2.merge(model.edges, how='left', left_on='ref', right_on='target')
        data3 = data3[['levels_ref','ref','view_name','view_id','id_x','source']]
        data3.columns = ['levels_ref','ref','view_name','view_id','id','rel']
        data3 = pd.concat([data4,data3])
        data3 = data3.fillna('missing')
        
        data3['comparison'] = data3.apply(lambda x: x.rel == x.levels_ref, axis=1)
        data4 = data3[data3.comparison==True]
        
        # all nested concepts, which have also corresponding relationships in the model
        l = list(data4.id)
        
        div2 = Div(text="""<H3>Nested View Elements</H3><p>Views may contain nested elements, i.e. an element shape in a view which is included completely in another element shape. 
                   Since the graphical notation implies a sort of nesting relationship of some sort, this nesting relationship may not be included in the model itself.
                   Thus, in the following the nested elements are investigated and it is checked whether such a relationship exists and if so, whether the underlying relationships
                   are used consistently. I.e. whether for a mapping of business processes always the same relationship type has been used.</p>
                   <p>There are in total """+str(len(data))+""" nested elements of which """+str(len(l))+""" elements have a corresponding relationship in the model. 
                   Whether and in which view nesting relationships are missing is depicted int eh next figure. The type of existing relationships and the details about the 
                   nested concepts are displayed in subsequent figures.</p>
                   <p>Not ok nestings into graphical elements could also be caused by missing relations between nested elements included in the graphical elements, which are dicussed in the next section.</p>""",
                  width=640, height=250)
        playout.append([widgetbox(div2)])
        
    
    
        # determine the type, name of the source and the target elements as well as the rlationship type
        data5 = data2[data2.id.isin( l)]
        data6 = model.edges
        res_nested = pd.concat([data5.merge(data6, how='inner', left_on=['ref','levels_ref'], right_on=['source','target']),
                        data5.merge(data6, how='inner', left_on=['levels_ref','ref'], right_on=['source','target'])])
        #res_nested = []
        #t = [res_nested.append((n.ref, nn)) for index, n in data5.iterrows() 
        #            for nn in list(data6[np.logical_and(np.logical_or(data6.source==n.ref, data6.target==n.ref),
        #               np.logical_or(data6.source==n.levels_ref, data6.target==n.levels_ref))].id)]
        #res_nested = pd.DataFrame(res_nested, columns=['ref','rel_id'])
        res_nested['rel_type_tag'] = res_nested['type'].apply(lambda d: d['tag'])
        #res_nested = res_nested.merge(data, how='left', on='ref')
        res_nested=res_nested[['parent','ref','rel_type_tag','view_name','view_id']]
        res_nested= res_nested.merge(nodes, how='left', left_on='parent', right_on='id')
        res_nested=res_nested[['parent','ref','rel_type_tag','view_name','view_id','type','label']]
        res_nested.columns=['parent','ref','rel_type_tag','view_name','view_id','parent_type','parent_label']
        res_nested= res_nested.merge(nodes, how='left', left_on='ref', right_on='id')
        res_nested=res_nested[['parent','ref','rel_type_tag','view_name','view_id','parent_type','parent_label', 'type', 'label']]
        res_nested.columns=['parent','ref','rel_type_tag','view_name','view_id','parent_type','parent_label','ref_type','ref_label']
        res_nested['ref_type_tag'] = res_nested['ref_type'].apply(lambda d: d['tag'])
        res_nested['parent_type_tag'] = res_nested['parent_type'].apply(lambda d: d['tag'])
        
            
        # this includes transitive closure!
        data5 = data2[np.logical_not(data2.id.isin( l))]
        data6 = data5.groupby(by=['ref','parent', 'view_name','view_id']).size().rename('cnt').reset_index()
        res_missing = data6.merge(nodes, how='left', left_on='ref', right_on='id')
        res_missing['ref_type_tag'] = res_missing['type'].apply(lambda d: d['tag'])
        res_missing = res_missing[['parent','ref','view_name','view_id','ref_type_tag','label']]
        res_missing.columns = ['parent','ref','view_name','view_id','ref_type_tag','ref_label']
        res_missing = res_missing.merge(nodes, how='left', left_on='parent', right_on='id')
        res_missing['parent_type_tag'] = res_missing['type'].apply(lambda d: d['tag'])
        res_missing = res_missing[['parent','ref','view_name','view_id','ref_type_tag','ref_label','parent_type_tag','label']]
        res_missing.columns = ['parent','ref','view_name','view_id','ref_type_tag','ref_label','parent_type_tag','parent_label']
        
        # display information for nested relationships
        #
        # aggregate number of found nesting relationships potentially per view
        res = res_nested[['view_name']].copy()
        res['mapped']=True
        res2 = res_missing[['view_name']].copy()
        res2['mapped']=False
        res = pd.concat([res,res2])
        res_agg = res.groupby(by=['view_name','mapped']).size().rename('cnt').reset_index()
        
        res_aggP = res_agg.pivot(index='view_name', columns='mapped', values='cnt')
        res_aggP = res_aggP.fillna(0)
        res_aggP = res_aggP.reset_index()
        columns = list(res_aggP.columns[1:])
        columns_new = ['view_name']
        if len(columns)<2:
                if True in columns:
                    res_aggP[False] = 0
                    res_aggP = res_aggP[['view_name',False,True]]
                if False in columns:
                    res_aggP[True] = 0
                    res_aggP = res_aggP[['view_name',False,True]]
                columns = list(res_aggP.columns[1:])
        ii=1
        for c in res_aggP.columns[1:]:
            columns_new.append('c'+str(ii))
            ii=ii+1
        res_aggP.columns = columns_new
        columns=['missing','available']
        
        p = figure(y_range=list(res_aggP.view_name), plot_height=40+15*len(res_aggP), plot_width=640, 
                   title="Distribution of nested relations in views also contained in model per view",
                   toolbar_location=None)
        
        p.hbar_stack(list(columns_new[1:]), y='view_name', height=0.9, color=['orange', 'green'], 
                     source=ColumnDataSource(res_aggP), legend=["%s " % x for x in columns])
        
        p.y_range.range_padding = 0.1
        p.ygrid.grid_line_color = None
        p.legend.location = "top_left"
        p.axis.minor_tick_line_color = None
        p.outline_line_color = None
        new_legend = p.legend[0]
        #p.legend[0].plot = None
        p.add_layout(new_legend, 'right')
        
        playout.append([p])
        
        # display the type of relationships used for nesting the elements
        rel_type_agg = res_nested.groupby(by='rel_type_tag').size().rename('cnt').reset_index()
        bar4 = figure(toolbar_location='right', tools=TOOLS, title='Absolute frequency of relationship types',
                        plot_width=640, plot_height=400,x_range=list(rel_type_agg.rel_type_tag.drop_duplicates()))
        bar4.vbar(x=list(rel_type_agg.rel_type_tag), width=0.5, bottom=0, top=list(rel_type_agg.cnt))
        bar4.xaxis.major_label_orientation = pi/2
        playout.append([bar4])
        
        
        # show a list of nested elements and their relations as a data table
        dataTable = dict(
                ref_label=res_nested.ref_label,
                ref_type_tag=res_nested.ref_type_tag,
                parent_label=res_nested.parent_label,
                parent_type_tag=res_nested.parent_type_tag,
                rel_type_tag=res_nested.rel_type_tag,
                view_name=res_nested.view_name,
                )
        source = ColumnDataSource(dataTable)
        
        columns = [
                TableColumn(field="ref_label", title="Nested Element Label"),
                TableColumn(field="ref_type_tag", title="Nested Element Type"),
                TableColumn(field="parent_label", title="Parent Element Label"),
                TableColumn(field="parent_type_tag", title="Parent Element Type"),
                TableColumn(field="rel_type_tag", title="Relationship Type"),
                TableColumn(field="view_name", title="View Name"),
                ]
        data_table33 = DataTable(source=source, columns=columns, width=640, height=280)
        playout.append([widgetbox(data_table33)])
        
        
        # display information for missing relationships
        #
        div2 = Div(text="""<p>It may happen that certain nested elements in a view are not related in the model. In the following figures these unmapped elements are investigated.
                   An initial figure shows the distribution of unmapped element types per view, followd by a heatmap showing the absolute frequency of the combination of nested and parent element type.
                   Finally, the details of the unmapped elements are displayed in a list.</p>""",
                  width=640, height=80)
        playout.append([widgetbox(div2)])
        
        # aggregate number of found nesting relationships potentially per view by nested element type
        res_agg = res_missing.groupby(by=['view_name', 'ref_type_tag']).size().rename('cnt').reset_index()
        
        res_aggP = res_agg.pivot(index='view_name', columns='ref_type_tag', values='cnt')
        res_aggP = res_aggP.fillna(0)
        res_aggP = res_aggP.reset_index()
        columns = list(res_aggP.columns[1:])
        columns_new = ['view_name']
        ii=1
        for c in res_aggP.columns[1:]:
            columns_new.append('c'+str(ii))
            ii=ii+1
        res_aggP.columns = columns_new
        #views_aggT= views_aggP.stack().rename("cnt").reset_index()
        
        p = figure(y_range=list(res_aggP.view_name), plot_height=max(40+15*len(res_aggP),300), plot_width=640, 
                   title="Distribution of view concepts per view per concept type",
                   toolbar_location=None)
        
        p.hbar_stack(list(columns_new[1:]), y='view_name', height=0.9, color=Category20[max(3,len(columns))][0:len(columns)], 
                     source=ColumnDataSource(res_aggP), legend=["%s " % x for x in columns])
        
        p.y_range.range_padding = 0.1
        p.ygrid.grid_line_color = None
        p.legend.location = "top_left"
        p.axis.minor_tick_line_color = None
        p.outline_line_color = None
        #p.legend.orientation = "horizontal"
        #p.legend.location=(300,0)
        
        if len(p.legend)>0:
            new_legend = p.legend[0]
            #p.legend[0].plot = None
            p.add_layout(new_legend, 'right')
            
        playout.append([p])
        
        # heatmap of occurrences of nested and parent element type
        res_agg = res_missing.groupby(by=['parent_type_tag', 'ref_type_tag']).size().rename('cnt').reset_index()
        
        res_aggP = res_agg.pivot(index='parent_type_tag', columns='ref_type_tag', values='cnt')
        res_aggP = res_aggP.fillna(0)
        #res_aggP = res_aggP.reset_index()
        if len(res_aggP)>0:
            source = ColumnDataSource(dict(parent_type=res_agg.parent_type_tag, ref_type=res_agg.ref_type_tag, cnt=res_agg.cnt))
            opts = dict(x='parent_type', y='ref_type', line_color=None, source=source)
            
            mapper = LinearColorMapper(palette=list(reversed(linear_palette(Plasma256, max(res_agg.cnt)+1))), low=0, high=res_aggP.values.max()+1)
            hm33 = figure(toolbar_location='right', tools=TOOLS, title='occurrences of nested and parent element type',
                           x_range=list(res_agg.ref_type_tag.drop_duplicates()), y_range=list(res_agg.parent_type_tag.drop_duplicates()),
                            plot_width=640, plot_height=300)
            hm33color_bar = ColorBar(color_mapper=mapper, location=(0, 0))
            hm33.rect(
                    x='ref_type', y='parent_type', 
                    fill_color={'field': 'cnt', 'transform': mapper}, line_color=None,
                    source=source, width=1, height=1
                )
            hm33.add_layout(hm33color_bar, 'right')
            hm33.xaxis.major_label_orientation = pi/2
            
            playout.append([hm33])
            
        
        # show a list of nested elements which are missing a nesting relation as a data table
        dataTable = dict(
                ref_label=res_missing.ref_label,
                ref_type_tag=res_missing.ref_type_tag,
                parent_label=res_missing.parent_label,
                parent_type_tag=res_missing.parent_type_tag,
                view_name=res_missing.view_name,
                )
        source = ColumnDataSource(dataTable)
        
        columns = [
                TableColumn(field="ref_label", title="Nested Element Label"),
                TableColumn(field="ref_type_tag", title="Nested Element Type"),
                TableColumn(field="parent_label", title="Parent Element Label"),
                TableColumn(field="parent_type_tag", title="Parent Element Type"),
                TableColumn(field="view_name", title="View Name"),
                ]
        data_table34 = DataTable(source=source, columns=columns, width=640, height=280)
        playout.append([widgetbox(data_table34)])
        
        
    ###########################
    # create the graph
    ##########################
    
    # make a grid
    #grid = gridplot(layout)
    grid = layout(playout, sizing_mode='scale_width')
    show(grid)
    
#%%
#if __name__ == '__main__':    

    #%%
#model_options = {
#                'projectName': 'Archisurance', 
#                'projectOwner': 'dev', 
#                'branchName': 'MASTER', 
#                'userid': 'test_user'
#            }
#
# analyze_model(model_options)