import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging

from modules.json2xml_pruner import prune_tree
from modules.xml2json_parser import parse_tree
from modules.panacea_script import panacea
from modules.txt2json_parser import extract_policy

from db.models import db, TreesXML, Tree, Policy, TreePolicy

app = Flask(__name__)
CORS(app)


# Usa la variabile d'ambiente DATABASE_URL per connettersi al database
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@database:5432/flaskdb')

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configure the logging system
logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Directory configuration
BASE_DIR = "server"
DATA_DIR = os.path.join(BASE_DIR,"data")
JSON_FOLDER = os.path.join(DATA_DIR, "json")
XML_FOLDER = os.path.join(DATA_DIR, "xml")
PRISM_OUTPUT_DIR = os.path.join(DATA_DIR, "prism")

JSON_RECEIVED_FILES_DIR = os.path.join(JSON_FOLDER, "received_trees")
XML_RECEIVED_FILES_DIR = os.path.join(XML_FOLDER, "received_trees")

PRUNED_FILES_DIR = os.path.join(XML_FOLDER, "pruned_trees")

PARSED_FILES_DIR = os.path.join(JSON_FOLDER, "parsed_trees")

POLICIES_DIR = os.path.join(JSON_FOLDER, "parsed_policies")

XML_BASE_TREE = None

# Create directories if they do not exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(JSON_FOLDER, exist_ok=True)
os.makedirs(XML_FOLDER, exist_ok=True)

os.makedirs(JSON_RECEIVED_FILES_DIR, exist_ok=True)
os.makedirs(XML_RECEIVED_FILES_DIR, exist_ok=True)

os.makedirs(PRUNED_FILES_DIR, exist_ok=True)

os.makedirs(PARSED_FILES_DIR, exist_ok=True)

os.makedirs(POLICIES_DIR, exist_ok=True)

os.makedirs(PRISM_OUTPUT_DIR, exist_ok=True)

def find_matching_xml(original_name):
    """
    Trova il file XML corrispondente nella cartella XML_RECEIVED_FILES_DIR 
    basandosi sul nome originale fornito, che termina sicuramente con .xml.
    
    Args:
        original_name (str): Nome del file con estensione .xml (es. "documento.xml").
    
    Returns:
        str: Percorso completo del file XML corrispondente, se trovato.
        None: Se nessuna corrispondenza viene trovata.
    """
    base_name = os.path.splitext(original_name)[0]  # Rimuove l'estensione .xml

    # Cerca un file XML che inizia con lo stesso nome di base
    for file in os.listdir(XML_RECEIVED_FILES_DIR):
        if file.startswith(base_name) and file.endswith('.xml'):
            return os.path.join(XML_RECEIVED_FILES_DIR, file)  # Ritorna il percorso completo del file XML trovato

    return None  # Nessuna corrispondenza trovata

@app.route('/receive_json', methods=['POST'])
def receive_json():
    """
    Endpoint per ricevere JSON, trovare l'XML corrispondente e processare il file.
    """
    try:
        # Riceve il JSON dal client
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data received"}), 400

        # Estrae il nome originale fornito dal JSON
        original_name = data.get("original_name")
        if not original_name:
            return jsonify({"error": "Original name not provided"}), 400

        # Genera un timestamp
        timestamp = datetime.now().strftime("%y%m%d_%H%M")

        # Costruisce il nome del file JSON con timestamp
        filename = f"{os.path.splitext(original_name)[0]}_{timestamp}.json"
        received_file_path = os.path.join(JSON_RECEIVED_FILES_DIR, filename)

        # Salva il JSON nel filesystem
        try:
            with open(received_file_path, "w") as f:
                json.dump(data, f, indent=4)
            logging.info(f"JSON file received and saved at: {received_file_path}")
        except Exception as e:
            logging.error(f"Failed to save JSON file {filename}: {e}")
            raise
        
        # Recupera il nome dell'albero originale dal json
        xml_base_tree_name = data.get("xml_file_name")

        # Trova il file XML corrispondente
        xml_base_tree_path = find_matching_xml(original_name)

        if not xml_base_tree_path:
            return jsonify({"error": "No matching XML file found"}), 400

        logging.info(f"Matching XML file selected: {xml_base_tree_path}")

        # Esegui prune_tree con il file XML trovato
        pruned_xml_path = prune_tree(
            json_input_file=received_file_path,
            xml_input_file=xml_base_tree_path,
            output_folder=PRUNED_FILES_DIR
        )

        # Esegui PANACEA
        panacea_output = panacea(pruned_xml_path, PRISM_OUTPUT_DIR)
        
        # Ottieni il percorso del file TXT generato da PRISM
        txt_file_path = panacea_output["txt_path"]

        # Invoke the parsing script to convert the TXT to JSON containing the policy
        policy_path = extract_policy(
            json_input_path=txt_file_path, 
            output_dir=POLICIES_DIR,
            timestamp=timestamp)

        # Leggi il contenuto della policy
        with open(policy_path, "r") as f:
            policy_content = json.load(f)

        # Restituisci il JSON ricevuto e la policy generata
        response = jsonify({
            "message": "File processed successfully",
            "file_name": filename,
            "tree_data": data,
            "policy_content": policy_content  # Policy content
        })
        response.headers['Content-Type'] = 'application/json'
        return response, 200
    except Exception as e:
        # Log degli errori
        logging.error(f"Error: {e}")
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

        # Generate timestamp
        timestamp = datetime.now().strftime("%y%m%d_%H%M")
        
        # Save the received XML file
        xml_received_path = os.path.join(XML_RECEIVED_FILES_DIR, file.filename)

        file.save(xml_received_path)

        logging.info(f"XML file received and saved at: {xml_received_path}")

        # Invoke parse_tree to convert the XML file to JSON
        parsed_json_path = parse_tree(
            xml_input_path=xml_received_path,
            output_dir=PARSED_FILES_DIR,
            timestamp=timestamp
        )

        # Invoke the PANACEA script
        panacea_output = panacea(xml_received_path, PRISM_OUTPUT_DIR, timestamp)

        # Path to the TXT file generated by PRISM
        txt_file_path = panacea_output["txt_path"]
        
        # Invoke the parsing script to convert the TXT to JSON containing the policy
        policy_path = extract_policy(
            json_input_path=txt_file_path, 
            output_dir=POLICIES_DIR,
            timestamp=timestamp)

        # Extract only the name of the parsed JSON file
        filename_json = os.path.basename(parsed_json_path)

        # Read the content of the policy file
        with open(policy_path, "r") as f:
            policy_content = json.load(f)

        # Read the content of the parsed JSON file
        with open(parsed_json_path, "r") as json_file:
            parsed_data = json.load(json_file)

        with db.session.begin():
            xml_record = TreesXML(name=filename, content=open(xml_received_path, "r").read())
            db.session.add(xml_record)
            db.session.flush()  # Otteniamo l'ID generato    
            logging.info(f"XML saved in database with ID: {xml_record.id}")

            json_record = Tree(name=os.path.basename(parsed_json_path), content=parsed_data)
            db.session.add(json_record)
            db.session.flush()
            logging.info(f"Parsed JSON saved in database with ID: {json_record.id}")

            policy_record = Policy(name=os.path.basename(policy_path), content=policy_data)
            db.session.add(policy_record)
            db.session.flush()
            logging.info(f"Policy JSON saved in database with ID: {policy_record.id}")

            tree_policy_entry = TreePolicy(
                tree_id=json_record.id,
                treexml_id=xml_record.id,
                policy_id=policy_record.id
            )
            db.session.add(tree_policy_entry)
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
        db.session.rollback()  # Rollback in caso di errore
        logging.error(f"Error processing XML: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
