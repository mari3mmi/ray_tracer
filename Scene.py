from PIL import Image
import numpy
import functools
from numbers import Number


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