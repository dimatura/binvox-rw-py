binvox-rw-py
============

Python module to read and write .binvox files. The voxel data is represented as
dense 3-dimensional Numpy arrays in Python, a direct if somewhat wasteful
representation. If your models are large and sparse Scipy.sparse should be of
help.

[Binvox](http://www.cs.princeton.edu/~min/binvox/) is a neat little program to
convert 3D models into binary voxel format. The .binvox file format is a simple
run length encoding format described [here](http://www.cs.princeton.edu/~min/binvox/binvox.html).

Daniel Maturana
dimatura@cmu.edu
