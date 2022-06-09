from m4i_analytics.m4i.platform.PlatformUtils import PlatformUtils


if __name__ == '__main__':
    
    '''
    This example shows you how to retrieve the history of a project via the m4i api
    '''
    
    model_options = {
        'project_name': 'Example Factory',
        'project_owner': 'thijsfranck'
    }
    
    #Retrieves the provenance of an example model and prints it to the console
    provenance = PlatformUtils.retrieve_model_provenance(**model_options)
    
    for p in provenance:
        print('Run by: {0}\nBranch name: {1}\nOperation type: {2}\nComment: {3}\nTimestamp: {4}\n'.format(p.start_user, p.branch, p.operation, p.comment, p.start_date))