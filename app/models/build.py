from app.extensions import db
from datetime import datetime

class BuildPC(db.Model):
    __tablename__ = 'builds'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    publica = db.Column(db.Boolean, default=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Peças da build (cada uma é FK para produto)
    cpu_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    gpu_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    ram_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    ram_quantidade = db.Column(db.Integer, default=2, nullable=False)  # nº de pentes
    motherboard_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    storage_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    fonte_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    gabinete_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    cooler_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)

    # Loja escolhida para cada peça (nome da loja, ex: "Pichau")
    cpu_loja = db.Column(db.String(100), nullable=True)
    gpu_loja = db.Column(db.String(100), nullable=True)
    ram_loja = db.Column(db.String(100), nullable=True)
    motherboard_loja = db.Column(db.String(100), nullable=True)
    storage_loja = db.Column(db.String(100), nullable=True)
    fonte_loja = db.Column(db.String(100), nullable=True)
    gabinete_loja = db.Column(db.String(100), nullable=True)
    cooler_loja = db.Column(db.String(100), nullable=True)

    # Relacionamentos para cada peça
    cpu = db.relationship('Produto', foreign_keys=[cpu_id])
    gpu = db.relationship('Produto', foreign_keys=[gpu_id])
    ram = db.relationship('Produto', foreign_keys=[ram_id])
    motherboard = db.relationship('Produto', foreign_keys=[motherboard_id])
    storage = db.relationship('Produto', foreign_keys=[storage_id])
    fonte = db.relationship('Produto', foreign_keys=[fonte_id])
    gabinete = db.relationship('Produto', foreign_keys=[gabinete_id])
    cooler = db.relationship('Produto', foreign_keys=[cooler_id])

    def consumo_total(self):
        pecas = [self.cpu, self.gpu, self.motherboard, self.storage, self.fonte, self.gabinete, self.cooler]
        total = sum(p.consumo_watts for p in pecas if p and p.consumo_watts)
        if self.ram and self.ram.consumo_watts:
            total += self.ram.consumo_watts * (self.ram_quantidade or 1)
        return total

    def preco_total(self):
        pecas = [self.cpu, self.gpu, self.motherboard, self.storage, self.fonte, self.gabinete, self.cooler]
        total = 0
        for p in pecas:
            if p and p.menor_preco():
                total += p.menor_preco().preco
        if self.ram and self.ram.menor_preco():
            total += self.ram.menor_preco().preco * (self.ram_quantidade or 1)
        return total

    def __repr__(self):
        return f'<Build {self.nome}>'