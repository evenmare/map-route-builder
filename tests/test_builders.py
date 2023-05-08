import pytest

import networkx as nx

from route_builder import builders
from route_builder.utils import Bbox


bbox = Bbox(55.98323, 55.97630, 37.19288, 37.18280)


@pytest.mark.geo
@pytest.mark.parametrize('network_type', ['all', 'bike', 'drive', 'not exist'])
def test_graph_builder(disable_osmnx_cache, disable_osmnx_logs, network_type: str):
    """ Проверка построителя графа """
    if network_type not in builders.NETWORK_TYPES:
        with pytest.raises(Exception) as ex:
            _build_graph(network_type)
        isinstance(ex.value, ValueError)

    else:
        graph = _build_graph(network_type)
        assert isinstance(graph.graph, nx.MultiDiGraph)
        assert len(graph.graph.nodes)
        assert len(graph.graph.edges)
        assert graph.graph.pred, graph.graph.succ

        del graph._graph  # pylint: disable=protected-access
        assert isinstance(graph.graph, nx.MultiDiGraph)


@pytest.mark.geo
@pytest.mark.parametrize('network_type, coordinates, extra_params',
                         [('drive', [(55.97999, 37.18581), (55.97863, 37.18954)], {'with_map': True}),
                          ('walk', [(55.97999, 37.18581), (55.98006, 37.18981), (55.97863, 37.18954)], {}),
                          ('drive', [(55.97999, 37.18581), (55.97863, 37.18954)], {'optimizer': 'travel_time'})])
def test_route_builder(disable_osmnx_cache, disable_osmnx_logs, network_type, coordinates, extra_params):
    """ Проверка построителя маршрута """
    graph = _build_graph(network_type)
    route = builders.RouteBuilder(graph, coordinates, **extra_params).build()
    assert isinstance(route, builders.Route)

    assert isinstance(route.paths, list)
    assert isinstance(route.travel_time, float)
    assert isinstance(route.length, float)
    assert isinstance(route.map, str) if extra_params.get('with_map') else route.map is None


def test_route_builder_with_invalid_coordinates(disable_osmnx_cache, disable_osmnx_logs):
    """ Проверка возникновения ошибки при передаче координат, не принадлежащих зоне графа """
    graph = _build_graph('all')

    with pytest.raises(Exception) as ex:
        builders.RouteBuilder(graph, [(180.02345, 32.32145), (170.32134, 32.32145)])

    assert isinstance(ex.value, ValueError)


def _build_graph(network_type) -> builders.Graph:
    """ Строительство графа """
    graph = builders.Graph(bbox, network_type)
    graph.build()
    return graph
