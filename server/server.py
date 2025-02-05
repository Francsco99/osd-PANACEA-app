import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging
import sys
from flask_sqlalchemy import SQLAlchemy


from modules.json2xml_pruner import prune_tree
from modules.xml2json_parser import parse_tree
from modules.panacea_script import panacea
from modules.txt2json_parser import extract_policy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from database.models import db, TreeXML, TreeJSON, Policy, TreePolicy

app = Flask(__name__)
CORS(app)


# Usa la variabile d'ambiente DATABASE_URL per connettersi al database
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@database:5432/flaskdb')

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Configure the logging system
logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@app.route('/receive_json', methods=['POST'])
def receive_json():
    """
    Endpoint per ricevere JSON, trovare l'XML corrispondente e processare il file.
    """
    try:
        # Receive JSON string from client
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data received"}), 400

        # Extract original JSON tree id
        tree_id = data.get("tree_id")
        if not tree_id:
            return jsonify({"error": "Missing tree_id"}), 400

        # Extract filename
        file_name = data.get("file_name")
        if not file_name:
            return jsonify({"error": "Missing file_name"}), 400

        logging.info(f"Processing JSON for Tree ID: {tree_id}")
        with db.session.begin():
            # Find treesxml_id in TreePolicy table
            tree_policy_entry = TreePolicy.query.filter_by(tree_id = tree_id).first()
            if not tree_policy_entry:
                return jsonify({"error": "No matching TreePolicy found"})
            
            treesxml_id = tree_policy_entry.treexml_id
            logging.info(f"Found associated TreeXML ID: {treesxml_id}")
            
            # Get XML content from TreeXML table
            tree_xml_entry = TreeXML.query.get(treesxml_id)
            xml_base_tree = tree_xml_entry.content

            logging.info("XML loaded from DB")
        db.session.commit()

        # Remove tree_id and file_name from JSON before saving
        json_tree_content = {k: v for k, v in data.items() if k not in ["tree_id", "file_name"]}

        # Prune XML tree
        pruned_xml = prune_tree(json_tree_content, xml_base_tree)

        # Execute panacea on pruned tree
        panacea_output=panacea(pruned_xml)

        # Extract txt content from PANACEA output
        txt_content = panacea_output["txt_content"]

        # Invoke parse_tree to convert the XML file to JSON
        json_policy_content = extract_policy(txt_content)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%y%m%d_%H%M")

        with db.session.begin():
            # Save JSON tree data inside db (table trees)
            json_record = TreeJSON(name=f"{file_name}_{timestamp}.json",content=json_tree_content)
            db.session.add(json_record)
            db.session.flush()
            logging.info(f"New JSON tree saved with ID: {json_record.id}")

            # Save JSON policy data inside db (table policies)
            policy_record = Policy(name=f"{file_name}_policy_{timestamp}.json", content=json_policy_content)
            db.session.add(policy_record)
            db.session.flush()
            logging.info(f"New Policy saved with ID: {policy_record.id}")

            # Update TreePoliocy with new JSON and Policy
            new_tree_policy_entry = TreePolicy(
                tree_id=json_record.id,
                treexml_id=treesxml_id,
                policy_id=policy_record.id
            )
            db.session.add(new_tree_policy_entry)
            db.session.flush()
            logging.info(f"Updated TreePolicy with new JSON and Policy.")

        db.session.commit()

        response_data = {
            "message": "File processed successfully",
            "tree_json_id": json_record.id,
            "policy_json_id": policy_record.id
        }

        return jsonify(response_data), 200

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error processing JSON: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/receive_xml', methods=['POST'])
def receive_xml():
    """
    Endpoint to handle XML files sent by the client.

    Processes the received XML, converts it to JSON, and returns the parsed data.

    Returns:
        A JSON response containing the parsed data from the XML file.
    """
    try:
        # Check if the file is included in the request
        if 'file' not in request.files:
            return jsonify({"message": "No file part in the request"}), 400

        file = request.files['file']

        # Check if a file was selected
        if file.filename == '':
            return jsonify({"message": "No file selected"}), 400

        # Check the file extension
        if not file.filename.endswith('.xml'):
            return jsonify({"message": "Only XML files are allowed"}), 400

        # Read XML tree file content
        xml_tree_content = file.read().decode("utf-8")
        logging.info("XML file received and processed in memory")

        # Invoke parse_tree to convert the XML file to JSON
        json_tree_content = parse_tree(xml_tree_content)
        
        # Invoke the PANACEA script
        panacea_output = panacea(xml_tree_content)

        # Extract txt content from PANACEA output
        txt_content = panacea_output["txt_content"]

        # Invoke parse_tree to convert the XML file to JSON
        json_policy_content = extract_policy(txt_content)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%y%m%d_%H%M")

        # Extract filename without extensions
        base_filename = os.path.splitext(file.filename)[0]

        with db.session.begin():
            # Save XML tree data inside db (table treesxml)
            xml_filename = f"{base_filename}_{timestamp}.xml"
            xml_record = TreeXML(name=xml_filename, content=xml_tree_content)
            db.session.add(xml_record)
            db.session.flush() 
            logging.info(f"XML saved in database with ID: {xml_record.id}")
            
            # Save JSON tree data inside db (table trees)
            json_filename = f"{base_filename}_{timestamp}.json"
            json_record = TreeJSON(name=json_filename, content=json_tree_content)
            db.session.add(json_record)
            db.session.flush()
            logging.info(f"Parsed JSON saved in database with ID: {json_record.id}")

            # Save JSON policy data inside db (table policies)
            policy_filename = f"{base_filename}_policy_{timestamp}.json"
            policy_record = Policy(name=policy_filename, content=json_policy_content)
            db.session.add(policy_record)
            db.session.flush()
            logging.info(f"Policy JSON saved in database with ID: {policy_record.id}")

            # Save relationship between XML tree, JSON tree and JSON policy
            tree_policy_entry = TreePolicy(
                tree_id=json_record.id,
                treexml_id=xml_record.id,
                policy_id=policy_record.id
            )
            db.session.add(tree_policy_entry)
            db.session.flush()
            logging.info(f"TreePolicy record created with ID: {tree_policy_entry.id}")

        db.session.commit()
        # **Risposta al client con gli ID del Tree JSON e della Policy JSON**
        response_data = {
        "message": "File processed successfully",
        "tree_json_id": json_record.id,
        "policy_json_id": policy_record.id
        }

        return jsonify(response_data), 200

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error processing XML: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
