from flask import Flask,request,jsonify, json,send_from_directory
from app import app
from db import my_col
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
from util import *


@app.route("/api/marketer/<string:id>", methods=['GET'])
def view_marketer(id:str):
    marketer = my_col('marketer').find_one(
        {"_id":ObjectId(id)},
        {"_id":0}
        )
    marketer['contract_doc_id'] = str(marketer['contract_doc_id']) if marketer['contract_doc_id']!=None else ''
    return jsonify({
        "marketer":marketer
    })

@app.route("/api/marketer-dropdown/<int:type>", methods=['GET'])
def list_marketers_dropdown(type:int):
    cursor = my_col('marketer').find(
        {"deleted_at":None, 'type.value':type},
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


@app.route('/api/save-marketer/<string:id>', methods=['POST'])
async def update_marketer(id:str):
    if request.method == 'POST':
        data = json.loads(request.data)

        marketer_id = None
        message = None
        error = 0

        try:
            myquery = { "_id" :ObjectId(id)}

            newvalues = { "$set": {           
                'name':data['name'],
                'address':data['address'],
                'phoneNumber':data['phoneNumber'],
                'email':data['email'],                                
                'type':data['type'],
                'contract_type':data['contract_type'],
                'contract_doc_id':ObjectId(data['contract_doc_id']) if data['contract_doc_id']!='' else None,              
                "updated_at":datetime.now(),
                "deleted_at":None
            } }
            marketer =  my_col('marketer').update_one(myquery, newvalues)
            marketer_id = id if marketer.modified_count else None
            error = 0 if marketer.modified_count else 1
            message = 'Marketer Data Update Successfully'if marketer.modified_count else 'Marketer Data Update Failed'

        except Exception as ex:
            marketer_id = None
            print('Marketer Save Exception: ',ex)
            message = 'Marketer Data Update Failed'
            error  = 1
        
        return jsonify({
            "marketer_id":marketer_id,
            "message":message,
            "error":error
        })



@app.route('/api/save-marketer', methods=['POST'])
async def save_marketer():
    if request.method == 'POST':
        data = json.loads(request.data)

        marketer_id = None
        message = None
        error = 0
        try:

            marketer_data = my_col('marketer').insert_one({           
                'name':data['name'],
                'address':data['address'],
                'phoneNumber':data['phoneNumber'],
                'email':data['email'],                                
                'type':data['type'],
                'contract_type':data['contract_type'],
                'contract_doc_id':ObjectId(data['contract_doc_id']) if data['contract_doc_id']!='' else None,              
                "created_at":datetime.now(),
                "updated_at":datetime.now(),
                "deleted_at":None
            })
            marketer_id = str(marketer_data.inserted_id)
            message = 'Marketer Data Saved Successfully'
            error = 0
        except Exception as ex:
            marketer_id = None
            print('Marketer Save Exception: ',ex)
            message = 'Marketer Data Saving Failed'
            error  = 1

        return jsonify({
            "marketer_id":marketer_id,
            "message":message,
            "error":error
        })
    



collection = my_col('marketer')

@app.route('/api/marketer', methods=['POST'])
def list_marketer():
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
            {"email": {"$regex": global_filter, "$options": "i"}},
            {"type.value": {"$regex": global_filter, "$options": "i"}},
            {"contract_type.value": {"$regex": global_filter, "$options": "i"}},            
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



@app.route('/api/delete-marketer', methods=['POST'])
def delete_marketer():
    if request.method == 'POST':
        data = json.loads(request.data)

        id = data['id']

        marketer_id = None
        message = None
        error = 0
        deleted_done = 0

        try:
            myquery = { "_id" :ObjectId(id)}

            newvalues = { "$set": {                                     
                "deleted_at":datetime.now()                
            } }
            marketer =  my_col('marketer').update_one(myquery, newvalues)
            marketer_id = id if marketer.modified_count else None
            error = 0 if marketer.modified_count else 1
            deleted_done = 1 if marketer.modified_count else 0
            message = 'Marketer Data Deleted Successfully'if marketer.modified_count else 'Marketer Data Deletion Failed'

        except Exception as ex:
            marketer_id = None
            print('Marketer Save Exception: ',ex)
            message = 'Marketer Data Deletion Failed'
            error  = 1
            deleted_done = 0
        
        return jsonify({
            "marketer_id":marketer_id,
            "message":message,
            "error":error,
            "deleted_done":deleted_done
        })