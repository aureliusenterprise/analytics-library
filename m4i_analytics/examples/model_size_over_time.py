from m4i_analytics.m4i.platform.PlatformUtils import PlatformUtils
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.m4i.platform.model.ModelProvenance import OperationEnum
from m4i_analytics.m4i.portal.DBUtils import DBUtils, InsertBehavior
from m4i_analytics.graphs.GraphComplexity import GraphComplexity
from pandas import DataFrame, to_datetime
import numpy as np

if __name__ == '__main__':
    
    project_options = {
        'project_name': 'Example Factory',
        'project_owner': 'thijsfranck',        
    }
    
    model_options = {
        'branchName': 'MASTER',
        'userid': 'test_user'
    }
    
    provenance = PlatformUtils.retrieve_model_provenance(**project_options)

    provenance = [p for p in provenance if p.operation in [OperationEnum.BRANCH_CLONE.value
                                                           , OperationEnum.BRANCH_MERGE.value
                                                           , OperationEnum.UPLOAD.value
                                                           , OperationEnum.MERGE.value]]
    
    models_over_time = [{'model': ArchimateUtils.load_model_from_repository(
            projectName=project_options['project_name']
            , projectOwner=project_options['project_owner']
            , version=p.start_date, **model_options)
        , 'timestamp': p.start_date
        , 'branch': p.branch
        , 'comment': p.comment} for p in provenance]    
        
    # Calculate the size of the model over time
    model_size_over_time = DataFrame([{'size': 0, 'timestamp': 0}] 
        + [{ 'size': len(model['model'].nodes) + len(model['model'].edges)
            , 'timestamp': model['timestamp']
            , 'branch': model['branch']
            , 'comment': model['comment']} 
        for model in models_over_time]).sort_values(by='timestamp')
    
    model_size_over_time['timestampfmt'] = to_datetime(model_size_over_time['timestamp'], unit='ms')

    # Next, calculate by how much the model has grown between each iteration
    model_size_delta_over_time = model_size_over_time.copy()
    model_size_delta_over_time['delta'] = model_size_delta_over_time['size'].diff()
    model_size_delta_over_time['diff'] = model_size_delta_over_time['size'].div(model_size_delta_over_time['size'].shift())
    model_size_delta_over_time['timestampfmt'] = to_datetime(model_size_delta_over_time['timestamp'], unit='ms')
    
    # Calculate the unique number of concepts accross all branches
    concepts = []
    for model in models_over_time: 
        timestamp = model['timestamp']
        for node in model['model'].nodes.to_dict(orient='records'):
            concepts.append({
                'timestamp': timestamp,
                'concept_id': node['id']
            })
        # END LOOP
        for edge in model['model'].edges.to_dict(orient='records'):
            concepts.append({
                'timestamp': timestamp,
                'concept_id': edge['id']
            })
        # END LOOP
    # END LOOP
    
    unique_concept_count_over_time = DataFrame(concepts).groupby(by='timestamp').size().reset_index()  
    unique_concept_count_over_time.columns = ['timestamp', 'unique_concepts']    
    
    def format_way_of_working(model):
        wow = GraphComplexity.way_of_working(model['model'])
        return{
            'timestamp': model['timestamp'],
            'h1': wow['h1'],
            'h2': wow['h2'],
            'assessment': wow['assessment']
        }
    # END format_way_of_working
   
    # Calculate way of working metrics for every version of the model
    way_of_working = DataFrame([format_way_of_working(model) for model in models_over_time])   
    
    wow_rows = way_of_working.to_dict(orient='records')
    
    def compare_to_previous(row, index):
        if index > 0:
            return GraphComplexity.way_of_working_dynamics(row['h1'], row['h2'], wow_rows[index - 1]['h1'], wow_rows[index - 1]['h2'])
        else:
            return GraphComplexity.way_of_working_dynamics(row['h1'], row['h2'], None, None)
    # END compare_to_previous   
    
    way_of_working['dynamics'] = [compare_to_previous(row, index) for index, row in enumerate(wow_rows)]

    model_summary = model_size_delta_over_time.merge(unique_concept_count_over_time, on=['timestamp'], how='left').merge(way_of_working, on=['timestamp'], how='left').replace([np.inf, -np.inf], np.nan)
    model_summary['timestampfmt'] = model_summary['timestampfmt'].apply(lambda t: str(t))    
    
    DBUtils.insert_dataset(model_summary, 'model_summary', InsertBehavior.REPLACE)    
    