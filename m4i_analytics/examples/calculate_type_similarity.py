#%%
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.graphs.languages.archimate.metamodel.Concepts import ElementType, RelationshipType, Aspect,Layer
from m4i_analytics.graphs.GraphUtils import GraphUtils
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

from sqlalchemy import create_engine

#%%
def get_data(model_options):
    model = ArchimateUtils.load_model_from_repository(**model_options)
 
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
#%%
def get_management_data(model_options):
    project_owner = 'dev'
    project_name = 'Engineering company demo'
    model_options = {
                'projectName': project_name, 
                'projectOwner': 'dev', 
                'branchName': 'MASTER', 
                'userid': 'test_user'
            }

    model = ArchimateUtils.load_model_from_repository(**model_options)
 
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
    rels['relcls'] = rels.type.apply(lambda x:x['tag'])
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
#%% 
if __name__ == '__main__':    
    
    project_owner = 'dev'
    project_name = 'Engineering company demo'
    provenance = PlatformApi.model_provenance(
        'dev__Engineering_company_demo'
    )
    data_provenance = []
    data_model = pd.DataFrame()
    for p in provenance:
        if p.operation in [OperationEnum.COMMIT.value, OperationEnum.BRANCH_CLONE.value, OperationEnum.BRANCH_MERGE.value, OperationEnum.MERGE.value] :
            print('Run by: {0}\nBranch name: {1}\nOperation type: {2}\nComment: {3}\nTimestamp: {4}\n'.format(p.start_user, p.branch, p.operation, p.comment, p.start_date))
            model_options = {
                'projectName': project_name, 
                'projectOwner': project_owner, 
                'branchName': p.branch, 
                'userid': 'test_user',
                'version': p.start_date
            }
            # get the data
            data_new = get_data(model_options)
            data_new['branch'] = p.branch
            data_new['ts'] = p.start_date
            data_new['committer'] = p.start_user
            tu = way_of_working(model_options)
            data_new['way_of_working_h'] = tu[0]
            data_new['way_of_working_h2'] = tu[1]
            data_new['assessment'] = tu[2]
            
            data_model = pd.concat([data_model,data_new])
            
            # get the changes to the prvious version
            #model_query = PlatformApi.query_model('dev__Engineering_company_demo','300903ba-2f24-45a4-81cb-40c2c3bc235c'   )
            #dif_result = model_query.difResult
            #state = dif_result.state
            #add_left = dif_result.addListLeft
            #delete_left = dif_result.deleteListLeft
            #add_right = dif_result.addListRight
            #delete_right = dif_result.deleteListRight
            
            # assign provenance data
            data_provenance.append({'committer':p.start_user, 'branch': p.branch, 'operation': p.operation, 'ts': p.start_date, 'comment': p.comment, 'derived_from_left': p.derived_from_left, 'derived_from_right': p.derived_from_right})
#%%
    DBUtils.insert_dataset(data_model, 'dev__Engineering_company_demo_data2', if_exists=InsertBehavior.REPLACE)
    DBUtils.insert_dataset(data_provenance, 'dev__Engineering_company_demo_metadata2', if_exists=InsertBehavior.REPLACE)
    
    portal_project = {
        'taskid': 'dev__Engineering_company_demo_data',
        'projectid': 'dev__Engineering_company_demo_data',
        'run_by': 'dev',
        'owner_username': 'dev',
        'owner_email': 'office@aureliusenterprise.com',
        'owner_firstname': 'Andreas',
        'owner_lastname': 'Wombacher'
    }
    
    PortalApi.create_project(**portal_project)
    
    portal_project = {
        'taskid': 'dev__Engineering_company_demo_metadata',
        'projectid': 'dev__Engineering_company_demo_metadata',
        'run_by': 'dev',
        'owner_username': 'dev',
        'owner_email': 'office@aureliusenterprise.com',
        'owner_firstname': 'Andreas',
        'owner_lastname': 'Wombacher'
    }
    
    PortalApi.create_project(**portal_project)
    
    portal_dashboard = {
        'taskid': 'dev__Engineering_company_demo_data',
        'projectid': 'dev__Engineering_company_demo_data',
        'run_by': 'dev',
        'tablename': 'dev__Engineering_company_demo_data'
    }
    
    PortalApi.create_table_dashboard(**portal_dashboard)

    portal_dashboard = {
        'taskid': 'dev__Engineering_company_demo_metadata',
        'projectid': 'dev__Engineering_company_demo_metadata',
        'run_by': 'dev',
        'tablename': 'dev__Engineering_company_demo_metadata'
    }
    
    PortalApi.create_table_dashboard(**portal_dashboard)
    
    '''
    filteredModel = GraphUtils.groupByNodeType(model)

    nodesEntropy = sum([-(t['count']/len(ElementType)*log(t['count']/len(ElementType))) for t in filteredModel.nodes.to_dict(orient='records')])
    
    def edgeP(e):
        return e['count']/sum(filteredModel.edges['count'])/(pow(len(ElementType),2)*len(RelationshipType))
    
    def maxP():
        return 1/(pow(len(ElementType),2)*len(RelationshipType))
    
    edgesEntropy = sum([-(edgeP(e)*log(edgeP(e))) for e in filteredModel.edges.to_dict(orient='records')])
    maxEntropy = -(maxP()*log(maxP())*len(RelationshipType))
            
    print(nodesEntropy) 
    print(edgesEntropy)
    print(maxEntropy)
    print(edgesEntropy/maxEntropy*100)
    '''
#%%
#%% 
# load data from database
#%%

    def getConnection(db):
        engine = create_engine('mysql+mysqlconnector://lib_user:biJ!71ax@127.0.0.1/'+db, echo=False)
        return engine
    
    #%%
    engine = getConnection('m4i')
    data_model.to_sql(name='dev__Engineering_company_demo_data2', con = engine, if_exists = 'replace')
    df = pd.DataFrame(data_provenance)
    df.to_sql(name='dev__Engineering_company_demo_metadata2', con = engine, if_exists = 'replace')
    
    #%%
    #%%
    # calculate heterogenity
    
    model_options = {
                    'projectName': 'AgriCOmp', 
                    'projectOwner': 'dev', 
                    'branchName': 'MASTER', 
                    'userid': 'test_user'
                }
    
    #%%
    def way_of_working(model_options):
        model = ArchimateUtils.load_model_from_repository(**model_options)    
        ## heterogenity metric
        # select all nodes
        nodes = model.nodes
        
        # select and associate related Relationships
        rel = model.edges
        trans = nodes.merge(rel, how='inner', left_on='id', right_on='source')
        trans = trans[['source','type_x','target','type_y']]
        trans.columns=['source','src_type','target','rel_type']
        
        # associate the relevant elements
        data = trans.merge(model.nodes, how='left', left_on='target', right_on='id')
        data = data[['src_type','rel_type','type']]
        data.columns=['src_type','rel_type','trg_type']
        
        data = data.apply(lambda x: x.apply(lambda y: y['tag']))
        
        dataAgg = data.groupby(by=['src_type','rel_type','trg_type']).size()
        dataAgg = dataAgg.reset_index()
        dataAgg.columns = ['src_type','rel_type','trg_type', 'cnt']
        
        #elem_types = [elem.name for elem_name, elem in ElementType.__members__.items()]
        #rel_types = [rel.name for rel_name, rel in RelationshipType.__members__.items()]
        n = len(ElementType.getAll())*len(ElementType.getAll())*len(RelationshipType.getAll())
        
        h = 0
        for index,row in dataAgg.iterrows():
            s = row.src_type
            su = dataAgg[dataAgg.src_type==s].agg({'cnt': np.sum})
            p = row.cnt / su / n * len(ElementType.getAll())
            h = h - p*log(p)
            
        #print('max entropy: '+str(-n*(1/n)*log(1/n)))
        #print('entropy: '+str(h))
        
        # the higher the entropy the more heterogeneous the usage of relations is
        #    -> more different relations are used could be because of a bad model or 
        #       extending the model to cover more of the context
        # the lower the entropy the less different relation types are used
        #    -> less different relation types means that the model is using fewer relation types 
        #       means a bad model or focus on a particular layer of the model
        # metric is independent of the number of concepts
        
        ## layer and aspect metric
        # select all nodes
        nodes = model.nodes
        
        data = pd.DataFrame.from_records(nodes.type.apply(lambda x: {'tag': x['tag'], 
                                                'aspect': x['aspect'], 'layer': x['layer'] }))
        dataAgg = data.groupby(by=['aspect','layer']).size() / len(data) / (len(Aspect.getAll())*len(Layer.getAll()))
        #scipy.stats.entropy(dataAgg)
        h2 = dataAgg.apply(lambda x: (-1)*x*log(x)).sum()
        #print('entropy part 2: '+str(h2))
        
        # assessment
        str_ = 'hard to make an assessment'
        if h.cnt<=0.125:
            if h2<=0.1:
                str_='looks like a basic model'
            else:
                str_='Are there some relations missing or can relation types be distinguished?'
        else:
            if h2<=0.1:
                str_='Are all model patterns applied?'
            else:
                str_='healthy model growth'
        return (h.cnt,h2, str_)
    
    #%%
    def way_of_working_dynamics(h_past,h2_past,h_now,h2_now):
       v_x=h_new-v_past
       v_y = h2_new-h2_past
       res= 'no clear direction observed'
       l = sqrt(v_x*v_x+v_y*v_y)
       if l>0.01:
           res2 = ''
           if l>0.1:
               res2 = 'high '
           if v_x>0 and c_y>0:
               res = res2+'extend model accross multiple layers'
           if v_x>0 and c_y<0:
               res = res2+'risk of model patterns are not applied'
           if v_x<0 and c_y>0:
               res = res2+'harmonization of model'
           if v_x<0 and c_y<0:
               res = res2+'reduction of model'
       return res
    #%%
    model_options = {
                    'projectName': 'Archisurance', 
                    'projectOwner': 'dev', 
                    'branchName': 'MASTER', 
                    'userid': 'test_user'
                }
    data_model = way_of_working(model_options)
    model = ArchimateUtils.load_model_from_repository(**model_options)    
        
    #%%
    # investigate the data_model for the way of working
    #
    # get an overview of the different versions
    sum_ = data_model[['branch','ts', 'committer','way_of_working_h','way_of_working_h2', 'assessment' ]]
    sum_ = sum_.groupby(by=['branch','ts', 'committer','way_of_working_h','way_of_working_h2', 'assessment']).size()
    sum_ = sum_.reset_index()
    sum_.columns=['branch','ts', 'committer','way_of_working_h','way_of_working_h2','assessment','cnt']
    sum_ = sum_.sort_values(by='ts')
    sum_ = sum_.reset_index()
    sum_= sum_.drop('index', axis=1)
    sum_ = sum_.reset_index()
    ann_ = sum_.groupby(by=['way_of_working_h','way_of_working_h2']).apply(lambda x: list(x.index))
    ann_ = ann_.reset_index()
    ann_.columns=['way_of_working_h','way_of_working_h2','ann']
    
    ii = 1
    plt.figure()
    for index,row in sum_.iterrows():
        plt.scatter(row.way_of_working_h, row.way_of_working_h2, label=str(ii), alpha=0.3)
        ii = ii+1
    plt.scatter(data_archisurance[0],data_archisurance[1], alpha=0.3, label='archisurance')
    ii = 1
    for index,row in ann_.iterrows():
        plt.annotate(str(row.ann), (row.way_of_working_h, row.way_of_working_h2))
        ii = ii +1
    plt.annotate('archisurance', data_archisurance)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.show()
    
    #%%
    # histogram of layer and aspect
    model = ArchimateUtils.load_model_from_repository(**model_options)    
    
    nodes = model.nodes
    data = pd.DataFrame.from_records(nodes.type.apply(lambda x: {'tag': x['tag'], 
                                                'aspect': x['aspect'], 'layer': x['layer'] }))
    dataAgg = data.groupby(by=['aspect','layer']).size() 
    dataAgg = dataAgg.reset_index()
    dataAgg.columns = ['aspect','layer', 'cnt']
    
    dataP = dataAgg.pivot(index='layer', columns='aspect', values='cnt')
    dataP = dataP.fillna(0)
    
    import seaborn as sns
    sns.heatmap(dataP,cmap="RdYlGn", center = 0)
    
    #%%
    
    data = model.nodes
    
    trans = data.merge(model.edges, how='left', left_on='id', right_on='source')
    trans = trans[['source','type_x','target','type_y']]
    trans.columns=['source','src_type','target','rel_type']
    trans = trans[np.logical_not(trans.rel_type.isnull())]
        
    # associate the relevant elements
    data = trans.merge(model.nodes, how='left', left_on='target', right_on='id')
    data = data[['src_type','rel_type','type']]
    data.columns=['src_type','rel_type','trg_type']
    
    data.src_type = data.src_type.apply(lambda x: x['tag'])
    data.trg_type = data.trg_type.apply(lambda x: x['tag']+'_')
    data.rel_type = data.rel_type.apply(lambda x: x['tag'])
    
    data2 = data[['src_type','rel_type']]
    data2.columns=['src','trg']
    data3 = data[['rel_type','trg_type']]
    data3.columns=['src','trg']
    data = pd.concat([data2,data3])
    
    DBUtils.insert_dataset(data, 'metrics_example_layer_aspect', if_exists=InsertBehavior.REPLACE)
        
    portal_project = {
            'taskid': 'storing_and_publishing_a_dataset',
            'projectid': 'dev__metrics_example_layer_aspect',
            'run_by': 'dev',
            'owner_username': 'thijsfranck',
            'owner_email': 'thijs.franck@aureliusenterprise.com',
            'owner_firstname': 'Thijs',
            'owner_lastname': 'Franck'
        }
        
    PortalApi.create_project(**portal_project)
        
    portal_dashboard = {
            'taskid': 'storing_and_publishing_a_dataset',
            'projectid': 'dev__metrics_example_layer_aspect',
            'run_by': 'dev',
            'tablename': 'metrics_example_layer_aspect'
        }
        
    PortalApi.create_table_dashboard(**portal_dashboard)
    #%%
    data = model.nodes
    
    trans = data.merge(model.edges, how='left', left_on='id', right_on='source')
    trans = trans[['source','type_x','target','type_y']]
    trans.columns=['source','src_type','target','rel_type']
    trans = trans[np.logical_not(trans.rel_type.isnull())]
        
    # associate the relevant elements
    data = trans.merge(model.nodes, how='left', left_on='target', right_on='id')
    data = data[['src_type','rel_type','type']]
    data.columns=['src_type','rel_type','trg_type']
    
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
    
    dataP = dataAgg.pivot(index='src_type', columns='trg_type', values='cnt')
    dataP = dataP.fillna(0)
    
    import seaborn as sns
    plt.figure()
    sns.heatmap(dataP,cmap="RdYlGn", center = 0)
    plt.show()
