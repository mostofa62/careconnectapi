from flask import Flask,request,jsonify, json,send_from_directory
from app import app
from db import my_col
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
from util import *


@app.route("/api/agency-rate/<string:id>", methods=['GET'])
def view_agencyrate(id:str):
    agencyrate = my_col('agencyrate').find_one(
        {"_id":ObjectId(id)},
        {"_id":0}
        )
    agency = my_col('agency').find_one(
        {"_id":agencyrate['agency']['value']},
        {"_id":0,"name":1}
        )

    insurance = my_col('insurance').find_one(
        {"_id":agencyrate['insurance']['value']},
        {"_id":0,"name":1}
        )
    
    agencyrate['agency']['value'] = str(agencyrate['agency']['value'])
    agencyrate['agency']['label'] = agency['name']

    agencyrate['insurance']['value'] = str(agencyrate['insurance']['value'])
    agencyrate['insurance']['label'] = insurance['name']

    return jsonify({
        "agencyrate":agencyrate
    })

@app.route('/api/save-agency-rate', methods=['POST'])
async def save_agencyrate():
    if request.method == 'POST':
        data = json.loads(request.data)

        agencyrate_id = None
        message = None
        error = 0
        try:

            agencyrate_data = my_col('agencyrate').insert_one({           
                'rate':int(data['rate']),
                'agency':{
                    'value':ObjectId(data['agency']['value'])
                },
                'insurance':{
                    'value':ObjectId(data['insurance']['value']),
                    #'label':data['insurance']['label']
                },
                'county':data['county'],                                                   
                "created_at":datetime.now(),
                "updated_at":datetime.now(),
                "deleted_at":None
            })
            agencyrate_id = str(agencyrate_data.inserted_id)
            message = 'Agency Rate Data Saved Successfully'
            error = 0
        except Exception as ex:
            agencyrate_id = None
            print('Agency Rate Save Exception: ',ex)
            message = 'Agency Rate Data Saving Failed'
            error  = 1

        return jsonify({
            "agencyrate_id":agencyrate_id,
            "message":message,
            "error":error
        })
    


@app.route('/api/save-agency-rate/<string:id>', methods=['POST'])
async def update_agencyrate(id:str):
    if request.method == 'POST':
        data = json.loads(request.data)

        agencyrate_id = None
        message = None
        error = 0

        try:
            myquery = { "_id" :ObjectId(id)}

            newvalues = { "$set": {           
                'rate':data['rate'],
                'agency':{
                    'value':ObjectId(data['agency']['value'])
                },
                'insurance':{
                    'value':ObjectId(data['insurance']['value']),
                    #'label':data['insurance']['label']
                },
                'county':data['county'],                                                    
                "updated_at":datetime.now()
            } }
            agencyrate_data =  my_col('agencyrate').update_one(myquery, newvalues)
            agencyrate_id = id if agencyrate_data.modified_count else None
            error = 0 if agencyrate_data.modified_count else 1
            message = 'Agency Rate Data Update Successfully'if agencyrate_data.modified_count else 'Agency Rate Data Update Failed'

        except Exception as ex:
            agencyrate_id = None
            print('Agency Rate Save Exception: ',ex)
            message = 'Agency Rate Data Update Failed'
            error  = 1
        
        return jsonify({
            "agencyrate_id":agencyrate_id,
            "message":message,
            "error":error
        })



collection = my_col('agencyrate')
@app.route('/api/agencyrates', methods=['POST'])
def list_agencyrates(angtid=None):
    try:
        data = request.get_json()
        page_index = data.get('pageIndex', 0)
        page_size = data.get('pageSize', 10)
        global_filter = data.get('filter', '')
        sort_by = data.get('sortBy', [])
        group_by_field = 'agency.value'
        #group_by_field = f"${data.get('groupByField', '')}"
        #group_by_field = f"${data.get('agency.value', '')}"
        #group_by_field = data.get('groupByField', 'agency.value')  # Field name only, no '$'

        # Construct MongoDB filter query
        query = {
            #'role':{'$gte':10}
            "deleted_at":None
        }

        
            

        if global_filter:
            
            agency_id_list=[]
            agency = my_col('agency').find(
                {'name':{"$regex":global_filter,"$options":"i"}},
                {'_id':1}
            )
            agency_list = list(agency)
            if len(agency_list) > 0:
                agency_id_list = [d.pop('_id') for d in agency_list]

            insurance_id_list=[]
            insurance = my_col('insurance').find(
                {'name':{"$regex":global_filter,"$options":"i"}},
                {'_id':1}
            )
            insurance_list = list(insurance)
            if len(insurance_list)> 0:
                insurance_id_list = [d.pop('_id') for d in insurance_list]


            query["$or"] = [
                {"rate": {"$regex": global_filter, "$options": "i"}},            
                {"agency.value": {"$in":agency_id_list}},
                {"insurance.value": {"$in":insurance_id_list}}
                # Add other fields here if needed
            ]

        

        # Generate sort condition
        sort_params = {}
        for sort in sort_by:
            sort_field = sort['id']
            sort_direction = -1 if sort['desc'] else 1
            sort_params[sort_field] = sort_direction

        # Calculate the number of documents to skip
        skip_count = page_index * page_size

        # Aggregation pipeline
        '''
        pipeline = [
            # 1. Global filter stage
            {"$match": query},
            
            # 2. Group stage
            {
                "$group": {
                    "_id": f"${group_by_field}",
                    "count": {"$sum": 1},  # Count the number of documents in each group
                    "data": {"$push": "$$ROOT"}  # Collect all documents in the group
                }
            },
            
            # 3. Sort stage
            #{"$sort": sort_params},
            
            # 4. Pagination stages
            #{"$skip": skip_count},  # Skip to the correct page
            #{"$limit": page_size}   # Limit the number of documents returned
        ]
        '''

        # Construct aggregation pipeline with a facet for counting and data retrieval
        pipeline = [
            {"$match": query},
            {"$facet": {
                "totalCount": [
                    {"$group": {
                        "_id": f"${group_by_field}",
                        "count": {"$sum": 1}
                    }},
                    {"$count": "count"}
                ],
                "data": [
                    {"$group": {
                        "_id": f"${group_by_field}",
                        "count": {"$sum": 1},
                        "data": {"$push": "$$ROOT"}
                    }},
                    {"$unwind": "$data"},
                    {"$sort": {"data.updated_at": -1}},  # Sort by 'updated_at' within the group
                    {"$group": {
                        "_id": "$_id",
                        "count": {"$first": "$count"},  # Preserve the count
                        "data": {"$push": "$data"}
                    }},
                    # Add sorting stage if sort_params is not empty
                    #*([{"$sort": sort_params}] if sort_params else {}),
                    {"$sort": sort_params if sort_params else {"_id": -1}},
                    {"$skip": skip_count},
                    {"$limit": page_size}
                ]
            }}
        ]

       # Add sorting stage if sort_params is not empty
        '''
        if sort_params:
            pipeline.append({"$sort": sort_params})
        '''

        # Add pagination stages
        '''
        pipeline.extend([
            {"$skip": skip_count},
            {"$limit": page_size}
        ])
        '''

        # Print the pipeline for debugging
        #print("Aggregation Pipeline:", pipeline)

        # Execute the aggregation query
        #result = list(collection.aggregate(pipeline))

        #print(result)

        result = list(collection.aggregate(pipeline))
        #total_count = collection.count_documents(query)
        # Extract the count and data from the result
        total_count = result[0]['totalCount'][0]['count'] if result[0]['totalCount'] else 0
        data = result[0]['data']
        

        data_list = []

        for todo in data:
            agency_id = todo['_id']
            agency = my_col('agency').find_one(
            {"_id":ObjectId(agency_id)},
            {"_id":0,"name":1}
            )

            agency_data = []

            for data in todo['data']:

                insurance_id = data['insurance']['value']
                insurance = my_col('insurance').find_one(
                {"_id":insurance_id},
                {"_id":0,"name":1}
                )

                entry = {
                    "_id":data["_id"],
                    "rate":data["rate"],            
                    "county":data["county"]["value"],
                    "insurance":insurance["name"]
                }
                agency_data.append(entry)
            data_list.append({'agency_id':todo['_id'],'agency_name':agency['name'],'count':todo['count'],'data':agency_data})

        #total_count = len(data_list)

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
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/delete-agencyrate', methods=['POST'])
def delete_agencyrate():
    if request.method == 'POST':
        data = json.loads(request.data)

        id = data['id']

        agencyrate_id = None
        message = None
        error = 0
        deleted_done = 0

        try:
            myquery = { "_id" :ObjectId(id)}

            newvalues = { "$set": {                                     
                "deleted_at":datetime.now()                
            } }
            agencyrate =  my_col('agencyrate').update_one(myquery, newvalues)
            agencyrate_id = id if agencyrate.modified_count else None
            error = 0 if agencyrate.modified_count else 1
            deleted_done = 1 if agencyrate.modified_count else 0
            message = 'Agency Rate Data Deleted Successfully'if agencyrate.modified_count else 'Agency Rate Data Deletion Failed'

        except Exception as ex:
            agencyrate_id = None
            print('Agency Rate Save Exception: ',ex)
            message = 'Employee Data Deletion Failed'
            error  = 1
            deleted_done = 0
        
        return jsonify({
            "agencyrate_id":agencyrate_id,
            "message":message,
            "error":error,
            "deleted_done":deleted_done
        })