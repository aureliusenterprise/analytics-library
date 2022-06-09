import apache_log_parser
from pandas import DataFrame
from m4i_analytics.m4i.portal.DBUtils import DBUtils, InsertBehavior

if __name__ == '__main__':    
    
    log_path = '/var/log/apache2/other_vhosts_access.log.1'
    parser_string = '%v:%p %h %l %u %t \"%r\" %>s %O \"%{Referer}i\" \"%{User-Agent}i\"'
    api_prefixes = ('/api','/RestApi','/m4i/rest')
    
    parser = apache_log_parser.make_parser(parser_string)
    
    with open(log_path, 'r') as logfile:        
        parsed_logs = [parser(line) for line in logfile.readlines()]
    # END with
    
    dataframe = DataFrame(parsed_logs)
    api_requests = dataframe[dataframe['request_url_path'].str.startswith(api_prefixes)]
    groupby_cols = ['request_url', 'time_received_datetimeobj', 'remote_host', 'status']
    activity_log = api_requests.groupby(by=groupby_cols, as_index=False).size().reset_index()
    activity_log.columns = groupby_cols + ['count']
    
    #DBUtils.insert_dataset(DataFrame(parsed_logs), 'apache logs', if_exists=InsertBehavior.REPLACE)
# END if    
        
        
        