import time
import sys

if sys.version_info[:3] >= (2, 6, 0):
    import multiprocessing as processing
else:
    import processing


def drange(start, stop, step):
    float_list = []
    r = start
    print start
    print stop
    print step
    while r < stop-step:
        float_list.append(r)
        r += step
    return float_list

n_procs = processing.cpu_count()

print "n procs: %s" % n_procs

def run(ncprocs, compare_by_number_of_processors=False):

    shape = None
    x_min, y_min, z_min, x_max, y_max, z_max = get_boundingbox()
    z_delta = abs(z_min - z_max)
    n_slice = 50


    def get_z_coord_for_n_procs(n_slices, n_procs):
        z_slices = drange(z_min, z_max, z_delta/n_slices)
        slices = []
        n = len(z_slices) // n_procs
        for i in range(1, n_procs+1):
            print i
            if i == 1:
                slices.append(z_slices[:i*n])
                pass
            elif i == n_procs:
                slices.append(z_slices[(i-1)*n:])
                pass
            else:
                slices.append(z_slices[(i-1)*n:i*n])
                pass
        return slices

    def arguments(n_slices, n_procs):
        _tmp = []
        slices = get_z_coord_for_n_procs(n_slices, n_procs)
        for i in slices:
            _tmp.append([i, shape])
        return _tmp

    if not compare_by_number_of_processors:
        _results = []
        p = processing.Pool(n_procs)
        _results = p.map(vectorized_slicer, arguments(n_slice, n_procs))
        pass
    else:
        arr = [[i, shape] for i in drange(z_min,z_max, z_delta/n_slice)]
        for i in range(1, 9):
            tA = time.time()
            _results = []
            if i == 1:
                _results = vectorized_slicer,
        pass
    pass

    get_z_coord_for_n_procs(50, ncprocs)


def get_boundingbox(shape=None):
    return 0.0,0.0,0.0,5.0,10.0,15.0
    pass


def foo(x):
    return x*x

if __name__ == '__main__':
    run(n_procs)