from flask import Flask,request,jsonify, json,send_from_directory
from app import app
from db import my_col
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
from util import *


@app.route("/api/agency/<string:id>", methods=['GET'])
def view_agency(id:str):
    agency = my_col('agency').find_one(
        {"_id":ObjectId(id)},
        {"_id":0}
        )

    return jsonify({
        "agency":agency
    })
@app.route('/api/save-agency', methods=['POST'])
async def save_agency():
    if request.method == 'POST':
        data = json.loads(request.data)

        agency_id = None
        message = None
        error = 0
        try:

            agency_data = my_col('agency').insert_one({           
                'name':data['name'],
                'address':data['address'],
                'phoneNumber':data['phoneNumber'],
                'zipCode':data['zipCode'],
                'county':data['county'],
                'state':data['state'],
                "created_at":datetime.now(),
                "updated_at":datetime.now(),
                "deleted_at":None
            })
            agency_id = str(agency_data.inserted_id)
            message = 'Agency Data Saved Successfully'
            error = 0
        except Exception as ex:
            agency_id = None
            print('Agency Save Exception: ',ex)
            message = 'Agency Data Saving Failed'
            error  = 1

        return jsonify({
            "agency_id":agency_id,
            "message":message,
            "error":error
        })


@app.route('/api/save-agency/<string:id>', methods=['POST'])
async def update_agency(id:str):
    if request.method == 'POST':
        data = json.loads(request.data)

        agency_id = None
        message = None
        error = 0

        try:
            myquery = { "_id" :ObjectId(id)}

            newvalues = { "$set": {           
                'name':data['name'],
                'address':data['address'],
                'phoneNumber':data['phoneNumber'],
                'zipCode':data['zipCode'],
                'county':data['county'],
                'state':data['state'],                
                "updated_at":datetime.now()
            } }
            agency =  my_col('agency').update_one(myquery, newvalues)
            agency_id = id if agency.modified_count else None
            error = 0 if agency.modified_count else 1
            message = 'Agency Data Update Successfully'if agency.modified_count else 'Agency Data Update Failed'

        except Exception as ex:
            agency_id = None
            print('Agency Save Exception: ',ex)
            message = 'Agency Data Update Failed'
            error  = 1
        
        return jsonify({
            "agency_id":agency_id,
            "message":message,
            "error":error
        })



collection = my_col('agency')

@app.route('/api/agencys', methods=['POST'])
def list_agencys():
    data = request.get_json()
    page_index = data.get('pageIndex', 0)
    page_size = data.get('pageSize', 10)
    global_filter = data.get('filter', '')
    sort_by = data.get('sortBy', [])

    # Construct MongoDB filter query
    query = {
        #'role':{'$gte':10}
    }
    if global_filter:
        query["$or"] = [
            {"name": {"$regex": global_filter, "$options": "i"}},
            {"address": {"$regex": global_filter, "$options": "i"}},
            {"phoneNumber": {"$regex": global_filter, "$options": "i"}},
            {"zipCode": {"$regex": global_filter, "$options": "i"}},
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
    data_list = list(cursor)
    data_json = MongoJSONEncoder().encode(data_list)
    data_obj = json.loads(data_json)

    # Calculate total pages
    total_pages = (total_count + page_size - 1) // page_size
    

    return jsonify({
        'rows': data_obj,
        'pageCount': total_pages,
        'totalRows': total_count
    })


@app.route("/api/agencys-dropdown", methods=['GET'])
def list_agencys_dropdown():
    cursor = my_col('agency').find(
        {},
        {'_id':1,'name':1}
        )
    list_cur = []
    for todo in cursor:               
        list_cur.append({'value':str(todo['_id']),'label':todo['name']})
    #list_cur = list(cursor)
    #data_json = MongoJSONEncoder().encode(list_cur)
    #data_obj = json.loads(data_json)
    return jsonify({
        "list":list_cur
    })  