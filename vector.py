
import numpy
import functools
from numbers import Number

def extract(cond, x):
    if not isinstance(x, Number):
        return numpy.extract(cond, x)
    else:
        return x


class vec():
    def __init__(self, x, y, z):
        (self.x, self.y, self.z) = (x, y, z)

    def __add__(self, other):
        return vec(self.x+other.x, self.y+other.y, self.z+other.z)

    def __sub__(self, other):
        return vec(self.x-other.x, self.y-other.y, self.z-other.z)

    def __mul__(self, other):
        return vec(self.x*other, self.y*other, self.z*other)

    def __abs__(self): #CHANGED
        return self.x**2 + self.y**2 + self.z**2

    def __pow__(self, other):
        return vec(self.x**other, self.y**other, self.z**other)

    def dot(self, other):
        return self.x*other.x + self.y*other.y + self.z*other.z

    def mag(self):
        return numpy.sqrt(abs(self))

    def normal(self):
        return self * (1.0/numpy.where(self.mag() == 0, 1, self.mag()))

    def extract(self, condition):
        return vec(extract(condition, self.x), extract(condition, self.y), extract(condition, self.z))

    def place(self, condition):
        r = vec(numpy.zeros(condition.shape), numpy.zeros(condition.shape), numpy.zeros(condition.shape))
        numpy.place(r.x, condition, self.x)
        numpy.place(r.y, condition, self.y)
        numpy.place(r.z, condition, self.z)
        return r

    def components(self):
        return self.x, self.y, self.z
