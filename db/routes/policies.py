from flask import Blueprint, request, jsonify
from models import db, Policy
import json

policy_routes = Blueprint('policy_routes', __name__)

@policy_routes.route('', methods=['GET'])
def get_policies():
    policies = Policy.query.all()
    return jsonify([{"id": p.id, "name": p.name} for p in policies])

@policy_routes.route('/<int:policy_id>', methods=['GET'])
def get_policy(policy_id):
    policy = Policy.query.get(policy_id)
    if not policy:
        return jsonify({"error": "Policy not found"}), 404
    return jsonify({"id": policy.id, "name": policy.name, "content": policy.content})

@policy_routes.route('', methods=['POST'])
def create_policy():
    data = request.json

    # Serializza il contenuto in una stringa JSON
    serialized_content = json.dumps(data['content'])

    policy = Policy(name=data['name'], content=serialized_content)
    db.session.add(policy)
    db.session.commit()
    return jsonify({"message": "Policy created", "id": policy.id})
