from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.graphs.GraphComplexity import GraphComplexity

if __name__ == '__main__':    
    
    '''
    This example shows the use of some complexity metrics.
    
    The script below retrieves the latest version of a public ArchiMate model and calculates some complexity dimensions about it.
    
    The load model function takes four arguments
        
        * The name of the project    
        * The username of the project owner (your username)
        * The name of the branch
        * The name of the user making the request (your username)
        * Optionally, the timestamp of the version you wish to retrieve (add version as an additional parameter)
    
    '''

    ' To load your own model from the repository make the changes indicated by the comments below: '
    model_options = {
        'projectName': 'test project steel 093209',  # change to your project name
        'projectOwner': 'thijsfranck',     # change to the user name of the owner of the project
        'branchName': 'MASTER',
        'userid': 'test_user'              # change to your user name
    }
    
    model = ArchimateUtils.load_model_from_repository(**model_options)
    
    #in_degree = GraphComplexity.in_degree(model, return_node=True)
    #out_degree = GraphComplexity.out_degree(model)
    #degree_centrality = GraphComplexity.degree_centrality(model)
    #in_degree_centrality = GraphComplexity.in_degree_centrality(model)
    #out_degree_centrality = GraphComplexity.out_degree_centrality(model)
    #closeness_centrality = GraphComplexity.closeness_centrality(model)
    #betweenness_centrality = GraphComplexity.betweenness_centrality(model)
    #edge_betweenness_centrality = GraphComplexity.edge_betweenness_centrality(model, return_edge=True)
    way_of_working = GraphComplexity.way_of_working(model)
    
    
    print(way_of_working)
    