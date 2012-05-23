import numpy as np

class BinvoxModel(object):
    """ Holds a binvox model.
    voxels is a 3-dimensional numpy array.
    dims, translate and scale are the model metadata (see binvox docs).
    """
    def __init__(self, voxels, dims, translate, scale):
        self.voxels = voxels
        self.dims = dims
        self.translate = translate
        self.scale = scale

    def clone(self):
        voxels = self.voxels.copy()
        dims = self.dims[:]
        translate = self.translate[:]
        scale = self.scale
        return BinvoxModel(voxels, dims, translate, scale)

    def write(self, fname):
        write_binvox(self, fname)

def read_binvox(fname):
    """ Read binary binvox format.
    Doesn't do any checks on input except for the '#binvox' line.
    Unoptimized.
    """
    fhandle = open(fname, 'rb')
    line = fhandle.readline().strip()
    if not line.startswith('#binvox'):
        raise IOError('Not a binvox file')
    dims = map(int, fhandle.readline().strip().split(' ')[1:])
    translate = map(float, fhandle.readline().strip().split(' ')[1:])
    scale = map(float, fhandle.readline().strip().split(' ')[1:])[0]
    line = fhandle.readline()
    data = np.frombuffer(fhandle.read(), dtype=np.uint8)
    fhandle.close()

    sz = np.prod(dims)
    voxels = np.empty(sz, dtype=np.bool)
    index, end_index = 0, 0
    i = 0
    while i < len(data):
        value, count = map(int, (data[i], data[i+1]))
        end_index = index+count
        voxels[index:end_index] = value
        index = end_index
        i += 2
    voxels = voxels.reshape(dims)
    return BinvoxModel(voxels, dims, translate, scale)

def write_binvox(voxel_model, fname):
    """ Write binary binvox format.
    Unoptimized.
    Doesn't check if the model is 'sane'.
    """
    fhandle = open(fname, 'wb')
    fhandle.write('#binvox 1\n')
    fhandle.write('dim '+' '.join(map(str, voxel_model.dims))+'\n')
    fhandle.write('translate '+' '.join(map(str, voxel_model.translate))+'\n')
    fhandle.write('scale '+str(voxel_model.scale)+'\n')
    fhandle.write('data\n')
    # we assume they are in the correct order (y, z, x)
    voxels_flat = voxel_model.voxels.flatten()
    # keep a sort of state machine for writing run length encoding
    state = voxels_flat[0]
    ctr = 0
    for c in voxels_flat:
        if c==state:
            ctr += 1
            # if ctr hits max, dump
            if ctr==255:
                fhandle.write(chr(state))
                fhandle.write(chr(ctr))
                ctr = 0
        else:
            # if switch state, dump
            fhandle.write(chr(state))
            fhandle.write(chr(ctr))
            state = c
            ctr = 1
    # flush out remainders
    if ctr > 0:
        fhandle.write(chr(state))
        fhandle.write(chr(ctr))
    fhandle.close()

if __name__ == '__main__':
    vm = read_binvox('chair.binvox')
    vm.write('chair_out.binvox')

