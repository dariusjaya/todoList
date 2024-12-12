from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields


    
app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:0811565827@localhost:5432/todoList' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = '4875OxObs2iaXJEmCUjSgQ6h%Jt3@gbOYh'

db = SQLAlchemy(app)
jwt = JWTManager(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Checklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('checklists', lazy=True))

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    checklist_id = db.Column(db.Integer, db.ForeignKey('checklist.id'), nullable=False)
    checklist = db.relationship('Checklist', backref=db.backref('items', lazy=True))


class UserSchema(Schema):
    id = fields.Int()
    username = fields.Str()

class ChecklistSchema(Schema):
    id = fields.Int()
    title = fields.Str()

class ItemSchema(Schema):
    id = fields.Int()
    description = fields.Str()
    completed = fields.Bool()




@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists"}), 400

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "User registered successfully"}), 201


@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token)
    return jsonify({"msg": "Bad username or password"}), 401


@app.route('/checklist', methods=['POST'])
@jwt_required()
def create_checklist():
    title = request.json.get('title')
    user_id = get_jwt_identity()
    
    new_checklist = Checklist(title=title, user_id=user_id)
    db.session.add(new_checklist)
    db.session.commit()
    
    return jsonify({"msg": "Checklist created", "id": new_checklist.id}), 201


@app.route('/checklist/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_checklist(id):
    user_id = get_jwt_identity()
    checklist = Checklist.query.filter_by(id=id, user_id=user_id).first()
    
    if checklist:
        db.session.delete(checklist)
        db.session.commit()
        return jsonify({"msg": "Checklist deleted"}), 200
    return jsonify({"msg": "Checklist not found"}), 404


@app.route('/checklists', methods=['GET'])
@jwt_required()
def get_checklists():
    user_id = get_jwt_identity()
    checklists = Checklist.query.filter_by(user_id=user_id).all()
    checklist_schema = ChecklistSchema(many=True)
    return jsonify(checklist_schema.dump(checklists)), 200


@app.route('/checklist/<int:id>', methods=['GET'])
@jwt_required()
def get_checklist_details(id):
    user_id = get_jwt_identity()
    checklist = Checklist.query.filter_by(id=id, user_id=user_id).first()
    
    if checklist:
        checklist_schema = ChecklistSchema()
        return jsonify(checklist_schema.dump(checklist)), 200
    return jsonify({"msg": "Checklist not found"}), 404


@app.route('/checklist/<int:checklist_id>/item', methods=['POST'])
@jwt_required()
def create_item(checklist_id):
    description = request.json.get('description')
    user_id = get_jwt_identity()
    
    checklist = Checklist.query.filter_by(id=checklist_id, user_id=user_id).first()
    
    if checklist:
        new_item = Item(description=description, checklist_id=checklist.id)
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"msg": "Item created", "id": new_item.id}), 201
    return jsonify({"msg": "Checklist not found"}), 404


@app.route('/item/<int:id>', methods=['GET'])
@jwt_required()
def get_item(id):
    item = Item.query.get(id)
    
    if item:
        item_schema = ItemSchema()
        return jsonify(item_schema.dump(item)), 200
    return jsonify({"msg": "Item not found"}), 404


@app.route('/item/<int:id>', methods=['PUT'])
@jwt_required()
def update_item(id):
    description = request.json.get('description')
    completed = request.json.get('completed')
    
    item = Item.query.get(id)
    
    if item:
        if description:
            item.description = description
        if completed is not None:
            item.completed = completed
        db.session.commit()
        return jsonify({"msg": "Item updated"}), 200
    return jsonify({"msg": "Item not found"}), 404


@app.route('/item/<int:id>/status', methods=['PUT'])
@jwt_required()
def update_item_status(id):
    completed = request.json.get('completed')
    
    item = Item.query.get(id)
    
    if item:
        item.completed = completed
        db.session.commit()
        return jsonify({"msg": "Item status updated"}), 200
    return jsonify({"msg": "Item not found"}), 404


@app.route('/item/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_item(id):
    item = Item.query.get(id)
    
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"msg": "Item deleted"}), 200
    return jsonify({"msg": "Item not found"}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True)
    
