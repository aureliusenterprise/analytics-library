#%%
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.graphs.languages.archimate.metamodel.Concepts import ElementType, RelationshipType, Aspect,Layer
from m4i_analytics.graphs.GraphUtils import GraphUtils
from m4i_analytics.graphs.languages.archimate.model.ArchimateModel import ArchimateModel, ViewAttribute
from m4i_analytics.graphs.model.Graph import NodeAttribute, EdgeAttribute
from m4i_analytics.graphs.visualisations.GraphPlotter import GraphPlotter 

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
# Analyze model structures of AgriComp

    model_options = {
                    'projectName': 'AgriCOmp', 
                    'projectOwner': 'dev', 
                    'branchName': 'MASTER', 
                    'userid': 'test_user'
                }
    model = ArchimateUtils.load_model_from_repository(**model_options)    
    
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
    elems.type = elems.type.apply(lambda x: x.tag)
    g0 = derive_model_graph(model)
    
    cluster = []
    
    jj = 0
    for rel_type in rel_types:
        print(rel_type)
        m2 = slice_model(model, [rel_type]) 
        #g2= GraphUtils.toNXGraph(m2)
        g2 = derive_model_graph(m2)
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
    nx.write_graphml(g0,'g.xml')
    
    #%%
    # plot cluster 15
    # specialization and 5 elements, but no tree
    g2 = derive_model_graph(model)
    g15 = g2.subgraph(cluster.elems[15])
    g15 = g15.reverse()
    g15.in_degree()
    g15.out_degree()
    nx.is_arborescence(g15)
    
    #%%
    # plot cluster 0
    # specialization and 5 elements, but no tree
    g2 = derive_model_graph(model)
    g15 = g2.subgraph(cluster.elems[0])
    #g15 = g15.reverse()
    g15.in_degree()
    g15.out_degree()
    nx.is_arborescence(g15)
    
    #%%
    # plot cluster 4
    # specialization and 5 elements, but no tree
    g2 = derive_model_graph(model)
    g15 = g2.subgraph(cluster.elems[4])
    
    g15=nx.DiGraph( [ (u,v,d) for u,v,d in g15.edges(data=True) if d['type']==RelationshipType.ACCESS.tag] )
    #g15 = g15.reverse()
    g15.in_degree()
    g15.out_degree()
    nx.is_arborescence(g15)
    
    #GraphPlotter.visualize(g15)
    
    plt.figure()
    plt.plot()
    
    graph_pos5 = nx.spring_layout(g15, scale=100, k=2)
    #groups = set(nx.get_node_attributes(g15,'type').values())
    #mapping = dict(zip(sorted(groups), list(range(0,len(groups)))))
    #nodes = g15.nodes(data=True)
    #colors = [mapping[g15.node[n]['type']] for n in nodes]
    
    #groups2 = set(nx.get_edge_attributes(g15,'type').values())
    #mapping2 = dict(zip(sorted(groups2), list(range(0,len(groups2)))))
    #edges = g15.edges()
    #colors2 = [mapping2[n['type']] for n in edges]
    #nc = nx.draw_networkx_nodes(g15, graph_pos5, node_shape='o', node_color=colors, alpha=0.3)
        
    nc = nx.draw_networkx_nodes(g15, graph_pos5, node_shape='o', alpha=0.3)
    
    #edges,colors2 = zip(*nx.get_edge_attributes(g15,'type').items())
    #colors2 = [mapping2[n] for n in colors2]
    #nx.draw_networkx_edges(g15, graph_pos5, edge_color=colors2, arrows=True)
    
    #nx.draw(g15,edgelist=edges,edge_color=colors,width=10)
    nx.draw_networkx_edges(g15, graph_pos5, arrows=True)
    plt.axis('off')
    plt.show()
    
    
    #%%
    # plot cluster 7
    
    g2 = derive_model_graph(model)
    g15 = g2.subgraph(cluster.elems[2])
    
    graph_pos5 = nx.spring_layout(g15, scale=100, k=2)
    #groups = set(nx.get_node_attributes(g15,'type').values())
    #mapping = dict(zip(sorted(groups), list(range(0,len(groups)))))
    #nodes = g15.nodes(data=True)
    #colors = [mapping[g15.node[n]['type']] for n in nodes]
    
    rel_type = cluster.relation[2]
    g15=nx.DiGraph( [ (u,v,d) for u,v,d in g15.edges(data=True) if d['type']==rel_type ])
    #g15 = g15.reverse()
    g15.in_degree()
    g15.out_degree()
    nx.is_arborescence(g15)
    
    #GraphPlotter.visualize(g15)
    
    plt.figure()
    plt.plot()
    
    
    groups2 = set(nx.get_edge_attributes(g15,'type').values())
    #mapping2 = dict(zip(sorted(groups2), list(range(0,len(groups2)))))
    #edges = g15.edges()
    #colors2 = [mapping2[n['type']] for n in edges]
    #nc = nx.draw_networkx_nodes(g15, graph_pos5, node_shape='o', node_color=colors, alpha=0.3)
        
    nc = nx.draw_networkx_nodes(g15, graph_pos5, node_shape='o', alpha=0.3)
    
    #edges,colors2 = zip(*nx.get_edge_attributes(g15,'type').items())
    #colors2 = [mapping2[n] for n in colors2]
    #nx.draw_networkx_edges(g15, graph_pos5, edge_color=colors2, arrows=True)
    
    #nx.draw(g15,edgelist=edges,edge_color=colors,width=10)
    nx.draw_networkx_edges(g15, graph_pos5, arrows=True)
    plt.axis('off')
    plt.show()
    
    
    #%%
    # classify clusters of elements
    
    
    #%%
    # represent connected components as nodes with a color for the relationship type
    g5 = nx.DiGraph()
    #nodes = []
    for rel_type in rel_types:
        print(rel_type)
        node4 = elems[['type',rel_type]].groupby(by=['type',rel_type]).size()
        node4 = node4.reset_index()
        node4.columns = ['type', rel_type, 'cnt']
        node4 = node4[node4[rel_type] > 0]
        #node4 = node4.groupby(by='ar3_Triggering').apply(lambda x: ','.join("{'type': '"+x.type+"', 'cnt': "+str(x.cnt)+"}"))
        node4 = node4[[rel_type,'type']].groupby(by=rel_type).apply(lambda x: list(x.type))
        node4 = node4.reset_index()
        node4.columns = [rel_type, 'label']
        print(node4)
        print("--"+rel_type)
        for row in node4.iterrows():
            #nodes.append({'id': rel_type+str(row[1][rel_type]), 'label':str(row[1].label)})
            id_ = rel_type+str(row[1][rel_type])
            g5.add_node(id_)
            g5.nodes[id_]["label"] = str(row[1].label)
            g5.nodes[id_]["type"] = str(rel_type)
    
    #relas = []
    for rel_type in rel_types:
        for rel_type2 in rel_types:
            if rel_type != rel_type2:
                data = elems[[rel_type,rel_type2]]
                data = data[np.logical_and(data[rel_type]>0, data[rel_type2]>0)]
                if len(data)>0: 
                    data = data.drop_duplicates()
                    for row in data.iterrows():
                        relas.append({'src': rel_type+str(row[1][rel_type]), 'trg':  rel_type2+str(row[1][rel_type2])})
                        src = rel_type+str(row[1][rel_type])
                        trg = rel_type2+str(row[1][rel_type2])
                        g5.add_edge(src,trg)
                        
    #%%
    
    plt.figure()
    plt.plot()
    
    graph_pos5 = nx.spring_layout(g5, scale=100, k=2)
    #graph_pos = nx.fruchterman_reingold_layout(g, scale=100, k=0.3)
    #graph_pos = nx.fruchterman_reingold_layout(g2, scale=100)
    #graph_pos2 = principalDf.apply(lambda x: x['pc1'], axis=1)
    #graph_pos2 = {}
    #for index,row in principalDf.iterrows():
    #    graph_pos2[row['id']] = [row['pc1'], row['pc2']]
    
    #graph_pos2 = principalDf.apply(lambda x: dict([('Key',x['id']), ('Value',[x['pc1'], x['pc2']])]), axis=1)
    groups = set(nx.get_node_attributes(g5,'type').values())
    mapping = dict(zip(sorted(groups),count()))
    nodes = g5.nodes()
    colors = [mapping[g5.node[n]['type']] for n in nodes]
        
    nc = nx.draw_networkx_nodes(g5, graph_pos5, node_shape='o', node_color=colors, alpha=0.3)
    nx.draw_networkx_edges(g5, graph_pos5, arrows=True)
    
    plt.axis('off')
    # show graph
    plt.show()
    
    
    #%%
    # PCA
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    
    #selected_rel = 'ar3_Specialization' 
    selected_rel = 'ar3_Triggering' 
    #selected_rel = 'ar3_Composition' 
    
    # features = ['sepal length', 'sepal width', 'petal length', 'petal width']
    # Separating out the features
    x = elems[elems.columns[3:12]]
    
    # Separating out the target
    # y = df.loc[:,['target']].values
    # Standardizing the features
    x = StandardScaler().fit_transform(x)
    
    pca = PCA(n_components=2, svd_solver='full', whiten=True)
    principalComponents = pca.fit_transform(x)
    principalDf = pd.DataFrame(data = principalComponents
                 , columns = ['pc1', 'pc2'])
    
    principalDf['name'] = elems.name
    principalDf['type'] = elems.type
    principalDf['cluster'] = elems[selected_rel]
    
    #principalDf = principalDf.reset_index()
    #principalDf['index'] = principalDf['index']+1
    #t = principalDf.iloc[0,0:]
    #t['index'] = 0
    #principalDf = principalDf.append(t)
    #principalDf = principalDf.sort_values(by='type')
    
    #principalDf.plot.scatter(x='pc1', y='pc2', data=principalDf, c='type', s=100)
    #ax = plt.gca()
    #ax.grid()
    
    #threedee = plt.figure()
    #threedee.scatter(principalDf['pc1'], principalDf['pc2'])
    #threedee.set_xlabel('pc1')
    #threedee.set_ylabel('pc2')
    #plt.show()
    
    #%%
    import seaborn as sns
    #sns.lmplot('pc1', 'pc2', data=principalDf, hue='type', palette="Set2", fit_reg=False)
    
    # Unique category labels: 'D', 'F', 'G', ...
    color_labels = list(principalDf['type'].unique())
    markers = [".","o","v","<",">","^","+","x","|","-"]
    principalDf['marker'] = principalDf['cluster'].apply(lambda x: markers[x])
    
    # List of RGB triplets
    rgb_values = sns.color_palette("Set2", len(color_labels))
    
    # Map label to RGB
    color_map = dict(zip(color_labels, rgb_values))
    
    # Finally use the mapped values
    cluster_lables = list(principalDf['cluster'].unique())
    
    for ii in list(principalDf['cluster']):
        data = principalDf[principalDf['cluster'] == ii]
        plt.scatter(data['pc1'], data['pc2'], c=data['type'].map(color_map), marker=markers[ii], alpha=0.2)
    
    plt.show()
    
    #%%
    
    principalDf['type_color'] = pd.Categorical(principalDf['type'])
    principalDf['type_color'] = principalDf['type_color'].cat.codes
    plt.scatter(principalDf['pc1'], principalDf['pc2'], c=principalDf['type_color'], alpha=0.2)
    plt.show()
    
    #%%
    g2 = derive_model_graph(model)
    
    #%%
    #from bokeh.io import show, output_file
    import bokeh.plotting as bkh
    from bokeh.models.graphs import from_networkx
    from bokeh.models import HoverTool
    from bokeh.models import ColumnDataSource
    
    #%%
    # bokeh visualization
    #nodes_source = ColumnDataSource(dict(x=nodes_xs, y=nodes_ys,
    #                                     name=nodes))
    hover = HoverTool(tooltips=[('type', '@type')])
    TOOLS=["pan","wheel_zoom","box_zoom","reset","box_select","lasso_select", hover]
    
    
    fig = bkh.figure(title="Networkx Integration Demonstration", x_range=(-1.1,1.1), y_range=(-1.1,1.1),
                  tools=TOOLS, toolbar_location='right')
    
    graph = from_networkx(g2, nx.spring_layout, center=(0,0))
    graph.document
    fig.renderers.append(graph)
    
    bkh.output_file("networkx_graph3.html")
    bkh.show(fig)
    
    #%%
    
    selected_rel = 'ar3_Specialization' 
    #selected_rel = 'ar3_Triggering' 
    #selected_rel = 'ar3_Composition' 
    
    # features = ['sepal length', 'sepal width', 'petal length', 'petal width']
    # Separating out the features
    x = elems[elems.columns[3:12]]
    
    # Separating out the target
    # y = df.loc[:,['target']].values
    # Standardizing the features
    x = StandardScaler().fit_transform(x)
    
    pca = PCA(n_components=2, svd_solver='full', whiten=True)
    principalComponents = pca.fit_transform(x)
    principalDf = pd.DataFrame(data = principalComponents
                 , columns = ['pc1', 'pc2'])
    
    principalDf['id'] = elems.id
    principalDf['name'] = elems.name
    principalDf['type'] = elems.type
    principalDf['cluster'] = elems[selected_rel]
    
    plt.figure()
    plt.plot()
    
    #graph_pos = nx.spring_layout(g, scale=100, k=2)
    #graph_pos = nx.fruchterman_reingold_layout(g, scale=100, k=0.3)
    graph_pos = nx.fruchterman_reingold_layout(g2, scale=100)
    graph_pos2 = principalDf.apply(lambda x: x['pc1'], axis=1)
    graph_pos2 = {}
    for index,row in principalDf.iterrows():
        graph_pos2[row['id']] = [row['pc1'], row['pc2']]
    
    #graph_pos2 = principalDf.apply(lambda x: dict([('Key',x['id']), ('Value',[x['pc1'], x['pc2']])]), axis=1)
    
    nx.draw_networkx_nodes(g2, graph_pos2, node_shape='o', node_color=principalDf['cluster'], alpha=0.3)
    nx.draw_networkx_edges(g2, graph_pos2, arrows=True)
    
    # show graph
    plt.show()
    
