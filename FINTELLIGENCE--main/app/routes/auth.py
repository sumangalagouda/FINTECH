from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, limiter
from app.models.user import User
from app.models.registration_request import RegistrationRequest

auth_bp = Blueprint('auth', __name__)


def _get_requesting_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)



@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role', 'investigator')
    
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already exists"}), 400
        
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password_hash=hashed_password, name=name, role=role)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "User created successfully"}), 201


@auth_bp.route('/register-request', methods=['POST'])
@limiter.limit("5 per minute")
def register_request():
    data = request.get_json(silent=True) or {}

    name = data.get('name')
    email = data.get('email')
    employee_id = data.get('employee_id')
    organization = data.get('organization')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    requested_role = data.get('requested_role')

    if not all([name, email, employee_id, organization, password, confirm_password, requested_role]):
        return jsonify({"error": "Missing required fields"}), 400

    if password != confirm_password:
        return jsonify({"error": "password must match confirm_password"}), 400

    # Avoid duplicates: if user already exists, reject request.
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    if RegistrationRequest.query.filter_by(email=email, status='pending').first():
        return jsonify({"error": "Pending request already exists"}), 400

    hashed_password = generate_password_hash(password)
    req = RegistrationRequest(
        name=name,
        email=email,
        employee_id=employee_id,
        organization=organization,
        password_hash=hashed_password,
        requested_role=requested_role,
        status='pending'
    )
    db.session.add(req)
    db.session.commit()

    return jsonify({"message": "Registration submitted for admin approval", "request_id": req.id}), 201


@auth_bp.route('/pending-registrations', methods=['GET'])
@jwt_required()
def pending_registrations():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    reqs = RegistrationRequest.query.filter_by(status='pending').order_by(RegistrationRequest.requested_at.desc()).all()

    return jsonify([
        {
            "id": r.id,
            "name": r.name,
            "email": r.email,
            "employee_id": r.employee_id,
            "organization": r.organization,
            "requested_role": r.requested_role,
            "requested_at": r.requested_at.isoformat() if r.requested_at else None,
        } for r in reqs
    ]), 200


@auth_bp.route('/approve-registration/<req_id>', methods=['POST'])
@jwt_required()
def approve_registration(req_id: str):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    req = RegistrationRequest.query.get_or_404(req_id)

    data = request.get_json(silent=True) or {}
    approve = data.get('approve')

    if approve not in [True, False]:
        return jsonify({"error": "approve must be true or false"}), 400

    if req.status != 'pending':
        return jsonify({"error": "Request is not pending"}), 400

    from datetime import datetime, timezone

    req.reviewed_by = user_id
    req.reviewed_at = datetime.now(timezone.utc)

    if approve:
        # Create the actual user account.
        if User.query.filter_by(email=req.email).first():
            req.status = 'rejected'
            db.session.commit()
            return jsonify({"status": "rejected", "error": "User already exists"}), 200

        new_user = User(
            name=req.name,
            email=req.email,
            password_hash=req.password_hash,
            role=req.requested_role,
            is_active=True,
        )
        db.session.add(new_user)
        req.status = 'approved'
        db.session.commit()
        return jsonify({"status": 'approved', "user_id": new_user.id}), 200

    # Reject path
    req.status = 'rejected'
    db.session.commit()
    return jsonify({"status": 'rejected'}), 200


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"msg": "Bad email or password"}), 401
        
    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role, "email": user.email})
    return jsonify(access_token=access_token), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    current_user = get_jwt_identity()
    user = User.query.get(current_user)
    if not user:
        return jsonify({"msg": "User not found"}), 404
        
    return jsonify({
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "is_active": user.is_active
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # In a real app, you might want to implement token blocklisting here
    return jsonify({"msg": "Successfully logged out"}), 200

