from m4i_analytics.shared.model.BaseModel import BaseModel
from m4i_analytics.m4i.platform.model.DataContent import DataContent


class MetricExemption(BaseModel):

    _fields = [
        ("branch", str, False),
        ("comment", str, False),
        ("concept_id", str, False),
        ("id", str, False),
        ("metric", str, False),
        ("project_id", str, False),
        ("version", int, False),
        ("userid", str, False),
        ("start_date", int, False),
    ]

# END MetricExemption
