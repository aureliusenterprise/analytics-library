import copy
import json
import uuid
import warnings
import xml.etree.ElementTree as ET
from enum import Enum
from itertools import chain
from typing import Iterable, List, Optional, Tuple

import numpy as np
from pandas import DataFrame

from m4i_analytics.graphs.GraphUtils import GraphUtils
from m4i_analytics.graphs.languages.archimate.metamodel.Archi import \
    ArchiElement
from m4i_analytics.graphs.languages.archimate.metamodel.Concepts import (
    ElementType, RelationshipType)
from m4i_analytics.graphs.languages.archimate.model.ArchimateModel import (
    ArchimateModel, ViewAttribute)
from m4i_analytics.graphs.model.Graph import EdgeAttribute, NodeAttribute
from m4i_analytics.graphs.visualisations.model.Layout import Layout
from m4i_analytics.m4i.M4IUtils import M4IUtils
from m4i_analytics.m4i.platform.PlatformApi import PlatformApi
from m4i_analytics.m4i.platform.PlatformUtils import PlatformUtils


class ModelFormat(Enum):

    """
    Each entry corresponds to a format in which a model can be encoded. XML corresponds to the Open Group XML Exchange format.
    """

    ARCHI = "archimate"
    JSON = "json"
    XML = "xml"
# END ModelFormat


class ArchimateUtils(GraphUtils):

    PARSER_NAME = "archimate3"

    @staticmethod
    def retrieve_model(branchName, userid, projectOwner=None, projectName=None, fullProjectName=None, modelId='TRUNK', withViews=True, version=None, format=ModelFormat.JSON, username=None, password=None, totp=None, access_token=None):
        """
        Retrieves a raw model string in the specified format from the repository, matching the parameters provided.

        :returns: A raw model string of the model that matches the parameters provided.
        :rtype: str

        :param str branchName: The specific branch of the model you wish to retrieve.
        :param str userid: The name of the user performing this action.
        :param str projectOwner: *Optional*. The username of the owner of the project containing the model. You need to supply either this and the project name, or the full project name. Defaults to None.
        :param str projectName: *Optional*. The name of the project containing the model. You need to supply either this and the project owner, or the full project name. Defaults to None.
        :param str fullProjectName: *Optional*. The fully qualified name of the project as you might have retrieved it from the repository. You need to supply either this, or the project owner and project name. Defaults to None.
        :param boolean withViews: *Optional*. Indicating whether the retrieved model should contain views. For analysis of the model, the views are often not used for analysis, thus can be omitted when downloading the model.
        :param long version: *Optional*.The version of the model you wish to retrieve. If you leave this empty, you retrieve the latest version. Is empty by default.
        :param ModelFormat format: *Optional*. The format in which you wish to retrieve the model. Defaults to ModelFormat.JSON.

        :exception TypeError: Thrown when any of the parameters (excluding version) is not defined.
        :exception ValueError: Thrown when any of the parameters is not valid.
        :exception requests.exceptions.HTTPError: Thrown when the request returned with a 400/500 code variant.
        """

        if isinstance(format, ModelFormat):
            format = format.value

        if fullProjectName is None:
            fullProjectName = M4IUtils.construct_model_id(
                projectOwner, projectName)

        result = PlatformApi.retrieve_model(
            branchName,
            fullProjectName,
            userid,
            withViews=withViews,
            version=version,
            contentType=format,
            parserName=ArchimateUtils.PARSER_NAME,
            username=username,
            password=password,
            totp=totp,
            access_token=access_token
        )

        return result
    # END retrieve_model

    @staticmethod
    def _load_name(model, format=ModelFormat.JSON):

        name = None

        if isinstance(format, ModelFormat):
            format = format.value

        if format == ModelFormat.JSON.value:
            root = model["ar3_model"]
            name = "Archimate model"
            try:
                name = root["ar3_name"][0]["value"]
            except:
                pass

        elif format == ModelFormat.ARCHI.value:
            pass

        elif format == ModelFormat.XML.value:
            pass

        return name
    # END _load_name

    @staticmethod
    def _load_elements(model, format=ModelFormat.JSON):

        nodes = None

        if isinstance(format, ModelFormat):
            format = format.value

        if format == ModelFormat.JSON.value:

            def load_type(n):

                # First, try to get the type from the ArchiMate metamodel
                result = ElementType.getElementByTag(n["@xsi_type"])

                # If no match was found, check whether we're dealing with an Archi-specific element
                if result is None:
                    result = ArchiElement.getElementByTag(n["@xsi_type"])

                # If still no match is found, issue a warning to the user
                if result is None:
                    warnings.warn('Type {0} of node {1} is not recognized. Therefore, the node will not be included in the loaded model.'.format(
                        n["@xsi_type"], n["@identifier"]))

                return result
            # END load_type

            root = model["ar3_model"]
            elems = root["ar3_elements"]["ar3_element"]

            nodes = list(map(lambda n: {
                "id": n["@identifier"],
                "name": n["ar3_name"][0]["value"] if "ar3_name" in n else "",
                "label": n["ar3_name"][0]["value"] if "ar3_name" in n else "",
                "type": load_type(n)
            }, elems))

            nodes = [node for node in nodes if node['type'] is not None]

        elif format == ModelFormat.ARCHI.value:
            pass
        elif format == ModelFormat.XML.value:
            pass

        result = DataFrame(nodes)

        return result
    # END _load_elements

    @staticmethod
    def _load_relationships(model, format=ModelFormat.JSON):

        def fmt_attributes(relationship):
            result = {}
            if relationship["@xsi_type"] == RelationshipType.ACCESS['tag']:
                result['accessType'] = relationship.get(
                    '@accessType', RelationshipType.ACCESS_ACCESS['attributes']['accessType'])
            elif relationship["@xsi_type"] == RelationshipType.ASSOCIATION['tag'] and '@isDirected' in relationship:
                result['isDirected'] = relationship['@isDirected']
            # END IF
            return result
        # END fmt_attributes

        edges = None

        if isinstance(format, ModelFormat):
            format = format.value

        if format == ModelFormat.JSON.value:

            def load_type(r):
                result = RelationshipType.getRelationshipByTag(
                    r["@xsi_type"], fmt_attributes(r))
                if not result:
                    warnings.warn('Type {0} of relationship {1} is not recognized. Therefore, the relationship will not be included in the loaded model.'.format(
                        r["@xsi_type"], r["@identifier"]))
                return result
            # END load_type

            root = model["ar3_model"]
            rels = root["ar3_relationships"]["ar3_relationship"]

            edges = list(map(lambda r: {
                "id": r["@identifier"],
                "name": r["ar3_name"][0]["value"] if "ar3_name" in r else "",
                "label": r["ar3_name"][0]["value"] if "ar3_name" in r else "",
                "source": r["@source"],
                "target": r["@target"],
                "type": load_type(r),
                "is_bidirectional": False
            }, rels))

            edges = [edge for edge in edges if edge['type'] is not None]

        elif format == ModelFormat.ARCHI.value:
            pass
        elif format == ModelFormat.XML.value:
            pass

        result = DataFrame(edges)

        return result
    # END _load_relationships

    @staticmethod
    def _load_views(model, format=ModelFormat.JSON):

        viewset = None

        if isinstance(format, ModelFormat):
            format = format.value

        if format == ModelFormat.JSON.value:

            root = model["ar3_model"]
            views = root["ar3_views"]["ar3_diagrams"]["ar3_view"]

            def view_mapper(view):

                result = {
                    "id": view["@identifier"],
                    "name": view["ar3_name"][0]["value"] if "ar3_name" in view else "",
                    "type": view["@xsi_type"],
                    "connections": None,
                    "nodes": None,
                    "properties": None
                }

                if "ar3_connection" in view:
                    result["connections"] = view["ar3_connection"]

                if "ar3_node" in view:
                    result["nodes"] = view["ar3_node"]

                if "ar3_properties" in view and "ar3_property" in view["ar3_properties"]:
                    result["properties"] = view["ar3_properties"]["ar3_property"]

                return result
            # END view_mapper

            viewset = list(map(lambda view: view_mapper(view), views))

        elif format == ModelFormat.ARCHI.value:
            pass
        elif format == ModelFormat.XML.value:
            pass

        result = DataFrame(viewset)

        return result
    # END _load_views

    @staticmethod
    def _load_organizations(model, format=ModelFormat.JSON):

        organizations = None

        if isinstance(format, ModelFormat):
            format = format.value

        if format == ModelFormat.JSON.value:

            root = model["ar3_model"]
            orgs = root["ar3_organizations"]

            def organization_mapper(organization, levels={}, depth=0):

                result = []
                levels = levels.copy()
                
                keys = organization.keys()

                if "ar3_label" in keys:
                    levels["level" +
                           str(depth)] = organization["ar3_label"][0]["value"]

                if "ar3_item" in keys:
                    result += [item for list in map(lambda o: organization_mapper(
                        o, levels, depth + 1), organization["ar3_item"]) for item in list]

                if "@identifierRef" in keys:
                    result.append(
                        dict(idRef=organization["@identifierRef"], **levels))

                return result
            # END organization_mapper

            organizations = [item for list in map(
                lambda o: organization_mapper(o), orgs) for item in list]

        elif format == ModelFormat.ARCHI.value:
            pass
        elif format == ModelFormat.XML.value:
            pass

        result = DataFrame(organizations)

        # This adds a none column to the end of the dataframe to make sure that the organization can also be exported again consistently as JSON
        result['level'+str(len(list(result.columns)))] = None
        # somehow sometimes there get nan values instead of None values. However, further processing expects None values.
        # nan values produce a lot of extra folders and result in problems with RestApi
        result = result.applymap(lambda x: x if x == x else None)

        return result
    # END _load_organizations

    @staticmethod
    def load_model(raw_model, raw_data=None, withViews=True, format=ModelFormat.JSON):
        """
        Loads the provided raw model (as retrieved from the repository) into an ArchimateModel instance, which provides separate Pandas Dataframes of the nodes, edges, views and organizations in your model.

        :returns: An ArchimateModel instance containing the nodes, edges, views and organizations from the provided model as separate Pandas Dataframes.
        :rtype: ArchimateModel

        :param str raw_model: The unparsed model string as retrieved from the repository
        :param DataRetrieve raw_data: The unparsed data as retrieved from the repository
        :param ModelFormat format: The format in which you retrieved the model. This needs to match the actual format of the model for the loading to complete successfully.

        :exception ValueError: Thrown when the raw model could not be parsed as the expected format.
        """

        model = None

        if isinstance(format, ModelFormat):
            format = format.value

        if format == ModelFormat.JSON.value:
            model = json.loads(raw_model)

        elif format == ModelFormat.ARCHI.value or format == ModelFormat.XML.value:
            model = ET.fromstring(raw_model)

        result = ArchimateModel(**{
            "name": ArchimateUtils._load_name(model, format),
            "nodes": ArchimateUtils._load_elements(model, format),
            "edges": ArchimateUtils._load_relationships(model, format),
            "views": ArchimateUtils._load_views(model, format) if withViews else DataFrame(columns=["id", "name", "type", "nodes", "connections", "properties"]),
            "organizations": ArchimateUtils._load_organizations(model, format),
            "defaultAttributeMapping": True
        })

        if raw_data:
            GraphUtils.loadGraphData(result, raw_data)

        return result
    # END load_model

    @staticmethod
    def load_model_from_repository(branchName, userid, projectOwner=None, projectName=None, fullProjectName=None, modelId='TRUNK', version=None, format=ModelFormat.JSON, withData=False, withViews=True, username=None, password=None, totp=None, access_token=None):
        """
        Retrieves a model matching the parameters provided from the repository and loads it into an ArchimateModel instance

        :returns: An ArchimateModel instance containing the nodes and relationships from the provided model as separate Pandas Dataframes.
        :rtype: ArchimateModel

        :param str branchName: The specific branch of the model you wish to retrieve.
        :param str userid: The name of the user performing this action.
        :param str projectOwner: *Optional*. The username of the owner of the project containing the model. You need to supply either this and the project name, or the full project name. Defaults to None.
        :param str projectName: *Optional*. The name of the project containing the model. You need to supply either this and the project owner, or the full project name. Defaults to None.
        :param str fullProjectName: *Optional*. The fully qualified name of the project as you might have retrieved it from the repository. You need to supply either this, or the project owner and project name. Defaults to None.
        :param long version: *Optional*.The version of the model you wish to retrieve. If you leave this empty, you retrieve the latest version. Is empty by default.
        :param ModelFormat format: *Optional*. The format in which you wish to retrieve the model. Defaults to ModelFormat.JSON.

        :exception TypeError: Thrown when any of the parameters (excluding version) is not defined.
        :exception ValueError: Thrown when any of the parameters is not valid.
        :exception requests.exceptions.HTTPError: Thrown when the request returned with a 400/500 code variant.
        """

        model = ArchimateUtils.retrieve_model(branchName, userid, projectOwner, projectName,
                                              fullProjectName, modelId, withViews, version, format, username=username, password=password, totp=totp, access_token=access_token)

        data = PlatformUtils.retrieve_data(projectOwner=projectOwner, projectName=projectName, fullProjectName=fullProjectName,
                                           modelId=modelId, branchName=branchName, parserName='archimate3', username=username, password=password, totp=totp, access_token=access_token) if withData else None

        return ArchimateUtils.load_model(model, raw_data=data, format=format, withViews=withViews)
    # END load_model

    @staticmethod
    def to_JSON(model):
        """
        Converts an archimate model to a JSON string that can be ingested by the M4I repository.

        :returns: A JSON string representing the given model.
        :rtype: str

        :param ArchimateModel model: The model you want to convert to a JSON string.
        """

        def format_element(id_, type_, name):
            return {'@identifier': id_, '@xsi_type': type_['tag'], 'ar3_name': [{'@xml_lang': 'en', 'value': str(name)}]}
        # END format_element

        def format_relationship(id_, type_, name, source, target):
            result = {'@identifier': id_, '@target': target, '@source': source, '@xsi_type': type_[
                'tag'], 'ar3_name': [{'@xml_lang': 'en', 'value': str(name)}]}
            if type_.is_instance_of(RelationshipType.ACCESS):
                result['@accessType'] = type_['attributes']['accessType']
            if type_.is_instance_of(RelationshipType.ASSOCIATION):
                result['@isDirected'] = type_['attributes']['isDirected']
            return result
        # END format_relationship

        def format_view(id_, type_, nodes, connections, name):
            return {'@identifier': id_, '@xsi_type': type_, 'ar3_node': nodes if nodes is not None else [], 'ar3_connection': connections if connections is not None else [], 'ar3_name': [{'@xml_lang': 'en', 'value': str(name)}]}
        # END format_view

        def format_organizations(orgs):

            levels = [
                colname for colname in orgs if colname.startswith('level')]
            levels.sort()

            root = {'ar3_item': []}

            def find_item(root, name):
                return next((item for item in root['ar3_item'] if next(iter(item.get('ar3_label', [])), {}).get('value') == name), None)
            # END find_item

            def format_label(name):
                return {'ar3_label': [{'@xml_lang': 'en', 'value': str(name)}], 'ar3_item': []}
            # END format_label

            def format_item(id):
                return {'@identifierRef': id}
            # END format_item

            def parse_organization(org, current_root=root, depth=0):

                name = org[levels[depth]]

                if name and depth < (len(levels) - 1):

                    item = find_item(current_root, name)

                    if not item:
                        item = format_label(name)
                        current_root['ar3_item'].append(item)

                    parse_organization(org, item, depth + 1)
                else:
                    current_root['ar3_item'].append(format_item(org['idRef']))
            # END parse_organization

            for org in orgs.to_dict(orient='records'):
                parse_organization(org)
            # END LOOP

            return [root]
        # END format_organization

        elems = [format_element(row[model.getNodeAttributeMapping(NodeAttribute.ID)], row[model.getNodeAttributeMapping(
            NodeAttribute.TYPE)], row[model.getNodeAttributeMapping(NodeAttribute.NAME)]) for row in model.nodes.to_dict(orient='records')]

        relations = [format_relationship(row[model.getEdgeAttributeMapping(EdgeAttribute.ID)], row[model.getEdgeAttributeMapping(EdgeAttribute.TYPE)], row[model.getEdgeAttributeMapping(
            EdgeAttribute.NAME)], row[model.getEdgeAttributeMapping(EdgeAttribute.SOURCE)], row[model.getEdgeAttributeMapping(EdgeAttribute.TARGET)]) for row in model.edges.to_dict(orient='records')]

        views = [format_view(row[model.getViewAttributeMapping(ViewAttribute.ID)], row[model.getViewAttributeMapping(ViewAttribute.TYPE)], row[model.getViewAttributeMapping(
            ViewAttribute.NODES)], row[model.getViewAttributeMapping(ViewAttribute.CONNECTIONS)], row[model.getViewAttributeMapping(ViewAttribute.NAME)]) for row in model.views.to_dict(orient='records')]

        organizations = format_organizations(model.organizations)

        model_dict = {'ar3_model': {'@identifier': str(model.name), 'ar3_name': [{'@xml_lang': 'en', 'value': str(model.name)}], 'ar3_elements': {
            'ar3_element': elems}, 'ar3_relationships': {'ar3_relationship': relations}, 'ar3_views': {'ar3_diagrams': {'ar3_view': views}}, 'ar3_organizations': organizations}}

        return json.dumps(model_dict)
    # END to_JSON

    @staticmethod
    def generate_view(model: ArchimateModel, view_id: str = None, nodes: List[str] = None, edges: List[str] = None, viewpoint: str = None, layout: Layout = None, name: str = 'Generated view', coords: dict = {}, labels: List = [], node_width: int = 120, node_height: int = 55, path: List[str] = ['Generated views']):
        """
        Generate a view containing the given nodes.

        :returns: The generated view keyed by the attribute mappings of the model.

        :param ArchimateModel model: The model for which you want to generate a view.
        :param list nodes: *Optional*. A list of node ids. If given, only includes these nodes in the view. If None, includes all nodes in the view. By default, is None.
        :param list edges: *Optional*. A list of edge ids. If given, only includes these edges in the view. If None, includes all edges between the selected nodes in the view. By default, is None.
        :param any viewpoint: *Optional*. The viewpoint which should be applied to the view. If you select a viewpoint, only those nodes that fit the viewpoint will be included in the view. If None, does not apply a viewpoint. By default, is None.
        :param Layout layout: *Optional*. The layout which to apply to the nodes. This affects the coordinates of the nodes in your view. By default, is Layout.RANDOM.
        :param str name: *Optional*. The name of the view.
        :param dict coords: *Optional*. A dictionary of the positions per node for use with the manual layout option.
        """

        if not view_id:
            view_id = str(uuid.uuid4())

        def find_viewnodes(viewnodes, nodeid):
            return [viewnode["@identifier"] for viewnode in viewnodes if viewnode["@elementRef"] == nodeid]
        # END find_viewnodes

        def format_view(viewid, nodes, edges):
            return {
                model.getViewAttributeMapping(ViewAttribute.ID): viewid,
                model.getViewAttributeMapping(ViewAttribute.TYPE): "ar3_Diagram",
                model.getViewAttributeMapping(ViewAttribute.NAME): name,
                model.getViewAttributeMapping(ViewAttribute.NODES): nodes,
                model.getViewAttributeMapping(ViewAttribute.CONNECTIONS): edges,
                model.getViewAttributeMapping(ViewAttribute.PROPERTIES): []
            }
        # END format_view

        def format_label(label):
            return {
                "@identifier": label['id'],
                "@x": label['x'],
                "@y": label['y'],
                "@w": label['width'],
                "@h": label['height'],
                "@xsi_type": "ar3_Label",
                "@textAlignment": 1,
                "ar3_label": [{
                    "@xml_lang": "en",
                    "value": label["name"]
                }]
            }
        # END format_label

        def format_node(view_id, nodeid, x, y, w, h, ii=1):
            return {
                "@identifier": '%s-%s--%d' % (view_id, nodeid, ii),
                "@x": x,
                "@y": y,
                "@w": w,
                "@h": h,
                "@elementRef": nodeid,
                "@xsi_type": "ar3_Element"
            }
        # END format_node

        def format_edge(view_id, edgeid, sourceid, targetid, ii=1):
            return {
                "@identifier": '%s-%s--%d' % (view_id, edgeid, ii),
                "@source": sourceid,
                "@target": targetid,
                "@relationshipRef": edgeid,
                "@xsi_type": "ar3_Relationship",
            }
        # END format_edge

        viewmodel = copy.deepcopy(model)

        if nodes:
            viewmodel.nodes = viewmodel.nodes[viewmodel.nodes[viewmodel.getNodeAttributeMapping(
                NodeAttribute.ID)].isin(nodes)]

            viewmodel.edges = viewmodel.edges[np.logical_and(viewmodel.edges[viewmodel.getEdgeAttributeMapping(EdgeAttribute.SOURCE)].isin(viewmodel.nodes[viewmodel.getNodeAttributeMapping(NodeAttribute.ID)]),
                                                             viewmodel.edges[viewmodel.getEdgeAttributeMapping(EdgeAttribute.TARGET)].isin(viewmodel.nodes[viewmodel.getNodeAttributeMapping(NodeAttribute.ID)]))]
        if edges:
            viewmodel.edges = viewmodel.edges[viewmodel.edges[viewmodel.getEdgeAttributeMapping(
                EdgeAttribute.ID)].isin(edges)]

        coords = layout.get_coordinates(
            viewmodel, coords=coords, node_width=node_width, node_height=node_height)

        viewlabels = [format_label(label) for label in labels]
        viewnodes = []
        ii = 0
        for key in coords.keys():
            node_ref = next(iter(model.nodes[model.nodes[model.getNodeAttributeMapping(
                NodeAttribute.ID)] == key].to_dict(orient='records')), {})
            node_type = node_ref.get(
                model.getNodeAttributeMapping(NodeAttribute.TYPE))
            # Make an exception for junctions..
            viewnodes.append(format_node(view_id, key, int(round(float(coords[key][0]))), int(round(float(coords[key][1]))), node_width if not node_type in [
                             ElementType.JUNCTION, ElementType.AND_JUNCTION, ElementType.OR_JUNCTION] else 14, node_height if not node_type in [ElementType.JUNCTION, ElementType.AND_JUNCTION, ElementType.OR_JUNCTION] else 14, ii))
            ii = ii + 1
        # END LOOP

        viewedges = []
        ii = 0
        for viewedge in viewmodel.edges.to_dict(orient='records'):

            edgeid = viewedge[viewmodel.getEdgeAttributeMapping(
                EdgeAttribute.ID)]
            sources = find_viewnodes(
                viewnodes, viewedge[viewmodel.getEdgeAttributeMapping(EdgeAttribute.SOURCE)])
            targets = find_viewnodes(
                viewnodes, viewedge[viewmodel.getEdgeAttributeMapping(EdgeAttribute.TARGET)])

            for source in sources:
                for target in targets:
                    viewedges.append(format_edge(
                        view_id, edgeid, source, target, ii))
                    ii = ii + 1
                # END LOOP
            # END LOOP
        # END LOOP

        view = format_view(view_id, viewlabels + viewnodes, viewedges)
        model.views = model.views.append(view, ignore_index=True)

        organization_path = {'idRef': view_id}

        for index, level in enumerate(path):
            organization_path['level%s' % str(index + 1)] = level
        # END LOOP

        organization_path['level%s' % str(len(path) + 1)] = None

        model.organizations = model.organizations.append(
            organization_path, ignore_index=True)
        model.organizations.fillna('')

        return view
    # END generate_view

    @staticmethod
    def sliceByEdgeType(model, edge_types):
        """
        Slice a model by the specified edge types. The resulting model will contain only these edge types, as well as any nodes connected by these edges.

        :returns: A model sliced by the specified edge types
        :rtype: ArchimateModel

        :param list edge_types: A list of the edge types to slice by
        """

        relationships = model.edges
        rels = relationships[relationships.type.isin(edge_types)]

        elem_ids = list(rels.source.unique()) + list(rels.target.unique())
        elements = model.nodes
        elems = elements[elements.id.isin(elem_ids)]

        organizations = model.organizations
        orgs = organizations[organizations.idRef.isin(elem_ids)]

        return ArchimateModel(**{
            "name": model.name+' slice for '+str(edge_types),
            "nodes": elems,
            "edges": rels,
            "views": DataFrame(columns=['id', 'name', 'type', 'connections', 'nodes', 'properties']),
            "organizations": orgs,
            "defaultAttributeMapping": True
        })
    # END sliceByEdgeType

    @staticmethod
    def slicebyNodeType(model, node_types):
        """
        Slice a model by the specified node types. The resulting model will contain only these node types, as well as any edges connecting these nodes.

        :returns: A model sliced by the specified node types
        :rtype: ArchimateModel

        :param list edge_types: A list of the node types to slice by
        """

        nodes = model.nodes
        sliced_nodes = nodes[nodes.type.isin(node_types)]

        relations = model.edges
        sliced_relations = relations[relations.source.isin(
            sliced_nodes.id) or relations.target.isin(sliced_nodes.id)]

        organizations = model.organizations
        sliced_organizations = organizations[organizations.idRef.isin(
            sliced_nodes.id)]

        return ArchimateModel(**{
            "name": model.name+' slice for '+str(node_types),
            "nodes": sliced_nodes,
            "edges": sliced_relations,
            "views": DataFrame(columns=['id', 'name', 'type', 'connections', 'nodes', 'properties']),
            "organizations": sliced_organizations,
            "defaultAttributeMapping": True
        })

    # END sliceByNodeType

    @staticmethod
    def commit_model_to_repository(model, projectName, projectOwner, branchName, userid, description, modelId='TRUNK', username=None, password=None, totp=None, access_token=None):
        """
        Commit a model to the Models4Insight model repository.

        :returns: A ModelCommit instance describing the commit operation. Note that the commit happens asynchronously on the server side. You can monitor the progress via query_model requests.
        :rtype: ModelCommit

        :param File model: The model you wish to commit.
        :param str projectName: The name of the project to which you want to commit the model.
        :param str projectOwner: The username of the user who owns the project you are committing your model to.
        :param str branchName: The name of the branch to which you want to commit the model.
        :param str userid: The id of the user committing the model.
        :param str description: Describe the purpose of your commit.

        :exception TypeError: Thrown when any of the parameters (excluding module) is not defined or when the query result could not be parsed into a ModelCommit instance.
        :exception ValueError: Thrown when any of the parameters is not valid or when the query result could otherwise not be parsed.
        :exception requests.exceptions.HTTPError: Thrown when the request returned with a 400/500 code variant.
        """

        result = PlatformUtils.commit_model_to_repository(ArchimateUtils.to_JSON(
            model), projectName, projectOwner, branchName, userid, ModelFormat.JSON.value, ArchimateUtils.PARSER_NAME, modelId, description, username=username, password=password, totp=totp, access_token=access_token)

        return result
    # END commit_model_to_repository

    @staticmethod
    def commit_model_to_repository_with_conflict_resolution(model, projectName, projectOwner, branchName, userid, description, conflict_resolution_template, modelId='TRUNK', model_query_interval=1,  username=None, password=None, totp=None, access_token=None):
        """
        Commit a model to the Models4Insight model repository.

        :returns: A ModelCommit instance describing the commit operation. Note that the commit happens asynchronously on the server side. You can monitor the progress via query_model requests.
        :rtype: ModelCommit

        :param File model: The model you wish to commit.
        :param str projectName: The name of the project to which you want to commit the model.
        :param str projectOwner: The username of the user who owns the project you are committing your model to.
        :param str branchName: The name of the branch to which you want to commit the model.
        :param str userid: The id of the user committing the model.
        :param str description: Describe the purpose of your commit.

        :exception TypeError: Thrown when any of the parameters (excluding module) is not defined or when the query result could not be parsed into a ModelCommit instance.
        :exception ValueError: Thrown when any of the parameters is not valid or when the query result could otherwise not be parsed.
        :exception requests.exceptions.HTTPError: Thrown when the request returned with a 400/500 code variant.
        """

        result = PlatformUtils.commit_to_repository_resolve_conflict(
            model=ArchimateUtils.to_JSON(model), projectName=projectName, projectOwner=projectOwner, branch=branchName, userid=userid, parserName=ArchimateUtils.PARSER_NAME, model_query_interval=model_query_interval,  description=description, conflict_resolution_template=conflict_resolution_template, username=username, password=password, totp=totp, access_token=access_token
        )

        return result
    # END commit_model_to_repository

    @staticmethod
    def color_view_node(view_node: dict, fill_color_red: int, fill_color_green: int, fill_color_blue: int):
        """
        Adds the given fill color to the given view node. The fill color is specified in RGB format.

        :returns: A copy of the view node with the given fill color set as a property.
        :rtype: dict

        :param dict view_node: The view node for which to set the fill color
        :param int fill_color_red: The redness of the fill color between 0-255
        :param int fill_color_green: The greenness of the fill color between 0-255
        :param int fill_color_blue: The blueness of the fill color  between 0-255
        """

        if fill_color_red < 0 or fill_color_red > 255:
            raise ValueError(
                'Redness should be specified as a number between 0 and 255')
        # END IF

        if fill_color_green < 0 or fill_color_green > 255:
            raise ValueError(
                'Greenness should be specified as a number between 0 and 255')
        # END IF

        if fill_color_blue < 0 or fill_color_blue > 255:
            raise ValueError(
                'Blueness should be specified as a number between 0 and 255')
        # END IF

        return {
            **view_node,
            'ar3_style': {
                **view_node.get('ar3_style', {}),
                'ar3_fillColor': {
                    '@r': fill_color_red,
                    '@g': fill_color_green,
                    '@b': fill_color_blue
                }
            }
        }
    # END color_view_node

    @staticmethod
    def color_view_edge(view_edge: dict, line_color_red: int, line_color_green: int, line_color_blue: int):
        """
        Adds the given line color to the given view edge. The line color is specified in RGB format.

        :returns: A copy of the view edge with the given line color set as a property.
        :rtype: dict

        :param dict view_edge: The view edge/connection for which to set the line color
        :param int line_color_red: The redness of the fill line between 0-255
        :param int line_color_green: The greenness of the line color between 0-255
        :param int line_color_blue: The blueness of the line color  between 0-255
        """

        if line_color_red < 0 or line_color_red > 255:
            raise ValueError(
                'Redness should be specified as a number between 0 and 255')
        # END IF

        if line_color_green < 0 or line_color_green > 255:
            raise ValueError(
                'Greenness should be specified as a number between 0 and 255')
        # END IF

        if line_color_blue < 0 or line_color_blue > 255:
            raise ValueError(
                'Blueness should be specified as a number between 0 and 255')
        # END IF

        return {
            **view_edge,
            'ar3_style': {
                **view_edge.get('ar3_style', {}),
                'ar3_lineColor': {
                    '@r': line_color_red,
                    '@g': line_color_green,
                    '@b': line_color_blue
                }
            }
        }
    # END color_view_edge

    @staticmethod
    def get_view_nodes(view_nodes: Iterable[dict]) -> Iterable[dict]:
        """
        Returns a flat sequence of all given nodes and their children. 

        :returns: A flat sequence of all given nodes and their children
        :rtype: Generator of dict

        :param Iterable view_nodes: The top level set of nodes in the view
        """
        for node in view_nodes:
            yield node
            # If the ar3_node field is present, this node has child nodes
            if 'ar3_node' in node:
                for child_node in ArchimateUtils.get_view_nodes(node['ar3_node']):
                    yield child_node
                # END LOOP
            # END IF
        # END LOOP
    # END get_view_nodes

    @staticmethod
    def get_view_nodes_child_parent_pairs(view_nodes: Iterable[dict], parent: Optional[str] = None) -> Iterable[Tuple[str, str]]:
        """
        Returns a flat sequence of tuples representing the given nodes and their direct parents. 
        The returned sequence also includes the children of the given nodes.

        :returns: A flat sequence of tuples representing the given nodes and their direct parents
        :rtype: Generator of (str, str)

        :param Iterable view_nodes: The top level set of nodes in the view
        :param str parent: *Optional*. The node id of the parent node for the given `view_nodes`
        """
        for node in view_nodes:
            # Continue only if the node is an element
            if '@elementRef' in node:
                node_id = node['@elementRef']
                yield (node_id, parent)
                # If the ar3_node field is present, this node has child nodes
                if 'ar3_node' in node:
                    for child_node in ArchimateUtils.get_view_nodes_child_parent_pairs(node['ar3_node'], node_id):
                        yield child_node
                    # END LOOP
                # END IF
            # END IF
        # END LOOP
    # END get_view_nodes_child_parent_pairs

    @staticmethod
    def get_view_object_by_id(view: dict, object_id: str) -> dict:
        """
        Finds the view object (node, edge or other) with the given ID. Also checks nested objects.

        :return: The view object with the given id
        :rtype: dict

        :param view: The view to search in
        :type view: dict
        :param object_id: The id of the element to search for
        :type object_id: str
        """
        result = None
        if view != None and 'nodes' in view and 'edges' in view:
            if view['edges'] !=None:
                view_edges = view['edges']
            else:
                view_edges = []
            if view['nodes'] !=None:
                view_nodes = view['nodes']
            else:
                view_nodes = []
            for view_object in chain(view_nodes, view_edges):
                if view_object['@identifier'] == view_object:
                    result = view_object
                elif 'ar3_node' in view_object:
                    result = ArchimateUtils.get_view_object_by_id(
                        view_object['ar3_node'], object_id)
                # END IF
                if result:
                    break
                # END IF
            # END LOOP
        # END IF
        return result
    # END get_view_node_by_id

    @staticmethod
    def get_view_node_by_element_id(view_nodes: Iterable[dict], node_id: str) -> Iterable[dict]:
        """
        Finds the view nodes that reference the model node with the given node ID. Also checks nested elements.

        :return: The view nodes that reference the model node with the given id
        :rtype: Iterable[dict]

        :param view_nodes: The set of view nodes to search in
        :type view_nodes: Iterable
        :param node_id: The id of the model node for which to search
        :type node_id: str
        """
        if view_nodes!=None:
            for node in view_nodes:
                if node!=None and '@elementRef' in node and node['@elementRef'] == node_id:
                    yield node
                # END IF
                if node!=None and 'ar3_node' in node:
                    for child_node in ArchimateUtils.get_view_node_by_element_id(node['ar3_node'], node_id):
                        yield child_node
                # END IF
            # END LOOP
        # END IF
    # END get_view_node_by_node_id

    @staticmethod
    def get_view_edge_by_relationship_id(view_edges: Iterable[dict], relationship_id: str) -> Iterable[dict]:
        """
        Finds the view edges that reference the model relationship with the given relationship ID.

        :return: The view edges that reference the model relationship with the given id
        :rtype: Iterable[dict]

        :param view_edges: The set of edges to search in
        :type view_nodes: Iterable
        :param node_id: The id of the model relationship for which to search
        :type node_id: str
        """
        if view_edges!=None:
            for edge in view_edges:
                if '@relationshipRef' in edge and edge['@relationshipRef'] == relationship_id:
                    yield edge
                # END IF
            # END LOOP
        # END IF
    # END get_view_edge_by_relationship_id

# END ArchimateUtils
