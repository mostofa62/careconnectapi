from flask import Flask,request,jsonify, json,send_from_directory
from app import app
from db import my_col
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
from util import *

@app.route('/api/save-patient', methods=['POST'])
async def save_patient():
    if request.method == 'POST':
        data = json.loads(request.data)

        patient_id = None
        message = None
        error = 0
        try:



            append_data = {
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
                "deleted_at":None
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