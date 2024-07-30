from flask import Flask,request,jsonify, json,send_from_directory
from app import app
from db import my_col
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
from util import *


@app.route("/api/employee/<string:id>", methods=['GET'])
def view_employee(id:str):
    employee = my_col('employee').find_one(
        {"_id":ObjectId(id)},
        {"_id":0}
        )
    agency = my_col('agency').find_one(
        {"_id":employee['agency']['value']},
        {"_id":0,"name":1}
        )
    
    employee['agency']['value'] = str(employee['agency']['value'])
    employee['agency']['label'] = agency['name']

    return jsonify({
        "employee":employee
    })

@app.route('/api/save-employee', methods=['POST'])
async def save_employee():
    if request.method == 'POST':
        data = json.loads(request.data)

        employee_id = None
        message = None
        error = 0
        try:

            employee_data = my_col('employee').insert_one({           
                'name':data['name'],
                'agency':{
                    'value':ObjectId(data['agency']['value'])
                },
                'address':data['address'],
                'phoneNumber':data['phoneNumber'],
                'zipCode':data['zipCode'],
                'county':data['county'],                
                "created_at":datetime.now(),
                "updated_at":datetime.now()
            })
            employee_id = str(employee_data.inserted_id)
            message = 'Employee Data Saved Successfully'
            error = 0
        except Exception as ex:
            employee_id = None
            print('Employee Save Exception: ',ex)
            message = 'Employee Data Saving Failed'
            error  = 1

        return jsonify({
            "employee_id":employee_id,
            "message":message,
            "error":error
        })
    


@app.route('/api/save-employee/<string:id>', methods=['POST'])
async def update_employee(id:str):
    if request.method == 'POST':
        data = json.loads(request.data)

        employee_id = None
        message = None
        error = 0

        try:
            myquery = { "_id" :ObjectId(id)}

            newvalues = { "$set": {           
                'name':data['name'],
                'agency':{
                    'value':ObjectId(data['agency']['value'])
                },
                'address':data['address'],
                'phoneNumber':data['phoneNumber'],
                'zipCode':data['zipCode'],
                'county':data['county'],                                
                "updated_at":datetime.now()
            } }
            employee =  my_col('employee').update_one(myquery, newvalues)
            employee_id = id if employee.modified_count else None
            error = 0 if employee.modified_count else 1
            message = 'Employee Data Update Successfully'if employee.modified_count else 'Employee Data Update Failed'

        except Exception as ex:
            employee_id = None
            print('Employee Save Exception: ',ex)
            message = 'Employee Data Update Failed'
            error  = 1
        
        return jsonify({
            "employee_id":employee_id,
            "message":message,
            "error":error
        })



collection = my_col('employee')
@app.route('/api/employees', methods=['POST'])
@app.route('/api/employees/<angtid>', methods=['POST'])
def list_employees(angtid=None):
    data = request.get_json()
    page_index = data.get('pageIndex', 0)
    page_size = data.get('pageSize', 10)
    global_filter = data.get('filter', '')
    sort_by = data.get('sortBy', [])

    # Construct MongoDB filter query
    query = {
        #'role':{'$gte':10}
    }


    agency_id_list=[]
    if(angtid==None and global_filter!= ''):
        agency = my_col('agency').find(
            {'name':{"$regex":global_filter,"$options":"i"}},
            {'_id':1}
        )
        agency_list = list(agency)
        agency_id_list = [d.pop('_id') for d in agency_list]    

    if(angtid!=None):    
        query = {
            'agency.value':ObjectId(angtid)
        }

    if global_filter:
        query["$or"] = [
            {"name": {"$regex": global_filter, "$options": "i"}},
            {"address": {"$regex": global_filter, "$options": "i"}},
            {"phoneNumber": {"$regex": global_filter, "$options": "i"}},
            {"agency.value": {"$in":agency_id_list}},
            # Add other fields here if needed
        ]

    # Construct MongoDB sort parameters
    sort_params = []
    for sort in sort_by:
        sort_field = sort['id']
        sort_direction = -1 if sort['desc'] else 1
        sort_params.append((sort_field, sort_direction))

    # Fetch data from MongoDB
    if sort_params:
        cursor = collection.find(query).sort(sort_params).skip(page_index * page_size).limit(page_size)
    else:
        # Apply default sorting or skip sorting
        cursor = collection.find(query).skip(page_index * page_size).limit(page_size)

    total_count = collection.count_documents(query)
    data_list = []

    for todo in cursor:
        agency_id = todo['agency']['value']
        agency = my_col('agency').find_one(
        {"_id":ObjectId(agency_id)},
        {"_id":0,"name":1}
        )

        entry = {
            "_id":todo["_id"],
            "name":todo["name"],
            "phoneNumber":todo["phoneNumber"],
            "agency":agency["name"]
        }
        data_list.append(entry)

    #data_list = list(cursor)
    data_json = MongoJSONEncoder().encode(data_list)
    data_obj = json.loads(data_json)

    # Calculate total pages
    total_pages = (total_count + page_size - 1) // page_size
    

    return jsonify({
        'rows': data_obj,
        'pageCount': total_pages,
        'totalRows': total_count
    })