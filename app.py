import os
import sys
import logging
import requests
from flask import Flask, request, jsonify
from validator import process_document
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- TEMP FILE DIRECTORY ---
UPLOAD_FOLDER = '/tmp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Logging setup ---
logging.basicConfig(level=logging.INFO, force=True)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.INFO)


@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Validator API is live"}), 200


# 🔽 DOWNLOAD FILE FROM GOOGLE DRIVE
def download_file_from_drive(file_id):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(url)

    temp_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.pdf")

    with open(temp_path, "wb") as f:
        f.write(response.content)

    return temp_path


@app.route('/validate-multiple', methods=['POST'])
def validate_multiple_endpoint():
    app.logger.info("=== /validate-multiple hit ===")

    data = request.form.to_dict()
    app.logger.info("Received data: %s", data)
    sys.stdout.flush()

    results = []

    # Loop through multiple files (file_id_1, file_id_2, file_id_3)
    for i in range(1, 4):
        file_id = data.get(f"file_id_{i}")
        doc_type = data.get(f"doc_type_{i}")

        if not file_id:
            continue

        try:
            # --- Download file ---
            file_path = download_file_from_drive(file_id)
            app.logger.info(f"Downloaded file: {file_path}")

            # --- Process document ---
            result = process_document(file_path, {
                "doc_type": doc_type,
                "name": data.get("name"),
                "id_number": data.get("id_number")
            })

            results.append(result)

        except Exception as e:
            app.logger.exception("Error processing file")
            results.append({
                "doc_type": doc_type,
                "status": f"Error: {str(e)}",
                "validation_passed": False
            })

        finally:
            # --- Clean up file ---
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    app.logger.info(f"Deleted temp file: {file_path}")
            except Exception:
                app.logger.exception("Failed to delete temp file")

    return jsonify(results)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)