from blobmaker.generic_classes import CubitInstance, CubismError, cmd, cubit
from blobmaker.cubit_functions import cmd_check, get_id_string, to_bodies
import numpy as np


def create_2d_vertex(x, y):
    '''Create a vertex in the x-y plane

    :param x: x-coordinate of vertex
    :type x: int
    :param y: y-coordinate of vertex
    :type y: int
    :raises CubismError: If unable to create vertex
    :return: created vertex
    :rtype: CubitInstance
    '''
    vertex = cmd_check(f"create vertex {x} {y} 0", "vertex")
    if vertex:
        return vertex
    else:
        raise CubismError("Failed to create vertex")


def connect_vertices_straight(vertex1: CubitInstance, vertex2: CubitInstance):
    '''Connect 2 vertices with a straight curve

    :param vertex1: Vertex to connect
    :type vertex1: CubitInstance
    :param vertex2: Vertex to connect
    :type vertex2: CubitInstance
    :return: Connection curve or False if connection fails
    :rtype: CubitInstance/ bool
    '''
    if vertex1.geometry_type == "vertex" and vertex2.geometry_type == "vertex":
        connection = cmd_check(f"create curve vertex {vertex1.cid} {vertex2.cid}", "curve")
    else:
        raise CubismError("Given geometries are not vertices")
    return connection


def connect_curves_tangentially(vertex1: CubitInstance, vertex2: CubitInstance):
    '''Connect 2 curves at the given vertices,
    with the connection tangent to both curves.

    :param vertex1: Vertex to connect
    :type vertex1: CubitInstance
    :param vertex2: Vertex to connect
    :type vertex2: CubitInstance
    :return: Connection curve or False if connection fails
    :rtype: CubitInstance/ bool
    '''
    if vertex1.geometry_type == "vertex" and vertex2.geometry_type == "vertex":
        connection = cmd_check(f"create curve tangent vertex {vertex1.cid} vertex {vertex2.cid}", "curve")
    else:
        raise CubismError("Given geometries are not vertices")
    return connection


def make_surface_from_curves(curves_list: list[CubitInstance]):
    '''Make surface from bounding curves

    :param curves_list: List of bounding curves
    :type curves_list: list[CubitInstance]
    :return: surface geometry/ false
    :rtype: CubitInstance/ bool
    '''
    curve_id_string = get_id_string(curves_list)
    surface = cmd_check(f"create surface curve {curve_id_string}", "surface")
    return surface


def make_cylinder_along(radius: int, length: int, axis="z"):
    '''Make a cylinder along one of the cartesian axes

    :param radius: radius of cylinder
    :type radius: int
    :param length: length of cylinder
    :type length: int
    :param axis: axes to create cylinder along: x, y, or z
    :type axis: str
    :return: cylinder geometry
    :rtype: CubitInstance
    '''
    cylinder = cmd_check(f"create cylinder radius {radius} height {length}", "volume")
    if axis == "x":
        cmd(f"rotate volume {cylinder.cid} about Y angle -90")
    elif axis == "y":
        cmd(f"rotate volume {cylinder.cid} about X angle -90")
    return cylinder


def make_loop(vertices: list[CubitInstance], tangent_indices: list[int]):
    '''Connect vertices with straight curves.
    For specified indices connect with curves tangential to adjacent curves.

    :param vertices: Vertices to connect
    :type vertices: list[CubitInstance]
    :param tangent_indices: Vertices to start tangent curves from
    :type tangent_indices: list[int]
    :return: curve geometries
    :rtype: list[CubitInstance]
    '''
    curves = list(np.zeros(len(vertices)))
    for i in range(len(vertices)-1):
        if i not in tangent_indices:
            curves[i] = connect_vertices_straight(vertices[i], vertices[i+1])
    curves[-1] = connect_vertices_straight(vertices[-1], vertices[0])
    # need to do this after straight connections for tangents to actually exist
    for i in tangent_indices:
        curves[i] = connect_curves_tangentially(vertices[i], vertices[i+1])
    return curves


def hypotenuse(*sides: int):
    '''Take root of sum of squares

    :return: hypotenuse
    :rtype: float
    '''
    squared = [np.square(side) for side in sides]
    return np.sqrt(np.sum(squared))


def arctan(opposite: int, adjacent: int):
    '''Arctan with range 0, 2pi. Takes triangle side lengths.

    :param opposite: 'Opposite' side of a right-angled triangle
    :type opposite: int
    :param adjacent: 'Adjacent' side of a right-angled triangle
    :type adjacent: int
    :return: arctan(opposite/ adjacent)
    :rtype: int
    '''
    if adjacent == 0:
        arctan_angle = np.pi/2
    elif adjacent > 0:
        arctan_angle = np.arctan(opposite / adjacent)
    else:
        arctan_angle = np.pi + np.arctan(opposite / adjacent)
    return arctan_angle


class Vertex():
    '''Representation of a vertex'''
    def __init__(self, x: int, y=0, z=0) -> None:
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        x = self.x + other.x
        y = self.y + other.y
        z = self.z + other.z
        return Vertex(x, y, z)

    def __str__(self) -> str:
        return f"{self.x} {self.y} {self.z}"

    def create(self):
        '''Create this vertex in cubit.

        :return: created vertex
        :rtype: CubitInstance
        '''
        vertex = cmd_check(f"create vertex {str(self)}", "vertex")
        if vertex:
            return vertex
        else:
            raise CubismError("Failed to create vertex")

    def rotate(self, z: int, y=0, x=0):
        '''Rotate about z, then y, and then x axes.

        :param z: Angle to rotate about the z axis
        :type z: int
        :param y: Angle to rotate about the y axis, defaults to 0
        :type y: int, optional
        :param x: Angle to rotate about the x axis, defaults to 0
        :type x: int, optional
        :return: Rotated vertex
        :rtype: Vertex
        '''
        x_rotated = (self.x*np.cos(z)*np.cos(y)) + (self.y*(np.cos(z)*np.sin(y)*np.sin(x) - np.sin(z)*np.cos(x))) + (self.z*(np.cos(z)*np.sin(y)*np.cos(x) + np.sin(z)*np.sin(x)))
        y_rotated = (self.x*np.sin(z)*np.cos(y)) + (self.y*(np.sin(z)*np.sin(y)*np.sin(x) + np.cos(z)*np.cos(x))) + (self.z*(np.sin(z)*np.sin(y)*np.cos(x) - np.cos(z)*np.sin(x)))
        z_rotated = (-self.z*np.sin(y)) + (self.y*np.cos(y)*np.sin(x)) + (self.z*np.cos(y)*np.cos(x))
        return Vertex(x_rotated, y_rotated, z_rotated)

    def distance(self):
        '''Return distance from (0, 0, 0)

        :return: Distance
        :rtype: np.float64
        '''
        return np.sqrt(np.square(self.x)+np.square(self.y)+np.square(self.z))


def make_surface(vertices: list[Vertex], tangent_indices: list[int]):
    vertices = [vertex.create() for vertex in vertices]
    loop = make_loop(vertices, tangent_indices)
    surface = make_surface_from_curves(loop)
    return surface


def union(geometries: list[CubitInstance], destroy=True):
    as_bodies = to_bodies(geometries)
    body_ids = {body.cid for body in as_bodies}
    if destroy:
        cubit.unite([body.cubitInstance for body in as_bodies])
        all_bodies = set(cubit.get_entities("body"))
        created_body = list(body_ids.intersection(all_bodies))
    else:
        pre_bodies = set(cubit.get_entities("body"))
        cubit.unite([body.cubitInstance for body in as_bodies], keep_old_in=True)
        post_bodies = set(cubit.get_entities("body"))
        created_body = list(post_bodies.difference(pre_bodies))
    if len(created_body) > 1:
        raise CubismError("i have misunderstood how cubit unite works")
    return CubitInstance(created_body[0], "body")


def subtract(subtract_from: list[CubitInstance], subtract: list[CubitInstance], destroy=True):
    from_ids = {body.cid for body in to_bodies(subtract_from)}
    subtract_from = [body.cubitInstance for body in to_bodies(subtract_from)]
    subtract = [body.cubitInstance for body in to_bodies(subtract)]
    pre_ids = set(cubit.get_entities("body"))
    if destroy:
        cubit.subtract(subtract_from, subtract)
        post_ids = set(cubit.get_entities("body"))

        common_body_ids = post_ids.intersection(from_ids)
        new_ids = post_ids.difference(pre_ids)

        subtract_ids = list(common_body_ids.union(new_ids))
    else:
        cubit.subtract(subtract_from, subtract, keep_old_in=True)
        post_ids = set(cubit.get_entities("body"))

        subtract_ids = list(post_ids.difference(pre_ids))
    return [CubitInstance(sub_id, "body") for sub_id in subtract_ids]

def convert_to_3d_vector(dim):
    if type(dim) is int:
        return_vector = [dim for i in range(3)]
    elif len(dim) == 1:
        return_vector = [dim[0] for i in range(3)]
    elif len(dim) == 3:
        return_vector = dim
    else:
        raise CubismError("thickness should be either a 1D or 3D vector (or scalar)")
    return return_vector