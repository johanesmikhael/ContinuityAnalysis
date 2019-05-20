from tkinter import Tk
from tkinter import filedialog
from os.path import isfile
import networkx as nx
from grakel import GraphKernel
import numpy as np
import SimpSOM as sps
from matplotlib import pyplot
import os
from xml.dom.minidom import Document, parse, parseString


temporal_graph_list = []
prototype_number = 10
kernel = None
prototype_selectors_index = []
embedded_graphs = None
som_size = 50
init_learning_rate = 0.1
num_epoch = 100000
clustered_graph = None
item_coordinates = None


def add_folder():
    root = Tk()
    # root.withdraw()
    folder_name = filedialog.askdirectory()
    root.destroy()
    i = 0
    base = folder_name.split("/")[-1]
    name = base + "-%d" % i
    file_name = name + ".graphml"
    path = folder_name + "/" + file_name
    print(path)
    while isfile(path):
        print(path)
        G = nx.read_graphml(path, node_type=str, edge_key_type=float)
        if G:
            print(G.adj)
            temporal_graph_list.append([G, name])
        i += 1
        name = base + "-%d" % i
        file_name = name + ".graphml"
        path = folder_name + "/" + file_name
    print(temporal_graph_list)


def calculate_kernel(graph_list):
    wl_kernel = GraphKernel(kernel=[{"name": "weisfeiler_lehman", "niter": 5}, {"name": "subtree_wl"}],
                            normalize=True)
    grakel_graphs = []
    for i, g in enumerate(graph_list):
        adj = nx.to_numpy_matrix(g[0])
        nodes = g[0].nodes()
        # print(adj)
        # print(nodes)
        # print("----------------------------------------------------------------")
        node_dict = dict()
        for k, l in enumerate(nodes):
            node_dict[k] = l.split("-")[1]  # assign object type as node
        h = [adj.tolist(), node_dict]
        grakel_graphs.append(h)
    new_kernel = wl_kernel.fit_transform(grakel_graphs)
    print(new_kernel)
    print(type(new_kernel))
    fig = pyplot.figure(figsize=(5, 5))
    pyplot.imshow(new_kernel,
                  cmap="Greys",
                  interpolation="none")
    pyplot.show()
    return new_kernel


def embed_graph_coordinate(temporal_graphs, coordinates):
    for i, graph in enumerate(temporal_graphs):
        graph.append(coordinates[i])

def select_prototype_selectors(graph_kernel, prototype_index, prototype_num):
    for i in range(0, prototype_num):
        if i == 0:
            init_index = get_median(graph_kernel)
            prototype_index.append(init_index)
        else:
            size = len(graph_kernel)
            row = np.ndarray(shape=(size,), dtype=float)
            '''for k in self.prototype_selectors_index:
                copy_row.put(k, 1.0)'''
            for j in range(0, len(graph_kernel)):
                max_kernel_distance = 1.0
                if j not in prototype_index:
                    iterator = 0
                    for index in prototype_index:
                        selected_row = graph_kernel[index]
                        if iterator == 0:
                            max_kernel_distance = selected_row[j]
                        elif max_kernel_distance < selected_row[j]:
                            max_kernel_distance = selected_row[j]
                        iterator += 1
                row.put(j, max_kernel_distance)
            print(row)
            furthest_index = row.argmin()
            print(furthest_index)
            prototype_index.append(furthest_index)
            print(prototype_index)
    print("selected index")
    print(prototype_index)
    return prototype_index


def embed_graph(graph_kernel, prototype_index):
    embed_list = []
    for row in graph_kernel:
        embedded_vector = []
        for index in prototype_index:
            embedded_vector.append(row.item(index))
        embed_list.append(embedded_vector)
    embedded = np.array(embed_list)
    print(embedded)
    return embedded


def get_median(graph_kernel):
    distances = np.ndarray(shape=(len(graph_kernel),))
    size = len(graph_kernel)
    for i in range(0, size):
        sum = 0.0
        for j in range(0, size):
            if i != j:
                sum += graph_kernel[j][i]
        distances.put(i, sum)
    index = distances.argmin()
    return index


def generate_som(size, embd_graph_list, init_learning_r, n_epoch, prototype_index):
    labels = []
    for embd_graph in range(0, len(embd_graph_list)):
        labels.append(embd_graph)
    # net = sps.somNet(size, size, embd_graph_list, loadFile='weight_map', PBC=True)
    net = sps.somNet(size, size, embd_graph_list, PBC=True)
    net.train(init_learning_r, n_epoch)
    net.save('weight_map')
    for i in range(0, len(prototype_index)):
        net.nodes_graph(colnum=i)
    net.diff_graph()
    coordinate = net.project(embd_graph_list, labels=labels)
    print(coordinate)
    clusters = net.cluster(embd_graph_list, type='qthresh')
    return clusters, coordinate


def write_data(prototype_index, size, init_learning_r, n_epoch, clusters, temporal_graphs):
    f = open("data.txt", "w")
    f.write("prototypes index:" + "\n")
    f.write(str(prototype_index) + "\n")
    f.write("SOM size:" + "\n")
    f.write(str(size) + "\n")
    f.write("initial learning rate:" + "\n")
    f.write(str(init_learning_r) + "\n")
    f.write("epoch number:" + "\n")
    f.write(str(n_epoch) + "\n")
    f.close()

    dirpath = os.getcwd()
    doc = Document()
    clusters_xml = doc.createElement("clusters")
    doc.appendChild(clusters_xml)
    for i, cluster in enumerate(clusters):
        cluster_xml = doc.createElement("cluster")
        clusters_xml.appendChild(cluster_xml)
        cluster_num_xml = doc.createElement("cluster_num")
        cluster_xml.appendChild(cluster_num_xml)
        cluster_num_text = doc.createTextNode(str(i))
        cluster_num_xml.appendChild(cluster_num_text)
        sum_x = 0.0
        sum_y = 0.0
        for item in cluster:
            sum_x += temporal_graphs[item][2][0]
            sum_y += temporal_graphs[item][2][1]
            cluster_item_xml = doc.createElement("cluster_item")
            cluster_xml.appendChild(cluster_item_xml)
            cluster_item_name_xml = doc.createElement("name")
            cluster_item_xml.appendChild(cluster_item_name_xml)
            cluster_item_name_text = doc.createTextNode(temporal_graphs[item][1])
            cluster_item_name_xml.appendChild(cluster_item_name_text)
            cluster_item_isproto_xml = doc.createElement("is_prototype")
            cluster_item_xml.appendChild(cluster_item_isproto_xml)
            is_prototype = item in prototype_index
            is_prototype_text = doc.createTextNode(str(is_prototype))
            cluster_item_isproto_xml.appendChild(is_prototype_text)
        center_x = sum_x/len(cluster)
        center_y = sum_y/len(cluster)
        cluster_center_xml = doc.createElement("center")
        cluster_xml.appendChild(cluster_center_xml)
        center_x_xml = doc.createElement("x")
        center_y_xml = doc.createElement("y")
        cluster_center_xml.appendChild(center_x_xml)
        cluster_center_xml.appendChild(center_y_xml)
        center_x_text = doc.createTextNode(str(center_x))
        center_y_text = doc.createTextNode(str(center_y))
        center_x_xml.appendChild(center_x_text)
        center_y_xml.appendChild(center_y_text)
    doc.writexml(open(dirpath + "/clusters.xml", 'w'),
                 indent="  ",
                 addindent="  ",
                 newl='\n')
    doc.unlink()

    doc_prototypes = Document()
    prototypes_xml = doc_prototypes.createElement("prototypes")
    doc_prototypes.appendChild(prototypes_xml)
    for index in prototype_index:
        prototype_xml = doc_prototypes.createElement("prototype")
        prototypes_xml.appendChild(prototype_xml)
        name_xml = doc_prototypes.createElement("name")
        prototype_xml.appendChild(name_xml)
        name_text = doc_prototypes.createTextNode(temporal_graphs[index][1])
        name_xml.appendChild(name_text)
        coordinate_xml = doc_prototypes.createElement("coordinate")
        prototype_xml.appendChild(coordinate_xml)
        x_xml = doc_prototypes.createElement("x")
        y_xml = doc_prototypes.createElement("y")
        coordinate_xml.appendChild(x_xml)
        coordinate_xml.appendChild(y_xml)
        coordinate_x = doc_prototypes.createTextNode(str(temporal_graphs[index][2][0]))
        coordinate_y = doc_prototypes.createTextNode(str(temporal_graphs[index][2][1]))
        x_xml.appendChild(coordinate_x)
        y_xml.appendChild(coordinate_y)
    doc_prototypes.writexml(open(dirpath + "/prototypes.xml", 'w'),
                 indent="  ",
                 addindent="  ",
                 newl='\n')
    doc_prototypes.unlink()

    print("finish write data")


if __name__ == '__main__':
    is_add_folder = True
    while is_add_folder is True:
        print("add folder? y/n")
        is_adding = input()
        if is_adding == 'y':
            add_folder()
        elif is_adding == 'n':
            print("finish adding folder")
            is_add_folder = False
    kernel = calculate_kernel(temporal_graph_list)
    prototype_selectors_index = select_prototype_selectors(kernel, prototype_selectors_index, prototype_number)
    embedded_graphs = embed_graph(kernel, prototype_selectors_index)
    clustered_graph, item_coordinates = generate_som(som_size, embedded_graphs, init_learning_rate, num_epoch, prototype_selectors_index)
    embed_graph_coordinate(temporal_graph_list, item_coordinates)
    write_data(prototype_selectors_index, som_size, init_learning_rate, num_epoch, clustered_graph, temporal_graph_list)
