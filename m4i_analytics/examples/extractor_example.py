import pandas as pd

from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.graphs.languages.archimate.model.ArchimateModel import ArchimateModel
from m4i_analytics.graphs.languages.archimate.metamodel.Concepts import ElementType, RelationshipType

from m4i_analytics.m4i.platform.PlatformUtils import ConflictResolutionTemplate, PlatformUtils

from m4i_analytics.model_extractor.ExtractorLanguagePrimitives import ExtractorLanguagePrimitives, ElementDefinition, RelationshipDefinition, AttributeMapping

from m4i_networkx_layouts.FruchtermanReingoldLayout import FruchtermanReingoldLayout
# these are additional layout options. The manual layout requires to add x and y coordinates to the dataframe and a different definition.
# the hierarchical layout requires to install graphviz and the related models4insight extension to use it.
# Grpahviz installation was a problem in some systems, that's why it is commented out here.
#from m4i_graphviz_layouts import HierarchicalLayout
#from m4i_analytics.graphs.visualisations.ManualLayout import ManualLayout

if __name__ == '__main__':\

    # Set up the parameters for the script to point to your project here    
    model_options = {
    	'projectOwner': 'dev'
    	, 'projectName': 'test324537'
      , 'branchName': 'demo'
    }
    username = 'example'    
    
    #%%
    # prepare the data as a dataframe
    nodes = ['node1','node2','node3']
    relations = [ ['rel1-2','node1','node2'],['rel2-3','node2','node3']]
    views = [['view1','test view']]
    
    # nodes are defined by their name
    nodes_df = pd.DataFrame(nodes)
    nodes_df.columns=['node_name']
    
    # relations have an id, a source and a target
    rel_df = pd.DataFrame(relations)
    rel_df.columns = ['rel_id', 'source', 'target' ]
    
    # views have an id and a name and obviously nodes and relations which are displayed in the view
    # the latter is added later in to the data structure
    view_df = pd.DataFrame(views)
    view_df.columns = ['view_id', 'view_name' ]
    
    #%%
    # next we create an empty model instance
    model = ArchimateModel('demo model', defaultAttributeMapping=True)
            
    
    # then we create the nodes
    script_name = 'extractor_example' # this is just a label which gets added to the metadata of the concept, which can be found back in the properties of the concept in Archi
    data_only = False # 
    nodes = [] # container to collect all nodes before adding them to the model object
    edges = [] # container to collect all relations before adding them to the model object
    metadata = [] # container to collect metadat of all concepts related to the model
    
    # create all nodes of the model usng the data frame
    definition = [ElementDefinition(**{'id_prefix': 'demo_'
               , 'id_key': 'node_name'
               , 'concept_name_key': 'node_name'
               , 'concept_label_key': 'node_name'
               , 'concept_type': ElementType.APPLICATION_PROCESS
        })]
    res = ExtractorLanguagePrimitives.parse_concept(nodes_df, definition, script_name, data_only)
    metadata.extend(res['metadata'])
    nodes.extend(res['nodes'])
    # add the created nodes to the model
    model.nodes = pd.DataFrame(nodes)
    
    #%%
    # then the relations in the model
    definition = [RelationshipDefinition(**{'id_prefix': 'demo_'
               , 'id_key': 'rel_id'
               , 'relationship_type': RelationshipType.TRIGGERING
               , 'source_prefix': 'demo_'
               , 'source_id_key': 'source'
               , 'target_prefix': 'demo_'
               , 'target_id_key': 'target'
               , 'mapping': [
                    AttributeMapping(**{'key': 'foo', 'value': 'bar'})
            ]})]
    rel_df['bar'] = 15
    res = ExtractorLanguagePrimitives.parse_relationship(rel_df, model, definition, script_name, data_only)
    metadata.extend(res['metadata'])
    edges.extend(res['edges'])
    
    # add the created edges to the model
    model.edges = pd.DataFrame(edges)
    
    # organizing the model makes sure that all nodes and relations are assigned to the right folder in the ArhciMate model
    model.organize()
    
    #%%
    # then we create the views.
    definition = [{'id_type':'dynamic'
           ,'id_prefix':'demo_'
           ,'id_key':'view_id'
           ,'view_name_type':'dynamic'
           ,'view_name_prefix':''
           ,'view_name_key':'view_name'
           ,'view_path': [{'type':'static', 'value':'demo'}] # adds all created views under the views folder in a folder demo
           ,'view_nodes': [{'id_prefix':'demo_', 'id_key':'node_name'}] # this id specification has to be aligned with the id definition of the nodes you want to use.
           ,'view_edges': [] # if no edges are specified all edges defined between the included nodes are added. You can define edges like nodes.
           ,'view_layout': FruchtermanReingoldLayout} #various layouts are possible. For a database structure the hierarchical layout would be best, but it requires an installation of graphviz, which is not always so easy.... thus feel free to use a different one.
         ]
    # prepare the data by make a left join of views and nodes
    nodes_df['view_id'] = 'view1' 
    df = view_df.merge(nodes_df, how='left', on='view_id')
    res = ExtractorLanguagePrimitives.parse_view(df, model, definition, script_name, data_only) 
    # different to the other functions parse functions this function directly adds the view into the model and adds it properly to the folder structure of the model
    metadata.extend(res['metadata'])
    #created metadata still have to be added manually
    
    #%%
    # and this is the result
    print('nodes:')
    print(model.nodes)
    print()
    print('relations')
    print(model.edges)
    print()
    print('views:')
    print(model.views)
    
    #%%
    # have a look at the resulting metadata
    print(metadata)
    
    #%%
    # last step is to upload the model to the models4insight repository

    
    # exchange with your username
    # add the created model to a new branch and after you checked the model and you are happy merge it with your working branch 
    res2 = ArchimateUtils.commit_model_to_repository_with_conflict_resolution(
        model=model
        , userid=username
        , description='created demo model'
        , conflict_resolution_template=ConflictResolutionTemplate.UPLOAD_ONLY.value
        , **model_options)
    #%%
    # this command uploads the related data
    res3 = PlatformUtils.upload_model_data(conceptData=metadata, **model_options)
