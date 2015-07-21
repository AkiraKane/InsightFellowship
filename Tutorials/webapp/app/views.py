from flask import render_template, request
from app import app
import pymysql as mdb
from a_Model import ModelIt

db= mdb.connect(user="root", host="localhost", passwd="123", db="world_innodb", charset='utf8')

@app.route('/_add_numbers')
def add_numbers():
    """Add two numbers server side, ridiculous but well..."""
    a = request.args.get('a', 0, type=int)
    b = request.args.get('b', 0, type=int)
    return jsonify(result=a + b)


@app.route('/')
def index():
    return render_template('myindex.html')

if __name__ == '__main__':
    app.run()


@app.route('/db')
def cities_page():
    with db: 
        cur = db.cursor()
        cur.execute("SELECT Name FROM City LIMIT 15;")
        query_results = cur.fetchall()
    cities = ""
    for result in query_results:
        cities += result[0]
        cities += "<br>"
    return cities

@app.route("/db_fancy")
def cities_page_fancy():
    with db:
        cur = db.cursor()
        cur.execute("SELECT Name, CountryCode, Population FROM City ORDER BY Population LIMIT 15;")

        query_results = cur.fetchall()
    cities = []
    for result in query_results:
        cities.append(dict(name=result[0], country=result[1], population=result[2]))
    return render_template('cities.html', cities=cities) 

@app.route('/input')
def cities_input():
  return render_template("input.html")

@app.route('/output')
def cities_output():
  city = request.args.get('ID')

  with db:
    cur = db.cursor()
    #just select the city from the world_innodb that the user inputs
    cur.execute("SELECT Name, CountryCode,  Population FROM City WHERE Name='%s';" % city)
    query_results = cur.fetchall()

  cities = []
  for result in query_results:
    cities.append(dict(name=result[0], country=result[1], population=result[2]))

  #call a function from a_Model package. note we are only pulling one result in the query
  pop_input = cities[0]['population']
  the_result = ModelIt(city, pop_input)
  return render_template("output.html", cities = cities, the_result = the_result)
  