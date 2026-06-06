from app.extensions import db
from datetime import datetime


class Avaliacao(db.Model):
    __tablename__ = 'avaliacoes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    nota = db.Column(db.Integer, nullable=False)   # 1 a 5
    comentario = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Avaliacao {self.nota} - produto {self.produto_id}>'


class AvaliacaoBuild(db.Model):
    __tablename__ = 'avaliacoes_build'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    build_id = db.Column(db.Integer, db.ForeignKey('builds.id'), nullable=False)
    nota = db.Column(db.Integer, nullable=False)   # 1 a 5
    comentario = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('User', backref='avaliacoes_build', lazy=True)
    build   = db.relationship('BuildPC', backref='avaliacoes', lazy=True)

    def __repr__(self):
        return f'<AvaliacaoBuild {self.nota} - build {self.build_id}>'


class Favorito(db.Model):
    __tablename__ = 'favoritos'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    build_id = db.Column(db.Integer, db.ForeignKey('builds.id'), nullable=False)

    build = db.relationship('BuildPC', backref='favoritado_por')

    def __repr__(self):
        return f'<Favorito user={self.user_id} build={self.build_id}>'