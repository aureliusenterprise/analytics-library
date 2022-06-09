from m4i_analytics.graphs.languages.archimate.metamodel.Concepts import ElementType, RelationshipType
from m4i_analytics.graphs.model.Graph import EdgeAttribute, NodeAttribute
from m4i_analytics.graphs.languages.archimate.ArchimateUtils import ArchimateUtils
from m4i_analytics.m4i.portal.DBUtils import DBUtils, InsertBehavior

import networkx as nx
import copy
from pandas import concat, DataFrame


SOURCE_ID_PREFIX = 'oms_equ_'
TARGET_ID_PREFIX = 'superset_dashboard-'

# Index node attributes so we don't have to look them up every time
node_status_index = {}
node_name_index = {}

def get_nodes(model):

    data = model.data.to_dict(orient='records')
    node_ids = model.nodes[model.getNodeAttributeMapping(NodeAttribute.ID)].tolist()

    sources = (item['id'] for item in data if SOURCE_ID_PREFIX in item['data'].get('m4i_id_prefix', '') and item['id'] in node_ids)
    targets = (item['id'] for item in data if TARGET_ID_PREFIX in item['data'].get('m4i_original_id', '') and item['id'] in node_ids)

    return sources, targets
# END get_nodes

def prepare_model(model, allowed_relationship_types):

    # Create a working copy of the model so we don't modify the original
    working_copy = copy.deepcopy(model)

    # Translate all junctions into actual nodes and edges
    junctions = working_copy.nodes[working_copy.nodes['type'].isin([ElementType.AND_JUNCTION, ElementType.OR_JUNCTION])]

    transition_matrix = ArchimateUtils.toTransitionMatrix(working_copy)
    junction_sources = transition_matrix[transition_matrix['target'].isin(junctions['id'])].to_dict(orient='records')
    junction_targets = transition_matrix[transition_matrix['source'].isin(junctions['id'])].to_dict(orient='records')

    junction_bypasses = [{'id': '{0}-{1}'.format(source['source'], target['target'])
                             , 'source': source['source']
                             , 'target': target['target']
                             , 'type': source['type'] # Assume the type of the relation going into the junction
                             , 'name': ''
                             , 'label': ''
                             , 'weight': 3
                          } for source in junction_sources for target in junction_targets]

    working_copy.edges = working_copy.edges.append(junction_bypasses)

    # Remove all junctions from the model
    working_copy.nodes = working_copy.nodes[~working_copy.nodes['type'].isin([ElementType.AND_JUNCTION, ElementType.OR_JUNCTION])]
    working_copy.edges = working_copy.edges[~working_copy.edges['source'].isin(junctions['id']) & ~working_copy.edges['target'].isin(junctions['id'])]

    # Filter out all relationship types that are not allowed
    edge_type_key = working_copy.getEdgeAttributeMapping(EdgeAttribute.TYPE)

    if allowed_relationship_types:
        working_copy.edges = working_copy.edges[working_copy.edges[edge_type_key].isin(allowed_relationship_types)]

    # Apply a default weight to all edges we didn't assign one to already
    working_copy.edges['weight'] = working_copy.edges['weight'].fillna(1)

    return working_copy
# END prepare_model


def get_paths(model, sources, targets):

    def get_routes(nxgraph, route_source, route_target):

        def node_status(id_):

            status = node_status_index.get(id_)

            if status is None:

                # Retrieve the data for this node from the model
                data = next(iter(model.data[model.data.id == id_].to_dict(orient='records')), {})\
                    .get('data', {})

                # Aggregate the node status to a single value and return it
                status = max(data.get('combined_service', 0)
                             , data.get('combined_processing', 0)
                             , data.get('combined_data_in', 0)
                             , data.get('combined_data_out', 0))

                node_status_index[id_] = status
            # END IF

            return status
        # END node_status

        # Calculate the shortest path from source to target.
        # This generates a list of paths including all nodes that are passed.
        # Return the set of routes between the source and the target along with the status of each node in these routes
        # , or an empty list of no routes are found
        try:
            for path in nx.all_shortest_paths(nxgraph, route_source, route_target, weight='weight'):
                yield {'origin': source_id
                        , 'destination': target_id
                        , 'path': ({'id': id_, 'status': node_status(id_)}
                    for id_ in path)}
        except nx.exception.NetworkXNoPath:
            yield {'origin': source_id
                   , 'destination': target_id
                   , 'path': iter([])}
    # END get_routes

    # Transform the graph for use with the nx library
    nxgraph = ArchimateUtils.toNXGraph(model)

    all_targets = list(targets)

    for source_id in sources:
        for target_id in all_targets:
            yield get_routes(nxgraph, source_id, target_id)
        # END LOOP
    # END LOOP
# END get_paths


def fmt_path(model, path):

    def fmt_name(id_):

        # Appends a number corresponding to the name of a node to ensure it's uniqueness.
        # The value corresponds to the current number of occurrences of that name.
        def uniqueify(n, appendage=2):
            result = '{0} {1}'.format(n, appendage)
            if result in node_name_index.values():
                result = uniqueify(n, appendage + 1)
            return result
        # END uniqueify

        name = node_name_index.get(id_)

        if name is None:

            node_id_key = model.getNodeAttributeMapping(NodeAttribute.ID)
            node_name_key = model.getNodeAttributeMapping(NodeAttribute.NAME)

            name = next(iter(model.nodes[model.nodes[node_id_key] == id_].to_dict(orient='records')), {})\
                .get(node_name_key, '')

            if name in node_name_index.values():
                name = uniqueify(name)

            node_name_index[id_] = name
        # END IF

        return name
    # END node_name

    def fmt_status(value):
        mapping = {
            1: 'OK',
            2: 'WARN',
            3: 'CRIT'
        }
        return mapping.get(value, 'UNK')
    # END fmt_status
    prev_node = next(path['path'], {}) # Placeholder value in case the path is empty
    for node in path['path']:
        yield {
            'path_origin': '{0} {1}'.format(fmt_name(path['origin']), fmt_status(path['origin']))
            , 'path_destination': '{0} {1}'.format(fmt_name(path['destination']), fmt_status(path['destination']))
            , 'source': '{0} {1}'.format(fmt_name(prev_node['id']), fmt_status(prev_node['status']))
            , 'target': '{0} {1}'.format(fmt_name(node['id']), fmt_status(node['status']))
            , 'status': fmt_status(prev_node['status'])
        }
        prev_node = node
    # END LOOP
# END superset_format

if __name__ == '__main__': 
    
    model_options = {
        'projectOwner': 'dev'
        , 'projectName': 'test3000'
        , 'branchName': 'propagation5'
        , 'userid': 'thijsfranck'
    }
    
    allowed_relationship_types = [
        RelationshipType.ACCESS_READ
        , RelationshipType.ACCESS_WRITE
        , RelationshipType.ACCESS_READ_WRITE
        , RelationshipType.ACCESS_ACCESS
        , RelationshipType.COMPOSITION
        , RelationshipType.SERVING
        , RelationshipType.TRIGGERING
    ]
    
    # Load the model from the repository
    model = ArchimateUtils.load_model_from_repository(withData=True, **model_options)
    
    # Get the id's of the nodes between which we should calculate the paths
    sources, targets = get_nodes(model)
    
    # Prepare the model
    prepared_model = prepare_model(model, allowed_relationship_types)
    
    # Calculate the paths
    paths = get_paths(prepared_model, sources, targets)
    
    # Format the paths
    paths_fmt = DataFrame((step for routes in paths for route in routes for step in fmt_path(prepared_model, route)))
    
    # Aggregate the paths
    paths_grp = paths_fmt.groupby(['source', 'target', 'path_origin', 'path_destination', 'status']).size().reset_index(name='counts')
    
    # Insert the paths into the database
    DBUtils.insert_dataset(paths_grp, 'thijsfranck__paths_test_342526', if_exists=InsertBehavior.REPLACE)
