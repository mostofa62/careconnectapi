import re
from flask import Flask,request,jsonify, json,send_from_directory
from app import app
from db import my_col,mydb
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
from util import *
from pymongo import  ASCENDING

collection_name = 'patient'

if collection_name in mydb.list_collection_names():
    collection = mydb[collection_name]

    # Check if the index already exists
    index_name = 'patient_id_1'  # Automatically generated index name in MongoDB
    existing_indexes = collection.index_information()

    if index_name not in existing_indexes:
        # Create a unique index on a specific field if it doesn't already exist
        result = collection.create_index([('patient_id', ASCENDING)], unique=True)
        print(f"Index created: {result}")
    else:
        print("Index already exists.")
else:
    print(f"Collection '{collection_name}' does not exist.")

patient = collection


@app.route('/api/patinets', methods=['POST'])
def list_patinet():
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

        pattern_str = r'^\d{4}-\d{2}-\d{2}$'
        dob = None
        #try:
        if re.match(pattern_str, global_filter):
            dob = datetime.strptime(global_filter,"%Y-%m-%d")
        #except ValueError:
        else:
            dob = None
        query["$or"] = [
            {"patient_id": {"$regex": global_filter, "$options": "i"}},
            {"first_name": {"$regex": global_filter, "$options": "i"}},
            {"middle_name": {"$regex": global_filter, "$options": "i"}},
            {"last_name": {"$regex": global_filter, "$options": "i"}},
            {"address": {"$regex": global_filter, "$options": "i"}},
            {"phoneNumber": {"$regex": global_filter, "$options": "i"}},
            {"zipCode": {"$regex": global_filter, "$options": "i"}},
            {"service_type.label": {"$regex": global_filter, "$options": "i"}},

            {"dob":dob}                
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
    #data_list = list(cursor)
    data_list = []

    for todo in cursor:        
        #todo['dob'] = datetime.strptime(todo['dob'], "%Y-%m-%d").strftime("%-d %b, %Y") if todo['dob']!="" else ""
        data_list.append(todo)
    data_json = MongoJSONEncoder().encode(data_list)
    data_obj = json.loads(data_json)

    # Calculate total pages
    total_pages = (total_count + page_size - 1) // page_size
    

    return jsonify({
        'rows': data_obj,
        'pageCount': total_pages,
        'totalRows': total_count
    })


def generate_patient_id():
    today = datetime.today()
    start_of_today = datetime(today.year, today.month, today.day)
    end_of_today = start_of_today + timedelta(days=1)

    patient_count = patient.count_documents({
        'created_at': {
            '$gte': start_of_today,
            '$lt': end_of_today
        }
    })
    current_date = today.strftime("%Y%m%d")
    sequence_number = patient_count+1
    sequence_str = f"{sequence_number:04d}" # 1000 patient perday 9999
    unique_id = f"{current_date}{sequence_str}"
    return unique_id
    
@app.route("/api/patient/<string:id>", methods=['GET'])
def view_patient(id:str):
    patient = my_col('patient').find_one(
        {"_id":ObjectId(id)},
        {"_id":0}
        )
    
    patient['nyia_form_id'] = str(patient['nyia_form_id']) if patient['nyia_form_id']!=None else ''
    patient['doh_form_id'] = str(patient['doh_form_id']) if patient['doh_form_id']!=None else ''
    patient['m11q_form_id'] = str(patient['m11q_form_id']) if patient['m11q_form_id']!=None else ''
    patient['enrollment_doc_id'] = str(patient['enrollment_doc_id']) if patient['enrollment_doc_id']!=None else ''
    patient['mou_form_id'] = str(patient['mou_form_id']) if patient['mou_form_id']!=None else ''


    patient['letterofsupport_id'] = str(patient['letterofsupport_id']) if patient['letterofsupport_id']!=None else ''
    patient['supplymentaform_id'] = str(patient['supplymentaform_id']) if patient['supplymentaform_id']!=None else ''
    patient['bankstatement_id'] = str(patient['bankstatement_id']) if patient['bankstatement_id']!=None else ''
    patient['addn_doc_id1'] = str(patient['addn_doc_id1']) if patient['addn_doc_id1']!=None else ''
    patient['addn_doc_id2'] = str(patient['addn_doc_id2']) if patient['addn_doc_id2']!=None else ''

    return jsonify({
        "patient":patient
    })


@app.route('/api/save-patient', methods=['POST'])
async def save_patient():
    if request.method == 'POST':
        data = json.loads(request.data)

        patient_id = None
        message = None
        error = 0
        try:

            patient_unique_id = generate_patient_id()

            dob = datetime.strptime(data['dob'],"%Y-%m-%d") if data['dob']!='' else None,
            service_start_date = datetime.strptime(data['service_start_date'],"%Y-%m-%d") if data['service_start_date']!='' else None,
            service_end_date = datetime.strptime(data['service_end_date'],"%Y-%m-%d") if data['service_end_date']!='' else None,

            append_data = {
                'patient_id':patient_unique_id,
                'nyia_form_id':ObjectId(data['nyia_form_id']) if data['nyia_form_id']!='' else None,
                'doh_form_id':ObjectId(data['doh_form_id']) if data['doh_form_id']!='' else None,
                'm11q_form_id':ObjectId(data['m11q_form_id']) if data['m11q_form_id']!='' else None,
                'enrollment_doc_id':ObjectId(data['enrollment_doc_id']) if data['enrollment_doc_id']!='' else None,
                'mou_form_id':ObjectId(data['mou_form_id']) if data['mou_form_id']!='' else None,

                'letterofsupport_id':ObjectId(data['letterofsupport_id']) if data['letterofsupport_id']!='' else None,
                'supplymentaform_id':ObjectId(data['supplymentaform_id']) if data['supplymentaform_id']!='' else None,
                'bankstatement_id':ObjectId(data['bankstatement_id']) if data['bankstatement_id']!='' else None,
                'addn_doc_id1':ObjectId(data['addn_doc_id1']) if data['addn_doc_id1']!='' else None,
                'addn_doc_id2':ObjectId(data['addn_doc_id2']) if data['addn_doc_id2']!='' else None,

                "created_at":datetime.now(),
                "updated_at":datetime.now(),
                "deleted_at":None,


                'dob':dob,
                'service_start_date':service_start_date,
                'service_end_date':service_end_date

                
            }
            print('data',data)
            print('appendata',append_data)
            

            merge_data = data | append_data

            print('mergedata',merge_data)

            patient_data = my_col('patient').insert_one(merge_data)
            patient_id = str(patient_data.inserted_id)
            message = 'Patient Data Saved Successfully'
            error = 0
        except Exception as ex:
            patient_id = None
            print('Patient Save Exception: ',ex)
            message = 'Patient Data Saving Failed'
            error  = 1

        return jsonify({
            "patient_id":patient_id,
            "message":message,
            "error":error
        })