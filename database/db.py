import os
import time
from flask import Flask
from models import db
from routes.trees import tree_routes
from routes.policies import policy_routes
from routes.treesxml import treesxml_routes
from routes.treepolicy import treepolicy_routes
from sqlalchemy.exc import OperationalError

app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@database:5432/flaskdb')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Try to connect to database
MAX_RETRIES = 5
for attempt in range(MAX_RETRIES):
    try:
        db.init_app(app)
        with app.app_context():
            db.create_all()
        print("Connection to database succesfull!")
        break
    except OperationalError as e:
        print(f"Attempt {attempt + 1} failed: {e}")
        time.sleep(5)
else:
    print("Impossible to connect to database.")
    exit(1)

# Register routes
app.register_blueprint(tree_routes, url_prefix='/api/trees')
app.register_blueprint(policy_routes, url_prefix='/api/policies')
app.register_blueprint(treesxml_routes, url_prefix='/api/treesxml')
app.register_blueprint(treepolicy_routes, url_prefix='/api/treepolicy')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
