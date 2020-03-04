#!/bin/python3
# bottle lib for POST and GET requests
from bottle import run, request, route, post
from math import sin, cos, sqrt, atan2, radians 
import sqlite3 
import json

IP = '127.0.0.1'
PORT = 12345
Name_db = 'ITea.db'


@post('/insert')
def insert():
    conn = sqlite3.connect(Name_db)
    cursor = conn.cursor()
    values = request.json
    cursor.execute(
       "INSERT INTO `Points` (`id`, `tag`, `lat`, `lng`, `name`, `description`) VALUES " +
       ("(NULL, '%(tag)s', '%(lat)s', '%(lng)s', '%(name)s', '%(desc)s');" % values))
    conn.commit()


#@route('/create')
def create_db():
    conn = sqlite3.connect(Name_db)
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE Points" +
        "(id INTEGER PRIMARY KEY AUTOINCREMENT," +
        " lng real, lat real, tag varchar(15)," +
        " name varchar(32), description varchar(255))")


def dist(lat1, lon1, lat2, lon2):
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return 6373.0 * c


def near_points(user_lng, user_lat, points, dist_expected):
    answer = []
    for point in points:
        lat1 = radians(float(point["lat"]))
        lng1 = radians(float(point["lng"]))
        lat2 = radians(user_lat)
        lng2 = radians(user_lng)
        dist_real = dist(lat1, lng1, lat2, lng2)
        if dist_real <= dist_expected:
            answer.append(point)
    print("OK -- " + str(len(answer)))
    return answer


def get_value(req_info):
    conn = sqlite3.connect(Name_db)
    cursor = conn.cursor()
    tags = []  # All tags form user
    request_db = ""  # Full sql request to database
    count_tags = len(req_info["tags"])
    for j in req_info["tags"]:
        tags.append(j["tag"])

    for tag_index in range(count_tags):  # Create sql request
        request_db += "tag = '" + tags[tag_index] + "'"
        if count_tags != tag_index + 1:  # If it's tag is NOT last
            request_db += " or "

    cursor.execute("select lat, lng, tag from Points where " + request_db)
    recurs = []  # Answer from database to list:
    columns = [column[0] for column in cursor.description]
    for row in cursor.fetchall():
        recurs.append(dict(zip(columns, row)))
    return recurs


@post('/getPoints')  # Return near points by tags
def get_points():
    distance = 1.5  # Limit of reach
    req_info = request.json
    ans_db = get_value(req_info)  # Sort by tags
    answer = near_points(         # Sort by distance
        req_info["personLan"],
        req_info["personLng"],
        ans_db, distance)
    return json.dumps({'entries': answer})


def get_all_db():
    conn = sqlite3.connect(Name_db)
    cursor = conn.cursor()
    cursor.execute(
        "select * from Points"
    )
    recurs = []
    columns = [column[0] for column in cursor.description]
    for row in cursor.fetchall():
        recurs.append(dict(zip(columns, row)))
    return recurs


@post('/getInfo')
def get_info():
    coordinates = request.json  # Lng, lat
    points = get_all_db()
    min_dist = 10000
    nearest_point = []
    answer = {}
    for point in points:
        distance = dist(
            radians(float(point["lat"])),
            radians(float(point["lng"])),
            radians(float(coordinates["Lat"])),
            radians(float(coordinates["Lng"])))

        if distance < min_dist:
            min_dist = distance
            nearest_point = point
    if min_dist <= 0.1:
        answer = {
            'name': nearest_point["name"],
            'description': nearest_point["description"]}
    return json.dumps(answer)


run(host=IP, port=PORT)
