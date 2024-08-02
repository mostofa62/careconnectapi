from flask import Flask,request,jsonify, json,send_from_directory
from app import app
from db import my_col
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
from util import *


@app.route("/api/insurance/<string:id>", methods=['GET'])
def view_insurance(id:str):
    insurance = my_col('insurance').find_one(
        {"_id":ObjectId(id)},
        {"_id":0}
        )

    return jsonify({
        "insurance":insurance
    })
@app.route('/api/save-insurance', methods=['POST'])
async def save_insurance():
    if request.method == 'POST':
        data = json.loads(request.data)

        insurance_id = None
        message = None
        error = 0
        try:

            insurance_data = my_col('insurance').insert_one({           
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
            insurance_id = str(insurance_data.inserted_id)
            message = 'Insurance Data Saved Successfully'
            error = 0
        except Exception as ex:
            insurance_id = None
            print('Insurance Save Exception: ',ex)
            message = 'Insurance Data Saving Failed'
            error  = 1

        return jsonify({
            "insurance_id":insurance_id,
            "message":message,
            "error":error
        })


@app.route('/api/save-insurance/<string:id>', methods=['POST'])
async def update_insurance(id:str):
    if request.method == 'POST':
        data = json.loads(request.data)

        insurance_id = None
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
                "updated_at":datetime.now(),
                "deleted_at":None
            } }
            insurance =  my_col('insurance').update_one(myquery, newvalues)
            insurance_id = id if insurance.modified_count else None
            error = 0 if insurance.modified_count else 1
            message = 'Insurance Data Update Successfully'if insurance.modified_count else 'Insurance Data Update Failed'

        except Exception as ex:
            insurance_id = None
            print('Insurance Save Exception: ',ex)
            message = 'Insurance Data Update Failed'
            error  = 1
        
        return jsonify({
            "insurance_id":insurance_id,
            "message":message,
            "error":error
        })





collection = my_col('insurance')

@app.route('/api/insurances', methods=['POST'])
def list_insurance():
    data = request.get_json()
    page_index = data.get('pageIndex', 0)
    page_size = data.get('pageSize', 10)
    global_filter = data.get('filter', '')
    sort_by = data.get('sortBy', [])

    # Construct MongoDB filter query
    query = {
        #'role':{'$gte':10}
        "deleted_at":None
    }
    if global_filter:
        query["$or"] = [
            {"name": {"$regex": global_filter, "$options": "i"}},
            {"address": {"$regex": global_filter, "$options": "i"}},
            {"phoneNumber": {"$regex": global_filter, "$options": "i"}},
            {"zipCode": {"$regex": global_filter, "$options": "i"}},
            {"state.value": {"$regex": global_filter, "$options": "i"}},
            {"county.label": {"$regex": global_filter, "$options": "i"}},
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


@app.route("/api/insurances-dropdown", methods=['GET'])
def list_insurances_dropdown():
    cursor = my_col('insurance').find(
        {"deleted_at":None},
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



@app.route('/api/delete-insurances', methods=['POST'])
def delete_insurance():
    if request.method == 'POST':
        data = json.loads(request.data)

        id = data['id']

        insurance_id = None
        message = None
        error = 0
        deleted_done = 0

        try:
            myquery = { "_id" :ObjectId(id)}

            newvalues = { "$set": {                                     
                "deleted_at":datetime.now()                
            } }
            insurance =  my_col('insurance').update_one(myquery, newvalues)
            insurance_id = id if insurance.modified_count else None
            error = 0 if insurance.modified_count else 1
            deleted_done = 1 if insurance.modified_count else 0
            message = 'Insurance Data Deleted Successfully'if insurance.modified_count else 'Insurance Data Deletion Failed'

        except Exception as ex:
            insurance_id = None
            print('Insurance Save Exception: ',ex)
            message = 'Insurance Data Deletion Failed'
            error  = 1
            deleted_done = 0
        
        return jsonify({
            "insurance_id":insurance_id,
            "message":message,
            "error":error,
            "deleted_done":deleted_done
        })