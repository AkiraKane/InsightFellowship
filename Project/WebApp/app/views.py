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
# import datetime as dt
import pymysql as mdb

# my modules
from buildingmapping import *
from skyline import *
from sun import *
from observer import *


#  declare global instances
obs = Observer()
sil = Silhouette()
sun = SunPath()
buildings = {}
x_grid = None
y_grid = None


con = mdb.connect('localhost', 'root', '123', 'Manhattan_buildings')

obs.load_basic_geography(con)
(x_grid, y_grid) = load_grid_data(con)


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

    address_placeholder = str(obs.lat) + ', ' + str(obs.lon)
    floor_placeholder = str(int(round(obs.z / 3.0)))
    day_placeholder = str(sun.date.month) + '/' + str(sun.date.day)
    return render_template(\
        "input.html", \
        message=message, \
        address_placeholder=address_placeholder, \
        floor_placeholder=floor_placeholder, \
        day_placeholder=day_placeholder \
    )
    


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
    sil.draw(ax, theta_offset=0, phi_offset=0)

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


@app.route('/polar_plot')
def draw_polar_plot():
    fig = plt.figure()
    ax = fig.add_subplot(111)

    theta_offset = 1.5
    phi_offset = -np.pi/2
    sil.draw(ax, polar=True, fill=False, theta_offset=theta_offset, phi_offset=phi_offset)
    sun.draw_polar(ax, theta_offset=theta_offset, phi_offset=phi_offset)
    fig.set_size_inches(10, 10)

    # post-process for html
    canvas = FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response 


@app.route('/inverted_polar_plot')
def draw_inverted_polar_plot():
    fig = plt.figure()
    ax = fig.add_subplot(111)

    sil.draw_inverted_polar(ax, color='k')
    sun.draw_inverted_polar(ax, color='#ffa700', linewidth=3.0)

    fig.set_size_inches(8, 8)


    # post-process for html
    canvas = FigureCanvas(fig)
    png_output = StringIO.StringIO()
    canvas.print_png(png_output)
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response 



