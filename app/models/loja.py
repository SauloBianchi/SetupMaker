from app.extensions import db

class Loja(db.Model):
    __tablename__ = 'lojas'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)   # ex: Kabum
    url = db.Column(db.String(500))
    logo_url = db.Column(db.String(500))

    precos = db.relationship('Preco', backref='loja', lazy=True)

    def __repr__(self):
        return f'<Loja {self.nome}>'


class Preco(db.Model):
    __tablename__ = 'precos'

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    loja_id = db.Column(db.Integer, db.ForeignKey('lojas.id'), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    url_produto = db.Column(db.String(500))   # link direto do produto na loja
    fonte = db.Column(db.String(20), default='seed')  # 'seed' ou 'usuario'

    def __repr__(self):
        return f'<Preco R${self.preco} - {self.loja_id}>'