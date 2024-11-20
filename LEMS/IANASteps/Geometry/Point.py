#!/usr/bin/python
# vi:ts=3:ai

import operator
import math

"""Simple geometry module"""

##
# Class for handling points
class Point(tuple):
    ##
    # Constructor which will create a point from a iterator or a list of param
    #
    # @param cls Class reference
    # @param components Point components
    def __new__(cls, *components):
        if len(components) == 1:
            return tuple.__new__(cls, components[0])
        else:
            return tuple.__new__(cls, components)

    ##
    # Add two points (self + other)
    #
    # @param self Instance reference
    # @param other Other point
    # @param return Point
    def __add__(self, other):
        try:
            if len(self) != len(other):
                return NotImplemented
        except:
            return NotImplemented

        return Point(*map(operator.add, self, other))

    ##
    # Add two points (other + self)
    #
    # @param self Instance reference
    # @param other Other point
    # @param return Point
    def __radd__(self, other):
        return self + other

    ##
    # Subtracts two points (self - other)
    #
    # @param self Instance reference
    # @param other Other point
    # @param return Point
    def __sub__(self, other):
        try:
            if len(self) != len(other):
                return NotImplemented
        except:
            return NotImplemented

        return Point(*map(operator.sub, self, other))

    ##
    # Subtracts two points (other - self)
    #
    # @param self Instance reference
    # @param other Other point
    # @param return Point
    def __rsub__(self, other):
        try:
            if len(self) != len(other):
                return NotImplemented
        except:
            return NotImplemented

        return Point(*map(operator.sub, other, self))

    ##
    # Multiplies two points (self * other)
    #
    # @param self Instance reference
    # @param other Other point
    # @param return Point
    def __mul__(self, other):
        if hasattr(other, '__getitem__'):
            return NotImplemented

        return Point(*[other * component for component in self])

    ##
    # Multiplies two points (other * self)
    #
    # @param self Instance reference
    # @param other Other point
    # @param return Point
    def __rmul__(self, other):
        return self * other

    ##
    # Divides two points (self / other)
    #
    # @param self Instance reference
    # @param other Other point
    # @param return Point
    def __div__(self, other):
        if hasattr(other, '__getitem__'):
            return NotImplemented

        return Point(*[component / other for component in self])

    ##
    # Prohibit non equality comparison
    #
    # @param self Instance reference
    # @param other Other Point
    def __lt__(self, other):
        raise TypeError('only equality comparison is supported')

    ##
    # Prohibit non equality comparison
    #
    # @param self Instance reference
    # @param other Other Point
    def __le__(self, other):
        raise TypeError('only equality comparison is supported')

    ##
    # Prohibit non equality comparison
    #
    # @param self Instance reference
    # @param other Other Point
    def __ge__(self, other):
        raise TypeError('only equality comparison is supported')

    ##
    # Prohibit non equality comparison
    #
    # @param self Instance reference
    # @param other Other Point
    def __gt__(self, other):
        raise TypeError('only equality comparison is supported')

    ##
    # Computes the distance between two points or the origin if omitted
    #
    # @param self Instance reference
    # @param origin Point to use as the origin
    # @returns distance
    def distance(self, origin=None):
        if origin is None:
            end = self
        else:
            end = self - origin

        return math.sqrt(sum([component * component for component in end]))

    ##
    # performs the dot product of two points (as vectors)
    #
    # @param self Instance reference
    # @param other Other point
    def dot(self, other):
        compatible = False

        try:
            if len(self) == len(other):
                compatible = True
        except:
            raise TypeError('Not compatible types')

        if not compatible:
            raise TypeError('Not compatible lengths')

        return sum(map(operator.mul, self, other))

    ##
    # performs the cross product of two points (as vectors)
    #
    # @param self Instance reference
    # @param other Other point
    def cross(self, other):
        compatible = False

        try:
            if len(self) == 3 and len(other) == 3:
                compatible = True
        except:
            raise TypeError('Not compatible types')

        if not compatible:
            raise TypeError('Cross product is only defined for points in R3')

        other = Point(other)

        x, y, z = self
        return Point(other.dot((0, - z, y)),
                        other.dot((z, 0, -x)),
                        other.dot((-y, x, 0)))