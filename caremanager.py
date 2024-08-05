from flask import Flask,request,jsonify, json,send_from_directory
from app import app
from db import my_col
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
from util import *


@app.route("/api/caremanager/<string:id>", methods=['GET'])
def view_caremanager(id:str):
    caremanager = my_col('caremanager').find_one(
        {"_id":ObjectId(id)},
        {"_id":0}
        )

    insurance = my_col('insurance').find_one(
        {"_id":caremanager['insurance']['value']},
        {"_id":0,"name":1}
        )
    
    caremanager['insurance']['value'] = str(caremanager['insurance']['value'])
    caremanager['insurance']['label'] = insurance['name']

    return jsonify({
        "caremanager":caremanager
    })

@app.route('/api/save-caremanager', methods=['POST'])
async def save_caremanager():
    if request.method == 'POST':
        data = json.loads(request.data)

        caremanager_id = None
        message = None
        error = 0
        try:

            caremanager_data = my_col('caremanager').insert_one({           
                'name':data['name'],
                'insurance':{
                    'value':ObjectId(data['insurance']['value']),
                    #'label':data['insurance']['label']
                },                
                'designation':data['designation'],
                'phoneNumber':data['phoneNumber'],                             
                "created_at":datetime.now(),
                "updated_at":datetime.now(),
                "deleted_at":None
            })
            caremanager_id = str(caremanager_data.inserted_id)
            message = 'Caremanager Data Saved Successfully'
            error = 0
        except Exception as ex:
            caremanager_id = None
            print('Caremanager Save Exception: ',ex)
            message = 'Caremanager Data Saving Failed'
            error  = 1

        return jsonify({
            "caremanager_id":caremanager_id,
            "message":message,
            "error":error
        })
    


@app.route('/api/save-caremanager/<string:id>', methods=['POST'])
async def update_caremanager(id:str):
    if request.method == 'POST':
        data = json.loads(request.data)

        caremanager_id = None
        message = None
        error = 0

        try:
            myquery = { "_id" :ObjectId(id)}

            newvalues = { "$set": {           
                'name':data['name'],
                'insurance':{
                    'value':ObjectId(data['insurance']['value']),
                    #'label':data['insurance']['label']
                }, 
                'designation':data['designation'],
                'phoneNumber':data['phoneNumber'],                                                
                "updated_at":datetime.now()
            } }
            caremanager =  my_col('caremanager').update_one(myquery, newvalues)
            caremanager_id = id if caremanager.modified_count else None
            error = 0 if caremanager.modified_count else 1
            message = 'Caremanager Data Update Successfully'if caremanager.modified_count else 'Caremanager Data Update Failed'

        except Exception as ex:
            caremanager_id = None
            print('Caremanager Save Exception: ',ex)
            message = 'Caremanager Data Update Failed'
            error  = 1
        
        return jsonify({
            "caremanager_id":caremanager_id,
            "message":message,
            "error":error
        })
    


collection = my_col('caremanager')
@app.route('/api/caremanagers', methods=['POST'])
@app.route('/api/caremanagers/<insid>', methods=['POST'])
def list_caremanagers(insid=None):
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
    insurance_id_list=[]
    if(insid==None and global_filter!= ''):
        insurance = my_col('insurance').find(
            {'name':{"$regex":global_filter,"$options":"i"}},
            {'_id':1}
        )
        insurance_list = list(insurance)
        insurance_id_list = [d.pop('_id') for d in insurance_list]

    #print(insurance_id_list)    

    if(insid!=None):    
        query = {
            'insurance.value':ObjectId(insid),
            "deleted_at":None
        }

    if global_filter:
        query["$or"] = [
            {"name": {"$regex": global_filter, "$options": "i"}},
            {"designation": {"$regex": global_filter, "$options": "i"}},
            {"phoneNumber": {"$regex": global_filter, "$options": "i"}},
            {"insurance.value": {"$in":insurance_id_list}},
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
        insurance_id = todo['insurance']['value']
        insurance = my_col('insurance').find_one(
        {"_id":insurance_id},
        {"_id":0,"name":1}
        )

        entry = {
            "_id":todo["_id"],
            "name":todo["name"],
            "designation":todo["designation"],
            "phoneNumber":todo["phoneNumber"],
            "insurance":insurance["name"]
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


@app.route('/api/delete-caremanager', methods=['POST'])
def delete_caremanager():
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
            insurance =  my_col('caremanager').update_one(myquery, newvalues)
            insurance_id = id if insurance.modified_count else None
            error = 0 if insurance.modified_count else 1
            deleted_done = 1 if insurance.modified_count else 0
            message = 'Caremanager Data Deleted Successfully'if insurance.modified_count else 'Caremanager Data Deletion Failed'

        except Exception as ex:
            insurance_id = None
            print('Caremanager Save Exception: ',ex)
            message = 'Caremanager Data Deletion Failed'
            error  = 1
            deleted_done = 0
        
        return jsonify({
            "insurance_id":insurance_id,
            "message":message,
            "error":error,
            "deleted_done":deleted_done
        })