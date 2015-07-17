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
        
    def plot_footprint(self, ax, color='k'):
        x_list = []
        y_list = []
        for node in self.nodes:
            x_list.append(node.x)
            y_list.append(node.y)
        ax.plot(x_list,y_list, color=color)
        
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
    
    def plot_on_map(self, ax):
        x_list = []
        y_list = []
        for node in self.vertices:
            x_list.append(node.x)
            y_list.append(node.y)
        ax.plot(x_list, y_list)

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
        

class Roof:
    def __init__(self, phi1=None, phi2=None, theta=None):
        self.phi1 = phi1
        self.phi2 = phi2
        self.theta = theta
    
    def show(self):
        print "(phi1=" + str(self.phi1) + ", phi2=" + str(self.phi2) + ", theta=" + str(self.theta) +")"   


class Cliff:
    def __init__(self, phi=None, theta_L=None, theta_R=None ):
        self.phi = phi
        self.theta_L = theta_L
        self.theta_R = theta_R
    
    def show(self):
        print "(phi=" + str(self.phi) + ", theta_L=" + str(self.theta_L) + ", theta_R=" + str(self.theta_R) +")"   
    

class Silhouette:
    
    def __init__(self):
        self.cliffs = [] # list of cliffs ordered by phi
        # add the two extreme points
        self.cliffs.append(Cliff(-np.pi -1, 0,0))
        self.cliffs.append(Cliff(np.pi + 1, 0,0))
    
    def draw(self, color='k', deg=True, marker="None"):
        # set angle unit
        if deg:
            conversion_ratio = 180 / np.pi
            unit = 180
        else:
            conversion_ratio = 1
            unit = np.pi
        
        # generate (phi, theta) points from cliffs (phi, theta_R, theta_L)
        phi_list = []
        theta_list = []
        
        # phi_list.append(-unit)
        # theta_list.append(self.cliffs[0].theta_L * conversion_ratio)
        
        for cliff in self.cliffs:
            phi_list.append(cliff.phi * conversion_ratio)
            theta_list.append(cliff.theta_L * conversion_ratio)
            phi_list.append(cliff.phi * conversion_ratio)
            theta_list.append(cliff.theta_R * conversion_ratio)
        
        # phi_list.append(unit)
        # theta_list.append(self.cliffs[-1].theta_R * conversion_ratio)
        
        plt.plot(phi_list, theta_list, color=color, marker=marker)
        # plt.gca().set_aspect('equal', adjustable='box')
        plt.gcf().set_size_inches(10, 2.5)
        plt.axis((-unit, unit, 0, unit/2))
        plt.show()
        
    
    def add_roof(self, roof):
        # find the cliffs that are between the roof's phi1 and phi2
        cliffs_inside = []
        insert_index_1 = 0
        insert_index_2 = 0
        

        i = 0
        while self.cliffs[i].phi < roof.phi1:
            insert_index_1 += 1
            insert_index_2 += 1
            i += 1
        while self.cliffs[i].phi < roof.phi2:
            insert_index_2 += 1
            i += 1
            
            
        # in case the entire roof falls between too cliffs
        if not self.cliffs[insert_index_1 : insert_index_2]:
            # get the silhouette's height from previous cliff
            theta = self.cliffs[insert_index_1 -1].theta_R
            # add only if it's higher
            if theta < roof.theta:
                cliff1 = Cliff(roof.phi1, theta, roof.theta)
                cliff2 = Cliff(roof.phi2, roof.theta, theta)
                self.cliffs.insert(insert_index_1, cliff1)
                insert_index_2 += 1 # the first insertion shift the index
                self.cliffs.insert(insert_index_2, cliff2)
                
        # in case the roof spans over at least one cliff
        else:
            
            # process the cliffs between the roof endpoints
            cliffs_to_delete = []
            for i in range(insert_index_1, insert_index_2):
                L = self.cliffs[i].theta_L
                R = self.cliffs[i].theta_R
                H = roof.theta
                
                # if the cliff is under the roof, delete it
                if L < H and R < H:
                    cliffs_to_delete.insert(0,i)
                
                # if the cliff crosses the roof downwards, update it
                elif L > H and R < H:
                    self.cliffs[i].theta_R = roof.theta
                
                # if the cliff crosses the roof upwards, update it
                elif L < H and R > H:
                    self.cliffs[i].theta_L = roof.theta
                
                # if the cliff is above the roof, it shouldn't change
            
            # process the endpoints of the roof
            theta1 = self.cliffs[insert_index_1 -1].theta_R
            theta2 = self.cliffs[insert_index_2].theta_L
            
            # add phi2 first
            if theta2 < roof.theta:
                cliff2 = Cliff(roof.phi2, roof.theta, theta2)
                self.cliffs.insert(insert_index_2, cliff2)
            
            # delete cliffs under the roof
            for index in cliffs_to_delete:
                self.cliffs.pop(index)
            
            # add phi1 last
            if theta1 < roof.theta:
                cliff1 = Cliff(roof.phi1, theta1, roof.theta)
                self.cliffs.insert(insert_index_1, cliff1)
            
def get_GPS_from_address(address, lon=0, lat=0):
    match = re.search(r'(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)', address)
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
    return (lon, lat)


# convert (lon,lat) to (x,y) on the local map
def convert_to_cartesian(lon, lat, mean_lon, mean_lat, Earth_radius):
    deg2rad = np.pi/180
    cos_mean_lat = np.cos(mean_lat * deg2rad)
    x = Earth_radius * cos_mean_lat * (lon - mean_lon)* deg2rad
    y = Earth_radius * (lat - mean_lat)* deg2rad
    return Node(x,y)

# finds the block the Node(x,y) coordinates are in
# (blocks are indexed by (x_index, y_index), starting from (0,0) )
def find_my_block(x_my, y_my, x_grid, y_grid):
    # find x_index of the block
    x_index = -1
    for x in x_grid:
        if x_my > x:
            x_index += 1
        else:
            break
    
    # find y_index of the block
    y_index = -1
    for y in y_grid:
        if y_my > y:
            y_index += 1
        else:
            break
    
    return (x_index, y_index)


# distills a list of roofs from nodes of a building, given the observer's location
def get_roofs(obs_x, obs_y, obs_z, building, blur_epsilon=0.01):
    
    roofs = []
    
    # gather node coordinates
    dx_list = []
    dy_list = []
    for node in building.nodes:
        dx_list.append(node.x)
        dy_list.append(node.y)
    
    # calculate relative location with respect to the observer
    dx_list = np.array(dx_list) - obs_x
    dy_list = np.array(dy_list) - obs_y
    dz = building.z - obs_z
    
    # calclate distances from the observer
    dist_list = np.sqrt(dx_list**2 + dy_list**2)
 
    # calculate viewing angles
    theta_list = np.arctan( np.true_divide(dz, dist_list) )
    phi_list = -np.arctan2(dx_list, -dy_list)
    

    for i in range(0, len(dx_list)-1):
        # order the two endpoints in ascending order
        phi1 = min(phi_list[i], phi_list[i+1])
        phi2 = max(phi_list[i], phi_list[i+1])

        # get visible height of the building
        theta = np.mean(theta_list[i:i+2])
        
        # check if the building crosses the North line
        if dy_list[i] > 0 and dy_list[i+1] > 0 and dx_list[i] * dx_list[i+1] < 0:
            # if so, make two separate roof objects, on the two edges of the silhouette
            roof1 = Roof(-np.pi - blur_epsilon, phi1 + blur_epsilon, theta)
            roof2 = Roof(phi2 - blur_epsilon, np.pi + blur_epsilon, theta)
            roofs.append(roof1)
            roofs.append(roof2)
            
        # if not, make a single roof object
        else:
            roof = Roof(phi1 - blur_epsilon, phi2 + blur_epsilon, theta)
            roofs.append(roof)
    
    return roofs