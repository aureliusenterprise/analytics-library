from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.graphs.visualisations.GraphPlotter import Layout

if __name__ == '__main__': 
    
    """
    This script adds an automatically generated view to the retrieved model and writes the model to a file.
    """
    
    model_options = {
        'projectName': 'Example Factory',  # change to your project name
        'projectOwner': 'thijsfranck',     # change to the user name of the owner of the project
        'branchName': 'MASTER',
        'userid': 'test_user'              # change to your user name
    }
    
    output_path = 'C:/Users/Thijs/Desktop/model.json'
    
    model = ArchimateUtils.load_model_from_repository(**model_options)
    
    generatedview = ArchimateUtils.generate_view(model, layout=Layout.RANDOM)
    
    views = model.views
    '''
    with open(output_path, 'w') as output:
        output.write(ArchimateUtils.to_JSON(generatedviewmodel))
    # END WITH
    '''