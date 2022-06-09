from m4i_analytics.m4i.ApiUtils import ApiUtils, ContentType
from m4i_analytics.m4i.nifi.model.ObjectModel import ProcessGroupFlowEntity, ProcessorEntity

import m4i_analytics.m4i.nifi.config as config

class NifiApi():
    
    @staticmethod
    def retrieve_process_group(name):
        
        if name is None:
            raise TypeError('Name should not be undefined')
        elif type(name) != type(str()):
            raise ValueError('Name should be a string')
        
        result = ApiUtils.get(config.FLOW_PROCESS_GROUPS_ENDPOINT + name, contentType=ContentType.JSON)
        
        return ProcessGroupFlowEntity(**result)
    # END retrieve_process_group
            
# END NifiApi