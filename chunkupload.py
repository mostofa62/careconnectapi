from flask import Flask, request, jsonify, send_from_directory
#import gridfs
import os
from db import mydb
from bson import ObjectId
from datetime import datetime
from app import app

# Define upload and save folders
UPLOAD_FOLDER = os.path.join('tmp', 'uploads')
SAVE_FOLDER = os.path.join('uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAVE_FOLDER, exist_ok=True)


'''
#not using gridfs

fs = gridfs.GridFS(mydb)

@app.route('/api/upload-chunk', methods=['POST'])
def upload_chunk():
    chunk = request.files['chunk']
    file_name = request.form['fileName']
    chunk_number = int(request.form['chunkNumber'])
    total_chunks = int(request.form['totalChunks'])

    # Save chunk to temporary location
    chunk_file_name = f'{file_name}.part{chunk_number}'
    chunk.save(os.path.join(UPLOAD_FOLDER, chunk_file_name))

    # Check if all chunks are uploaded
    if chunk_number == total_chunks:
        # Combine chunks and save to a directory on disk
        combined_file_name = os.path.join(SAVE_FOLDER, file_name)
        with open(combined_file_name, 'wb') as combined_file:
            for i in range(1, total_chunks + 1):
                chunk_file_name = f'{file_name}.part{i}'
                chunk_path = os.path.join(UPLOAD_FOLDER, chunk_file_name)
                with open(chunk_path, 'rb') as chunk_file:
                    combined_file.write(chunk_file.read())
                os.remove(chunk_path)  # Remove chunk after combining

        # Save the combined file to GridFS
        with open(combined_file_name, 'rb') as combined_file:
            file_id = fs.put(combined_file, filename=file_name)

        # Optionally, you can remove the combined file from disk after saving it to GridFS
        # os.remove(combined_file_name)

        return jsonify({"fileId": str(file_id)}), 201

    return jsonify({"message": "Chunk uploaded"}), 200
'''
files_collection = mydb['files']

@app.route('/api/upload-chunk/<string:path>', methods=['POST'])
def upload_chunk(path):
    chunk = request.files['chunk']
    file_name = request.form['fileName']
    chunk_number = int(request.form['chunkNumber'])
    total_chunks = int(request.form['totalChunks'])


    # Create the directory dynamically if it doesn't exist
    upload_dir = os.path.join(SAVE_FOLDER, path)
    os.makedirs(upload_dir, exist_ok=True)

    # Save chunk to temporary location
    chunk_file_name = f'{file_name}.part{chunk_number}'
    chunk.save(os.path.join(UPLOAD_FOLDER, chunk_file_name))

    # Check if all chunks are uploaded
    if chunk_number == total_chunks:
        # Combine chunks and save to a directory on disk
        combined_file_name = os.path.join(upload_dir, file_name)
        with open(combined_file_name, 'wb') as combined_file:
            for i in range(1, total_chunks + 1):
                chunk_file_name = f'{file_name}.part{i}'
                chunk_path = os.path.join(UPLOAD_FOLDER, chunk_file_name)
                with open(chunk_path, 'rb') as chunk_file:
                    combined_file.write(chunk_file.read())
                os.remove(chunk_path)  # Remove chunk after combining

        # Save a record in the MongoDB 'files' collection
        file_record = {
            "_id": str(ObjectId()),
            "file_name": file_name,
            "file_path": combined_file_name,
            "file_size": os.path.getsize(combined_file_name),            
            'directory':path,
            "created_at":datetime.now(),
            "updated_at":datetime.now(),
        }
        files_collection.insert_one(file_record)

        return jsonify({"fileId": file_record["_id"]}), 201

    return jsonify({"message": "Chunk uploaded"}), 200




@app.route('/api/download/<string:file_id>', methods=['GET'])
def download_file(file_id):
    # Retrieve the file record from MongoDB
    file_record = mydb.files.find_one({"_id": file_id})
    
    if not file_record:
        return jsonify({"error": "File not found"}), 404

    file_name = file_record.get('file_name')
    upload_dir = file_record.get('directory')

    

    if not file_name or not upload_dir:
        return jsonify({"error": "File record is incomplete"}), 500
    
    upload_dir = os.path.join(SAVE_FOLDER, upload_dir)
    file_path = os.path.join(upload_dir, file_name)

    print(file_path)

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found on the server"}), 404

    # Determine if the file should be sent as an attachment or inline
    file_extension = os.path.splitext(file_name)[1].lower()
    #print(file_extension)
    inline_extensions = ['.pdf', '.html', '.txt']  # Add more extensions as needed
    as_attachment = file_extension in inline_extensions

    # Serve the file to the client
    return send_from_directory(directory=upload_dir, path=file_name, as_attachment=as_attachment)