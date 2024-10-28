import pymongo
import json


# Establishes a connection to the MongoDB server running on the provided URL. The client object acts as a gateway to this server
client = pymongo.MongoClient("mongodb://localhost:27017")
print("-------------------")
print(client)

# Accesses the database called 'Courses', or if it doesn't exist, it creates it
db = client["Courses"]
print("-------------------")
print(db)

# Accesses the collection within the 'Courses' database called 'CSE', creates if non-existent
collection = db["CSE"]
print("-------------------")
print(collection)

# Opens the 'courses.json' file in read mode and stores that data in the variable f, then it is loaded into the course_data variable
with open("courses.json", "r") as f:
    course_data = json.load(f)

print("-------------------")
print(course_data)

# Creates an index (using a method in the pymongo class) on the 'name' field in the JSON data for easier querying
collection.create_index("name")

# Adds a 'Rating' field for each course in the form of a dictionary that has the keywords 'Total' and 'Count'
for Course in course_data:
    Course['Rating'] = {'Total': 0, 'Count': 0}

# Checks if the 'Courses' have individual 'chapters' fields, then adds a 'Rating' field to each of those as well
for Course in course_data:    
    if 'chapters' in Course:
        for Chapter in Course['chapters']:
            Chapter['Rating'] = {'Total': 0, 'Count': 0}
    
for Course in course_data:   
    collection.insert_one(Course)

client.close()