from m4i_analytics.m4i.portal.model.superset.slices.AbstractSlice import AbstractSlice


class ModelViewSlice(AbstractSlice):
    
    VIZ_TYPE = 'model_view'
    
    def _init_params(self
             , datasource=None
             , druid_datasource_id=None
             , filters=[]
             , granularity_sqla=None
             , groupby=[]
             , having=''
             ,  metrics=[]
             , since=''
             , slice_id = None
             , time_grain_sqla=None
             , until='now'
             , url_params=None
             , viz_type=None
             , where=''
             , *arg
             , **kwarg):
        self.filters = filters
        self.granularity_sqla = granularity_sqla
        self.having = having
        self.time_grain_sqla = time_grain_sqla
        self.since = since
        self.groupby = groupby
        self.metrics = metrics if metrics else []
        self.until = until
        self.where = where
    # END _init_params
    
    def columnNames(self):
        return list(set(super(ModelViewSlice, self).columnNames() + self.groupby))
    # END directColumnDependencies
    
# END ModelViewSlice