from m4i_analytics.m4i.ApiUtils import ApiUtils
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.m4i.platform.PlatformApi import PlatformApi
from m4i_analytics.graphs.visualisations.GraphPlotter import Layout
from m4i_analytics.graphs.GraphComplexity import GraphComplexity
from m4i_analytics.graphs.GraphUtils import GraphUtils
import pydotplus as ptp

if __name__ == '__main__':    
    
    '''
    This example shows you how to load a model from the repository. 
    
    The script below retrieves the latest version of a public ArchiMate model and prints a description of the model to the console.
    
    The load model function takes four arguments
        
        * The name of the project    
        * The username of the project owner (your username)
        * The name of the branch
        * The name of the user making the request (your username)
        * Optionally, the timestamp of the version you wish to retrieve (add version as an additional parameter)
    
    '''

    ' To load your own model from the repository make the changes indicated by the comments below: '
    model_options = {
        'projectName': 'monitoring7',  # change to your project name
        'projectOwner': 'delphi',     # change to the user name of the owner of the project
        'branchName': 'all',
        'userid': 'dev'             # change to your user name
    }
        
    model = ArchimateUtils.load_model_from_repository(**model_options)
    
    #nodes = GraphUtils.toNXGraph(model).nodes(data=True)
    
    '''
    print('The model is named "{0}"'.format(model.name))
    print('The model contains {0} elements, {1} relationships, and {2} views'.format(len(model.nodes), len(model.edges), len(model.views)))
    
    print('Elements are described by the following attributes {0}'.format(list(model.nodes.columns)))
    print('   The id is a UUID used for referencing the element in the repository, thus altering this value results in overwriting an existing concept or creating a new one.')
    print('   The label and name describe the name assigned to the element.')
    print('   The type is the Archimate 3 type of the element. Each element type is prefixed with "ar3_" to indicate that this is an Archimate 3 type.')
    print(model.nodes.iloc[0])
    
    print('Relationships are described by the following attributes {0}'.format(list(model.edges.columns)))
    print('   The id is a UUID used for referencing the relationship in the repository, thus altering this value results in overwriting an existing concept or creating a new one.')
    print('   The is_bidirectional flag indicates whether the specific relationship is bidirectional, although the actual relationship is represented as a directed edge.')
    print('   The label and name describe the name assigned to the relationship. This value will often be empty.')
    print('   The type is the Archimate 3 type of the relationhsip. Each relationship type is prefixed with "ar3_" to indicate that this is an Archimate 3 type.')
    print(model.edges.iloc[0])
    
    print('Views are described by the following attributes {0}'.format(list(model.views.columns)))
    print('   The id is a UUID used for referencing the view in the repository, thus altering this value results in overwriting an existing concept or creating a new one.')
    print('   The name describe the name assigned to the view.')
    print('   The type is the Archimate 3 type of the view. Each relationship type is prefixed with "ar3_" to indicate that this is an Archimate 3 type.')
    print('   Connections is a JSON string containing information about the connections used in a view. A connection is referring to a relationship and describing its position in the view.')
    print('   Nodes is a JSON string containing information about the nodes used in a view. A node is referring to an element and describing its position in the view.')
    print('   Properties is a JSON string containing properties assigned to the view.')
    print(model.views.iloc[0])
    
    print('Organizations are organizing elements, relationships and views, by assigning them to folders to better be able to navigate and manage the model.')
    print('Each element, relationship and view is assigned a folder, thus the sum of {0}+{1}+{2} must be {3}'.format(len(model.nodes), len(model.edges), len(model.views), len(model.organizations)))
    print('Organizations are described by the following attributes {0}'.format(list(model.organizations.columns)))
    print('   The idRef is a reference to an id of an element, a relationship or a view.')
    print('   The levels are dynamically derived and there are as many levels as nestings in the folder structure of the model.')
    print('   The number of nestings is {0}'.format(len(model.organizations.columns)-1))
    print(model.organizations.iloc[0])
    
    print('Elements can now be extended with their organization information:')
    print(model.nodes.merge(model.organizations, left_on='id', right_on='idRef').iloc[0])
    '''