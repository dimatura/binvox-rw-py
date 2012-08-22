#  Copyright (C) 2012 Daniel Maturana
#  This file is part of binvox-rw-py.
#
#  binvox-rw-py is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  binvox-rw-py is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with binvox-rw-py. If not, see <http://www.gnu.org/licenses/>.
#

"""
Binvox to Numpy and back.

>>> import numpy as np
>>> import binvox_rw
>>> with open('chair.binvox', 'rb') as f:
...     m1 = binvox_rw.read(f)
...
>>> m1.dims
[32, 32, 32]
>>> m1.scale
41.133000000000003
>>> m1.translate
[0.0, 0.0, 0.0]
>>> with open('chair_out.binvox', 'wb') as f:
...     m1.write(f)
...
>>> with open('chair_out.binvox', 'rb') as f:
...     m2 = binvox_rw.read(f)
...
>>> m1.dims==m2.dims
True
>>> m1.scale==m2.scale
True
>>> m1.translate==m2.translate
True
>>> np.all(m1.data==m2.data)
True

"""

import numpy as np
import pdb

class Voxels(object):
    """ Holds a binvox model.
    data is either a three-dimensional numpy boolean array (dense representation)
    or a two-dimensional numpy float array (coordinate representation).

    dims, translate and scale are the model metadata.

    dims are the voxel dimensions, e.g. [32, 32, 32] for a 32x32x32 model.

    scale and translate relate the voxels to the original model coordinates.

    To translate voxel coordinates i, j, k to original coordinates x, y, z:

    x_n = (i+.5)/dims[0]
    y_n = (j+.5)/dims[1]
    z_n = (k+.5)/dims[2]
    x = scale*x_n + translate[0]
    y = scale*y_n + translate[1]
    z = scale*z_n + translate[2]

    """

    def __init__(self, data, dims, translate, scale):
        self.data = data
        self.dims = dims
        self.translate = translate
        self.scale = scale

    def clone(self):
        data = self.data.copy()
        dims = self.dims[:]
        translate = self.translate[:]
        scale = self.scale
        return Voxels(data, dims, translate, scale)

    def write(self, fp):
        write(self, fp)

def read_header(fp):
    """ Read binvox header. Mostly meant for internal use.
    """
    line = fp.readline().strip()
    if not line.startswith('#binvox'):
        raise IOError('Not a binvox file')
    dims = map(int, fp.readline().strip().split(' ')[1:])
    translate = map(float, fp.readline().strip().split(' ')[1:])
    scale = map(float, fp.readline().strip().split(' ')[1:])[0]
    line = fp.readline()
    return dims, translate, scale

def read(fp):
    """ Read binary binvox format as array.

    Returns the model with accompanying metadata.

    Voxels are stored in a three-dimensional numpy array, which is simple and
    direct, but may use a lot of memory for large models. (Storage requirements
    are 8*(d^3) bytes, where d is the dimensions of the binvox model. Numpy
    boolean arrays use a byte per element).

    Doesn't do any checks on input except for the '#binvox' line.
    """
    dims, translate, scale = read_header(fp)
    raw_data = np.frombuffer(fp.read(), dtype=np.uint8)

    sz = np.prod(dims)
    data = np.empty(sz, dtype=np.bool)
    index, end_index = 0, 0
    i = 0
    while i < len(raw_data):
        value, count = map(int, (raw_data[i], raw_data[i+1]))
        end_index = index+count
        data[index:end_index] = value
        index = end_index
        i += 2
    data = data.reshape(dims)
    return Voxels(data, dims, translate, scale)

def read_coords(fp):
    """ Read binary binvox format as coordinates.

    Returns binvox model with voxels in a "coordinate" representation, i.e.  an
    3 x N array where N is the number of nonzero voxels. Each column
    corresponds to a nonzero voxel and the 3 rows are the (x, z, y) coordinates
    of the voxel.  (The odd ordering is due to the way binvox format lays out
    data).  Note that coordinates refer to the binvox voxels, without any
    scaling or translation.

    Use this to save memory if your model is very sparse (mostly empty).

    Doesn't do any checks on input except for the '#binvox' line.
    """
    dims, translate, scale = read_header(fp)
    raw_data = np.frombuffer(fp.read(), dtype=np.uint8)

    sz = np.prod(dims)
    nz_voxels = []
    index, end_index = 0, 0
    i = 0
    while i < len(raw_data):
        value, count = map(int, (raw_data[i], raw_data[i+1]))
        end_index = index+count
        if value:
            nz_voxels.extend(range(index, end_index))
        index = end_index
        i += 2

    nz_voxels = np.array(nz_voxels)
    x = nz_voxels / (dims[0]*dims[1])
    zwpy = nz_voxels % (dims[0]*dims[1]) # z*w + y
    z = zwpy / dims[0]
    y = zwpy % dims[0]
    data = np.vstack((x, z, y))

    return Voxels(data, dims, translate, scale)

def write(voxel_model, fp):
    """ Write binary binvox format.
    Unoptimized.
    Doesn't check if the model is 'sane'.
    """
    fp.write('#binvox 1\n')
    fp.write('dim '+' '.join(map(str, voxel_model.dims))+'\n')
    fp.write('translate '+' '.join(map(str, voxel_model.translate))+'\n')
    fp.write('scale '+str(voxel_model.scale)+'\n')
    fp.write('data\n')
    # we assume they are in the correct order (y, z, x)
    voxels_flat = voxel_model.data.flatten()
    # keep a sort of state machine for writing run length encoding
    state = voxels_flat[0]
    ctr = 0
    for c in voxels_flat:
        if c==state:
            ctr += 1
            # if ctr hits max, dump
            if ctr==255:
                fp.write(chr(state))
                fp.write(chr(ctr))
                ctr = 0
        else:
            # if switch state, dump
            fp.write(chr(state))
            fp.write(chr(ctr))
            state = c
            ctr = 1
    # flush out remainders
    if ctr > 0:
        fp.write(chr(state))
        fp.write(chr(ctr))

def transform_voxels_coords(ijk, T, trunc=False, clip_dim=None):
    """ Transform voxels with matrix T.
    ijk is a 3xN matrix, with each column being a voxel. (Or any arbitrary point xyz).
    T is a 4x4 matrix representing a transform such as a scaling, rotation, etc.

    trunc: if true, output voxels are truncated to integers.
    clip_dim: if set to a positive integer, all voxels for which one coordinate
    is negative or larger or equal than clip_dim will be discarded. This is
    useful when all voxels should be contained within a certain volume.
    """
    # no reordering of coords
    xyzw_a = np.vstack((ijk, np.ones((1, ijk.shape[1]))))
    xyzw_b = np.dot(T, xyzw_a)
    xyzw_b /= xyzw_b[3]
    xyz_b = xyzw_b[:3]
    del xyzw_b
    if trunc:
        xyz_b = xyz_b.astype(np.int)
    if clip_dim is not None and clip_dim > 0:
        valid_ix = ~np.any((xyz_b < 0) | (xyz_b >= clip_dim), 0)
        xyz_b = xyz_b[:,valid_ix]
    return xyz_b

def dense_to_sparse(voxel_data, dtype=np.int):
    """ From dense representation to sparse (coordinate) representation.
    No coordinate reordering.
    """
    if voxel_data.ndim!=3:
        raise ValueError('voxel_data is wrong shape; should be 3D array.')
    return np.asarray(np.nonzero(voxel_data), dtype)

def sparse_to_dense(voxel_data, dims, dtype=np.bool):
    if voxel_data.ndim!=2 or voxel_data.shape[0]!=3:
        raise ValueError('voxel_data is wrong shape; should be 3xN array.')
    if np.isscalar(dims):
        dims = [dims]*3
    dims = np.atleast_2d(dims).T
    # truncate to integers
    xyz = voxel_data.astype(np.int)
    # discard voxels that fall outside dims
    valid_ix = ~np.any((xyz < 0) | (xyz >= dims), 0)
    xyz = xyz[:,valid_ix]
    out = np.zeros(dims.flatten(), dtype=dtype)
    out[tuple(xyz)] = True
    return out

def overlap(vox0, vox1):
    """ Volume of intersection divided by volume of union.
    This requires dense array representation.

    A measure of similarity between two models, with 0 being completely
    disjoint and 1 being equal.

    This is equivalent to treating the voxels as members of a set and computing
    the Jaccard similarity between the sets corresponding to each model.
    """
    return float(np.sum(vox0 & vox1))/np.sum(vox0 | vox1)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
