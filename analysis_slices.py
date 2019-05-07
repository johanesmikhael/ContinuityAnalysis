from OCC.gp import gp_Pnt, gp_Trsf, gp_Dir, gp_Ax1
import OCC.BRepTools
import OCC.GeomLProp
import OCC.TopoDS
import networkx as nx
from geom import *
from util import *
from OCC.BRepPrimAPI import BRepPrimAPI_MakeSphere
from math import floor, ceil
import ifcopenshell
from ifcproducts import *
import OCC.Quantity
from OCC.AIS import AIS_Shape
from OCC.Bnd import Bnd_Box
from OCC.BRepBndLib import brepbndlib_Add
from OCC.GProp import GProp_GProps
from OCC import BRepGProp
from itertools import filterfalse
import grakel
from grakel import GraphKernel
import numpy as np
import SimpSOM as sps
import os
import string

from slice_bounding_box import *


class SliceAnalysis(object):
    def __init__(self, parent):
        self._parent = parent
        self.slice_list = self._parent.slice_list
        self.horizontal_threshold = 0.5
        self.vertical_threshold = 0.5
        self.temporal_width = 2
        self.bounded_item_slice_list = []
        self.width_threshold = 0.5
        self.is_left_surface_visible = True
        self.is_right_surface_visible = True
        self.is_floor_surface_visible = True
        self.is_ceiling_surface_visible = True
        self.is_features_visible = True
        self.is_path_annotation_visible = True
        self.temporal_graph_list = []
        self.temporal_graph_list_label = []
        self.graph_slice_list = []
        self.in_between_graph_list = []
        self.item_labels = dict()
        self.color_dist_offset = 0.
        self.kernel = None
        self.prototype_selectors_index = []
        self.embedded_graph = None
        self.annotations = []
        self.som_size = 50
        self.init_learning_rate = 0.01
        self.num_epoch = 100000
        self.clusters = None

    def get_parent(self):
        return self._parent

    def perform(self):
        for i, slice in enumerate(self.slice_list):
            print("performing slice analysis on slice %d" % i)
            left_slice = []
            right_slice = []
            bottom_slice = []
            upper_slice = []
            feature_slice = []
            slices = [left_slice, right_slice, bottom_slice, upper_slice, feature_slice]
            for element_sliced in slice.get_element_slice_list():
                if isinstance(element_sliced.element, (Wall, Column, Door, Window, CurtainWall)):
                    print("this is wall-related element")
                    SliceAnalysis.get_wall_bounding_box(self, element_sliced, left_slice, right_slice)
                if isinstance(element_sliced.element, Slab):
                    print("this is floor-related element")
                    SliceAnalysis.get_floor_bounding_box(self, element_sliced, bottom_slice)
                if isinstance(element_sliced.element, Covering):
                    print("this is ceiling-related element")
                    SliceAnalysis.get_ceiling_bounding_box(self, element_sliced, upper_slice)
                if isinstance(element_sliced.element, (Railing, Furniture, FlowTerminal)):
                    print("this is room features or furnitures")
                    SliceAnalysis.get_features_bounding_box(self, element_sliced, feature_slice)
            for side_slice in slices:
                self.remove_small_bounded_item(i, side_slice, self.width_threshold, self.get_parent().section_distance)
            corner = self.get_corner(slices)
            for position, side_slice in enumerate(slices):
                if 0 <= position <= 3:
                    self.simplify_bounding_box(side_slice, position, corner)
                self.create_topods(side_slice)
                self.display_face(side_slice)
            self.bounded_item_slice_list.append(slices)

    def simplify_bounding_box(self, slice, position, corner):
        def get_bottom_z(item):
            return item.z_min()

        def get_negative_top_z(item):
            return -item.z_max()

        def get_negative_right_x(item):
            return -item.x_max()

        def get_left_x(item):
            return item.x_min()

        def get_absolute_center_x(item):
            return abs(0.5 * (item.x_min() + item.x_max()))

        if position == 0:
            slice.sort(key=get_bottom_z)
            slice.sort(key=get_negative_right_x)
        if position == 1:
            slice.sort(key=get_bottom_z)
            slice.sort(key=get_left_x)
        if position == 2:
            slice.sort(key=get_absolute_center_x)
            slice.sort(key=get_negative_top_z)
        if position == 3:
            slice.sort(key=get_absolute_center_x)
            slice.sort(key=get_bottom_z)
        domain_marker = []
        for bounded_item in slice:
            bound = None
            if position == 0 or position == 1:
                bound = (bounded_item.z_min(), bounded_item.z_max())
            if position == 2 or position == 3:
                bound = (bounded_item.x_min(), bounded_item.x_max())
            if bound:
                for i in bound:
                    if not (i in domain_marker):
                        domain_marker.append(i)
        self.trim_domain_marker(domain_marker, position, corner)
        domain_list, domain_dict = self.construct_domain_map(domain_marker, slice, 1e-2, position)
        merged_domain_list = self.construct_merged_domain_list(domain_list, domain_dict)
        self.modify_slice(merged_domain_list, domain_dict, slice, position)

    def calculate_kernel(self):
        # sp_kernel = GraphKernel(kernel={"name": "shortest_path"}, normalize=True)
        wl_kernel = GraphKernel(kernel=[{"name": "weisfeiler_lehman", "niter": 5}, {"name": "subtree_wl"}],
                                normalize=True)
        grakel_graphs = []
        for i, g in enumerate(self.temporal_graph_list):
            print(i)
            print(g)
            adj = nx.to_numpy_matrix(g)
            nodes = g.nodes()
            print(adj)
            print(nodes)
            node_dict = dict()
            for k, l in enumerate(nodes):
                node_dict[k] = type(l.element).__name__
            h = [adj.tolist(), node_dict]
            grakel_graphs.append(h)
        # k_train = sp_kernel.fit_transform(grakel_graphs)
        self.kernel = wl_kernel.fit_transform(grakel_graphs)
        print(self.kernel)
        self.select_prototype_selectors()
        self.embed_graph()

    def embed_graph(self):
        embed_list = []
        for row in self.kernel:
            print(row)
            embedded_vector = []
            for index in self.prototype_selectors_index:
                print(index)
                print(row.item(index))
                embedded_vector.append(row.item(index))
            embed_list.append(embedded_vector)
        self.embedded_graph = np.array(embed_list)
        print(self.embedded_graph)

    def select_prototype_selectors(self):
        for i in range(0, 9):
            if i == 0:
                init_index = int(len(self.temporal_graph_list) / 2.0)
                self.prototype_selectors_index.append(init_index)
            else:
                row = self.kernel[self.prototype_selectors_index[-1]]
                copy_row = row.copy()
                '''for k in self.prototype_selectors_index:
                    copy_row.put(k, 1.0)'''
                for j in range(0, len(self.kernel)):
                    sum = 0
                    for index in self.prototype_selectors_index:
                        selected_row = self.kernel[index]
                        sum += selected_row[j]
                    copy_row.put(j, sum)
                furthest_index = copy_row.argmin()
                self.prototype_selectors_index.append(furthest_index)
        print("selected index")
        print(self.prototype_selectors_index)

    def generate_som(self):
        labels = []
        for x in range(0, len(self.embedded_graph)):
            labels.append(x)
        net = sps.somNet(self.som_size, self.som_size, self.embedded_graph, PBC=True)
        net.train(self.init_learning_rate, self.num_epoch)
        net.save('filename_weights')
        for i in range(0, len(self.prototype_selectors_index)):
            net.nodes_graph(colnum=i)
        net.diff_graph()
        net.project(self.embedded_graph, labels=labels)
        self.clusters = net.cluster(self.embedded_graph, type='qthresh')
        self.create_som_graph()
        self.write_data()

    def save_graph(self):
        file_name = self.get_parent().get_visualizer().parent.filename.split("/")[-1].split(".")[0]
        print(file_name)
        for i, graph in enumerate(self.temporal_graph_list):
            if not nx.is_empty(graph):
                h = nx.relabel_nodes(graph, self.item_labels)
                dir = os.getcwd()
                name = dir + "\export\\"+file_name+"-graph-%d.graphml" % i
                nx.write_graphml(h, name)
        print("finish save graph")

    def write_data(self):
        for i, graph in enumerate(self.temporal_graph_list):
            if not nx.is_empty(graph):
                h = nx.relabel_nodes(graph, self.item_labels)
                name = "graph-%d.graphml" % i
                nx.write_graphml(h, name)
        f = open("data.txt", "w")
        f.write(str(self.prototype_selectors_index) + "\n")
        f.write(str(self.som_size) + "\n")
        f.write(str(self.init_learning_rate) + "\n")
        f.write(str(self.num_epoch) + "\n")
        f.close()

    def create_som_graph(self):
        start_color = Color.create_qcolor_from_rgb_tuple((255, 0, 0))
        end_color = Color.create_qcolor_from_rgb_tuple((0, 0, 255))
        start = 0.0
        end = len(self.clusters) - 1
        c_interp = ColorInterpolation(start_color, end_color, start, end)
        dy = self.get_parent().section_distance
        z = self.get_parent().path_elevation
        display = self.get_parent().get_visualizer().canvas.get_display()
        for i, cluster in enumerate(self.clusters):
            print("start display cluster %d" % i)
            q_color = c_interp.get_interpolation_from_value(i)
            r = q_color.redF()
            g = q_color.greenF()
            b = q_color.blueF()
            print(r, g, b)
            for item in cluster:
                y = (item + self.temporal_width) * dy + dy / 2.0
                origin_point = gp_Pnt(0, y, z)
                topods = create_box_from_center(origin_point, dy, dy, dy)
                ais_color = OCC.Quantity.Quantity_Color(r, g, b, OCC.Quantity.Quantity_TOC_RGB)
                ais_object = AIS_Shape(topods)
                ais_object.SetCurrentFacingModel(OCC.Aspect.Aspect_TOFM_BOTH_SIDE)
                ais_object.SetColor(ais_color)
                display.Context.Display(ais_object.GetHandle())
                self.annotations.append([topods, ais_object.GetHandle()])

    def create_graph(self):
        for i in range(0, len(self.bounded_item_slice_list)):
            self.create_slice_graph(i)
            self.create_in_between_graph(i)
        self.construct_temporal_graph()
        print("finish creating graph")

        '''import matplotlib.pyplot as plt
        for i, graph in enumerate(self.temporal_graph_list):
            print(graph.adj)
            if not nx.is_empty(graph):
                plt.subplot(4, 5, 1 + i)
                h = nx.relabel_nodes(graph, self.item_labels)
                self.temporal_graph_list_label.append(h)
                print(h.adj)
                pos = nx.spring_layout(h)
                nx.draw(h, pos)
                nx.draw_networkx_labels(h, pos)
        plt.show()'''


    def toggle_path_annotation_view(self):
        display = self.get_parent().get_visualizer().canvas.get_display()
        if self.is_path_annotation_visible:
            for item in self.annotations:
                display.Context.Erase(item[1])
        else:
            for item in self.annotations:
                display.Context.Display(item[1])
        self.is_path_annotation_visible = not self.is_path_annotation_visible

    def create_slice_graph(self, i):
        print("graph for %d slice" % i)
        G = nx.Graph()
        print(G)
        for a, side_slice in enumerate(self.bounded_item_slice_list[i]):
            for b, item in enumerate(side_slice):
                self.item_labels[item] = type(item.element).__name__ + ("-i%d" % i) + ("a%d" % a) + \
                                         ("b%d-%s" % (b, item.element.name))
                G.add_node(item)
                is_connected = None
                closest_item = None
                min_distance = None
                for c, test_side_slice in enumerate(self.bounded_item_slice_list[i]):
                    for d, test_item in enumerate(test_side_slice):
                        if (a, b) != (c, d):
                            is_connect = item.is_connect(test_item)
                            if not is_connect:
                                if a == 4 and c != 4:  # avoid measuring distance from feature list
                                    distance = item.distance(test_item)
                                    if distance > 0:
                                        if not min_distance:
                                            min_distance = distance
                                            closest_item = test_item
                                        else:
                                            if distance < min_distance:
                                                min_distance = distance
                                                closest_item = test_item
                            else:  # if connected
                                is_connected = is_connect
                                color_distance = item.get_color_distance(test_item) + self.color_dist_offset
                                G.add_edge(item, test_item, weight=color_distance)
                if not is_connected and a == 4:  # only features
                    color_distance = item.get_color_distance(closest_item) + self.color_dist_offset
                    G.add_edge(item, closest_item, weight=color_distance)
        self.graph_slice_list.append(G)

    def create_in_between_graph(self, i):
        print("in between graph for %d slice" % i)
        G = nx.Graph()
        if i < len(self.bounded_item_slice_list) - 1:
            slice1 = self.bounded_item_slice_list[i]
            slice2 = self.bounded_item_slice_list[i + 1]
            for j in range(0, 5):
                self.get_slice_connectivity(slice1[j], slice2[j], G)
        self.in_between_graph_list.append(G)

    def get_slice_connectivity(self, item_list1, item_list2, graph):
        for bounded_item1 in item_list1:
            for bounded_item2 in item_list2:
                is_adjacent = bounded_item1.is_adjacent_horizontal(bounded_item2)
                if is_adjacent:
                    color_distance = bounded_item1.get_color_distance(bounded_item2) + self.color_dist_offset
                    graph.add_edge(bounded_item1, bounded_item2, weight=color_distance)

    def construct_temporal_graph(self):
        for i in range(self.temporal_width, len(self.graph_slice_list) - self.temporal_width):
            graphs = []
            for k in range(-self.temporal_width, self.temporal_width + 1):
                graph = self.graph_slice_list[i + k]
                graphs.append(graph)
                if k < self.temporal_width:
                    in_between_graph = self.in_between_graph_list[i + k]
                    graphs.append(in_between_graph)
            temporal_graph = nx.compose_all(graphs)
            self.temporal_graph_list.append(temporal_graph)

    def toggle_left_surface_view(self):
        if self.is_left_surface_visible:
            self.hide(self.bounded_item_slice_list, 0)
        else:
            self.show(self.bounded_item_slice_list, 0)
        self.is_left_surface_visible = not self.is_left_surface_visible

    def toggle_right_surface_view(self):
        if self.is_right_surface_visible:
            self.hide(self.bounded_item_slice_list, 1)
        else:
            self.show(self.bounded_item_slice_list, 1)
        self.is_right_surface_visible = not self.is_right_surface_visible

    def toggle_floor_surface_view(self):
        if self.is_floor_surface_visible:
            self.hide(self.bounded_item_slice_list, 2)
        else:
            self.show(self.bounded_item_slice_list, 2)
        self.is_floor_surface_visible = not self.is_floor_surface_visible

    def toggle_ceiling_surface_view(self):
        if self.is_ceiling_surface_visible:
            self.hide(self.bounded_item_slice_list, 3)
        else:
            self.show(self.bounded_item_slice_list, 3)
        self.is_ceiling_surface_visible = not self.is_ceiling_surface_visible

    def toggle_feature_view(self):
        if self.is_features_visible:
            self.hide(self.bounded_item_slice_list, 4)
        else:
            self.show(self.bounded_item_slice_list, 4)
        self.is_features_visible = not self.is_features_visible

    @staticmethod
    def modify_slice(merged_domain_list, domain_dict, slice, position):
        slice.clear()
        for domain_list in merged_domain_list:
            bounded_item = domain_dict[domain_list[0]]
            bounding_box = bounded_item.bounding_box
            xmin, ymin, zmin, xmax, ymax, zmax = bounding_box.Get()
            bound_min = domain_list[0][0]
            bound_max = domain_list[-1][-1]
            bounded_item_copy = bounded_item.copy()
            if position == 0 or position == 1:
                bounded_item_copy.create_bounding_box(xmin, ymin, bound_min, xmax, ymax, bound_max)
            if position == 2 or position == 3:
                bounded_item_copy.create_bounding_box(bound_min, ymin, zmin, bound_max, ymax, zmax)
            slice.append(bounded_item_copy)

    @staticmethod
    def construct_merged_domain_list(domain_list, domain_dict):
        merged_domain_list = []
        for i, domain in enumerate(domain_list):
            if i == 0:
                merged_domain_list.append([domain])
            else:
                if domain_dict[domain] == domain_dict[merged_domain_list[-1][-1]]:  # if the domain pointing to the
                    # same item
                    merged_domain_list[-1].append(domain)
                else:
                    merged_domain_list.append([domain])
        return merged_domain_list

    @staticmethod
    def construct_domain_map(domain_marker, slice, tol, position):
        domain_marker = sort_remove_similar_value_in_list(domain_marker, tol)
        domain_list = []
        domain_dict = dict()
        for i in range(0, len(domain_marker) - 1):
            domain = (domain_marker[i], domain_marker[i + 1])
            domain_list.append(domain)
            for bounded_item in slice:
                domain_center = 0.5 * (domain[0] + domain[1])
                if position == 0 or position == 1:
                    bound = (bounded_item.z_min(), bounded_item.z_max())
                if position == 2 or position == 3:
                    bound = (bounded_item.x_min(), bounded_item.x_max())
                if bound[0] < domain_center < bound[1]:  # the center of bounded item is within domain:
                    domain_dict[domain] = bounded_item
                    break
        return domain_list, domain_dict

    @staticmethod
    def create_topods(slice):
        for bounded_item in slice:
            bounded_item.create_topods()

    @staticmethod
    def display_face(slice):
        for bounded_item in slice:
            bounded_item.display_item()

    @staticmethod
    def get_wall_bounding_box(analyzer, element_sliced, left_slice, right_slice):
        bounded_item = SliceBoundingBox(analyzer, element_sliced, element_sliced.is_decomposed)
        bounded_item.set_left_right_side(analyzer.vertical_threshold)
        if bounded_item.position == 0:
            print("left")
            print(bounded_item.element)
            left_slice.append(bounded_item)
        if bounded_item.position == 1:
            print("right")
            print(bounded_item.element)
            right_slice.append(bounded_item)

    @staticmethod
    def get_floor_bounding_box(analyzer, element_sliced, bottom_slice):
        bounded_item = SliceBoundingBox(analyzer, element_sliced, element_sliced.is_decomposed)
        bounded_item.set_bottom_side(analyzer.horizontal_threshold)
        if bounded_item.position == 2:
            print(bounded_item.element)
            bottom_slice.append(bounded_item)

    @staticmethod
    def get_ceiling_bounding_box(analyzer, element_sliced, upper_slice):
        bounded_item = SliceBoundingBox(analyzer, element_sliced, element_sliced.is_decomposed)
        bounded_item.set_upper_side(analyzer.horizontal_threshold)
        if bounded_item.position == 3:
            print(bounded_item.element)
            upper_slice.append(bounded_item)

    @staticmethod
    def get_features_bounding_box(analyzer, element_sliced, feature_slice):
        bounded_item = SliceBoundingBox(analyzer, element_sliced, element_sliced.is_decomposed)
        print(bounded_item.element)
        feature_slice.append(bounded_item)

    @staticmethod
    def remove_small_bounded_item(i, slice_element_list, limit, slice_width):
        y_bound_min = i * slice_width
        y_bound_max = (i + 1) * slice_width

        def is_small(bounded_item):
            y_min = bounded_item.y_min()
            y_max = bounded_item.y_max()
            if (y_max - y_min) < slice_width * limit:
                print("%s is small" % bounded_item.element.name)
                print(y_max - y_min)
                return True
            else:
                bounded_item.set_y_min(y_bound_min)
                bounded_item.set_y_max(y_bound_max)
                print("%s is is ok" % bounded_item.element.name)
                print(bounded_item.y_min())
                print(bounded_item.y_max())
                return False

        slice_element_list[:] = filterfalse(is_small, slice_element_list)

    @staticmethod
    def get_corner(slices):
        x_bottom_min = None  # 0
        x_bottom_max = None  # 1
        x_top_min = None  # 2
        x_top_max = None  # 3
        z_left_min = None  # 4
        z_left_max = None  # 5
        z_right_min = None  # 6
        z_right_max = None  # 7

        def get_min_x(item):
            return item.x_min()

        def get_neg_max_x(item):
            return -item.x_max()

        def get_bottom_z(item):
            return item.z_min()

        def get_neg_top_z(item):
            return -item.z_max()

        tol = 1e-2
        for i, slice in enumerate(slices):
            if i == 0:
                bottom_items = SliceAnalysis.get_similar_bottom_items(slice, tol)
                if bottom_items:
                    bottom_items.sort(key=get_neg_max_x)
                    x_bottom_min = bottom_items[0].x_max()
                top_items = SliceAnalysis.get_similar_top_items(slice, tol)
                if top_items:
                    top_items.sort(key=get_neg_max_x)
                    x_top_min = top_items[0].x_max()
            if i == 1:
                bottom_items = SliceAnalysis.get_similar_bottom_items(slice, tol)
                if bottom_items:
                    bottom_items.sort(key=get_min_x)
                    x_bottom_max = bottom_items[0].x_min()
                top_items = SliceAnalysis.get_similar_top_items(slice, tol)
                if top_items:
                    top_items.sort(key=get_min_x)
                    x_top_max = top_items[0].x_min()
            if i == 2:
                left_items = SliceAnalysis.get_similar_left_items(slice, tol)
                if left_items:
                    left_items.sort(key=get_neg_top_z)
                    z_left_min = left_items[0].z_max()
                right_items = SliceAnalysis.get_similar_right_items(slice, tol)
                if right_items:
                    right_items.sort(key=get_neg_top_z)
                    z_right_min = right_items[0].z_max()
            if i == 3:
                left_items = SliceAnalysis.get_similar_left_items(slice, tol)
                if left_items:
                    left_items.sort(key=get_bottom_z)
                    z_left_max = left_items[0].z_min()
                right_items = SliceAnalysis.get_similar_right_items(slice, tol)
                if right_items:
                    right_items.sort(key=get_bottom_z)
                    z_right_max = right_items[0].z_min()
        corner = [x_bottom_min, x_bottom_max, x_top_min, x_top_max, z_left_min, z_left_max, z_right_min, z_right_max]
        return corner

    @staticmethod
    def get_similar_bottom_items(slice, tol):
        def get_min_z(item):
            return item.z_min()

        slice.sort(key=get_min_z)
        bottom_items = []
        for item in slice:
            if len(bottom_items) == 0:
                bottom_items.append(item)
            else:
                if item.z_min() - tol < bottom_items[-1].z_min() < item.z_min() + tol:
                    bottom_items.append(item)
                else:
                    break
        if len(bottom_items) > 0:
            return bottom_items
        else:
            return None

    @staticmethod
    def get_similar_top_items(slice, tol):
        def get_neg_max_z(item):
            return -item.z_max()

        slice.sort(key=get_neg_max_z)

        top_items = []
        for item in slice:
            if len(top_items) == 0:
                top_items.append(item)
            else:
                if item.z_max() - tol < top_items[-1].z_max() < item.z_max() + tol:
                    top_items.append(item)
                else:
                    break
        if len(top_items) > 0:
            return top_items
        else:
            return None

    @staticmethod
    def get_similar_left_items(slice, tol):
        def get_min_x(item):
            return item.x_min()

        slice.sort(key=get_min_x)
        left_items = []
        for item in slice:
            if len(left_items) == 0:
                left_items.append(item)
            else:
                if item.x_min() - tol < left_items[-1].x_min() < item.x_min() + tol:
                    left_items.append(item)
                else:
                    break
        if len(left_items) > 0:
            return left_items
        else:
            return None

    @staticmethod
    def get_similar_right_items(slice, tol):
        def get_neg_max_x(item):
            return -item.x_max()

        slice.sort(key=get_neg_max_x)
        right_items = []
        for item in slice:
            if len(right_items) == 0:
                right_items.append(item)
            else:
                if item.x_max() - tol < right_items[-1].x_max() < item.x_max() + tol:
                    right_items.append(item)
                else:
                    break
        if len(right_items) > 0:
            return right_items
        else:
            return None

    @staticmethod
    def trim_domain_marker(domain_marker, position, corner):
        print(corner)
        domain_marker.sort()
        if position == 0:
            for i, point in enumerate(domain_marker):
                if corner[4]:
                    if point <= corner[4]:
                        domain_marker[i] = corner[4]
                if corner[5]:
                    if point >= corner[5]:
                        domain_marker[i] = corner[5]
        if position == 1:
            for i, point in enumerate(domain_marker):
                if corner[6]:
                    if point <= corner[6]:
                        domain_marker[i] = corner[6]
                if corner[7]:
                    if point >= corner[7]:
                        domain_marker[i] = corner[7]
        if position == 2:
            for i, point in enumerate(domain_marker):
                if corner[0]:
                    if point <= corner[0]:
                        domain_marker[i] = corner[0]
                if corner[1]:
                    if point >= corner[1]:
                        domain_marker[i] = corner[1]
        if position == 3:
            for i, point in enumerate(domain_marker):
                if corner[2]:
                    if point <= corner[2]:
                        domain_marker[i] = corner[2]
                if corner[3]:
                    if point >= corner[3]:
                        domain_marker[i] = corner[3]

    @staticmethod
    def show(slice_list, index):
        for slice in slice_list:
            for item in slice[index]:
                item.show()

    @staticmethod
    def hide(slice_list, index):
        for slice in slice_list:
            for item in slice[index]:
                item.hide()


class WallAnalysis(object):
    def __init__(self, parent):
        self._parent = parent
        self.slice_list = self._parent.slice_list
        self.point_lists = []
        self.left_faces = []
        self.right_faces = []
        self.continuity_edge_left = []
        self.continuity_edge_right = []
        self.internal_continuity_edge_left = []
        self.internal_continuity_edge_right = []
        self.is_left_surface = True
        self.is_right_surface = True
        self.notation_offset = 0.02
        self.notation_radius = 0.05
        self.vertical_threshold = 0.5
        pass

    '''
    bounded item dict:
    "bounding_box"
    "material"
    "element"
    "ais"
    "topods_face"
    "center"
    '''

    def get_parent(self):
        return self._parent

    def perform(self):
        for i, slice in enumerate(self.slice_list):
            print("performing wall analysis on slice %d" % i)
            slice_left = []
            slice_right = []
            for element_slice in slice.get_element_slice_list():
                if isinstance(element_slice.element, (Wall, Column, Door, Window, CurtainWall)):
                    print(element_slice.element)
                    WallAnalysis.analyze_by_bounding_box(self, element_slice, slice_left, slice_right)
            slice_left = WallAnalysis.remove_small_bounded_item(slice_left, self.vertical_threshold, self.get_parent()
                                                                .section_distance)
            slice_left = WallAnalysis.simplify_bounding_box(self, slice_left, True)
            self.left_faces.append(slice_left)
            slice_right = WallAnalysis.remove_small_bounded_item(slice_right, self.vertical_threshold, self.get_parent()
                                                                 .section_distance)
            slice_right = WallAnalysis.simplify_bounding_box(self, slice_right, False)
            self.right_faces.append(slice_right)
        self.display_left_faces()
        self.display_right_faces()
        pass

    @staticmethod
    def remove_small_bounded_item(slice, width_threshold, max_width):
        new_slice = []
        y_min_slice, y_max_slice = None, None
        slice.sort(key=get_bound_width)
        for bounded_item in slice:
            bound_width = get_bound_width(bounded_item)
            y_bound = get_y_bound(bounded_item)
            if not y_min_slice or y_min_slice > y_bound[0]:
                y_min_slice = y_bound[0]
            if not y_max_slice or y_max_slice < y_bound[1]:
                y_max_slice = y_bound[1]
            print(bound_width)
            if bound_width >= max_width * width_threshold:
                print("bounded item for %s pass %f width threshold" % (bounded_item["element"], width_threshold))
                new_slice.append(bounded_item)
        if len(new_slice) == 0 and len(slice) > 0:
            new_slice.append(slice[-1])
        for bounded_item in new_slice:
            x_min, y_min, z_min, x_max, y_max, z_max = bounded_item["bounding_box"].Get()
            bounded_item["bounding_box"].Update(x_min, y_min_slice, z_min, x_max, y_max_slice, z_max)
        return new_slice

    @staticmethod
    def simplify_bounding_box(analyzer, slice, is_left):
        slice.sort(key=getz)
        if is_left:
            slice.sort(key=getx_reversed)
        else:
            slice.sort(key=getx)
        print("start defining domain")
        domain_marker = []
        for bounded_item in slice:
            print(bounded_item)
            z_bound = get_z_bound(bounded_item)
            for z in z_bound:
                if not (z in domain_marker):
                    domain_marker.append(z)
        print("constructing domain map")
        domain_list, domain_dict = WallAnalysis.construct_domain_map(domain_marker, slice, 1e-2)
        print("map elements to domain")
        merged_domain_list = WallAnalysis.construct_merged_domain_list(domain_list, domain_dict)
        return WallAnalysis.create_new_slice(analyzer, merged_domain_list, domain_dict, is_left)

    @staticmethod
    def create_new_slice(analyzer, merged_domain_list, domain_dict, is_left):
        slice_copy = []
        for domain_list in merged_domain_list:
            print("----")
            bounded_item = domain_dict[domain_list[0]]
            bound_min = domain_list[0][0]
            bound_max = domain_list[-1][-1]
            bounded_item_copy = copy_bounded_item(bounded_item)
            bounding_box = bounded_item["bounding_box"]
            xmin, ymin, zmin, xmax, ymax, zmax = bounding_box.Get()
            bounded_item_copy["bounding_box"].Update(xmin, ymin, bound_min, xmax, ymax, bound_max)
            print(bounded_item_copy["element"])
            print(get_z_bound(bounded_item_copy))
            if is_left:
                bounding_box_surface, center = WallAnalysis \
                    .get_right_face(analyzer.notation_offset, bounded_item_copy["bounding_box"])
                bounded_item_copy["topods_face"] = bounding_box_surface
                bounded_item_copy["center"] = center
            else:
                bounding_box_surface, center = WallAnalysis. \
                    get_left_face(analyzer.notation_offset, bounded_item_copy["bounding_box"])
                bounded_item_copy["topods_face"] = bounding_box_surface
                bounded_item_copy["center"] = center
            slice_copy.append(bounded_item_copy)
        return slice_copy

    @staticmethod
    def construct_merged_domain_list(domain_list, domain_dict):
        merged_domain_list = []
        for i, domain in enumerate(domain_list):
            if i == 0:
                merged_domain_list.append([domain])
            else:
                if domain_dict[domain] == domain_dict[merged_domain_list[-1][-1]]:  # if the domain pointing to the
                    # same item
                    merged_domain_list[-1].append(domain)
                else:
                    merged_domain_list.append([domain])
        return merged_domain_list

    @staticmethod
    def construct_domain_map(domain_marker, slice, tol):
        domain_marker = sort_remove_similar_value_in_list(domain_marker, tol)
        domain_list = []
        domain_dict = dict()
        print("domain_marker_length %d" % len(domain_marker))
        for i in range(0, len(domain_marker) - 1):
            print(i)
            domain = (domain_marker[i], domain_marker[i + 1])
            domain_list.append(domain)
            for bounded_item in slice:
                domain_center = 0.5 * (domain[0] + domain[1])
                print(domain_center)
                z_bound = get_z_bound(bounded_item)
                print(z_bound)
                if z_bound[0] < domain_center < z_bound[1]:  # the center of bounded item is within doimain:
                    domain_dict[domain] = bounded_item
                    break
        return domain_list, domain_dict

    def toggle_left_surface_view(self):
        if self.is_left_surface:
            hide_surface(self, self.left_faces)
        else:
            show_surface(self, self.left_faces)
        self.is_left_surface = not self.is_left_surface

    def toggle_right_surface_view(self):
        if self.is_left_surface:
            hide_surface(self, self.right_faces)
        else:
            show_surface(self, self.right_faces)
        self.is_left_surface = not self.is_left_surface

    def display_left_faces(self):
        for slices in self.left_faces:
            for bounded_item in slices:
                display_face(bounded_item, self)

    def display_right_faces(self):
        for slice in self.right_faces:
            for bounded_item in slice:
                display_face(bounded_item, self)

    @staticmethod
    def get_right_face(offset, bounding_box):
        corner_min = bounding_box.CornerMin()
        corner_max = bounding_box.CornerMax()
        x_min = corner_min.X()
        y_min = corner_min.Y()
        z_min = corner_min.Z()
        x_max = corner_max.X()
        y_max = corner_max.Y()
        z_max = corner_max.Z()
        p1 = gp_Pnt(x_max, y_min, z_min)
        p2 = gp_Pnt(x_max, y_max, z_min)
        p3 = gp_Pnt(x_max, y_max, z_max)
        p4 = gp_Pnt(x_max, y_min, z_max)
        center_point = gp_Pnt(x_max + offset, 0.5 * (y_min + y_max), 0.5 * (z_min + z_max))
        bounding_box_surface = create_rectangular_face(p1, p2, p3, p4)
        return bounding_box_surface, center_point

    @staticmethod
    def get_left_face(offset, bounding_box):
        corner_min = bounding_box.CornerMin()
        corner_max = bounding_box.CornerMax()
        x_min = corner_min.X()
        y_min = corner_min.Y()
        z_min = corner_min.Z()
        x_max = corner_max.X()
        y_max = corner_max.Y()
        z_max = corner_max.Z()
        p1 = gp_Pnt(x_min, y_min, z_min)
        p2 = gp_Pnt(x_min, y_max, z_min)
        p3 = gp_Pnt(x_min, y_max, z_max)
        p4 = gp_Pnt(x_min, y_min, z_max)
        center_point = gp_Pnt(x_min - offset, 0.5 * (y_min + y_max), 0.5 * (z_min + z_max))
        bounding_box_surface = create_rectangular_face(p1, p2, p3, p4)
        return bounding_box_surface, center_point

    @staticmethod
    def analyze_by_bounding_box(analyzer, element_slice, slice_left, slice_right):
        print("begin_analysis_by_bounding_box")
        if not element_slice.is_decomposed:
            bounding_box = element_slice.bounding_box
            major_material = None
            if len(element_slice.shapes_slice) > 0:
                print("analyzing element_slice %s" % element_slice.name)
                print(element_slice.element)
                print(len(element_slice.shapes_slice))
                material_area_dict = dict()
                for shape_slice in element_slice.shapes_slice:
                    print("analysing shape_slice %s" % shape_slice)
                    material = shape_slice[1]
                    area = get_shape_area(shape_slice[0])
                    print(area)
                    if material in material_area_dict:
                        material_area_dict[material] += area
                    else:
                        material_area_dict[material] = area
                major_material = get_major_material(material_area_dict)
                print(major_material.name)
                WallAnalysis.put_into_left_right_slice(analyzer, element_slice.element, bounding_box, major_material,
                                                       slice_left, slice_right)
            else:
                print("this is it")
                pass
        else:
            bounding_box_new = Bnd_Box()
            material_dict = dict()
            analyze_decomposed(element_slice, bounding_box_new, material_dict)
            print("decomposed element")
            major_material = get_major_material(material_dict)
            WallAnalysis.put_into_left_right_slice(analyzer, element_slice.element, bounding_box_new, major_material,
                                                   slice_left,
                                                   slice_right)

    @staticmethod
    def put_into_left_right_slice(analyzer, parent_element, bounding_box, material, slice_left, slice_right):
        bounded_element = dict()
        bounded_element["bounding_box"] = bounding_box
        bounded_element["material"] = material
        bounded_element["element"] = parent_element
        corner_min = bounding_box.CornerMin()
        corner_max = bounding_box.CornerMax()
        x_min = corner_min.X()
        x_max = corner_max.X()
        x_median = 0.5 * (x_min + x_max)
        '''if x_median < 0:
            slice_left.append(bounded_element)
        if x_median > 0:
            slice_right.append(bounded_element)'''
        if x_max < -analyzer.vertical_treshold:
            slice_left.append(bounded_element)
        if x_min > analyzer.vertical_treshold:
            slice_right.append(bounded_element)

    def get_continuity(self):
        # WallAnalysis.get_internal_connectivity(self, self.left_faces, self.internal_continuity_edge_left,
        #                                       self.notation_radius)
        WallAnalysis.get_external_connectivity(self, self.left_faces, self.continuity_edge_left, self.notation_radius)
        # WallAnalysis.get_internal_connectivity(self, self.right_faces, self.internal_continuity_edge_right,
        #                                       self.notation_radius)
        WallAnalysis.get_external_connectivity(self, self.right_faces, self.continuity_edge_right, self.notation_radius)

    @staticmethod
    def get_internal_connectivity(analyzer, slice_list, continuity_edge, radius):
        for slice in slice_list:
            edge_list = []
            for i, bounded_item_1 in enumerate(slice):
                for j, bounded_item_2 in enumerate(slice):
                    if not i == j:  # not refer to the same instance
                        edge = WallAnalysis.get_wall_edge(analyzer, bounded_item_1, bounded_item_2, radius)
                        if edge:
                            edge_list.append(edge)
            continuity_edge.append(edge_list)

    @staticmethod
    def get_external_connectivity(analyzer, slice_list, continuity_edge, radius):
        if len(slice_list) > 1:  # at least we need two slices
            print("analyse wall continuity with %d slices" % len(slice_list))
            for i, slice in enumerate(slice_list):
                if i < len(slice_list) - 1:
                    edge_list = []
                    first_slice = slice
                    second_slice = slice_list[i + 1]
                    first_slice.sort(key=getz)
                    second_slice.sort(key=getz)
                    if len(first_slice) > 0 and len(second_slice) > 0:
                        for j, bounded_item_1 in enumerate(first_slice):
                            for k, bounded_item_2 in enumerate(second_slice):
                                edge = WallAnalysis.get_wall_edge(analyzer, bounded_item_1, bounded_item_2, radius)
                                if edge:
                                    edge_list.append(edge)
                    continuity_edge.append(edge_list)

    @staticmethod
    def get_wall_edge(analyzer, origin, destination, radius):
        # check spatial connectivity
        print("check bounding box algo")
        bounding_box_1 = origin["bounding_box"]
        bounding_box_2 = destination["bounding_box"]
        is_touching = is_adjacent_vertical(bounding_box_1, bounding_box_2)
        if not is_touching:
            return None
        edge_dict = dict()
        edge = create_edge_from_two_point(origin["center"], destination["center"])
        edge_dict["topods_edge"] = edge
        edge_dict["origin"] = origin
        edge_dict["destination"] = destination
        print(origin["element"].__class__.__name__)
        print(destination["element"].__class__.__name__)
        ais_object = AIS_Shape(edge)
        if origin["element"].__class__.__name__ == destination["element"].__class__.__name__:
            print("the same element")
            if origin["material"] == destination["material"]:
                print("the same material")
                material = origin["material"]
                color = material.get_shading_colour()
                ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
                ais_object.SetColor(ais_color)
            else:
                print("different_material")
                ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
                ais_object.SetColor(ais_color)
                color_diff_sym = WallAnalysis.get_material_differences(origin, destination)
                material_code_dict = dict()
                material_code_dict["topods_edge"] = color_diff_sym
                material_code_ais = AIS_Shape(color_diff_sym)
                material_code_ais.SetColor(ais_color)
                material_code_dict["ais"] = material_code_ais.GetHandle()
                edge_dict["material_code"] = material_code_dict
                pass
        else:
            print("different element")
            ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
            ais_object.SetColor(ais_color)
            origin_element_code = WallAnalysis.create_element_symbol(origin, radius)
            print(origin_element_code)
            destination_element_code = WallAnalysis.create_element_symbol(destination, radius)
            print(destination_element_code)
            if origin_element_code:
                edge_dict["origin_code"] = origin_element_code
            if destination_element_code:
                edge_dict["destination_code"] = destination_element_code

            if origin["material"] == destination["material"]:
                print("the same material")
                material = origin["material"]
                color = material.get_shading_colour()
                ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
                ais_object.SetColor(ais_color)
            else:
                print("different_material")
                ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
                ais_object.SetColor(ais_color)
                color_diff_sym = WallAnalysis.get_material_differences(origin, destination)
                material_code_dict = dict()
                material_code_dict["topods_edge"] = color_diff_sym
                material_code_ais = AIS_Shape(color_diff_sym)
                material_code_ais.SetColor(ais_color)
                material_code_dict["ais"] = material_code_ais.GetHandle()
                edge_dict["material_code"] = material_code_dict

        display = analyzer.get_parent().get_visualizer().canvas.get_display()
        display.Context.Display(ais_object.GetHandle())
        edge_dict["ais"] = ais_object.GetHandle()
        if "material_code" in edge_dict:
            material_code_dict = edge_dict["material_code"]
            if "ais" in material_code_dict:
                display.Context.Display(material_code_dict["ais"])
        if "origin_code" in edge_dict:
            origin_code_dict = edge_dict["origin_code"]
            if "ais" in origin_code_dict:
                display.Context.Display(origin_code_dict["ais"])
        if "destination_code" in edge_dict:
            destination_code_dict = edge_dict["destination_code"]
            if "ais" in destination_code_dict:
                display.Context.Display(destination_code_dict["ais"])
        return edge_dict

    @staticmethod
    def create_element_symbol(bounded_item, radius):
        type = bounded_item["element"].__class__.__name__
        print(type)
        center = bounded_item["center"]
        material = bounded_item["material"]
        wire = None
        if type == "Wall":
            wire = create_yz_square_center(center, radius)
        if type == "CurtainWall":
            wire = create_yz_diagonal_square_center(center, radius)
        if type == "Door":
            wire = create_yz_upside_triangle_center(center, radius)
        if type == "Window":
            wire = create_yz_downside_triangle_center(center, radius)
        if type == "Column":
            wire = create_yz_hexagon_center(center, radius)
        if wire:
            ais_object = AIS_Shape(wire)
            color = material.get_shading_colour()
            ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
            ais_object.SetColor(ais_color)
            element_code_dict = dict()
            element_code_dict["topods_wire"] = wire
            element_code_dict["ais"] = ais_object.GetHandle()
            return element_code_dict
        return None

    @staticmethod
    def get_material_differences(origin, destination):
        or_material = origin["material"]
        de_material = destination["material"]
        or_colour = or_material.get_surface_colour()
        de_colour = de_material.get_surface_colour()
        colour_distance = Color.colour_distance(or_colour, de_colour)
        print(colour_distance)
        center = middle_point(origin["center"], destination["center"])
        colour_diff_symbol = create_vertical_yz_rectangular_from_center(center, 0.02, colour_distance / 5.0)
        return colour_diff_symbol


class FloorAnalysis(object):
    def __init__(self, parent):
        self._parent = parent
        self.slice_list = self._parent.slice_list
        self.point_lists = []
        self.floor_faces = []
        self.continuity_edge = []
        self.internal_continuity_edge = []
        self.is_floor_surface = True
        self.notation_offset = 0.02
        self.notation_radius = 0.05
        pass

    def get_parent(self):
        return self._parent

    def perform(self):
        for i, slice in enumerate(self.slice_list):
            print("performing wall analysis on slice %d" % i)
            floor_slice = []
            for element_slice in slice.get_element_slice_list():
                if isinstance(element_slice.element, Slab):
                    print(element_slice.element)
                    FloorAnalysis.analyze_floor_by_bounding_box(self, element_slice, floor_slice)
            floor_slice = FloorAnalysis.remove_small_floor_bounded_item(floor_slice, 0.6,
                                                                        self.get_parent().section_distance)
            floor_slice = FloorAnalysis.simplify_floor_bounding_box(self, floor_slice)
            self.floor_faces.append(floor_slice)
        self.display_floor_faces()
        pass

    @staticmethod
    def remove_small_floor_bounded_item(floor_slice, width_threshold, max_width):
        new_slice = []
        y_min_slice, y_max_slice = None, None
        floor_slice.sort(key=get_bound_width)
        for bounded_item in floor_slice:
            bound_width = get_bound_width(bounded_item)
            y_bound = get_y_bound(bounded_item)
            if not y_min_slice or y_min_slice > y_bound[0]:
                y_min_slice = y_bound[0]
            if not y_max_slice or y_max_slice < y_bound[1]:
                y_max_slice = y_bound[1]
            print(bound_width)
            if bound_width >= max_width * width_threshold:
                print("bounded item for %s pass %f width threshold" % (bounded_item["element"], width_threshold))
                new_slice.append(bounded_item)
        if len(new_slice) == 0 and len(floor_slice) > 0:
            new_slice.append(floor_slice[-1])
        for bounded_item in new_slice:
            x_min, y_min, z_min, x_max, y_max, z_max = bounded_item["bounding_box"].Get()
            bounded_item["bounding_box"].Update(x_min, y_min_slice, z_min, x_max, y_max_slice, z_max)
        return new_slice

    @staticmethod
    def simplify_floor_bounding_box(analyzer, slice):
        slice.sort(key=getx)
        slice.sort(key=get_upper_z_reversed)
        print("start defining domain")
        domain_marker = []
        for bounded_item in slice:
            print(bounded_item)
            x_bound = get_x_bound(bounded_item)
            for x in x_bound:
                if not (x in bounded_item):
                    domain_marker.append(x)
        print("constructing domain map")
        domain_list, domain_dict = FloorAnalysis.construct_domain_map(domain_marker, slice, 1e-2)
        print("map elements to domain")
        merged_domain_list = WallAnalysis.construct_merged_domain_list(domain_list, domain_dict)
        return FloorAnalysis.create_new_slice(analyzer, merged_domain_list, domain_dict)

    @staticmethod
    def construct_domain_map(domain_marker, slice, tol):
        domain_marker = sort_remove_similar_value_in_list(domain_marker, tol)
        domain_list = []
        domain_dict = dict()
        print("domain_marker_length %d" % len(domain_marker))
        for i in range(0, len(domain_marker) - 1):
            print(i)
            domain = (domain_marker[i], domain_marker[i + 1])
            domain_list.append(domain)
            for bounded_item in slice:
                domain_center = 0.5 * (domain[0] + domain[1])
                print(domain_center)
                x_bound = get_x_bound(bounded_item)
                print(x_bound)
                if x_bound[0] < domain_center < x_bound[1]:  # the center of bounded item is within doimain:
                    domain_dict[domain] = bounded_item
                    break
        return domain_list, domain_dict

    @staticmethod
    def construct_merged_domain_list(domain_list, domain_dict):
        merged_domain_list = []
        for i, domain in enumerate(domain_list):
            if i == 0:
                merged_domain_list.append([domain])
            else:
                if domain_dict[domain] == domain_dict[merged_domain_list[-1][-1]]:  # if the domain pointing to the
                    # same item
                    merged_domain_list[-1].append(domain)
                else:
                    merged_domain_list.append([domain])
        return merged_domain_list

    @staticmethod
    def create_new_slice(analyzer, merged_domain_list, domain_dict):
        slice_copy = []
        for domain_list in merged_domain_list:
            print("----")
            bounded_item = domain_dict[domain_list[0]]
            bound_min = domain_list[0][0]
            bound_max = domain_list[-1][-1]
            bounded_item_copy = copy_bounded_item(bounded_item)
            bounding_box = bounded_item["bounding_box"]
            xmin, ymin, zmin, xmax, ymax, zmax = bounding_box.Get()
            bounded_item_copy["bounding_box"].Update(bound_min, ymin, zmin, bound_max, ymax, zmax)
            print(bounded_item_copy["element"])
            print(get_x_bound(bounded_item_copy))
            bounding_box_surface, center = FloorAnalysis \
                .get_upper_face(analyzer.notation_offset, bounded_item_copy["bounding_box"])
            bounded_item_copy["topods_face"] = bounding_box_surface
            bounded_item_copy["center"] = center
            slice_copy.append(bounded_item_copy)
        return slice_copy

    @staticmethod
    def analyze_floor_by_bounding_box(analyzer, element_slice, floor_slice):
        print("begin_floor_analysis_by_bounding_box")
        if not element_slice.is_decomposed:
            bounding_box = element_slice.bounding_box
            major_material = None
            if len(element_slice.shapes_slice) > 0:
                print("analyzing floor element_slice %s" % element_slice.name)
                print(element_slice.element)
                print(len(element_slice.shapes_slice))
                material_area_dict = dict()
                for shape_slice in element_slice.shapes_slice:
                    print("analysing floor shape_slice %s" % shape_slice)
                    material = shape_slice[1]
                    area = get_shape_area(shape_slice[0])
                    print(area)
                    if material in material_area_dict:
                        material_area_dict[material] += area
                    else:
                        material_area_dict[material] = area
                major_material = get_major_material(material_area_dict)
                print(major_material.name)
                FloorAnalysis.put_into_floor_slice(analyzer, element_slice.element, bounding_box, major_material,
                                                   floor_slice)
            else:
                print("this is it")
                pass
        else:
            bounding_box_new = Bnd_Box()
            material_dict = dict()
            analyze_decomposed(element_slice, bounding_box_new, material_dict)
            print("decomposed element")
            major_material = get_major_material(material_dict)
            FloorAnalysis.put_into_floor_slice(analyzer, element_slice.element, bounding_box_new, major_material,
                                               floor_slice)
        pass

    @staticmethod
    def put_into_floor_slice(analyzer, parent_element, bounding_box, material, floor_slice):
        bounded_element = dict()
        bounded_element["bounding_box"] = bounding_box
        bounded_element["material"] = material
        bounded_element["element"] = parent_element
        # bounding_box_surface, center = FloorAnalysis.get_upper_face(analyzer.notation_offset, bounding_box)
        # bounded_element["topods_face"] = bounding_box_surface
        # bounded_element["center"] = center
        floor_slice.append(bounded_element)

    def display_floor_faces(self):
        for slices in self.floor_faces:
            for bounded_item in slices:
                display_face(bounded_item, self)

    @staticmethod
    def get_upper_face(offset, bounding_box):
        corner_min = bounding_box.CornerMin()
        corner_max = bounding_box.CornerMax()
        x_min = corner_min.X()
        y_min = corner_min.Y()
        z_min = corner_min.Z()
        x_max = corner_max.X()
        y_max = corner_max.Y()
        z_max = corner_max.Z()
        p1 = gp_Pnt(x_min, y_min, z_max)
        p2 = gp_Pnt(x_max, y_min, z_max)
        p3 = gp_Pnt(x_max, y_max, z_max)
        p4 = gp_Pnt(x_min, y_max, z_max)
        center_point = gp_Pnt(0.5 * (x_min + x_max), 0.5 * (y_min + y_max), z_max + offset)
        bounding_box_surface = create_rectangular_face(p1, p2, p3, p4)
        return bounding_box_surface, center_point

    def get_continuity(self):
        # FloorAnalysis.get_internal_connectivity(self, self.floor_faces, self.internal_continuity_edge,
        #                                       self.notation_radius)
        FloorAnalysis.get_external_connectivity(self, self.floor_faces, self.continuity_edge, self.notation_radius)

    @staticmethod
    def get_internal_connectivity(analyzer, slice_list, continuity_edge, radius):
        for slice in slice_list:
            edge_list = []
            for i, bounded_item_1 in enumerate(slice):
                for j, bounded_item_2 in enumerate(slice):
                    if not i == j:  # not refer to the same instance
                        edge = FloorAnalysis.get_floor_edge(analyzer, bounded_item_1, bounded_item_2, radius)
                        if edge:
                            edge_list.append(edge)
            continuity_edge.append(edge_list)
        pass

    @staticmethod
    def get_external_connectivity(analyzer, slice_list, continuity_edge, radius):
        if len(slice_list) > 1:  # at least we need two slices
            print("analyse floor continuity with %d slices" % len(slice_list))
            for i, slice in enumerate(slice_list):
                if i < len(slice_list) - 1:
                    edge_list = []
                    first_slice = slice
                    second_slice = slice_list[i + 1]
                    first_slice.sort(key=getz)
                    second_slice.sort(key=getz)
                    if len(first_slice) > 0 and len(second_slice) > 0:
                        for j, bounded_item_1 in enumerate(first_slice):
                            for k, bounded_item_2 in enumerate(second_slice):
                                edge = FloorAnalysis.get_floor_edge(analyzer, bounded_item_1, bounded_item_2, radius)
                                if edge:
                                    edge_list.append(edge)
                    continuity_edge.append(edge_list)

    @staticmethod
    def get_floor_edge(analyzer, origin, destination, radius):
        # check spatial connectivity
        print("check bounding box algo")
        bounding_box_1 = origin["bounding_box"]
        bounding_box_2 = destination["bounding_box"]
        is_touching = is_adjacent_horizontal(bounding_box_1, bounding_box_2)
        if not is_touching:
            return None
        edge_dict = dict()
        edge = create_edge_from_two_point(origin["center"], destination["center"])
        edge_dict["topods_edge"] = edge
        edge_dict["origin"] = origin
        edge_dict["destination"] = destination
        print(origin["element"].__class__.__name__)
        print(destination["element"].__class__.__name__)
        ais_object = AIS_Shape(edge)
        if origin["element"].__class__.__name__ == destination["element"].__class__.__name__:
            print("the same element")
            if origin["material"] == destination["material"]:
                print("the same material")
                material = origin["material"]
                color = material.get_shading_colour()
                ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
                ais_object.SetColor(ais_color)
            else:
                print("different_material")
                ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
                ais_object.SetColor(ais_color)
                color_diff_sym = FloorAnalysis.get_material_differences(origin, destination)
                material_code_dict = dict()
                material_code_dict["topods_edge"] = color_diff_sym
                material_code_ais = AIS_Shape(color_diff_sym)
                material_code_ais.SetColor(ais_color)
                material_code_dict["ais"] = material_code_ais.GetHandle()
                edge_dict["material_code"] = material_code_dict
                pass
        else:
            print("different element")
            ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
            ais_object.SetColor(ais_color)
            origin_element_code = FloorAnalysis.create_element_symbol(origin, radius)
            print(origin_element_code)
            destination_element_code = FloorAnalysis.create_element_symbol(destination, radius)
            print(destination_element_code)
            if origin_element_code:
                edge_dict["origin_code"] = origin_element_code
            if destination_element_code:
                edge_dict["destination_code"] = destination_element_code
            if origin["material"] == destination["material"]:
                print("the same material")
                material = origin["material"]
                color = material.get_shading_colour()
                ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
                ais_object.SetColor(ais_color)
            else:
                print("different_material")
                ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
                ais_object.SetColor(ais_color)
                color_diff_sym = FloorAnalysis.get_material_differences(origin, destination)
                material_code_dict = dict()
                material_code_dict["topods_edge"] = color_diff_sym
                material_code_ais = AIS_Shape(color_diff_sym)
                material_code_ais.SetColor(ais_color)
                material_code_dict["ais"] = material_code_ais.GetHandle()
                edge_dict["material_code"] = material_code_dict

        display = analyzer.get_parent().get_visualizer().canvas.get_display()
        display.Context.Display(ais_object.GetHandle())
        edge_dict["ais"] = ais_object.GetHandle()
        if "material_code" in edge_dict:
            material_code_dict = edge_dict["material_code"]
            if "ais" in material_code_dict:
                display.Context.Display(material_code_dict["ais"])
        if "origin_code" in edge_dict:
            origin_code_dict = edge_dict["origin_code"]
            if "ais" in origin_code_dict:
                display.Context.Display(origin_code_dict["ais"])
        if "destination_code" in edge_dict:
            destination_code_dict = edge_dict["destination_code"]
            if "ais" in destination_code_dict:
                display.Context.Display(destination_code_dict["ais"])
        return edge_dict
        pass

    @staticmethod
    def get_material_differences(origin, destination):
        or_material = origin["material"]
        de_material = destination["material"]
        or_colour = or_material.get_surface_colour()
        de_colour = de_material.get_surface_colour()
        colour_distance = Color.colour_distance(or_colour, de_colour)
        print(colour_distance)
        center = middle_point(origin["center"], destination["center"])
        colour_diff_symbol = create_horizontal_xy_rectangular_from_center(center, 0.02, colour_distance / 5.0)
        return colour_diff_symbol
        pass

    @staticmethod
    def create_element_symbol(bounded_item, radius):
        '''type = bounded_item["element"].__class__.__name__
        print(type)
        center = bounded_item["center"]
        material = bounded_item["material"]
        wire = None
        if type == "Wall":
            wire = create_yz_square_center(center, radius)
        if type == "CurtainWall":
            wire = create_yz_diagonal_square_center(center, radius)
        if type == "Door":
            wire = create_yz_upside_triangle_center(center, radius)
        if type == "Window":
            wire = create_yz_downside_triangle_center(center, radius)
        if type == "Column":
            wire = create_yz_hexagon_center(center, radius)
        if wire:
            ais_object = AIS_Shape(wire)
            color = material.get_shading_colour()
            ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
            ais_object.SetColor(ais_color)
            element_code_dict = dict()
            element_code_dict["topods_wire"] = wire
            element_code_dict["ais"] = ais_object.GetHandle()
            return element_code_dict'''
        return None

    def toggle_floor_surface_view(self):
        if self.is_floor_surface:
            hide_surface(self, self.floor_faces)
        else:
            show_surface(self, self.floor_faces)
        self.is_floor_surface = not self.is_floor_surface


def getz(elem):
    if "center" in elem:
        return elem["center"].Z()
    else:
        z_bound = get_z_bound(elem)
        return 0.5 * (z_bound[0] + z_bound[1])


def getz_reversed(elem):
    if "center" in elem:
        return -elem["center"].Z()
    else:
        z_bound = get_z_bound(elem)
        return -0.5 * (z_bound[0] + z_bound[1])


def getx(elem):
    if "center" in elem:
        return elem["center"].X()
    else:
        x_bound = get_x_bound(elem)
        return x_bound[0]


def getx_reversed(elem):
    if "center" in elem:
        return -elem["center"].X()
    else:
        x_bound = get_x_bound(elem)
        return -x_bound[1]


def get_x_bound(elem):
    bounding_box = elem["bounding_box"]
    x_min = bounding_box.CornerMin().X()
    x_max = bounding_box.CornerMax().X()
    return x_min, x_max


def get_y_bound(elem):
    bounding_box = elem["bounding_box"]
    y_min = bounding_box.CornerMin().Y()
    y_max = bounding_box.CornerMax().Y()
    return y_min, y_max


def get_z_bound(elem):
    bounding_box = elem["bounding_box"]
    z_min = bounding_box.CornerMin().Z()
    z_max = bounding_box.CornerMax().Z()
    return z_min, z_max


def get_upper_z_reversed(elem):
    return -get_z_bound(elem)[1]


def get_bound_width(elem):
    bounding_box = elem["bounding_box"]
    y_min = bounding_box.CornerMin().Y()
    y_max = bounding_box.CornerMax().Y()
    return abs(y_max - y_min)


def get_undecomposed(element_slice, not_decomposed_elements):
    children = element_slice.children
    for child in children:
        if not child.is_decomposed:
            not_decomposed_elements.append(child)
        else:
            get_undecomposed(child, not_decomposed_elements)


def get_shape_area(shape_list):
    area = 0
    for shape in shape_list:
        system = GProp_GProps()
        BRepGProp.brepgprop_SurfaceProperties(shape["topods_shape"], system)
        area += system.Mass()
    return area


def get_major_material(material_area_dict):
    major_material = None
    major_area = 0
    for key in material_area_dict:
        if material_area_dict[key] > major_area:
            major_area = material_area_dict[key]
            major_material = key
    return major_material


def analyze_decomposed(element_slice, bounding_box, material_dict):
    if element_slice.is_decomposed:
        print(element_slice.name)
        for child in element_slice.children:
            analyze_decomposed(child, bounding_box, material_dict)
    else:
        for shape_slice in element_slice.shapes_slice:
            print("analysing shape_slice in analyze_decomposed %s" % shape_slice)
            material = shape_slice[1]
            area = get_shape_area(shape_slice[0])
            for shape in shape_slice[0]:
                brepbndlib_Add(shape["topods_shape"], bounding_box)
            if material in material_dict:
                material_dict[material] += area
            else:
                material_dict[material] = area


def hide_surface(analyzer, faces):
    display = analyzer.get_parent().get_visualizer().canvas.get_display()
    for slice in faces:
        for bounded_item in slice:
            display.Context.Erase(bounded_item["ais"])


def show_surface(analyzer, faces):
    display = analyzer.get_parent().get_visualizer().canvas.get_display()
    for slice in faces:
        for bounded_item in slice:
            display.Context.Display(bounded_item["ais"])


def display_face(bounded_item, analyzer):
    material = bounded_item["material"]
    bounding_box_surface = bounded_item["topods_face"]
    color = material.get_surface_colour()
    ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
    transparency = material.get_transparency()
    display = analyzer.get_parent().get_visualizer().canvas.get_display()
    ais_object = AIS_Shape(bounding_box_surface)
    ais_object.SetCurrentFacingModel(OCC.Aspect.Aspect_TOFM_BOTH_SIDE)
    ais_object.SetColor(ais_color)
    display.Context.Display(ais_object.GetHandle())
    display.Context.SetTransparency(ais_object.GetHandle(), transparency)
    bounded_item["ais"] = ais_object.GetHandle()


def sort_remove_similar_value_in_list(old_list, tol):
    old_list.sort()
    new_list = []
    if len(old_list) > 1:  # at least there are two item
        for i, item in enumerate(old_list):
            if i == 0:
                new_list.append(item)
            else:
                if item - tol < new_list[-1] < item + tol:  # the next item is similar to item
                    pass  # do nothing
                else:
                    new_list.append(item)
    return new_list


def copy_bounded_item(bounded_item):
    for key in bounded_item:
        print(key, bounded_item[key])
    bounded_item_copy = dict()
    bounded_item_copy["material"] = bounded_item["material"]
    bounded_item_copy["element"] = bounded_item["element"]
    bounding_box_copy = Bnd_Box()
    bounded_item_copy["bounding_box"] = bounding_box_copy
    return bounded_item_copy
