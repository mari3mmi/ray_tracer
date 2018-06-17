from PIL import Image
import numpy
import functools
import vector
from numbers import Number
from itertools import islice

scene = []

# if passed a number, will return itself. If passed a collection, will vector.extract numbers that fulfill the condition

rgb = vector.vec

values = []


def normalizeColour(colour):
    colour_componenets = colour.components()
    min = 1e20
    for component in colour_componenets:
        if component < min: min = component
    return rgb(colour.x - min, colour.y - min, colour.z - min)


class Camera:
    def __init__(self, focal_length= None, fov= None, pos= None, ratio= None):
        self.focal_length = focal_length or 1000
        self.fov = fov or 60
        self.pos = pos or vector.vec(0, 0, -1)
        self.ratio = ratio or 1

class Light:
    def __init__(self, position= None, colour= None):
        self.position = position or vector.vec(0, 0, 0)
        self.colour = colour or vector.vec(0, 0, 0)

    def areaLight(self):
        global lights
        lights.append(Light(vector.vec(self.position.x + 0.5, self.position.y + 0.5, self.position.z + 0.5), self.colour))
        lights.append(Light(vector.vec(self.position.x - 0.5, self.position.y - 0.5, self.position.z - 0.5), self.colour))

def raytrace(origin, direction, bounce, scene):
    distances = [s.intersect(origin, direction) for s in scene]  # Calculate distances
    nearest = functools.reduce(numpy.minimum, distances)  # Generate a new list, element-wise choosing the lowest value
    colour = rgb(0, 0, 0)  # instantiate light colour
    for (d, s) in zip(distances, scene):
        collision = (nearest != infinity) & (d == nearest)  # Using bitwise AND to work around numpy arrays
        if numpy.any(collision):  # Tests every value along the collision axis to see if it evaluates to true
            dc = vector.extract(collision, d)  # Get the value of collision from d, using our vector.extract function
            originC = origin.extract(collision)
            directionC = direction.extract(collision)
            #  Calculate the colour at each collision
            for light in lights:
                colourC = s.light(originC, directionC, dc, scene, bounce, light)
                colour += colourC.place(collision)
    return colour*(1/len(lights))


class Plane:
    def __init__(self, pos=None, norm=None, amb=None, dif=None, spe=None, shine=None):
        self.pos = pos or vector.vec(0,0,0)
        self.norm = norm or 0
        self.amb = amb or vector.vec(0,0,0)
        self.dif = dif or vector.vec(0,0,0)
        self.spe = spe or vector.vec(0,0,0)
        self.shine = shine or 0
        self.bounce = 0

    def intersect(self, origin, direction):
        # Return the distance from O to the intersection of the ray (O, D) with the
        # plane (P, N), or +inf if there is no intersection.
        # O and P are 3D points, D and N (normal) are normalized vectors.
        denom = self.norm.dot(direction)

        w = origin - self.pos
        d = -self.norm.dot(w) / denom
        if numpy.abs(denom.any()) < 1e-6:
            return (numpy.where((numpy.abs(denom) < 1e-6)), infinity)
        result = w + direction * d + origin
        return numpy.where((d < 0), infinity, result.z)

    def ambient_light(self, light_colour):
        return self.amb  # + light_colour

    def diffuse_light(self, normal, lightDir, visibility, interesection, light_colour):
        colour = self.dif + light_colour
        lv = numpy.maximum(normal.dot(lightDir), 0)
        return colour * lv * visibility

    def specular_light(self, normal, lightDir, originDir, visibility, light_colour):
        colour = self.spe + light_colour
        phongModel = normal.dot((lightDir + originDir).normal())
        return colour * numpy.power(numpy.clip(phongModel, 0, 1), 50) * visibility

    def reflection(self, shifted, direction, normal, scene, bounce, light_colour):
        # if bounce < 2:  # TODO: is this needed?
            rayDirection = (direction - normal * 2 * direction.dot(normal)).normal()
            return raytrace(shifted, rayDirection, bounce+1, scene) * self.shine

    def light(self, origin, direction, d, scene, bounce, light):
        normalized_colour = normalizeColour(light.colour)
        intersection = origin + direction*d
        normal = self.norm
        lightDir = (light.position - intersection).normal()
        originDir = (camera.pos - intersection).normal()
        shifted = intersection + normal*1e-6  # shift the value just a bit

        # find out if the above intersection is the first one, or if it's shadowed
        intersections = [s.intersect(shifted, lightDir) for s in scene]
        nearest = functools.reduce(numpy.minimum, intersections)
        visibility = intersections[scene.index(self)] == nearest  # for each intersection indicates whether in light


        if bounce < 2:
             colour = self.ambient_light(normalized_colour) + self.diffuse_light(normal,lightDir,visibility, intersection,normalized_colour) + \
                self.reflection(shifted, direction, normal, scene, bounce, normalized_colour) + \
                self.specular_light(normal,lightDir, originDir, visibility, normalized_colour)

        else:
             colour = self.ambient_light(normalized_colour) + self.diffuse_light(normal,lightDir,visibility, intersection, normalized_colour) + \
                self.specular_light(normal,lightDir, originDir, visibility, normalized_colour)
        return colour


class Sphere:
    def __init__(self, pos=None, rad=None, amb=None, dif=None, spe=None, shine=None):
        self.pos = pos or vector.vec(0,0,0)
        self.rad = rad or 0
        self.amb = amb or vector.vec(0,0,0)
        self.dif = dif or vector.vec(0,0,0)
        self.spe = spe or vector.vec(0,0,0)
        self.shine = shine or 0
        self.bounce = 1

    def intersect(self, origin, direction):
        q = 2 * direction.dot(origin - self.pos)
        p = abs(self.pos) + abs(origin) - 2 * self.pos.dot(origin) - (self.rad ** 2)
        disc = -4 * p + q ** 2
        square = numpy.sqrt(numpy.maximum(0, disc))  # prevents invalid square-roots
        h0 = (-q - square) / 2
        h1 = (-q + square) / 2
        h = numpy.where((h0 > 0) & (h0 < h1), h0, h1)
        return numpy.where((disc > 0) & (h > 0), h, infinity)

    def ambient_light(self, light_colour):
        return self.amb  # + light_colour

    def diffuse_light(self, normal, lightDir, visibility, intersection, light_colour):
        colour = self.dif + light_colour
        lv = numpy.maximum(normal.dot(lightDir), 0)
        return colour * lv * visibility

    def specular_light(self, normal, lightDir, originDir, visibility, light_colour):
        colour = self.spe + light_colour
        phongModel = normal.dot((lightDir + originDir).normal())
        return colour * numpy.power(numpy.clip(phongModel, 0, 1), 50) * visibility

    def reflection(self, shifted, direction, normal, scene, bounce, light_colour):
        # if bounce < 2:  # TODO: is this needed?
            rayDirection = (direction - normal * 2 * direction.dot(normal)).normal()
            return raytrace(shifted, rayDirection, bounce+1, scene) * self.shine

    def light(self, origin, direction, d, scene, bounce, light):
        normalized_colour = normalizeColour(light.colour)
        intersection = origin + direction*d
        normal = (intersection - self.pos) * (1. / self.rad)
        lightDir = (light.position - intersection).normal()
        originDir = (camera.pos - intersection).normal()
        shifted = intersection + normal*1e-6  # shift the value just a bit

        # find out if the above intersection is the first one, or if it's shadowed
        intersections = [s.intersect(shifted, lightDir) for s in scene]
        nearest = functools.reduce(numpy.minimum, intersections)
        visibility = intersections[scene.index(self)] == nearest  # for each intersection indicates whether in light
        if bounce < 20:
            colour = self.ambient_light(normalized_colour) + self.diffuse_light(normal,lightDir,visibility, intersection,normalized_colour) + \
               self.reflection(shifted, direction, normal, scene, bounce, normalized_colour) + \
                self.specular_light(normal,lightDir, originDir, visibility, normalized_colour)

        else:
            colour = self.ambient_light(normalized_colour) + self.diffuse_light(normal,lightDir,visibility, intersection, normalized_colour) + \
                    self.specular_light(normal,lightDir, originDir, visibility, normalized_colour)
        return colour


def sphere_reader(properties):
    sphere = Sphere()
    for prop in properties:
        prop = prop.strip()
        props = prop.split(' ')
        if props[0] == 'pos:':
            sphere.pos = vector.vec(float(props[1]), float(props[2]), -float(props[3]))
            continue
        if props[0] == 'rad:':
            sphere.rad = float(props[1])
            continue
        if props[0] == 'amb:':
            sphere.amb = vector.vec(float(props[1]), float(props[2]), float(props[3]))
            continue
        if props[0] == 'dif:':
            sphere.dif = vector.vec(float(props[1]), float(props[2]), float(props[3]))
            continue
        if props[0] == 'spe:':
            sphere.spe = vector.vec(float(props[1]), float(props[2]), float(props[3]))
            continue
        if props[0] == 'shi:':
            sphere.shine = float(props[1])/5
    return sphere


def light_reader(properties):
    global lights
    light = Light()
    for prop in properties:
        prop = prop.strip()
        props = prop.split(' ')
        if props[0] == 'pos:':
            light.position = vector.vec(float(props[1]), float(props[2]), -float(props[3]))
            continue
        if props[0] == 'col:':
            light.colour = vector.vec(float(props[1]), float(props[2]), float(props[3]))
    return light


def camera_reader(properties):
    camera = Camera()
    for prop in properties:
        prop = prop.strip()
        props = prop.split(' ')
        if props[0] == 'pos:':
            camera.pos = vector.vec(float(props[1]), float(props[2]), (float(props[3]))-1)
            continue
        if props[0] == 'f:':
            camera.focal_length = (float(props[1]))
            continue
        if props[0] == 'fov:':
            camera.fov = ( 2*numpy.pi/360 * float(props[1]))  # values[0] == fov
            continue
        if props[0] == 'a:':
            camera.ratio = (float(props[1]))  # values[1] == aspect ratio
    return camera


def plane_reader(properties):
    plane = Plane()
    for prop in properties:
        prop = prop.strip()
        props = prop.split(' ')
        if props[0] == 'pos:':
            plane.pos = vector.vec(float(props[1]), float(props[2]), -float(props[3]))
            continue
        if props[0] == 'nor:':
            plane.norm = vector.vec(float(props[1]), float(props[2]), float(props[3]))
            continue
        if props[0] == 'amb:':
            plane.amb = vector.vec(float(props[1]), float(props[2]), float(props[3]))
            continue
        if props[0] == 'dif:':
            plane.dif = vector.vec(float(props[1]), float(props[2]), float(props[3]))
            continue
        if props[0] == 'spe:':
            plane.spe = vector.vec(float(props[1]), float(props[2]), float(props[3]))
            continue
        if props[0] == 'shi:':
            plane.shine = float(props[1])/10
    return plane


def scene_reader(path):
    objects = 0
    global scene
    global camera
    global lights
    with open(path, 'r') as f:
        while True:
            line = f.readline()
            if not line: break
            if isinstance(line, Number):
                objects = line
                continue
            if line.strip() == 'sphere':
                sphere = sphere_reader(list(islice(f, 6)))
                objects += 1
                scene.append(sphere)
            if line.strip() == 'plane':
                plane = plane_reader(list(islice(f, 6)))
                objects += 1
                scene.append(plane)
            if line.strip() == 'light':
                light = light_reader(list(islice(f, 2)))
                objects += 1
                lights.append(light)
            if line.strip() == 'camera':
                camera = camera_reader(list(islice(f, 4)))
                objects += 1
    return scene

#scene = [
#     Sphere(vector.vec(0., 0., 50), 10., rgb(0.5, 0.2, 0.7), rgb(0.2, 0.4, 0.2), rgb(0.1, 0.7, 0.2), 0.1),
#     Sphere(vector.vec(0., 10., 30.), 3., rgb(.1, .5, .5), rgb(0.4, .6, .2), rgb(.2, .5, .5), .1),
#     Sphere(vector.vec(30, 30, 80), 2., rgb(1., .572, .184), rgb(1., .572, .184), rgb(1., .572, .184), .4),
#     Sphere(vector.vec(0,-99999, 0), 99994, rgb(.3, .5, .2), rgb(.5, .6, .2), rgb(.5, .6, .2), .5),
#     Plane(vector.vec(0, -7, 0), vector.vec(0,1,0), rgb(.3, .5, .2), rgb(.5, .6, .2), rgb(.5, .6, .2))
#    ]

lights = list()
scene = list()
camera = Camera()
scene = scene_reader('scene5.txt')
infinity = 1.30e59
(WIDTH,HEIGHT) = (2 * camera.focal_length * numpy.tan(camera.fov/2) * camera.ratio, (2 * camera.focal_length * numpy.tan(camera.fov/2)))
print(lights)
lightlen = len(lights)
for light in lights:
    light.areaLight()
    if len(lights)== 3*lightlen:
        break
#lights.append(Light(vector.vec(1,0,1), vector.vec(0.9, 0., .2)))
# Screen coordinates: x0, y0, x1, y1.
S = (-camera.ratio * numpy.tan(camera.fov/2), numpy.tan(camera.fov/2) + 0.25, camera.ratio * numpy.tan(camera.fov/2), - numpy.tan(camera.fov/2) + 0.25)
x = numpy.tile(numpy.linspace(S[0], S[2], int(WIDTH)), int(HEIGHT))
y = numpy.repeat(numpy.linspace(S[1], S[3], int(HEIGHT)), int(WIDTH))


Q = vector.vec(x, y, 0.)
color = raytrace(camera.pos, (Q - camera.pos).normal(), 0, scene)

rgb = [Image.fromarray((255 * numpy.clip(c, 0, 1).reshape((int(HEIGHT), int(WIDTH)))).astype(numpy.uint8), "L") for c in color.components()]
Image.merge("RGB", rgb).save("fig.bmp")