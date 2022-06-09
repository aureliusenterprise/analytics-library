from m4i_analytics.shared.model.BaseModel import BaseModel
from m4i_analytics.m4i.platform.model.DataContent import DataContent


class DataRetrieve(BaseModel):
    
    _fields = [
        ("project", str, False),
        ("branch", str, False),
        ("model_id", str, False),
        ("content", DataContent, True)
    ]
    
# END DataRetrieve
