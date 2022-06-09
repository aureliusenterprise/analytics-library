from m4i_analytics.shared.model.BaseModel import BaseModel
from m4i_analytics.m4i.platform.model.ProjectMember import ProjectMember
from m4i_analytics.m4i.platform.model.Permission import Permission
from m4i_analytics.m4i.platform.model.PortalDashboards import PortalDashboards


class UserRole(BaseModel):
    
    _fields = [
        ('userid', str, False)
        , ('project', str, False)
        , ('email', str, False)
        , ('role_name', str, False)
        , ('role_id', int, False)
    ]
# END Project
