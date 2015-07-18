# observer module

import re
import numpy as np
import datetime as dt
from dateutil.parser import parse

LATITUTE_DEFAULT = 40.767946 
LONGITUDE_DEFAULT = -73.981831
ALTITUDE_DEFAULT = 0
    

class Observer:
    def __init__(self, \
            lon=LONGITUDE_DEFAULT, 
            lat=LATITUTE_DEFAULT,\
            alt=ALTITUDE_DEFAULT,\
            city_lon=-73.973351,\
            city_lat=40.771803,\
            planet_radius=6371009,\
        ):
        self.lon = lon
        self.lat = lat
        self.city_lon = city_lon
        self.city_lat = city_lat
        self.planet_radius = planet_radius
        self.x = None
        self.y = None
        self.z = alt
        self.block_xid = None
        self.block_yid = None


    def get_geocoordinates(self, address, floor):
        if address:
            match = re.search(r'(-?\d+\.?\d*)\s*,?\s*(-?\d+\.?\d*)', address)
            if match:
                self.lat = float(match.group(1))
                self.lon = float(match.group(2))

        if floor:
            match = re.search(r'(\d+)', address)
            if match:
                self.z = float(floor) * 3   # 1 floor =approx= 3 meters
            

    # convert (lon,lat) to (x,y) on the local map
    def convert_to_cartesian(self):
        deg2rad = np.pi/180
        cos_mean_lat = np.cos(self.city_lat * deg2rad)
        self.x = self.planet_radius * cos_mean_lat * (self.lon - self.city_lon)* deg2rad
        self.y = self.planet_radius * (self.lat - self.city_lat)* deg2rad
    

    # finds the block the Node(x,y) coordinates are in
    # (blocks are indexed by (x_index, y_index), starting from (0,0) )
    def find_my_block(self, x_grid, y_grid):
        # find x_index of the block
        x_index = -1
        for x in x_grid:
            if self.x > x:
                x_index += 1
            else:
                break
        
        # find y_index of the block
        y_index = -1
        for y in y_grid:
            if self.y > y:
                y_index += 1
            else:
                break
        
        self.block_xid = x_index
        self.block_yid = y_index



    def get_neighboring_block_ids(self):
        
        # relative integer coordinates of neighboring blocks (including the center block)
        deltax = [0,1,1,0,-1,-1,-1,0,1]
        deltay = [0,0,1,1,1,0,-1,-1,-1]

        xid_list = []
        yid_list = []
        for i in range(0, len(deltax)):
            xid_list.append(self.block_xid + deltax[i])
            yid_list.append(self.block_yid + deltay[i])
        
        return (xid_list, yid_list)


    def plot_observers_location(self, ax, color='k'):
        # center dot
        ax.plot([self.x], [self.y], color=color, marker='o', markersize=10)

        # corss
        L = 300
        ax.plot([self.x, self.x], [self.y - L, self.y + L], color=color)
        ax.plot([self.x - L, self.x + L], [self.y, self.y], color=color)
