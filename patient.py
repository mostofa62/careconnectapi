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
        pattern_zip = r'^\d+$'
        zipCode = None
        #try:
        if re.match(pattern_str, global_filter):
            dob = datetime.strptime(global_filter,"%Y-%m-%d")
        #except ValueError:
        else:
            dob = None


        if re.match(pattern_zip, global_filter):
            zipCode = int(global_filter)
        #except ValueError:
        else:
            zipCode = None
        

        query["$or"] = [

            # {
            # "first_name": {
            #     "$regex": f"^{global_filter}$",
            #     "$options": "i"
            # },
            # "first_name": {"$ne": None, "$ne": ""}
            # },
            # {
            #     "middle_name": {
            #         "$regex": f"^{global_filter}$",
            #         "$options": "i"
            #     },
            #     "middle_name": {"$ne": None, "$ne": ""}
            # },
            # {
            #     "last_name": {
            #         "$regex": f"^{global_filter}$",
            #         "$options": "i"
            #     },
            #     "last_name": {"$ne": None, "$ne": ""}
            # },
           
            # {
            #     "address": {
            #         "$regex": f"^{global_filter}$",
            #         "$options": "i"
            #     },
            #     "address": {"$ne": None, "$ne": ""}
            # },
            
            # Add other fields with similar structure

            {"dob": dob},  # Exact match for date of birth
            {"first_name": {"$regex": global_filter, "$options": "i"}},
            {"middle_name": {"$regex": global_filter, "$options": "i"}},
            {"last_name": {"$regex": global_filter, "$options": "i"}},             
            {"address": {"$regex": global_filter, "$options": "i"}},
            #{"phoneNumber": {"$regex": global_filter, "$options": "i"}},
            {"zipCode": zipCode},
            {"medicaid_id": {"$regex": global_filter, "$options": "i"}},
            {"ssn": {"$regex": global_filter, "$options": "i"}},
            {"consumer_status.label": {"$regex": global_filter, "$options": "i"}},
            {"city.label": {"$regex": global_filter, "$options": "i"}},
            {"county.label": {"$regex": global_filter, "$options": "i"}},
            {"phone": {"$regex": global_filter, "$options": "i"}},
            {"cell_phone": {"$regex": global_filter, "$options": "i"}},
            {"email": {"$regex": global_filter, "$options": "i"}},                            
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
        todo['dob'] = convertDateTostring(todo['dob'])
        todo['service_start_date'] = convertDateTostring(todo['service_start_date'])
        todo['service_end_date'] = convertDateTostring(todo['service_end_date'])
        todo['projected_encrollment_date'] = convertDateTostring(todo['projected_encrollment_date'])
        todo['confirmed_encrollment_date'] = convertDateTostring(todo['confirmed_encrollment_date'])
        todo['cha_appointment_date'] = convertDateTostring(todo['cha_appointment_date'])
        todo['ipp_appointment_date'] = convertDateTostring(todo['ipp_appointment_date'])
        todo['insrn_assessment_date'] = convertDateTostring(todo['insrn_assessment_date'])
        todo['addn_assessment_date'] = convertDateTostring(todo['addn_assessment_date'])    


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

'''
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
'''

def generate_patient_id():

    # Find the maximum patient_id
    max_patient = patient.find_one(
        {},  # No filter
        sort=[('patient_id', -1)]  # Sort in descending order to get the max
    )
    
    if max_patient:
        max_id = max_patient['patient_id']
        # Increment the sequence number by converting the current max_id to integer
        sequence_number = max_id  # Convert max_id to integer
    else:
        # If no IDs exist, start with 0
        sequence_number = 0
    
    # Increment the sequence number
    sequence_number += 1
    
    # Convert the sequence number to string
    #unique_id = str(sequence_number)
    unique_id = sequence_number
    
    return unique_id
    
@app.route("/api/patient/<string:id>", methods=['GET'])
def view_patient(id:str):
    patient = my_col('patient').find_one(
        {"_id":ObjectId(id)},
        {"_id":0}
        )
    
    patient['projected_encrollment_date'] = convertDateTostring(patient['projected_encrollment_date'],"%Y-%m-%d")
    patient['confirmed_encrollment_date'] = convertDateTostring(patient['confirmed_encrollment_date'],"%Y-%m-%d")
    patient['dob'] = convertDateTostring(patient['dob'],"%Y-%m-%d")
    patient['cha_appointment_date'] = convertDateTostring(patient['cha_appointment_date'],"%Y-%m-%d")
    patient['ipp_appointment_date'] = convertDateTostring(patient['ipp_appointment_date'],"%Y-%m-%d")
    patient['insrn_assessment_date'] = convertDateTostring(patient['insrn_assessment_date'],"%Y-%m-%d")
    patient['addn_assessment_date'] = convertDateTostring(patient['addn_assessment_date'],"%Y-%m-%d")
    patient['service_start_date'] = convertDateTostring(patient['service_start_date'],"%Y-%m-%d")
    patient['service_end_date'] = convertDateTostring(patient['service_end_date'],"%Y-%m-%d")
    
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


@app.route('/api/save-patient/<string:id>', methods=['POST'])
async def update_patient(id:str):
    if request.method == 'POST':
        data = json.loads(request.data)

        patient_id = None
        message = None
        error = 0
        try:

            #patient_unique_id = generate_patient_id()
            del data['patient_id']

            myquery = { "_id" :ObjectId(id)}

            dob = convertStringTodate(data['dob'])
            service_start_date = convertStringTodate(data['service_start_date'])
            service_end_date = convertStringTodate(data['service_end_date'])
            projected_encrollment_date = convertStringTodate(data['projected_encrollment_date'])
            confirmed_encrollment_date = convertStringTodate(data['confirmed_encrollment_date'])
            cha_appointment_date = convertStringTodate(data['cha_appointment_date'])
            ipp_appointment_date = convertStringTodate(data['ipp_appointment_date'])
            insrn_assessment_date = convertStringTodate(data['insrn_assessment_date'])
            addn_assessment_date = convertStringTodate(data['addn_assessment_date'])

            append_data = {
                #'patient_id':patient_unique_id,
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

                'projected_encrollment_date':projected_encrollment_date,
                'confirmed_encrollment_date':confirmed_encrollment_date,
                'dob':dob,
                'cha_appointment_date':cha_appointment_date,
                'ipp_appointment_date':ipp_appointment_date,
                'insrn_assessment_date':insrn_assessment_date,
                'addn_assessment_date':addn_assessment_date,
                'service_start_date':service_start_date,
                'service_end_date':service_end_date,
                

                
            }
            print('data',data)
            print('appendata',append_data)
            

            merge_data = data | append_data

            print('mergedata',merge_data)
            newvalues = { "$set": merge_data }

            patient = my_col('patient').update_one(myquery, newvalues)
            patient_id = id if patient.modified_count else None
            error = 0 if patient.modified_count else 1            
            message = 'Patient Data Update Successfully'if patient.modified_count else 'Patient Data Update Failed'
        except Exception as ex:
            patient_id = None
            print('data',data)
            print('Patient Updated Exception: ',ex)
            message = 'Patient Data Updated Failed'
            error  = 1

        return jsonify({
            "patient_id":patient_id,
            "message":message,
            "error":error
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

            dob = convertStringTodate(data['dob'])
            service_start_date = convertStringTodate(data['service_start_date'])
            service_end_date = convertStringTodate(data['service_end_date'])
            projected_encrollment_date = convertStringTodate(data['projected_encrollment_date'])
            confirmed_encrollment_date = convertStringTodate(data['confirmed_encrollment_date'])
            cha_appointment_date = convertStringTodate(data['cha_appointment_date'])
            ipp_appointment_date = convertStringTodate(data['ipp_appointment_date'])
            insrn_assessment_date = convertStringTodate(data['insrn_assessment_date'])
            addn_assessment_date = convertStringTodate(data['addn_assessment_date'])

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

                'projected_encrollment_date':projected_encrollment_date,
                'confirmed_encrollment_date':confirmed_encrollment_date,
                'dob':dob,
                'cha_appointment_date':cha_appointment_date,
                'ipp_appointment_date':ipp_appointment_date,
                'insrn_assessment_date':insrn_assessment_date,
                'addn_assessment_date':addn_assessment_date,
                'service_start_date':service_start_date,
                'service_end_date':service_end_date,
                

                
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