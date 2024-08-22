from flask import Flask, request, jsonify
import gridfs
import os
from db import mydb

from app import app
UPLOAD_FOLDER = os.path.join('tmp','uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
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
        # Combine chunks and save to GridFS
        combined_file_name = os.path.join(UPLOAD_FOLDER, file_name)
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

        os.remove(combined_file_name)  # Remove the combined file after saving

        return jsonify({"fileId": str(file_id)}), 201

    return jsonify({"message": "Chunk uploaded"}), 200