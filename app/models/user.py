from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    avatar = db.Column(db.String(500), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    email_verificado = db.Column(db.Boolean, default=False)

    # 2FA
    codigo_login = db.Column(db.String(6), nullable=True)

    # Relacionamentos
    builds = db.relationship('BuildPC', backref='usuario', lazy=True)
    avaliacoes = db.relationship('Avaliacao', backref='usuario', lazy=True)
    favoritos = db.relationship('Favorito', backref='usuario', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return True