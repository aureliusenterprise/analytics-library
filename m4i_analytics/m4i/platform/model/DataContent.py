from m4i_analytics.shared.model.BaseModel import BaseModel


class DataContent(BaseModel):
    
    _fields = [
        ("start_date", int, False),
        ("end_date", int, False),
        ("id", str, False),
        ("data", dict, False)
    ]
    
# END DataContent