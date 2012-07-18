# binvox-rw-py

Python module to read and write `.binvox` files. The voxel data is represented as
dense 3-dimensional Numpy arrays in Python, a direct if somewhat wasteful
representation. If your models are large and sparse `scipy.sparse` should be of
help.

[Binvox](http://www.cs.princeton.edu/~min/binvox/) is a neat little program to
convert 3D models into binary voxel format. The `.binvox` file format is a simple
run length encoding format described [here](http://www.cs.princeton.edu/~min/binvox/binvox.html).

## Code example

Suppose you have a voxelized chair model, `chair.binvox` (you can try it on the one in the repo).
Here's how it looks in [`viewvox`](http://www.cs.princeton.edu/~min/viewvox/):

![chair](https://github.com/downloads/dimatura/binvox-rw-py/chair.png)

Then

    >>> import binvox_rw
    >>> model = binvox_rw.read_binvox('chair.binvox')
    >>> model.voxels
    array([[[ True, False, False, ..., False, False, False],
            [ True, False, False, ..., False, False, False],
            [ True, False, False, ..., False, False, False],
            ..., 
           [[False, False, False, ..., False, False, False],
            [False, False, False, ..., False, False, False],
            [False, False, False, ..., False, False, False],
            ..., 
            [False, False, False, ..., False, False, False],
            [False, False, False, ..., False, False, False],
            [False, False, False, ..., False, False, False]]], dtype=bool)
    >>> model.scale
    41.133000000000003
    >>> model.dims
    [32, 32, 32]

You get the idea. `model.voxels` has the boolean 3D array. You can then
manipulate however you wish. For example, here we dilate it with
`scipy.ndimage` and write the dilated version to disk:

    >>> import scipy.ndimage 
    >>> scipy.ndimage.binary_dilation(model.voxels.copy(), output=model.voxels)
    >>> model.write('dilated.binvox')

Then we get a fat chair:

![fat chair](http://github.com/downloads/dimatura/binvox-rw-py/fat_chair.png)

--- 

Daniel Maturana
`dimatura@cmu.edu`
