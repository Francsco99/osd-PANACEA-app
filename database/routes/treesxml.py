from flask import Blueprint, request, jsonify
from models import db, TreeXML

treesxml_routes = Blueprint('treesxml_routes', __name__)

@treesxml_routes.route('', methods=['GET'])
def get_treesxml():
    """Restituisce tutti gli alberi in formato XML"""
    treesxml = TreeXML.query.all()
    return jsonify([{"id": t.id, "name": t.name} for t in treesxml])

@treesxml_routes.route('/<int:treexml_id>', methods=['GET'])
def get_treexml(treexml_id):
    """Restituisce un singolo albero XML in base all'ID"""
    treexml = TreeXML.query.get(treexml_id)
    if not treexml:
        return jsonify({"error": "Tree XML not found"}), 404
    return jsonify({"id": treexml.id, "name": treexml.name, "content": treexml.content})

@treesxml_routes.route('', methods=['POST'])
def create_treexml():
    """Crea un nuovo albero in formato XML"""
    data = request.json
    if 'name' not in data or 'content' not in data:
        return jsonify({"error": "Missing required fields: 'name' and 'content'"}), 400

    treexml = TreeXML(name=data['name'], content=data['content'])
    db.session.add(treexml)
    db.session.commit()
    
    return jsonify({"message": "Tree XML created", "id": treexml.id})
