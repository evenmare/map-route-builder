from typing import List, Sequence, Literal, Optional, get_args
from dataclasses import dataclass, astuple

import logging

import osmnx as ox
from osmnx.utils_graph import get_route_edge_attributes
import networkx as nx
import folium

import settings
from route_builder import utils


logger = logging.getLogger(__name__)
ox.config(log_console=settings.DEBUG, use_cache=settings.USE_CACHE)


NetworkTypesType = Literal['all_private', 'all', 'bike', 'drive', 'drive_service', 'walk']
NETWORK_TYPES = get_args(NetworkTypesType)


@dataclass
class Route:
    """ Маршрут """
    paths: list
    length: int
    travel_time: int
    map: Optional[folium.Map]


class Graph:
    """ Граф """
    bbox: utils.Bbox
    network_type: Optional[NetworkTypesType] = 'all'

    _graph: nx.MultiDiGraph = None

    def __init__(self, bbox: utils.Bbox, network_type: Optional[NetworkTypesType] = None):
        """
        Инициализация построителя графа
        :param bbox: конфигурация зоны графа
        :param network_type: тип связей графа
        """
        if not isinstance(bbox, utils.Bbox):
            raise ValueError('Некорректный тип bbox')

        self.bbox = bbox

        if network_type:
            if network_type not in NETWORK_TYPES:
                raise ValueError(f'Значения network_type: {", ".join(NETWORK_TYPES)}')

            self.network_type = network_type

    def build(self) -> nx.MultiDiGraph:
        """
        Построение графа
        :return: представление графа
        """
        logger.info("============== GRAPH BUILD START ==============")

        graph = ox.graph_from_bbox(*astuple(self.bbox), network_type=self.network_type)

        graph = ox.add_edge_speeds(graph)
        graph = ox.add_edge_travel_times(graph)

        self._graph = graph

        logger.info("============== GRAPH BUILD END ==============")

        return graph

    @property
    def graph(self) -> nx.MultiDiGraph:
        """
        Построенный граф
        :return: MultiDiGraph
        """
        return self._graph or self.build()


class RouteBuilder:  # pylint: disable=too-few-public-methods
    """ Построитель маршрута """
    graph: Graph

    coordinates: List[List[float]]
    extra_params: Optional[dict] = None

    route: list
    time: int
    length: int
    map: Optional[folium.Map]

    def __init__(self, graph: Graph, points_coordinates: List[Sequence[float]], **kwargs):
        """
        Инициализация построителя маршрута
        :param graph: абстракция графа
        :param points_coordinates: список координат
        :param kwargs: дополнительные параметры построения маршрута
        """
        self.graph = graph

        coordinates = utils.split_coordinates(points_coordinates)
        self.coordinates = self._validate_coordinates(coordinates) and coordinates

        self.extra_params = kwargs

    def _validate_coordinates(self, coordinates: List[List[float]]) -> bool:
        """
        Валидация координат маршрута
        :param coordinates: координаты маршрута
        :return: True
        """
        if (min(coordinates[1]) < self.graph.bbox.south or
                max(coordinates[1]) > self.graph.bbox.north or
                min(coordinates[0]) < self.graph.bbox.west or
                max(coordinates[0]) > self.graph.bbox.east):
            raise ValueError(f'Координаты должны быть в области {", ".join(map(str, astuple(self.graph.bbox)))}')

        return True

    def build(self) -> Route:
        """
        Построение маршрута
        :return: маршрут
        """
        graph = self.graph.graph
        nodes = ox.nearest_nodes(graph, *self.coordinates)
        route = ox.shortest_path(graph, *nodes)

        route_map = utils.get_map_html(ox.plot_route_folium(graph, route, **self.extra_params)) \
            if self.extra_params.get('with_map') else None

        return Route(paths=route,
                     map=route_map,
                     **{attr: int(sum(get_route_edge_attributes(graph, route, attr))) for attr in ('length', 'travel_time')})


def build_route(graph: Graph, **kwargs) -> Route:
    """
    Строительство маршрута
    :param graph: граф для построения маршрута
    :param kwargs: конфигурация маршрута
    :return: маршрут
    """
    route_builder = RouteBuilder(graph, **kwargs)
    return route_builder.build()
