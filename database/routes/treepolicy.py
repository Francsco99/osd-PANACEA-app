from flask import Blueprint, request, jsonify
from models import db, TreePolicy, TreeJSON, TreeXML, Policy

treepolicy_routes = Blueprint('treepolicy_routes', __name__)

@treepolicy_routes.route('', methods=['GET'])
def get_tree_policies():
    tree_policies = TreePolicy.query.all()
    return jsonify([{
        "id": tp.id,
        "tree_id": tp.tree_id,
        "treexml_id": tp.treexml_id,
        "policy_id": tp.policy_id
    } for tp in tree_policies])

@treepolicy_routes.route('/<int:treepolicy_id>', methods=['GET'])
def get_tree_policy(treepolicy_id):
    tree_policy = TreePolicy.query.get(treepolicy_id)
    if not tree_policy:
        return jsonify({"error": "TreePolicy not found"}), 404
    return jsonify({
        "id": tree_policy.id,
        "tree_id": tree_policy.tree_id,
        "treexml_id": tree_policy.treexml_id,
        "policy_id": tree_policy.policy_id
    })

@treepolicy_routes.route('', methods=['POST'])
def create_tree_policy():
    data = request.json

    tree = TreeJSON.query.get(data['tree_id'])
    treexml = TreeXML.query.get(data['treexml_id'])
    policy = Policy.query.get(data['policy_id'])

    if not tree or not treexml or not policy:
        return jsonify({"error": "Invalid tree_id, treexml_id, or policy_id"}), 400

    tree_policy = TreePolicy(tree_id=data['tree_id'], treexml_id=data['treexml_id'], policy_id=data['policy_id'])
    db.session.add(tree_policy)
    db.session.commit()
    
    return jsonify({"message": "TreePolicy created", "id": tree_policy.id})
