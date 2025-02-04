from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Text, ForeignKey
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class TreeJSON(db.Model):
    __tablename__ = 'trees'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=False)  # Nome del file
    content = db.Column(JSONB, nullable=False)  # Contenuto JSON
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class TreeXML(db.Model):
    __tablename__ = 'treesxml'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=False)  # Nome del file
    content = db.Column(Text, nullable=False)  # Contenuto XML salvato come stringa
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Policy(db.Model):
    __tablename__ = 'policies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=False, nullable=False)  # Nome del file
    content = db.Column(JSONB, nullable=False)  # Contenuto JSON
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class TreePolicy(db.Model):
    __tablename__ = 'treepolicy'
    id = db.Column(db.Integer, primary_key=True)
    tree_id = db.Column(db.Integer, ForeignKey('trees.id'), nullable=False)
    treexml_id = db.Column(db.Integer, ForeignKey('treesxml.id'), nullable=False)
    policy_id = db.Column(db.Integer, ForeignKey('policies.id'), nullable=False)

    tree = relationship('TreeJSON', backref='tree_policies')
    treexml = relationship('TreeXML', backref='tree_policies')
    policy = relationship('Policy', backref='tree_policies')

