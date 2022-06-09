from m4i_analytics.graphs.GraphUtils import GraphUtils
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.m4i.portal.PortalApi import PortalApi 
from m4i_analytics.m4i.portal.DBUtils import DBUtils, InsertBehavior


if __name__ == '__main__':
    
    '''
    This example shows you how to do some basic analytics and publish the results to the portal.
    
    First we retrieve an example model from the database.
    '''
    
    model_options = {
        'projectName': 'Example Factory',
        'projectOwner': 'thijsfranck',
        'branchName': 'MASTER',
        'userid': 'test_user'
    }
    
    model = ArchimateUtils.load_model_from_repository(**model_options)
    
    '''
    Next we do some basic analysis. For this example, we generate a transition matrix for the given model. This library offers many convenience functions for different types of analytics.
    '''
    
    transition_matrix = GraphUtils.toTransitionMatrix(model)
    
    '''
    Next, we store the transition matrix in the database. When storing your dataset, choose a name that describes the data you want to publish.
    
    You can overwrite your previous dataset by simply storing your data again. Alternatively, if you want to append data to your dataset rather than replacing it, change the insert behaviour to InsertBehavior.APPEND.
    '''
    
    DBUtils.insert_dataset(transition_matrix, 'example_factory_example', if_exists=InsertBehavior.REPLACE)
    
    '''
    Finally, we create a new project on the portal and publish a dashboard with our data on it. We need to create a project first before we can publish any data. 
    
    A project and corresponding dashboard will only be created once, no matter how many times you call the function.
    '''
    
    portal_project = {
        'taskid': 'storing_and_publishing_a_dataset',
        'projectid': 'thijsfranck__Example_Factory_demo',
        'run_by': 'thijsfranck',
        'owner_username': 'thijsfranck',
        'owner_email': 'thijs.franck@aureliusenterprise.com',
        'owner_firstname': 'Thijs',
        'owner_lastname': 'Franck'
    }
    
    PortalApi.create_project(**portal_project)
    
    portal_dashboard = {
        'taskid': 'storing_and_publishing_a_dataset',
        'projectid': 'thijsfranck__Example_Factory_demo',
        'run_by': 'thijsfranck',
        'tablename': 'example_factory_example'
    }
    
    PortalApi.create_table_dashboard(**portal_dashboard)