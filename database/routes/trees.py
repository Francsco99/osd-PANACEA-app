from flask import Blueprint, request, jsonify
from models import db, TreeJSON
import json

tree_routes = Blueprint('tree_routes', __name__)

@tree_routes.route('', methods=['GET'])
def get_trees():
    trees = TreeJSON.query.all()
    return jsonify([{"id": t.id, "name": t.name} for t in trees])

@tree_routes.route('/<int:tree_id>', methods=['GET'])
def get_tree(tree_id):
    tree = TreeJSON.query.get(tree_id)
    if not tree:
        return jsonify({"error": "TreeJSON not found"}), 404
    return jsonify({"id": tree.id, "name": tree.name, "content": tree.content})

@tree_routes.route('', methods=['POST'])
def create_tree():
    data = request.json
    
    # Serializza il contenuto in una stringa JSON
    serialized_content = json.dumps(data['content'])

    tree = TreeJSON(name=data['name'], content=serialized_content)
    db.session.add(tree)
    db.session.commit()
    
    return jsonify({"message": "TreeJSON created", "id": tree.id})