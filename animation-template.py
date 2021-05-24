#!/usr/bin/env python3

import chess as chess
import chess.pgn as pgn
import bpy
from mathutils import Vector

# useful shortcut
scene = bpy.context.scene

# this shows you all objects in scene
scene.objects.keys()

# when you start default Blender project, first object in scene is a Cube
kostka = scene.objects[0]

# you can change location of object simply by setting the values
kostka.location = (1,2,0)

# same with rotation
kostka.rotation_euler = (45,0,0)

# this will make object cease from current scene
scene.objects.unlink(kostka)

# clear everything for now
scene.camera = None
for obj in scene.objects:
    scene.objects.unlink(obj)

# create sphere and make it smooth
bpy.ops.mesh.primitive_uv_sphere_add(location = (2,1,2), size=0.5)
bpy.ops.object.shade_smooth()
kule = bpy.context.object

# create new cube
bpy.ops.mesh.primitive_cube_add(location = (-2,1,2))
kostka = bpy.context.object

# create plane
bpy.ops.mesh.primitive_plane_add(location=(0,0,0))
plane = bpy.context.object
plane.dimensions = (20,20,0)

# for every object add material - here represented just as color
for col, ob in zip([(1, 0, 0), (0,1,0), (0,0,1)], [kule, kostka, plane]):
    mat = bpy.data.materials.new("mat_" + str(ob.name))
    mat.diffuse_color = col
    ob.data.materials.append(mat)

# now add some light
lamp_data = bpy.data.lamps.new(name="lampa", type='POINT')
lamp_object = bpy.data.objects.new(name="Lampicka", object_data=lamp_data)
scene.objects.link(lamp_object)
lamp_object.location = (-3, 0, 12)

# and now set the camera
cam_data = bpy.data.cameras.new(name="cam")
cam_ob = bpy.data.objects.new(name="Kamerka", object_data=cam_data)
scene.objects.link(cam_ob)
cam_ob.location = (-3, 0, 5)
cam_ob.rotation_euler = (3.14/6,0,-0.3)
cam = bpy.data.cameras[cam_data.name]
cam.lens = 10


### animation
positions = (0,0,2),(0,1,2),(3,2,1),(3,4,1),(1,2,1)

# start with frame 0
number_of_frame = 0
for pozice in positions:

    # now we will describe frame with number $number_of_frame
    scene.frame_set(number_of_frame)

    # set new location for sphere $kule and new rotation for cube $kostka
    kule.location = pozice
    kule.keyframe_insert(data_path="location", index=-1)

    kostka.rotation_euler = pozice
    kostka.keyframe_insert(data_path="rotation_euler", index=-1)

    # move next 10 frames forward - Blender will figure out what to do between this time
    number_of_frame += 10
