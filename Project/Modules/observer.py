# observer module

import re
import numpy as np

def get_GPS_from_address(address):
    match = re.search(r'(-?\d+\.?\d*)\s*,?\s*(-?\d+\.?\d*)', address)
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
    return (x,y)

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


def get_neighboring_block_ids(lon, lat, mean_lon, mean_lat, Earth_radius, x_grid, y_grid):
    x_id_list = []
    y_id_list = []

    # determine integer ids of block
    cart = convert_to_cartesian(lon, lat, mean_lon, mean_lat, Earth_radius)
    t = find_my_block(cart[0], cart[1], x_grid, y_grid)
    x_id_list.append(t[0])
    y_id_list.append(t[1])

    # generate a list of neighboring block ids:
    x_id_list.append(t[0] + 1)
    y_id_list.append(t[1])

    x_id_list.append(t[0] + 1)
    y_id_list.append(t[1] - 1)

    x_id_list.append(t[0])
    y_id_list.append(t[1] - 1)
    
    x_id_list.append(t[0] - 1)
    y_id_list.append(t[1] - 1)

    x_id_list.append(t[0] - 1)
    y_id_list.append(t[1])

    x_id_list.append(t[0] - 1)
    y_id_list.append(t[1] + 1)

    x_id_list.append(t[0])
    y_id_list.append(t[1] + 1)

    x_id_list.append(t[0] + 1)
    y_id_list.append(t[1] + 1)

    return (x_id_list, y_id_list)
