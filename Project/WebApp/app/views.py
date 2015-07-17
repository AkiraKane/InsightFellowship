from flask import render_template, request, make_response
from app import app
import StringIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from my_classes import *

con = mdb.connect('localhost', 'root', '123', 'Manhattan_buildings')

@app.route('/input')
def input():
  # default values
  LATITUTE_DEFAULT = 40.756636
  LONGITUDE_DEFAULT = -73.986362
  FLOOR_DEFAULT = 0

  address = request.args.get('Address')
  floor = request.args.get('Floor')
  day_of_year = request.args.get('Day')
  
  if address:
  # get coordinates from address
    (lon, lat) = get_GPS_from_address(address)
  else:
    lat = LATITUTE_DEFAULT
    lon = LONGITUDE_DEFAULT
  
  # ckeck if floor is entered
  if not floor:
    floor = FLOOR_DEFAULT

  z = floor *0.333333 # each floor is roughly 3 meter

  return render_template("input.html", observer_lon=lon, observer_lat=lat, observer_z=z)
  


@app.route('/block_map')
def draw_block():

  # get input arguments
  obs_lon = float(request.args.get('lon'))
  obs_lat = float(request.args.get('lat'))
  obs_z = float(request.args.get('z'))

  # print '================================'
  # print [obs_lon, obs_lat, obs_z]
  # print '================================'
  
  # load basic geography of Manhattan
  with con:
    cur = con.cursor()
    cur.execute("SELECT * FROM Cities WHERE Name = 'New York Manhattan'")
    result = cur.fetchall()[0]
    Earth_radius = result[2]
    mean_lon = result[3]
    mean_lat = result[4]
  
  # load grid data 
  with con:
    cur = con.cursor()
    cur.execute("SELECT * FROM Grids WHERE Id = 1")
    result = cur.fetchall()[0]

    x_min = result[1]
    x_max = result[2]
    x_step = result[3]
    y_min = result[4]
    y_max = result[5]
    y_step = result[6]

    x_grid = np.arange(x_min, x_max, x_step)
    y_grid = np.arange(y_min, y_max, y_step)

  # determine integer ids of block
  cart = convert_to_cartesian(obs_lon, obs_lat, mean_lon, mean_lat, Earth_radius)
  t = find_my_block(cart.x, cart.y, x_grid, y_grid)
  x_id = t[0]
  y_id = t[1]

  block_id = None
  with con: 
    cur = con.cursor()
    # get block_id
    cur.execute("SELECT Id\
                    FROM Blocks\
                    WHERE X_id = " + str(x_id) + "\
                    AND Y_id = " + str(y_id) + "\
    ")
    result = cur.fetchall()
    
    if result:
      block_id = result[0][0]
      
      # select all nodes in the block
      cur.execute("SELECT X, Y, Z, \
                      Order_in_building,\
                      Number_of_nodes_in_building,\
                      Building_id \
                      FROM Nodes \
                      WHERE Block_id = " + str(block_id) + " \
                      AND Z > 0 \
      ")
      rows = cur.fetchall()
      
      # load it into a dict of buildings
      buildings = {}
      i = 0
      while i < len(rows):
        
        # find the first "1" in the Order_in_building column
        if rows[i][3] == 1:
          
          building_id = rows[i][5]
          building = Building()
          
          number_of_nodes = rows[i][4]
          
          # loop through the consecutive nodes
          for j in range(0, number_of_nodes):
            i_cursor = i + j
            x = rows[i_cursor][0]
            y = rows[i_cursor][1]
            building.nodes.append(Node(x,y))
          
          z = rows[i_cursor][2]
          building.z = z
          building.calculate_center()
          
          buildings[building_id] = building
          
          i += number_of_nodes
        else:
          i += 1

  # initialize figure
  fig = plt.figure()
  ax = fig.add_subplot(111)

  for key in buildings:
    # set color of the buildings
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
    # plot each building
    buildings[key].plot_footprint(ax, color) 

  # plot observer's location
  ax.plot([cart.x], [cart.y], color='k', marker='o', markersize=10)
  # plot North-South, East-West lines crossing at the observer's location
  length = 300
  ax.plot([cart.x, cart.x], [cart.y - length, cart.y + length], color='k')
  ax.plot([cart.x - length, cart.x + length], [cart.y, cart.y], color='k')

  ax.set_aspect('equal', adjustable='box')
  fig.set_size_inches(8, 8)

  canvas = FigureCanvas(fig)
  png_output = StringIO.StringIO()
  canvas.print_png(png_output)
  response = make_response(png_output.getvalue())
  response.headers['Content-Type'] = 'image/png'
  return response 



