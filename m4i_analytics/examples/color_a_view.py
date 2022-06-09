from random import randrange

from m4i_analytics.graphs.languages.archimate.ArchimateUtils import \
    ArchimateUtils

if __name__ == '__main__':

    model_options = {
        'projectName': 'altran nutrucia',
        'projectOwner': 'dev',
        'branchName': 'tekdan as-is',
        'userid': 'thijsfranck'
    }

    auth_options = {
        'username': 'example',
        'password': 'example'
    }
    from auth_options import auth_options

    # Retrieve a model from the repository
    model = ArchimateUtils.load_model_from_repository(
        **model_options, **auth_options)

    # Select a view
    example_view = model.views.iloc[0]

    # Assign each node in the view a random background color. Colors are specified
    # as RGB values between 0 and 255.
    def random_color() -> (int, int, int):
        return (
            randrange(256),
            randrange(256),
            randrange(256)
        )
    # END random_color

    colored_nodes = [ArchimateUtils.color_view_node(
        node, *random_color()) for node in example_view['nodes']]

    # Assign the colored nodes to the view
    example_view['nodes'] = colored_nodes

    # Convert the model to back to json to see the result
    json_model = ArchimateUtils.to_JSON(model)
