from m4i_analytics.graphs.GraphUtils import GraphUtils
from m4i_analytics.graphs.visualisations.GraphPlotter import GraphPlotter, Layout
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils 


if __name__ == '__main__':
    
    '''
    This example retrieves the latest version of an example model generates some graph plots.
    
    Alter the plot options to change the apperance of the generated graphs. This library provides several kinds of standardized layouts, such as:
        
        * CIRCULAR
        * FRUCHTERMAN_REINGOLD
        * KAMADA_KAWAI
        * RANDOM
        * SHELL
        * SPECTRAL
    
    Please have a look at the visualize function in the GraphPlotter class for additional customization parameters.
    '''
    
    plot_options = {
        'layout': Layout.CIRCULAR,
        'node_color': 'red',
        'node_size': 250,
        'edge_width': 1
    }
    
    model_options = {
        'projectName': 'Example Factory',
        'projectOwner': 'thijsfranck',
        'branchName': 'MASTER',
        'userid': 'test_user'
    }
    
    model = ArchimateUtils.load_model_from_repository(**model_options)    

    '''
    First we simply visualize the model as we retrieved it
    '''
    GraphPlotter.visualize(model, **plot_options)
    
    '''
    Next, let's do some analysis and plot the model again. This library offers many kinds of convenience functions for model analytics. Let's try grouping our nodes by type.
    '''
    filteredModel = GraphUtils.groupByNodeType(model)
    GraphPlotter.visualize(filteredModel, **plot_options)
    
    '''
    Alternatively, let's convert our model into a bipartite graph. This is especially useful when your model includes relations to relations.
    '''
    model = GraphUtils.toBipartiteGraph(model)
    GraphPlotter.visualize(model, **plot_options)