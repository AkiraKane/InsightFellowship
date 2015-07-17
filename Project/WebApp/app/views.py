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
  LATITUTE_DEFAULT = 40.767946 
  LONGITUDE_DEFAULT = -73.981831
  FLOOR_DEFAULT = 0
  MONTH_DEFAULT = 6
  DAY_DEFAULT = 23

  address = request.args.get('Address')
  floor = request.args.get('Floor')
  day_of_year = request.args.get('Day')
  
  if day_of_year:
  # extract month and day e.g. "4/13"
    try:
      input_date = parse(day_of_year)
      day = input_date.day
      month = input_date.month
    except:
      day_of_year = None

  if not day_of_year:
    day = DAY_DEFAULT
    month = MONTH_DEFAULT

  if address:
  # get coordinates from address
    (lon, lat) = get_GPS_from_address(address)
  else:
    lat = LATITUTE_DEFAULT
    lon = LONGITUDE_DEFAULT
  
  # ckeck if floor is entered
  if not floor:
    floor = FLOOR_DEFAULT

  z = float(floor) * 3 # each floor is roughly 3 meter

  return render_template("input.html", observer_lon=lon, observer_lat=lat, observer_z=z, \
                          day=day, month=month)
  


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


  # initialize figure
  fig = plt.figure()
  ax = fig.add_subplot(111)

  x_id_list = []
  y_id_list = []

  # determine integer ids of block
  cart = convert_to_cartesian(obs_lon, obs_lat, mean_lon, mean_lat, Earth_radius)
  t = find_my_block(cart.x, cart.y, x_grid, y_grid)
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

  for i in range(0, len(x_id_list)):
    x_id = x_id_list[i]
    y_id = y_id_list[i]
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

    
    for key in buildings:
      if buildings[key].z > obs_z:
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

  ax.set_aspect('equal')
  fig.set_size_inches(8, 8)

  canvas = FigureCanvas(fig)
  png_output = StringIO.StringIO()
  canvas.print_png(png_output)
  response = make_response(png_output.getvalue())
  response.headers['Content-Type'] = 'image/png'
  return response 




@app.route('/silhouette')
def draw_silhouette():

  # get input arguments
  obs_lon = float(request.args.get('lon'))
  obs_lat = float(request.args.get('lat'))
  obs_z = float(request.args.get('z'))
  day = int(request.args.get('day'))
  month = int(request.args.get('month'))

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

  x_id_list = []
  y_id_list = []


  
  # empty Silhouette
  sil = Silhouette()


  # determine integer ids of block
  cart = convert_to_cartesian(obs_lon, obs_lat, mean_lon, mean_lat, Earth_radius)
  t = find_my_block(cart.x, cart.y, x_grid, y_grid)
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

  for i in range(0, len(x_id_list)):
    x_id = x_id_list[i]
    y_id = y_id_list[i]
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

    # add building's roofs to silhouette
    for key in buildings:
      if buildings[key].z > obs_z:
        roofs = get_roofs(cart.x, cart.y, obs_z, buildings[key])
        for roof in roofs:
          sil.add_roof(roof)

  # calculate sun
  this_year = dt.datetime.today().year
  request_date = dt.datetime(this_year, month, day)

  sun = Sun_path(request_date, mean_lat, mean_lon)
  sun.calculate_path()
  v = sun.calculate_visibility(sil)
  message = str(v[0]) + ' min sunny / ' + str(v[1]) + ' min total'

  # draw figure
  fig = plt.figure()
  ax = fig.add_subplot(111)

  sun.draw(ax)       
  sil.draw(ax)

  plt.text(-50, 80, message)

  ax.set_ylim([0, 90])
  ax.set_xlim([-180, 180])
  ax.set_aspect('equal', adjustable='box')
  fig.set_size_inches(10, 2.5)

  #  send figure out
  canvas = FigureCanvas(fig)
  png_output = StringIO.StringIO()
  canvas.print_png(png_output)
  response = make_response(png_output.getvalue())
  response.headers['Content-Type'] = 'image/png'
  return response 




