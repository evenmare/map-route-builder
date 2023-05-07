from typing import List, Sequence
from dataclasses import dataclass

import folium


@dataclass
class Bbox:
    """ Зона ограничения для построения графа """
    north: float
    south: float
    east: float
    west: float


def split_coordinates(points_coordinates: List[Sequence[float]]) -> List[List[float]]:
    """
    Деление координат на отдельные списки
    :param points_coordinates: список координат вида [(Y, X), (Y, X), ...]
    :return: список координат вида [[X, X, ...], [Y, Y, ...]]
    """
    y_coordinates = []
    x_coordinates = [coordinate[1] for coordinate in points_coordinates
                     if not y_coordinates.append(coordinate[0])]

    return [x_coordinates, y_coordinates]


def get_map_html(route_map: folium.Map) -> str:
    """
    Получение HTML карты
    :param route_map: карта с маршрутом
    :return: текст HTML в кодировке UTF-8
    """
    root = route_map.get_root()
    html = root.render()
    return html