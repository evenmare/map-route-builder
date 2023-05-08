from typing import List, Sequence, Literal, Optional, Union, get_args
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
    length: Optional[float]
    travel_time: Optional[float]
    map: Optional[str]


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

    def build_map(self, route: Union[List[int], List[List[int]]]) -> str:
        """
        Построение карты маршрута
        :param route: маршрут
        :return: HTML-код карты маршрута
        """
        route_map = None

        if route and self.extra_params.get('with_map'):
            if isinstance(route[0], list):
                route: List[List[int]]
                raw_route_map = ox.plot_route_folium(self.graph.graph, route[0], **self.extra_params)

                for route_part in route[1:]:
                    raw_route_map = ox.plot_route_folium(self.graph.graph, route_part, raw_route_map,
                                                         **self.extra_params)

            else:
                route: List[int]
                raw_route_map = ox.plot_route_folium(self.graph.graph, route, **self.extra_params)

            route_map = utils.get_map_html(raw_route_map)

        return route_map

    def get_sum_route_edge_attributes(self, route: Union[List[int], List[List[int]]], attr_name: str) -> float:
        """
        Получение атрибута ребра
        :param route: маршрут
        :param attr_name: наименование атрибута
        :return: сумма атрибута ребра
        """
        route_edge_attribute_sum = None

        if route:
            route_edge_attribute_sum = 0

            if isinstance(route[0], list):
                route: List[List[int]]

                for route_part in route:
                    route_edge_attribute_sum += sum(
                        get_route_edge_attributes(self.graph.graph, route_part, attribute=attr_name))
            else:
                route: List[int]
                route_edge_attribute_sum += sum(get_route_edge_attributes(self.graph.graph, route, attribute=attr_name))

        return route_edge_attribute_sum

    def build(self) -> Route:
        """
        Построение маршрута
        :return: маршрут
        """
        graph = self.graph.graph
        nodes = utils.prepare_nodes(ox.nearest_nodes(graph, *self.coordinates))
        route = ox.shortest_path(graph, *nodes, self.extra_params.get('optimizer', 'length'), settings.CPU_LIMITER)

        route_map = self.build_map(route)
        length = self.get_sum_route_edge_attributes(route, 'length')
        travel_time = self.get_sum_route_edge_attributes(route, 'travel_time')

        return Route(paths=route, map=route_map, length=length, travel_time=travel_time)


def build_route(graph: Graph, **kwargs) -> Route:
    """
    Строительство маршрута
    :param graph: граф для построения маршрута
    :param kwargs: конфигурация маршрута
    :return: маршрут
    """
    route_builder = RouteBuilder(graph, **kwargs)
    return route_builder.build()
