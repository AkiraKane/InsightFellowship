# modules for the web app
from flask import render_template, request, make_response
from app import app
import StringIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

# modules for the processing
# import re
# import csv
# import pandas as pd
# import matplotlib.pyplot as plt
# import matplotlib.cm as cm
# import numpy as np
import datetime as dt
import pymysql as mdb

# my modules
from buildingmapping import *
from skyline import *
from sun import *
from observer import *


con = mdb.connect('localhost', 'root', '123', 'Manhattan_buildings')

#  declare global instances
obs = Observer()
sil = Silhouette()
sun = SunPath()
buildings = {}
x_grid = None
y_grid = None

# load basic geography of Manhattan
with con:
    cur = con.cursor()
    cur.execute("SELECT \
        Planet_radius, \
        Mean_lon, \
        Mean_lat \
        FROM Cities \
        WHERE Name = 'New York Manhattan'\
    ")
    result = cur.fetchall()[0]
    obs.planet_radius = result[0]
    obs.city_lon = result[1]
    obs.city_lat = result[2]

# load grid data 
with con:
    cur = con.cursor()
    cur.execute("SELECT \
        Xmin,\
        Xmax,\
        Xstep,\
        Ymin,\
        Ymax,\
        Ystep\
        FROM Grids \
        WHERE Id = 1"\
    )
    result = cur.fetchall()[0]

    x_min = result[0]
    x_max = result[1]
    x_step = result[2]
    y_min = result[3]
    y_max = result[4]
    y_step = result[5]

    x_grid = np.arange(x_min, x_max, x_step)
    y_grid = np.arange(y_min, y_max, y_step)



@app.route('/input')
def input():
    address = request.args.get('Address')
    floor = request.args.get('Floor')
    day_of_year = request.args.get('Day')
    
    obs.get_geocoordinates(address, floor)
    obs.convert_to_cartesian()
    obs.find_my_block(x_grid, y_grid)

    sun.get_date(day_of_year)
    sun.lat = obs.lat
    sun.lon = obs.lon

    # get all buildings in the proposed list of blocks
    buildings.clear()
    (x_id_list, y_id_list) = obs.get_neighboring_block_ids()
    for i in range(0, len(x_id_list)):
        buildings.update(\
            append_buildings_in_block(con, x_id_list[i], y_id_list[i])\
        )

    # add roofs of the buildigns to sil
    sil.cliffs = Silhouette().cliffs
    for key in buildings:
        if buildings[key].z > obs.z:
            roofs = buildings[key].get_roofs(obs.x, obs.y, obs.z)
            for tup in roofs:
                sil.add_roof( Roof(tup) )
    
    sun.positions = []
    sun.calculate_path()

    sun.visible = []
    v = sun.calculate_visibility(sil)
    message = str(v[0]) + ' min sunny / ' + str(v[1]) + ' min total'

    return render_template("input.html", message=message)
    


@app.route('/block_map')
def draw_block():
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for key in buildings:
        if buildings[key].z > obs.z:    # plot only if building is taller than observer
            if buildings[key].z < 20:
                color = 'k'
            elif buildings[key].z < 50:
                color = 'b'
            elif buildings[key].z < 100:
                color = 'g'
            elif buildings[key].z < 200:
                color = 'r'
            else:
                color = 'y'
            
            buildings[key].plot_footprint(ax, color) 

    obs.plot_observers_location(ax, color='k')
    
    ax.set_aspect('equal')
    fig.set_size_inches(8, 8)

    # post-process for html
    canvas = FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response 




@app.route('/silhouette')
def draw_silhouette():
    fig = plt.figure()
    ax = fig.add_subplot(111)

    sun.draw(ax)       
    sil.draw(ax)

    ax.set_ylim([0, 90])
    ax.set_xlim([-180, 180])

    ax.set_aspect('equal', adjustable='box')
    fig.set_size_inches(10, 2.5)

    # post-process for html
    canvas = FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response 





