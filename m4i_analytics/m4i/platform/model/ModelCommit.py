from m4i_analytics.shared.model.BaseModel import BaseModel
from enum import Enum


class ContentType(Enum):
    ARCHIMATE = 'archimate'
    XML = 'xml'
    JSON = 'json'
# END ContentType


class ModelCommit(BaseModel):
    
    _fields = [
        ('parserName', str, False)
       , ('projectName', str, False)
       , ('branchName', str, False)
       , ('module', str, False)
       , ('modelId', str, False)
       , ('contentType', str, False)
       , ('comment', str, False)
       , ('version', str, False)
       , ('userid', str, False)
       , ('taskId', str, False)
       , ('intFileName', str, False)
       , ('fileList', str, True)        
    ]
# END ModelCommit
