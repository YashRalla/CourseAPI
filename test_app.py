# TestClient is fastapi's inbuilt Unit test client
from fastapi.testclient import TestClient
from pymongo import MongoClient
from bson import ObjectId
import pytest
from main import app

# Run 'pytest' in terminal

client = TestClient(app)
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['Courses']

def test_get_courses_no_params():
    # A GET request is sent and its response is stored in the variable response
    response = client.get("/all_courses")
    # assert is a python keyword, it checks if the condition is true. If false, it raises an AssertionError and cancels the test.
    assert response.status_code == 200

def test_get_courses_sort_by_name():
    response = client.get("/all_courses?sort_by=name")
    assert response.status_code == 200
    # json() queries the JSON format object of the response and returns a Python Data Structure equivalent
    courses = response.json()
    assert len(courses) > 0
    # sorted(iterable, key, reverse) is a built in python method with the 3 parameters given, latter 2 being optional.
    # iterable is the sequence to sort e.g. list, dictionary, tuple
    # key is what decides the order according to which sorting is done
     # lambda in python is a keyword for using an anonymous function i.e. a function without a name. It is of the syntax 'lambda <variable> : <code involving the variable>' e.g. lambda a : a + 10
     # Here, the variable is 'x'. Each object in 'courses' will be assigned to 'x'. See below:

    #For instance, if the course list is as follows:
    # courses = [
    #               {'name': 'Math 101', 'id': 1},
    #               {'name': 'Biology 201', 'id': 2},
    #               {'name': 'Art 101', 'id': 3},
    #           ]
    # x will first take the value {'name': 'Math 101', 'id': 1}, so x['name'] would be 'Math 101'.
    # reverse determines the sorting order, takes -1 or 1. Default is 1 i.e. forward. This variable is not used here.
    assert sorted(courses, key=lambda x: x['name']) == courses
    # Basically, we are double checking the API's result with an internal python command.

def test_get_courses_sort_by_date():
    response = client.get("/all_courses?sort_by=date")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) > 0
    assert sorted(courses, key=lambda x: x['date'], reverse=True) == courses

def test_get_courses_sort_by_rating():
    response = client.get("/all_courses?sort_by=Rating")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) > 0
    assert sorted(courses, key=lambda x: x['Rating']['Total'], reverse=True) == courses

def test_get_courses_filter_by_domain():
    response = client.get("/all_courses?domain=mathematics")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) > 0
    # We are double checking if all of the values have the 'mathematics' domain
    assert all([c['domain'][0] == 'mathematics' for c in courses])

def test_get_courses_filter_by_domain_and_sort_by_alphabetical():
    response = client.get("/all_courses?domain=mathematics&sort_by=alphabetical")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) > 0
    assert all([c['domain'][0] == 'mathematics' for c in courses])
    assert sorted(courses, key=lambda x: x['name']) == courses

def test_get_courses_filter_by_domain_and_sort_by_date():
    response = client.get("/all_courses?domain=mathematics&sort_by=date")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) > 0
    assert all([c['domain'][0] == 'mathematics' for c in courses])
    assert sorted(courses, key=lambda x: x['date'], reverse=True) == courses

def test_get_course_by_id_exists():
    response = client.get("/all_courses/66e07c8d4ca6c59526066b95")
    assert response.status_code == 200
    course = response.json()
    course_db = db.CSE.find_one({'_id': ObjectId('66e07c8d4ca6c59526066b95')})
    name_db = course_db['name']
    name_response = course['name']
    assert name_db == name_response

def test_get_course_by_id_not_exists():
    response = client.get("/all_courses/66ec4463817a68750409cb4f")
    assert response.status_code == 404
    assert response.json() == {'detail': 'Course Not Found'}

def test_get_chapter_info():
    response = client.get("/all_courses/66ec4463817a68750409cb6c/1")
    assert response.status_code == 200
    chapter = response.json()
    assert chapter['name'] == 'Big Picture of Calculus'
    assert chapter['text'] == 'Highlights of Calculus'


def test_get_chapter_info_not_exists():
    response = client.get("/all_courses/66ec4463817a68750409cb6c/990")
    assert response.status_code == 404
    assert response.json() == {'detail': 'Chapter not found'}

def test_rate_chapter():
    course_id = "66ec4463817a68750409cb6f"
    chapter_id = "1"
    rating = 1

    response = client.post(f"/all_courses/{course_id}/{chapter_id}?Rating={rating}")

    assert response.status_code == 200

    # Check if the response body has the expected structure
    assert "name" in response.json()
    assert "Rating" in response.json()
    assert "Total" in response.json()["Rating"]
    assert "Count" in response.json()["Rating"]

    assert response.json()["Rating"]["Total"] > 0
    assert response.json()["Rating"]["Count"] > 0

def test_rate_chapter_not_exists():
    response = client.post("/all_courses/66ec4463817a68750409cb6f/990/rate", json={"Rating": 1})
    assert response.status_code == 404
    assert response.json() == {'detail': 'Not Found'}
