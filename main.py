import contextlib # Used to suppress exceptions e.g. missing keys in a dictionary
from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from bson import ObjectId
from fastapi.encoders import jsonable_encoder # Encodes objects into JSON-compatible format

app = FastAPI()
client = MongoClient("mongodb://localhost:27017")
db = client['Courses']

# GET All courses endpoint (/Courses - GET)

# @app.get is a decorator method that is a part of the FastAPI class, which was instantiated earlier.
@app.get('/all_courses') # The value in the parentheses can be named as per our wish
# The above decorator takes the optional parameters sort_by and domain, specified below
def get_courses(sort_by: str = 'date', domain: str = None):
    # find() queries all the documents in the CSE collection of the Courses database and returns them
    # The for loop then iterates through each of those documents
    # Trying the below line due to local variable referenced before assignment error when running pytest
    global sort_field, sort_order
    for course in db.CSE.find():
        #Initializing the variables total and count, setting them to 0
        total = 0
        count = 0
        for Chapter in course['chapters']:
            # Contextlib is used to avoid a traceback in case a chapter doesn't have a rating field
            with contextlib.suppress(KeyError):
                total = total + Chapter['Rating']['Total']
                count = count + Chapter['Rating']['Count']
        # See note at bottom
        db.CSE.update_one({'_id': course['_id']}, {'$set': {'Rating': {'Total': total, 'Count': count}}})

        # Depending on the sort_by variable defined in FastAPI.get(), we define sort_field and sort_order variables that later get used in querying

        # Sorting in descending order
        if sort_by == 'date':
            sort_field = 'date'
            sort_order = -1
        
        # Again sorting in descending order
        elif sort_by == 'Rating':
            sort_field = 'Rating.Total'
            sort_order = -1
        
        # This time in ascending
        elif sort_by == 'name':
            sort_field = 'name'
            sort_order = 1
        
        # Initializing an empty dictionary camed 'query'
        query = {}

        # If the domain parameter has a value:
        if domain:
            # Add a key-value pair to the query dictionary, 'domain' is key and domain is value
            query['domain'] = domain
        
        # Querying the collection and storing that in a new variable
        # See note 2 for more information

        course_list = db.CSE.find(query, {'name': 1, 'date': 1, 'description': 1, 'domain':1,'Rating':1,'_id': 0}).sort(sort_field, sort_order)
        return list(course_list)
    
    # Enter http://127.0.0.1:8000/all_courses in browser
    # Enter http://127.0.0.1:8000/docs in browser to get the interactive version that only gives what you asked for (do be sure to run 'uvicorn main:app --reload' in the terminal first)

# GET selected course overview Endpoint
@app.get('/all_courses/{course_id}')
def get_course(course_id: str):
    # find_one(query, projection) uses 2 parameters, one being query, the other being projection.
    # query = {'_id': ObjectId(course_id)}, searches for the object whose ObjectId (part of FastAPI class) matches the internal _id parameter
    # (This means we have to paste the ObjectID from the DB into the {course_id}) part of the URL
    # projection = {}, list of fields to be excluded from result. Key is the field to be excluded, value should be 0 if excluded.
    selected_course = db.CSE.find_one({'_id': ObjectId(course_id)}, {'_id':0, 'chapters': 0})
    # If selected_course isn't found, rather than get a nonsense exception raised, this is a more graceful solution
    if not selected_course:
        raise HTTPException(status_code=404, detail='Course Not Found')
    # If the field we wan't doesn't have a value, a traceback will be raised and the code will be interrupted. This is to prevent that
    try:
        selected_course['Rating'] = selected_course['Rating']['Total']
    except KeyError:
        selected_course['Rating'] = 'Not rated yet'
    
    return selected_course

# GET Selected chapter Endpoint
@app.get('/all_courses/{course_id}/{chapter_id}')
def get_chapter(course_id: str, chapter_id: str):
    # This time, the projection will only exclude the _id field as we actually need chapters
    # Is 0 the only option in the projection? Need to read more
    selected_course = db.CSE.find_one({'_id': ObjectId(course_id)}, {'_id': 0})
    if not selected_course:
        raise HTTPException(status_code=404, detail='Course not found')
    # Getting a list of chapters from the collection. The first parameter - if course has a chapters field, it gets the list of chapters
    # The second parameter - if the chapters field doesn't exist, an empty list is returned
    # Read more on the get method
    chapter_list = selected_course.get('chapters', [])
    try:
        # Indexes the chapter list according to chapter_id, which is converted to int for this purpose
        selected_chapter = chapter_list[int(chapter_id)]
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=404, detail='Chapter not found') from e
    return selected_chapter

# POST rating of chapter Endpoint (i.e. update chapter rating)
@app.post('/all_courses/{course_id}/{chapter_id}')
# The rating parameter is of a query type which reads a rating variable, reads input from -2 to 2 (In this case though, let's limit the approval rating to 1, and disapproval to -1)
def rate_chapter(course_id: str, chapter_id: str, Rating: int = Query(..., gt=-2, lt=2)):
    selected_course = db.CSE.find_one({'_id': ObjectId(course_id)}, {'_id': 0, })
    if not selected_course:
        raise HTTPException(status_code=404, detail='Course not found')
    chapter_list = selected_course.get('chapters', [])
    try:
        selected_chapter = chapter_list[int(chapter_id)]
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=404, detail='Chapter not found') from e
    try:
        selected_chapter['Rating']['Total'] += Rating
        selected_chapter['Rating']['Count'] += 1
    # KeyError will be raised if chapter doesn't have a rating field already
    except KeyError:
        selected_chapter['Rating'] = {'Total': Rating, 'Count': 1}
    db.CSE.update_one({'_id': ObjectId(course_id)}, {'$set': {'chapters': chapter_list}})
    return selected_chapter