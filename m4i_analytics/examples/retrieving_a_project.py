from m4i_analytics.m4i.platform.PlatformApi import PlatformApi


if __name__ == '__main__':
    
    '''
    This example shows you how to use the m4i platform api to retrieve information about a project.
    
    The script below retrieves a public project and prints some of its details to the console.
    
    The project ID used for this function can be found at the end of the url when your project is opened in the browser.
    '''
    
    projectOptions = {
        'projectid': '5af95bd8a434150ea364fb56'
    }
    
    #Retrieves a project and prints some details about it to the console
    project = PlatformApi.retrieve_project(**projectOptions)
    
    print('Project id: {0}\nOwner: {1}\nMembers: {2}\nDescription: {3}\nCreated on: {4}'.format(project.id, project.committer.username, list(map(lambda r: list(map(lambda u: u.username, r.users)), project.rights)), project.documentation, project.start_date))