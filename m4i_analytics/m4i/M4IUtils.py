class M4IUtils():
    
    @staticmethod
    def construct_model_id(project_owner, project_name):
        
        """
        Returns a string formatted as a model ID based on the given project owner and project name
        
        :returns: A model id string
        :rtype: str
        
        :param str project_owner: The name of the owner of the project.
        :param str project_name: The name of the project.
        """
        
        if not project_owner:
            raise ValueError("Project owner should be defined!")
        elif not project_name:
            raise ValueError("Project name should be defined!")
        
        return "{0}__{1}".format(project_owner, project_name).replace(" ","_")
    # END construct_model_id