
# coding: utf-8

# # Meshing ETOPO1
#
# In this notebook we:
#
# 1. Find the land surface in a region by filtering ETOPO1
# 2. Optionally correct for the geoid (important in low-gradient / low-lying areas)
# 4. Create a DM object and refine a few times
# 5. Save the mesh to HDF5 file

# In[1]:

from osgeo import gdal

import numpy as np

import quagmire
from quagmire import tools as meshtools

from scipy.ndimage import imread
from scipy.ndimage.filters import gaussian_filter



AusBounds = (110, -45 , 155, -5)
NZbounds  = (85.0, 18.0, 105.0, 36.0)

## Define region of interest (here NZ)

minX, minY, maxX, maxY = AusBounds

xres = 250
yres = 250

xx = np.linspace(minX, maxX, xres)
yy = np.linspace(minY, maxY, yres)
x1, y1 = np.meshgrid(xx,yy)
x1 += np.random.random(x1.shape) * 0.2 * (maxX-minX) / xres
y1 += np.random.random(y1.shape) * 0.2 * (maxY-minY) / yres

x1 = x1.flatten()
y1 = y1.flatten()

pts = np.stack((x1, y1)).T


##  The alternative to this is to pre-process ETOPO and save it as h5 or npz
##  That would eliminate the gdal dependency which is quite annoying on some machines

gtiff = gdal.Open("../Notebooks/data/ETOPO1_Ice_c_geotiff.tif")

width = gtiff.RasterXSize
height = gtiff.RasterYSize
gt = gtiff.GetGeoTransform()
img = gtiff.GetRasterBand(1).ReadAsArray().T

img = np.fliplr(img)

sliceLeft   = int(180+minX) * 60
sliceRight  = int(180+maxX) * 60
sliceBottom = int(90+minY) * 60
sliceTop    = int(90+maxY) * 60

LandImg = img[ sliceLeft:sliceRight, sliceBottom:sliceTop].T
LandImg = np.flipud(LandImg)


# In[37]:

coords = np.stack((y1, x1)).T

im_coords = coords.copy()
im_coords[:,0] -= minY
im_coords[:,1] -= minX

im_coords[:,0] *= LandImg.shape[0] / (maxY-minY)
im_coords[:,1] *= LandImg.shape[1] / (maxX-minX)
im_coords[:,0] =  LandImg.shape[0] - im_coords[:,0]


# In[38]:

from scipy import ndimage

meshheights = ndimage.map_coordinates(LandImg, im_coords.T, order=3, mode='nearest').astype(np.float)

# Fake geoid for this particular region
# meshheights -= 40.0 * (y1 - minY) / (maxY - minY)


# In[39]:

## Filter out the points we don't want at all

points = meshheights > -50

m1s = meshheights[points]
x1s = x1[points]
y1s = y1[points]

submarine = m1s < 0.0
subaerial = m1s >= 0.0


# ### 3. Create the DM
#
# The points are now read into a DM and refined so that we can achieve very high resolutions. Refinement is achieved by adding midpoints along line segments connecting each point.

# In[75]:

DM = meshtools.create_DMPlex_from_points(x1s, y1s, submarine, refinement_levels=3)
mesh = quagmire.SurfaceProcessMesh(DM, verbose=True)


# In[77]:

x2r = mesh.tri.x
y2r = mesh.tri.y
simplices = mesh.tri.simplices
bmaskr = mesh.bmask


# In[78]:

## Now re-do the allocation of points to the surface.
## In parallel this will be done process by process for a sub-set of points

coords = np.stack((y2r, x2r)).T

im_coords = coords.copy()
im_coords[:,0] -= minY
im_coords[:,1] -= minX

im_coords[:,0] *= LandImg.shape[0] / (maxY-minY)
im_coords[:,1] *= LandImg.shape[1] / (maxX-minX)
im_coords[:,0] =  LandImg.shape[0] - im_coords[:,0]


# In[79]:

from scipy import ndimage

spacing = 1.0
coords = np.stack((y2r, x2r)).T / spacing

meshheights = ndimage.map_coordinates(LandImg, im_coords.T, order=3, mode='nearest')
meshheights = mesh.rbf_smoother(meshheights, iterations=2)

subaerial =  meshheights >= 0.0
submarine = ~subaerial
mesh.bmask = subaerial


mesh.update_height(meshheights*0.001)
raw_height = mesh.height

for ii in range(0,2):

	new_heights=mesh.low_points_local_patch_fill(its=2, smoothing_steps=2)
	mesh._update_height_partial(new_heights)


	for iii in range(0, 5):
		new_heights = mesh.low_points_swamp_fill()
		mesh._update_height_partial(new_heights)
		glows, glow_points = mesh.identify_global_low_points(global_array=False)
		if mesh.rank == 0:
			print("Global low points: ",glows)

		if glows == 0:
			break


	new_heights=mesh.low_points_local_flood_fill(its=10, scale=1.0001)
	mesh._update_height_partial(new_heights)


	glows, glow_points = mesh.identify_global_low_points(global_array=False)
	if mesh.rank == 0:
		print("Global low points: ",glows)

	if glows == 0:
		break


mesh.update_height(new_heights)

nits, flowpaths = mesh.cumulative_flow_verbose(mesh.area*np.ones_like(mesh.height), verbose=True, maximum_its=2500)
flowpaths2 = mesh.rbf_smoother(flowpaths, iterations=1)


# ## 5. Save to HDF5
#
# Save the mesh to an HDF5 file so that it can be visualised in Paraview or read into Quagmire another time. There are two ways to do this:
#
# 1. Using the `save_DM_to_hdf5` function in meshtools, or
# 2. Directly from trimesh interface using `save_mesh_to_hdf5` method.
#
# Remember to execute `petsc_gen_xdmf.py austopo.h5` to create the XML file structure necessary to visualise the mesh in paraview.

# In[85]:

filename = 'AusFlow1a.h5'

decomp = np.ones_like(mesh.height) * mesh.dm.comm.rank

low_points = mesh.identify_low_points()
glow_points = mesh.lgmap_row.apply(low_points.astype(PETSc.IntType))
ctmt = mesh.uphill_propagation(low_points,  glow_points, scale=1.0, its=250, fill=-1).astype(np.int)


mesh.save_mesh_to_hdf5(filename)
mesh.save_field_to_hdf5(filename, height0=raw_height,
								  height=mesh.height,
                                  slope=mesh.slope,		
                                  flowLP=np.sqrt(flowpaths2),
                                  decomp=decomp,
                                  lpcatch=ctmt,
                                  lakes=mesh.height-raw_height)

# to view in Paraview
meshtools.generate_xdmf(filename)
