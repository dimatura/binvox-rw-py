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
    """
    inf = open(fname, 'rb')
    line = inf.readline().strip()
    if not line.startswith('#binvox'):
        raise IOError('Not a binvox file')
    dims = map(int, inf.readline().strip().split(' ')[1:])
    translate = map(float, inf.readline().strip().split(' ')[1:])
    scale = map(float, inf.readline().strip().split(' ')[1:])[0]
    line = inf.readline()
    data = np.frombuffer(inf.read(), dtype=np.uint8)
    inf.close()

    sz = np.prod(dims)
    voxels = np.empty(sz, dtype=np.bool)
    index = 0
    end_index = 0
    i = 0
    while i < len(data):
        value = int(data[i])
        count = int(data[i+1])
        end_index = index+count
        voxels[index:end_index] = value
        index = end_index
        i += 2
    voxels = voxels.reshape(dims)

    return BinvoxModel(voxels, dims, translate, scale)

def write_binvox(voxel_model, fname):
    """ Write binary binvox format.
    """
    outf = open(fname, 'wb')
    outf.write('#binvox 1\n')
    outf.write('dim '+' '.join(map(str, voxel_model.dims))+'\n')
    outf.write('translate '+' '.join(map(str, voxel_model.translate))+'\n')
    outf.write('scale '+str(voxel_model.scale)+'\n')
    outf.write('data\n')
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
                outf.write(chr(state))
                outf.write(chr(ctr))
                ctr = 0
        else:
            # if switch state, dump
            outf.write(chr(state))
            outf.write(chr(ctr))
            #print int(state), ctr
            state = c
            ctr = 1
    # flush out remainders
    if ctr > 0:
        outf.write(chr(state))
        outf.write(chr(ctr))
    outf.close()

if __name__ == '__main__':
    vm = read_binvox('chair.binvox')
    vm.write('chair_out.binvox')

