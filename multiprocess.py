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


def show_section(section_list, display, is_show_section):
    for section in section_list:
        section.set_visible(display, is_show_section)


def multiprocess_show (section_list, display, is_show_section):

    def get_section_list_for_n_procs(sections, n_procs):
        div_section_list = []
        n = len(sections) // n_procs
        for i in range(1, n_procs+1):
            if i == 1:
                div_section_list.append(sections[:i*n])
            elif i == n_procs:
                div_section_list.append(sections[(i-1)*n:])
            else:
                div_section_list.append(sections[(i-1)*n:i*n])
        return div_section_list

    def arguments(sections, display, is_show_section, n_procs):
        _tmp = []
        div_section_list = get_section_list_for_n_procs(sections, n_procs)
        for i in div_section_list:
            _tmp.append([i, display, is_show_section])
        return _tmp

    if __name__ == '__main__':
        n_procs = processing.cpu_count()
        P = processing.Pool(n_procs)
        P.map(create_section, arguments(section_list, display, is_show_section, n_procs))

