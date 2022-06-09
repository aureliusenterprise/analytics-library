from m4i_analytics.shared.model.BaseModel import BaseModel
from m4i_analytics.m4i.platform.model.ProjectMetadata import ProjectMetadata
from m4i_analytics.m4i.platform.model.ProjectGroupsMember import ProjectGroupsMember
from m4i_analytics.m4i.platform.model.ProjectBranchesMember import ProjectBranchesMember


class Project(BaseModel):
    
    _fields = [
        ('_id', str, False)
        , ('id', str, False)
        , ('metadata', ProjectMetadata, False)
        , ('branches', ProjectBranchesMember, True)
        , ('groups', ProjectGroupsMember, True)
        , ('__v', int, False)
    ]
# END Project
