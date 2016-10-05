import sys
from section_elements import Section, ElementSection

if sys.version_info[:3] >= (2, 6, 0):
    import multiprocessing as processing
else:
    import processing


def create_section(section_planes, elements):
    section_list = []
    for section_plane in section_planes:
        section = Section()
        for element in elements:
            element_section = ElementSection.create_element_section(section_plane, element)
            if element_section:
                section.add_element_section(element_section)
        section_list.append(section)
    return section_list


def run_multiprocess_cut(s_planes, elements, n_procs):

    def get_section_planes_for_n_procs(section_planes, n_procs):
        divided_section_planes = []
        n = len(section_planes) // n_procs

        for i in range(1, n_procs+1):
            if i == 1:
                divided_section_planes.append(section_planes[:i*n])
            elif i == n_procs:
                divided_section_planes.append(section_planes[(i-1)*n:])
            else:
                divided_section_planes.append(section_planes[(i-1)*n:i*n])
        return divided_section_planes

    def arguments(section_planes, elem, n_procs):
        _tmp = []
        divided_section_planes = get_section_planes_for_n_procs(section_planes, n_procs)
        for i in divided_section_planes:
            print i
            _tmp.append([i, elem])
        return _tmp

    P = processing.Pool(n_procs)
    _results = P.map(create_section, arguments(s_planes, elements,n_procs))
    print _results
    return _results