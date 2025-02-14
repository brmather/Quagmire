# -*- coding: utf-8 -*-

import pytest

pyfilesystem = pytest.importorskip("fs")
pywebdav = pytest.importorskip("webdavfs")
# ==========================

def test_numpy_import():
    import numpy
    return

def test_scipy_import():
    import scipy
    print("\t\t You have scipy version {}".format(scipy.__version__))
    return

def test_sympy_import():
    try:
        import sympy
        print("\t\t You have sympy version {}".format(sympy.__version__))
    except:
        pass # sympy is not really needed with the current functions module
    return

def test_pint_import():
    import pint
    return

def test_h5py_import():
    import h5py

def test_stripy_import():
    import stripy
    from stripy import spherical_meshes
    from stripy import cartesian_meshes
    from stripy import sTriangulation
    from stripy import Triangulation

def test_quagmire_modules():
    import quagmire
    from quagmire import documentation
    from quagmire import function
    from quagmire import mesh
    from quagmire import tools
    from quagmire import scaling
    from quagmire import QuagMesh
    from quagmire import _fortran

def test_quagmire_cloud_modules():
    import quagmire.tools.cloud  # by default this is not imported by tools
    from quagmire.tools.cloud import quagmire_cloud_fs

def test_jupyter_available():
    from subprocess import check_output
    try:
        result = str(check_output(['which', 'jupyter']))[2:-3]
    except:
        print( "jupyter notebook system is not installed" )
        print( "  - This is needed for notebook examples")
