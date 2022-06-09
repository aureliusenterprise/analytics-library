from m4i_analytics.m4i.platform.PlatformUtils import PlatformUtils
from m4i_analytics.m4i.platform.PlatformApi import PlatformApi
from m4i_analytics.m4i.portal.PortalApi import PortalApi
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils

from datetime import datetime
from rx import Observable


def print_msg(msg):
    print('{0} - {1}'.format(datetime.now(), msg))
# END print_msg

if __name__ == '__main__':    
    
    model_options = {
            'projectOwner': 'thijsfranck',
            'projectName': 'test project async test 7351358',
    }
    project_owner_email='thijs.franck@aureliusenterprise.com'
     
    
    create_project = (Observable.of(model_options)
        .tap(lambda m: print_msg('Creating project!'))
        .switch_map(lambda m: Observable.of(PortalApi.create_project(
            taskid='test_async_delta'
            , projectid='{0}__{1}'.format(
                model_options['projectOwner']
                , model_options['projectName'].replace(' ', '_'))
            , run_by='async_delta_test'
            , owner_username=model_options['projectOwner']
            , owner_email=project_owner_email
            )
        ))
        .tap(lambda r: print_msg('Project created!'))
    )
        
    delta_request = (create_project
        .tap(lambda r: print_msg('Sending delta request!'))
        .switch_map(lambda r: Observable.of(PortalApi.update_project_model_async(
            taskid='test_async_delta'
            , projectid='{0}__{1}'.format(
                model_options['projectOwner']
                , model_options['projectName'].replace(' ', '_'))
            , run_by='async_delta_test'
            , branch_name='MASTER'
            , version=1535035654947
            )
        ))
        .tap(lambda r: print_msg('Delta request completed!'))
        .tap(print_msg)
    )
            
    query = (delta_request.combine_latest(Observable.timer(0, 1000), lambda a, b: a)
        .tap(lambda r: print_msg('Delta query started!'))
        .switch_map(lambda r: Observable.of(PortalApi.instanceworkflow_query(
            taskid='test_async_delta'
            , projectid='{0}__{1}'.format(
                model_options['projectOwner']
                , model_options['projectName'].replace(' ', '_'))
            , run_by='async_delta_test'
            , instanceid=r['instance_id']
            )
        ))
        .tap(lambda r: print_msg('Delta query completed!'))
        .tap(print_msg)
        .filter(lambda q: q['end_time'] != 'None')
    )
        
    query.take(1).subscribe(lambda r: print_msg('Done!'))
        
        