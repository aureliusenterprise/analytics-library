from m4i_analytics.monitoring.generating_a_db_model import generate_db_model
from m4i_analytics.monitoring.generating_a_nifi_model import generate_nifi_model
from m4i_analytics.monitoring.generating_a_superset_model import generate_superset_model
from m4i_analytics.monitoring.generating_a_resin_model import generate_resin_model
from m4i_analytics.monitoring.retrieve_superset_status import retrieve_superset_status
from m4i_analytics.monitoring.retrieve_nifi_status import retrieve_nifi_status
from m4i_analytics.monitoring.propagation import propagate
from m4i_analytics.model_extractor.ResinExtractor import ResinExtractor

from m4i_analytics.m4i.platform.PlatformUtils import PlatformUtils
from m4i_analytics.m4i.platform.PlatformApi import PlatformApi
from m4i_analytics.m4i.portal.PortalApi import PortalApi
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.m4i.platform.model.ModelQuery import StateEnum as ModelQueryStateEnum
from m4i_analytics.m4i.platform.model.ModelQueryDifResult import StateEnum as ModelQueryDifResultStateEnum

from rx import Observable
from rx.concurrency import NewThreadScheduler

import threading
import time
import logging

# Config
model_options = {
        'projectOwner': 'thijsfranck',
        'projectName': 'status monitoring test 435168713',
}
project_owner_email='thijs.franck@aureliusenterprise.com'
 
nagios_host = 'localhost:8888'
nagios_credentials = {
        'username': 'nagiosadmin',
        'password': 'aurelius17'
}

superset_db_url = 'sqlite:///C:/Users/thijs/Downloads/superset/superset_1.db'
db_url = 'mysql+pymysql://m4i:Aurelius18UVA@localhost:3306/m4i'
#db_url = 'mysql+pymysql://m4i:6sn$s(_mjHh=@localhost:3306/m4i'

nifi_flow_paths = ['C:/Users/thijs/Downloads/local_flow.xml']

# extract resin model
resin_username ='delphi_admin' 
resin_password = 'Delphi!123' 

MODEL_GENERATION_INTERVAL = 3600000 # Refresh the models every hour
STATUS_RETRIEVAL_INTERVAL = 6000000 # Refresh the status data every 5 minutes
STATUS_RETRIEVAL_OFFSET = 6000000 # Start uploading statuses after x amount of time

MODEL_QUERY_INTERVAL = 1000

scheduler = NewThreadScheduler()

#Set up logging
logger = logging.getLogger('monitoring')
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)

file_handler = logging.FileHandler('monitoring.log')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s -%(relativeCreated)6d %(threadName)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

def set_branch_name(obj, branch_name):
    obj['branchName'] = branch_name
    return obj
# END set_branch_name 

def handle_commit(model, branch):
        
        model_commit = (Observable.of(ArchimateUtils.commit_model_to_repository(model, branchName=branch, userid='thijsfranck', description='db model', **model_options))
            .share()
            .replay(lambda m: m))
                
        model_query = (model_commit.combine_latest(Observable.timer(0, period=MODEL_QUERY_INTERVAL), lambda a, b: [a, b])
            .switch_map(lambda i: Observable.of(PlatformApi.query_model(i[0].projectName, i[0].taskId)))
            .tap(lambda q: logger.debug('Query state: {0}'.format(q.state)))
            .filter(lambda q: q.state in [ModelQueryStateEnum.COMPLETED.value, ModelQueryStateEnum.FAILURE.value])
            .switch_map(lambda q: Observable.throw(Exception('Query state failure!')) if q.state == ModelQueryStateEnum.FAILURE else Observable.of(q))
            .take(1))
                
        has_conflicts, no_conflicts = model_query.partition(lambda q: q.difResult.state == ModelQueryDifResultStateEnum.CONFLICT.value)                    
        
        conflict_resolution = (has_conflicts
            .with_latest_from(model_commit, lambda a, b: [a, b])
            .tap(lambda i: logger.info('Replacing old model version'))
            .switch_map(lambda i: Observable.of(PlatformApi.force_commit(
                addListLeft=[]
                , addListRight=[]
                , description='replacing old model version'
                , deleteListLeft=[]
                , deleteListRight=[]
                , fromBranch=branch
                , fromModelId=i[1].taskId
                , projectName=i[1].projectName
                , taskid=i[1].taskId
                , toBranch=branch
                , toModelId='TRUNK'
                , userid='thijsfranck'
                , template='upload_only')))
            .share()
            .replay(lambda c: c))
            
        conflict_resolution_query = (conflict_resolution.combine_latest(Observable.timer(0, period=MODEL_QUERY_INTERVAL), lambda a, b: [a, b])
            .switch_map(lambda i: Observable.of(PlatformApi.query_model(i[0].projectName, i[0].taskId)))
            .filter(lambda q: q.state in [ModelQueryStateEnum.COMPLETED.value, ModelQueryStateEnum.FAILURE.value])
            .switch_map(lambda q: Observable.throw(Exception('Query state failure!')) if q.state == ModelQueryStateEnum.FAILURE.value else Observable.of(q))
            .take(1))
        
        commit_result = Observable.merge(no_conflicts, conflict_resolution_query).take_last(1)
        
        commit_result.subscribe(lambda s: logger.info('Model commit successful!'), lambda e: logger.exception(e))
        
        return commit_result.map(lambda r: {'query': r, 'branchName': branch})

# END handle_commit
        
if __name__ == '__main__':

    # Generate the models, metadata and status info
    db_model = (Observable.timer(0, period=MODEL_GENERATION_INTERVAL)
        .tap(lambda s: logger.info('Generating DB model!'))
        .switch_map(lambda s: Observable.of(generate_db_model(db_url)))
        .tap(lambda i: logger.info('DB model generated!'))    
        .map(lambda i: set_branch_name(i, 'db'))
        .share())
    
    superset_model = (Observable.timer(0, period=MODEL_GENERATION_INTERVAL)
        .tap(lambda s: logger.info('Generating superset model!'))
        .switch_map(lambda s: Observable.of(generate_superset_model(superset_db_url)))
        .tap(lambda i: logger.info('Superset model generated!'))
        .map(lambda i: set_branch_name(i, 'superset'))
        .share())
    
    nifi_model = (Observable.timer(0, period=MODEL_GENERATION_INTERVAL)
        .tap(lambda s: logger.info('Generating nifi model!'))
        .switch_map(lambda s: Observable.of(generate_nifi_model(nifi_flow_paths)))
        .tap(lambda i: logger.info('Nifi model generated!'))     
        .map(lambda i: set_branch_name(i, 'nifi'))
        .share())
    
    resin_model = (Observable.timer(0, period=MODEL_GENERATION_INTERVAL)
        .tap(lambda s: logger.info('Generating resin model!'))
        .switch_map(lambda s: Observable.of(ResinExtractor.extract_resin_model(resin_username, resin_password)))
        .tap(lambda i: logger.info('Resin model generated!'))
        .map(lambda i: set_branch_name(i, 'resin'))
        .share())
    
    superset_status = (Observable.timer(STATUS_RETRIEVAL_OFFSET, period=STATUS_RETRIEVAL_INTERVAL)
        .tap(lambda s: logger.info('Retrieving superset status!'))
        .switch_map(lambda s: Observable.of(retrieve_superset_status(nagios_host, nagios_credentials, 'localhost', 'apache_vhosts')))
        .tap(lambda i: logger.info('Superset status calculated!'))
        .map(lambda i: {'branchName': 'superset', 'content': i})
        .share())
    
    nifi_status = (Observable.timer(STATUS_RETRIEVAL_OFFSET, period=STATUS_RETRIEVAL_INTERVAL)
        .tap(lambda s: logger.info('Retrieving nifi status!'))
        .switch_map(lambda s: Observable.of(retrieve_nifi_status()))
        .tap(lambda i: logger.info('Nifi status calculated!'))
        .map(lambda i: {'branchName': 'nifi', 'content': i})
        .share())

    # Commit the models and data to the repository
    db_model_commit = (db_model
        .tap(lambda i: logger.info('Committing DB model!'))
        .switch_map(lambda i: handle_commit(i['model'], i['branchName']))
        .tap(lambda r: logger.info('DB model committed!'))
        .share())
    
    db_data_commit = (db_model_commit
        .with_latest_from(db_model, lambda a, b: b)
        .tap(lambda i: logger.info('Committing DB data!'))
        .switch_map(lambda i: Observable.of(PlatformUtils.upload_model_data(branchName=i['branchName'], conceptData=i['data'], **model_options)))
        .tap(lambda r: logger.info('DB model metadata committed!'))
        .share())
    
    superset_model_commit = (superset_model
        .tap(lambda i: logger.info('Committing Superset model!'))
        .switch_map(lambda i: handle_commit(i['model'], i['branchName']))
        .tap(lambda r: logger.info('Superset model committed!'))
        .share())
    
    superset_data_commit = (superset_model_commit
        .with_latest_from(superset_model, lambda a, b: b)
        .tap(lambda i: logger.info('Committing Superset data!'))
        .switch_map(lambda i: Observable.of(PlatformUtils.upload_model_data(branchName=i['branchName'], conceptData=i['data'], **model_options)))
        .tap(lambda r: logger.info('Superset model metadata committed!'))
        .share())
    
    nifi_model_commit = (nifi_model
        .tap(lambda i: logger.info('Committing Nifi model!'))
        .switch_map(lambda i: handle_commit(i['model'], i['branchName']))
        .tap(lambda r: logger.info('Nifi model committed!'))
        .share())
    
    nifi_data_commit = (nifi_model_commit
        .with_latest_from(nifi_model, lambda a, b: b)
        .tap(lambda i: logger.info('Committing Nifi metadata!'))
        .switch_map(lambda i: Observable.of(PlatformUtils.upload_model_data(branchName=i['branchName'], conceptData=i['data'], **model_options)))
        .tap(lambda r: logger.info('Nifi model metadata committed!'))
        .share())
    
    resin_model_commit = (resin_model
        .tap(lambda i: logger.info('Committing resin model!'))
        .switch_map(lambda i: handle_commit(i['model'], i['branchName']))
        .tap(lambda r: logger.info('Resin model committed!'))
        .share())
    
    resin_data_commit = (resin_model_commit
        .with_latest_from(resin_model, lambda a, b: b)
        .tap(lambda i: logger.info('Committing Resin metadata!'))
        .switch_map(lambda i: Observable.of(PlatformUtils.upload_model_data(branchName=i['branchName'], conceptData=i['data'], **model_options)))
        .tap(lambda r: logger.info('Nifi model metadata committed!'))
        .share())
    
    superset_status_commit = (superset_status
        .tap(lambda i: logger.info('Committing Superset status!'))
        .switch_map(lambda i: Observable.of(PlatformUtils.upload_model_data(branchName=i['branchName'], conceptData=i['content'], **model_options)))
        .tap(lambda r: logger.info('Superset status committed!'))
        .share())
    
    superset_status_propagate = (superset_status_commit
        .tap(lambda i: logger.info('Propagating Superset status!'))
        .switch_map(lambda i: Observable.of(propagate({
            'projectOwner': model_options['projectOwner'],
            'projectName': model_options['projectName'],
            'branchName': 'superset'
         })))
        .tap(lambda i: PlatformUtils.upload_model_data(branchName='nifi', conceptData=i['measured_status'], **model_options))
        .tap(lambda i: PlatformUtils.upload_model_data(branchName='nifi', conceptData=i['propagated_status'], **model_options))
        .tap(lambda i: PlatformUtils.upload_model_data(branchName='nifi', conceptData=i['combined_status'], **model_options))
        .tap(lambda r: logger.info('Superset status propagated!'))
        .share())
    
    nifi_status_commit = (nifi_status
        .tap(lambda i: logger.info('Committing Nifi status!'))
        .switch_map(lambda i: Observable.of(PlatformUtils.upload_model_data(branchName=i['branchName'], conceptData=i['content']['status'], **model_options)))
        .tap(lambda r: logger.info('Nifi status committed!'))
        .share())
    
    nifi_status_propagate = (nifi_status_commit
        .tap(lambda i: logger.info('Propagating Nifi status!'))
        .switch_map(lambda i: Observable.of(propagate({
            'projectOwner': model_options['projectOwner'],
            'projectName': model_options['projectName'],
            'branchName': 'nifi'
         })))
        .tap(lambda i: PlatformUtils.upload_model_data(branchName='nifi', conceptData=i['measured_status'], **model_options))
        .tap(lambda i: PlatformUtils.upload_model_data(branchName='nifi', conceptData=i['propagated_status'], **model_options))
        .tap(lambda i: PlatformUtils.upload_model_data(branchName='nifi', conceptData=i['combined_status'], **model_options))
        .tap(lambda r: logger.info('Nifi status propagated!'))
        .share())
    
    nifi_status_data_commit = (nifi_status
        .tap(lambda i: logger.info('Committing Nifi status data!'))
        .switch_map(lambda i: Observable.of(PlatformUtils.upload_model_data(branchName=i['branchName'], conceptData=i['content']['data'], **model_options)))
        .tap(lambda r: logger.info('Nifi status data committed!'))
        .share())
    
    models_committed = (Observable.zip_array(db_model_commit
                                           , db_data_commit
                                           , superset_model_commit
                                           , superset_data_commit
                                           , nifi_model_commit
                                           , nifi_data_commit
                                           , resin_model_commit
                                           , resin_data_commit
                                           ))
    
    status_committed = (Observable.zip_array(superset_status_propagate
                                           , nifi_status_propagate
                                           , nifi_status_data_commit
                                           ))
        
    create_project = (Observable.merge(models_committed, status_committed)
        .tap(lambda i: logger.info('Creating project on the portal!'))
        .tap(lambda i: Observable.of(PortalApi.create_project(
            taskid='monitoring_create_project'
            , projectid='{0}__{1}'.format(
                model_options['projectOwner']
                , model_options['projectName'].replace(' ', '_'))
            , run_by='monitoring'
            , owner_username=model_options['projectOwner']
            , owner_email=project_owner_email)))
        .tap(lambda i: logger.info('Project created!'))
        .share())
            
    portal_update = Observable.zip(models_committed, create_project, lambda a, b: b)
    portal_data = Observable.zip(status_committed
                                 , create_project, lambda a, b: b)    
       
    delta_db = (portal_update
        .map(lambda i: [e for e in i if type(e) is dict and 'branchName' in e.keys() and e['branchName'] == 'db'])
        .tap(lambda i: logger.info('Updating DB model on the portal!'))
        .switch_map(lambda i: Observable.of(PortalApi        
            .update_project_model_async(
                taskid='monitoring_update_db'
                , projectid='{0}__{1}'.format(
                    model_options['projectOwner']
                    , model_options['projectName'].replace(' ', '_'))
                , run_by='monitoring'
                , branch_name='db'
                , version=i[0]['query'].version
        ))))
          
    data_db = (Observable.merge(portal_update, portal_data)
        .map(lambda i: [e for e in i if type(e) is dict and 'branchName' in e.keys() and e['branchName'] == 'db'])
        .tap(lambda i: logger.info('Updating DB data on the portal!'))
        .switch_map(lambda i: Observable.of(PortalApi        
            .update_project_data(
                taskid='monitoring_update_db'
                , projectid='{0}__{1}'.format(
                    model_options['projectOwner']
                    , model_options['projectName'].replace(' ', '_'))
                , run_by='monitoring'
                , branch_name='db'
                , version=int(time.time())
        ))))
                
    Observable.merge(delta_db, data_db).catch_exception(lambda e: Observable.of(logger.exception(e))).subscribe_on(scheduler).subscribe(lambda s: logger.info('Portal update for DB branch completed!'))
        
    delta_superset = (portal_update
        .map(lambda i: [e for e in i if type(e) is dict and 'branchName' in e.keys() and e['branchName'] == 'superset'])
        .tap(lambda i: logger.info('Updating Superset model on the portal!'))
        .switch_map(lambda i: Observable.of(PortalApi        
            .update_project_model_async(
                taskid='monitoring_update_superset'
                , projectid='{0}__{1}'.format(
                    model_options['projectOwner']
                    , model_options['projectName'].replace(' ', '_'))
                , run_by='monitoring'
                , branch_name='superset'
                , version=i[0]['query'].version
        ))))
          
    data_superset = (Observable.merge(portal_update, portal_data)
        .map(lambda i: [e for e in i if type(e) is dict and 'branchName' in e.keys() and e['branchName'] == 'superset'])
        .tap(lambda i: logger.info('Updating Superset data on the portal!'))
        .switch_map(lambda i: Observable.of(PortalApi        
            .update_project_data(
                taskid='monitoring_update_superset'
                , projectid='{0}__{1}'.format(
                    model_options['projectOwner']
                    , model_options['projectName'].replace(' ', '_'))
                , run_by='monitoring'
                , branch_name='superset'
                , version=int(time.time())
        ))))
        
    (Observable.merge(delta_superset, data_superset)
        .catch_exception(lambda e: Observable.of(lambda e: Observable.of(logger.exception(e))))
        .subscribe_on(scheduler)
        .subscribe(lambda s: logger.info('Portal update for Superset branch completed!')))

    delta_nifi = (portal_update
        .map(lambda i: [e for e in i if type(e) is dict and 'branchName' in e.keys() and e['branchName'] == 'nifi'])
        .tap(lambda i: logger.info('Updating Nifi model on the portal!'))
        .switch_map(lambda i: Observable.of(PortalApi        
        .update_project_model_async(
            taskid='monitoring_update_nifi'
            , projectid='{0}__{1}'.format(
                model_options['projectOwner']
                , model_options['projectName'].replace(' ', '_'))
            , run_by='monitoring'
            , branch_name='nifi'
            , version=int(i[0]['query'].version)
        ))))
          
    data_nifi = (Observable.merge(portal_update, portal_data)
        .map(lambda i: [e for e in i if type(e) is dict and 'branchName' in e.keys() and e['branchName'] == 'nifi'])
        .tap(lambda i: logger.info('Updating Nifi data on the portal!'))
        .switch_map(lambda i: Observable.of(PortalApi        
        .update_project_data(
            taskid='monitoring_update_nifi'
            , projectid='{0}__{1}'.format(
                model_options['projectOwner']
                , model_options['projectName'].replace(' ', '_'))
            , run_by='monitoring'
            , branch_name='nifi'
            , version=int(time.time())
        ))))
            
    Observable.merge(delta_nifi, data_nifi).catch_exception(lambda e: Observable.of(lambda e: Observable.of(logger.exception(e)))).subscribe_on(scheduler).subscribe(lambda s: logger.info('Portal update for Nifi branch completed!'))

    delta_resin = (portal_update
        .map(lambda i: [e for e in i if type(e) is dict and 'branchName' in e.keys() and e['branchName'] == 'resin'])
        .tap(lambda i: logger.info('Updating resin model on the portal!'))
        .switch_map(lambda i: Observable.of(PortalApi        
        .update_project_model_async(
            taskid='monitoring_update_resin'
            , projectid='{0}__{1}'.format(
                model_options['projectOwner']
                , model_options['projectName'].replace(' ', '_'))
            , run_by='monitoring'
            , branch_name='resin'
            , version=int(i[0]['query'].version)
        ))))
          
    data_resin = (Observable.merge(portal_update, portal_data)
        .map(lambda i: [e for e in i if type(e) is dict and 'branchName' in e.keys() and e['branchName'] == 'resin'])
        .tap(lambda i: logger.info('Updating resin data on the portal!'))
        .switch_map(lambda i: Observable.of(PortalApi        
        .update_project_data(
            taskid='monitoring_update_resin'
            , projectid='{0}__{1}'.format(
                model_options['projectOwner']
                , model_options['projectName'].replace(' ', '_'))
            , run_by='monitoring'
            , branch_name='resin'
            , version=int(time.time())
        ))))
            
    Observable.merge(delta_resin, data_resin).catch_exception(lambda e: Observable.of(logger.exception(e))).subscribe_on(scheduler).subscribe(lambda s: logger.info('Portal update for resin branch completed!'))
            
    keep_alive = threading.Condition()
    keep_alive.acquire()
    keep_alive.wait()