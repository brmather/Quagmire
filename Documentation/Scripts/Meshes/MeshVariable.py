from quagmire.tools import meshtools
from quagmire import FlatMesh, TopoMesh, SurfaceProcessMesh
from quagmire.mesh import MeshVariable, VectorMeshVariable

import petsc4py
import mpi4py
import quagmire

import numpy as np

comm = mpi4py.MPI.COMM_WORLD

minX, maxX = -5.0, 5.0
minY, maxY = -5.0, 5.0,
dx, dy = 0.1, 0.1

x, y, simplices = meshtools.elliptical_mesh(minX, maxX, minY, maxY, dx, dy)

DM = meshtools.create_DMPlex_from_points(x, y, bmask=None)

mesh = TopoMesh(DM, downhill_neighbours=1, verbose=False)

print("{}: mesh size:{}".format(comm.rank, mesh.npoints))


v = MeshVariable("stuff", mesh)
h = np.ones(mesh.npoints) * comm.rank

v.data = h
# v.data[1] = 2.0

gdata = DM.getGlobalVec()
v.getGlobalVector(gdata)

print("{}: vl min/max = {}/{}".format(comm.rank, v.data.min(), v.data.max()))
print("{}: vg min/max = {}/{}".format(comm.rank, gdata.min(), gdata.max()))

v.data = mesh.sync(v.data)


print("{}: vlSync min/max = {}/{}".format(comm.rank, v.data.min(), v.data.max()))
print("{}: vgSync min/max = {}/{}".format(comm.rank, gdata.min(), gdata.max()))

v.sync(mergeShadow=False)

print(v.data)
v.save()

v2 = MeshVariable("stuff", mesh)
v2.load("stuff.h5")
print("{}: save/load ".format(comm.rank), np.all(v2.data == v.data))

dv = v.gradient()
print(type(dv))


print("INTERP")
print(v.interpolate([0.1, 10.0], [0.1, 10.0], err=False))
print(v.interpolate(0.1, 0.1))
print(v.evaluate(0.1, 0.1))

v = VectorMeshVariable("more_stuff", mesh)
h = np.ones((mesh.npoints, 2)) * comm.rank

v.data = h

gdata = DM.getCoordinates().duplicate()
v.getGlobalVector(gdata)

print("VectorMeshVariable\n-------")
print("{}: vl min/max = {}/{}".format(comm.rank, v.data.min(), v.data.max()))
print("{}: vg min/max = {}/{}".format(comm.rank, gdata.min(), gdata.max()))

v.sync()
v.sync()

print("{}: vlSync min/max = {}/{}".format(comm.rank, v.data.min(), v.data.max()))
print("{}: vgSync min/max = {}/{}".format(comm.rank, gdata.min(), gdata.max()))

print(v.data)
v.save()


v2 = VectorMeshVariable("more_stuff", mesh)
v2.load("more_stuff.h5")
print("{}: save/load ".format(comm.rank), np.all(v2.data == v.data))
