from flask import Flask,request,jsonify, json,send_from_directory
from app import app
from db import my_col
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
from util import *


@app.route("/api/caregiver/<string:id>", methods=['GET'])
def view_caregiver(id:str):
    caregiver = my_col('caregiver').find_one(
        {"_id":ObjectId(id)},
        {"_id":0}
        )
    
    caregiver['photo_attachment_id'] = str(caregiver['photo_attachment_id']) if caregiver['photo_attachment_id']!=None else ''
    caregiver['ssn_attachment_id'] = str(caregiver['ssn_attachment_id']) if caregiver['ssn_attachment_id']!=None else ''
    caregiver['bank_attachment_id'] = str(caregiver['bank_attachment_id']) if caregiver['bank_attachment_id']!=None else ''
    caregiver['physical_form_attachment_id'] = str(caregiver['physical_form_attachment_id']) if caregiver['physical_form_attachment_id']!=None else ''
    caregiver['wfour_form_attachment_id'] = str(caregiver['wfour_form_attachment_id']) if caregiver['wfour_form_attachment_id']!=None else ''

    return jsonify({
        "caregiver":caregiver
    })

@app.route("/api/caregiver-dropdown", methods=['GET'])
def list_caregivers_dropdown():
    cursor = my_col('caregiver').find(
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


@app.route('/api/save-caregiver/<string:id>', methods=['POST'])
async def update_caregiver(id:str):
    if request.method == 'POST':
        data = json.loads(request.data)

        caregiver_id = None
        message = None
        error = 0

        try:
            myquery = { "_id" :ObjectId(id)}

            newvalues = { "$set": {           
                'name':data['name'],
                'address':data['address'],
                'phoneNumber':data['phoneNumber'],
                'email':data['email'],                                
                'ssn':data['ssn'],
                'bank_acc_no':data['bank_acc_no'],
                'bank_routing_no':data['bank_routing_no'],
                'working_schedule':data['working_schedule'],

                'photo_attachment_id':ObjectId(data['photo_attachment_id']) if data['photo_attachment_id']!='' else None,
                'ssn_attachment_id':ObjectId(data['ssn_attachment_id']) if data['ssn_attachment_id']!='' else None,
                'bank_attachment_id':ObjectId(data['bank_attachment_id']) if data['bank_attachment_id']!='' else None,
                'physical_form_attachment_id':ObjectId(data['physical_form_attachment_id']) if data['physical_form_attachment_id']!='' else None,
                'wfour_form_attachment_id':ObjectId(data['wfour_form_attachment_id']) if data['wfour_form_attachment_id']!='' else None,

                "updated_at":datetime.now(),
                "deleted_at":None
            } }
            caregiver =  my_col('caregiver').update_one(myquery, newvalues)
            caregiver_id = id if caregiver.modified_count else None
            error = 0 if caregiver.modified_count else 1
            message = 'Caregiver Data Update Successfully'if caregiver.modified_count else 'Caregiver Data Update Failed'

        except Exception as ex:
            caregiver_id = None
            print('Caregiver Save Exception: ',ex)
            message = 'Caregiver Data Update Failed'
            error  = 1
        
        return jsonify({
            "caregiver_id":caregiver_id,
            "message":message,
            "error":error
        })



@app.route('/api/save-caregiver', methods=['POST'])
async def save_caregiver():
    if request.method == 'POST':
        data = json.loads(request.data)

        caregiver_id = None
        message = None
        error = 0
        try:

            caregiver_data = my_col('caregiver').insert_one({           
                'name':data['name'],
                'address':data['address'],
                'phoneNumber':data['phoneNumber'],
                'email':data['email'],                                
                'ssn':data['ssn'],
                'bank_acc_no':data['bank_acc_no'],
                'bank_routing_no':data['bank_routing_no'],
                'working_schedule':data['working_schedule'],

                'photo_attachment_id':ObjectId(data['photo_attachment_id']) if data['photo_attachment_id']!='' else None,
                'ssn_attachment_id':ObjectId(data['ssn_attachment_id']) if data['ssn_attachment_id']!='' else None,
                'bank_attachment_id':ObjectId(data['bank_attachment_id']) if data['bank_attachment_id']!='' else None,
                'physical_form_attachment_id':ObjectId(data['physical_form_attachment_id']) if data['physical_form_attachment_id']!='' else None,
                'wfour_form_attachment_id':ObjectId(data['wfour_form_attachment_id']) if data['wfour_form_attachment_id']!='' else None,

                "created_at":datetime.now(),
                "updated_at":datetime.now(),
                "deleted_at":None
            })
            caregiver_id = str(caregiver_data.inserted_id)
            message = 'Caregiver Data Saved Successfully'
            error = 0
        except Exception as ex:
            caregiver_id = None
            print('Caregiver Save Exception: ',ex)
            message = 'Caregiver Data Saving Failed'
            error  = 1

        return jsonify({
            "caregiver_id":caregiver_id,
            "message":message,
            "error":error
        })
    



collection = my_col('caregiver')

@app.route('/api/caregiver', methods=['POST'])
def list_caregiver():
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
            {"ssn": {"$regex": global_filter, "$options": "i"}},
            {"bank_acc_no": {"$regex": global_filter, "$options": "i"}},
            {"bank_routing_no": {"$regex": global_filter, "$options": "i"}},            
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
        total_hours = sum(map(lambda item: item.get("total_hour", 0), todo['working_schedule']))
        todo['total_hour']=total_hours
        data_list.append(todo)
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



@app.route('/api/delete-caregiver', methods=['POST'])
def delete_caregiver():
    if request.method == 'POST':
        data = json.loads(request.data)

        id = data['id']

        caregiver_id = None
        message = None
        error = 0
        deleted_done = 0

        try:
            myquery = { "_id" :ObjectId(id)}

            newvalues = { "$set": {                                     
                "deleted_at":datetime.now()                
            } }
            caregiver =  my_col('caregiver').update_one(myquery, newvalues)
            caregiver_id = id if caregiver.modified_count else None
            error = 0 if caregiver.modified_count else 1
            deleted_done = 1 if caregiver.modified_count else 0
            message = 'Caregiver Data Deleted Successfully'if caregiver.modified_count else 'Caregiver Data Deletion Failed'

        except Exception as ex:
            caregiver_id = None
            print('Caregiver Save Exception: ',ex)
            message = 'Caregiver Data Deletion Failed'
            error  = 1
            deleted_done = 0
        
        return jsonify({
            "caregiver_id":caregiver_id,
            "message":message,
            "error":error,
            "deleted_done":deleted_done
        })