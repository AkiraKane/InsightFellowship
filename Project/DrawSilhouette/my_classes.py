import re
import csv
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import datetime as dt
import pymysql as mdb

# class to store a single node of a building
class Node:
    def __init__(self, input_x=0, input_y=0):
        self.x = input_x
        self.y = input_y
    
    def show(self):
        print '[x=' + str(self.x) + ', y=' + str(self.y) + ']'

# class to store geometries of a single building
class Building:
    def __init__(self):
        self.nodes = []   # list of Nodes
        self.center = Node()
        self.z = None        # height
        
    def show(self):
        print 'Nodes:'
        for node in self.nodes:
            node.show()
        print 'Center:\n' + 'x_center=' + str(self.center.x) + ', ' \
              + 'y_center=' + str(self.center.y)
        print 'Height:\n' + 'z=' + str(self.z)
        
    def plot_footprint(self, color = 'k'):
        x_list = []
        y_list = []
        for node in self.nodes:
            x_list.append(node.x)
            y_list.append(node.y)
        plt.plot(x_list,y_list, color=color)
        
    def calculate_center(self):
        x_array = []
        y_array = []
        for node in self.nodes:
            x_array.append(node.x)
            y_array.append(node.y)
        self.center.x = np.mean(x_array)
        self.center.y = np.mean(y_array)

# class for a block, haviing buildigns assigned to it
class Block:
    def __init__(self):
        self.vertices = []  # list of nodes
        self.building_ids = []  # list of building_ids
        self.max_z = 0  # maximum height of the buildings in it
    
    def __init__(self, node1, node2, node3, node4):
        self.vertices = [node1, node2, node3, node4]  # list of nodes
        self.building_ids = []  # list of building_ids
        self.max_z = 0  # maximum height of the buildings in it
    
    def calculate_max_z(self, buildings):
        current_max_z = 0
        for key in self.building_ids:
            this_z = buildings[key].z
            if this_z > current_max_z:
                current_max_z = this_z
        self.max_z = current_max_z
    
    def plot_on_map(self):
        x_list = []
        y_list = []
        for node in self.vertices:
            x_list.append(node.x)
            y_list.append(node.y)
        plt.plot(x_list, y_list)

# function to determine if a node lies outside a boundary piece
def is_outside(boundary_node_1, boundary_node_2, building_node):
    ux = building_node.x - boundary_node_1.x
    uy = building_node.y - boundary_node_1.y
    vx = boundary_node_2.x - boundary_node_1.x
    vy = boundary_node_2.y - boundary_node_1.y
    
    if ((vx*uy) > (vy*ux)):
        return True
    else:
        return False

# function to assign a building to a block, using its center coordinates
def assign_to_block(building_id, building, x_grid, y_grid, blocks):
    
    # find x_index of the block
    block_x_index = -1
    for x in x_grid:
        if building.center.x > x:
            block_x_index += 1
        else:
            break
    
    # find y_index of the block
    block_y_index = -1
    for y in y_grid:
        if building.center.y > y:
            block_y_index += 1
        else:
            break
            
    # compile key (as string)
    block_key = str(block_x_index) + ':' + str(block_y_index)
    
    # add the building id to the selected block
    blocks[block_key].building_ids.append(building_id)
    
    # add the selected block's id to the building
    building.block_id = block_key
        