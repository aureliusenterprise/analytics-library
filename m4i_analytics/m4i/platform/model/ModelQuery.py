from m4i_analytics.shared.model.BaseModel import BaseModel
from m4i_analytics.m4i.platform.model.ModelQueryDifResult import ModelQueryDifResult
from enum import Enum

class StateEnum(Enum):
    CREATED = 'created'
    WAITING = 'waiting'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILURE = 'failure'
# END StateEnum


class ModelQuery(BaseModel):
    
    _fields = [
        ('noNodes', int, False)
        , ('noRelations', int, False)
        , ('noViews', int, False)
        , ('message', str, False)
        , ('timestamp', int, False)
        , ('version', int, False)
        , ('state', str, False)
        , ('difResult', ModelQueryDifResult, False)
    ]

# END ModelQuery
