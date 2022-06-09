from typing import Iterable

from pandas import DataFrame

from auth_options import credentials
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import (
    ArchimateUtils, EdgeAttribute, NodeAttribute, ViewAttribute)
from m4i_analytics.graphs.languages.archimate.model.ArchimateModel import \
    ArchimateModel


def index_by_property(data: Iterable[dict], property_name: str):
    result = {}
    for row in data:
        key = row.get(property_name)
        if key is not None:
            result[key] = row
    # END LOOP
    return result
# END index_by_property

commit_options = {
    'projectName': 'test project 903290',
    'projectOwner': 'thijsfranck',
    'branchName': 'test12345',
    'userid': 'thijsfranck',
    'description': 'model from views test',
    'conflict_resolution_template': 'upload_only'
}

model_options = {
    'projectName': 'altran nutrucia',
    'projectOwner': 'dev',
    'branchName': 'tekdan as-is',
    'userid': 'thijsfranck'
}

selected_view_ids = [
    'id_1f8f164c-79d2-4ca8-b9f0-55c22ff8691d'
]

if __name__ == '__main__':

    # Retrieve a model from the repository
    model = ArchimateUtils.load_model_from_repository(
        **model_options,
        **credentials
    )

    def get_selected_views(views: DataFrame) -> Iterable[dict]:

        is_view_selected = views[
            model.getViewAttributeMapping(ViewAttribute.ID)
        ].isin(selected_view_ids)

        selected_views = views[is_view_selected]

        return selected_views.to_dict(orient='records')
    # END get_selected_views

    def filter_unselected_view_references(view_nodes: Iterable[dict]) -> Iterable[dict]:
        for node in view_nodes:
            is_unselected_view_reference = (
                'ar3_viewRef' in node
                and node['ar3_viewRef'] not in selected_view_ids
            )
            # Return the current node if it's not a view reference, or if the referenced view is one of the selected views
            if not is_unselected_view_reference:
                filtered_node = node
                # If the current node has children, filter them for unselected view references as well
                if 'ar3_node' in node:
                    filtered_subnodes = filter_unselected_view_references(
                        node['ar3_node']
                    )
                    filtered_node = {
                        **node,
                        'ar3_node': list(filtered_subnodes)
                    }
                # END IF
                yield filtered_node
            # END IF
        # END LOOP
    # END filter_unselected_view_references

    def format_views(selected_views: Iterable[dict]) -> Iterable[dict]:
        nodes_key = model.getViewAttributeMapping(ViewAttribute.NODES)
        for view in selected_views:
            filtered_nodes = filter_unselected_view_references(view[nodes_key])
            formatted_view = {
                **view,
                nodes_key: list(filtered_nodes)
            }
            yield formatted_view
        # END LOOP
    # END format_views

    def get_selected_view_nodes(selected_views: Iterable[dict]) -> Iterable[dict]:
        for view in selected_views:
            view_nodes = ArchimateUtils.get_view_nodes(view['nodes'])
            for node in view_nodes:
                yield node
            # END LOOP
        # END LOOP
    # END get_selected_view_nodes

    def get_selected_nodes(selected_view_nodes: Iterable[dict]) -> Iterable[dict]:

        nodes_by_id = index_by_property(
            model.nodes.to_dict(
                orient='records'
            ),
            model.getNodeAttributeMapping(NodeAttribute.ID)
        )

        def is_view_node_element_reference(view_node: dict) -> bool:
            return '@elementRef' in view_node
        # END is_view_node_element_reference

        view_elements = filter(
            is_view_node_element_reference, selected_view_nodes
        )

        for view_element in view_elements:
            node = nodes_by_id.get(view_element['@elementRef'])
            if node is not None:
                yield node
            # END IF
        # END LOOP

    # END get_selected_nodes

    def get_selected_edges(selected_node_ids: Iterable[str]) -> Iterable[dict]:

        source_key = model.getEdgeAttributeMapping(EdgeAttribute.SOURCE)
        target_key = model.getEdgeAttributeMapping(EdgeAttribute.TARGET)

        def is_edge_selected(edge: dict) -> bool:
            return edge[source_key] in selected_node_ids and edge[target_key] in selected_node_ids
        # END is_edge_selected

        return filter(is_edge_selected, model.edges.to_dict(orient='records'))
    # END get_selected_edges

    def get_selected_organization(selected_ids: Iterable[str]) -> DataFrame:
        is_selected_organization = model.organizations['idRef'].isin(
            selected_ids
        )
        return model.organizations[is_selected_organization]
    # END get_selected_organization

    selected_views = get_selected_views(model.views)

    formatted_views = list(format_views(selected_views))

    selected_view_nodes = get_selected_view_nodes(selected_views)

    selected_nodes = get_selected_nodes(selected_view_nodes)

    selected_nodes_by_id = index_by_property(
        selected_nodes,
        model.getNodeAttributeMapping(NodeAttribute.ID)
    )

    selected_edges = get_selected_edges(selected_nodes_by_id.keys())

    selected_edges_by_id = index_by_property(
        selected_edges,
        model.getEdgeAttributeMapping(EdgeAttribute.ID)
    )

    selected_organization = get_selected_organization([
        *selected_view_ids,
        *selected_nodes_by_id.keys(),
        *selected_edges_by_id.keys()
    ])

    filtered_model = ArchimateModel(
        nodes=DataFrame(selected_nodes_by_id.values()),
        edges=DataFrame(selected_edges_by_id.values()),
        views=DataFrame(formatted_views),
        organizations=selected_organization,
        defaultAttributeMapping=True
    )

    ArchimateUtils.commit_model_to_repository_with_conflict_resolution(
        model=filtered_model,
        **commit_options,
        **credentials
    )
# END IF
