from app.extensions import db

class Categoria(db.Model):
    __tablename__ = 'categorias'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)  # ex: CPU, GPU, RAM
    slug = db.Column(db.String(100), unique=True, nullable=False)  # ex: cpu, gpu, ram

    produtos = db.relationship('Produto', backref='categoria', lazy=True)

    def __repr__(self):
        return f'<Categoria {self.nome}>'


class Produto(db.Model):
    __tablename__ = 'produtos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    marca = db.Column(db.String(100))
    descricao = db.Column(db.Text)
    imagem_url = db.Column(db.String(500))
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)

    # Especificações técnicas (usadas na compatibilidade)
    socket = db.Column(db.String(50))        # ex: AM4, LGA1700
    tipo_ram = db.Column(db.String(20))      # ex: DDR4, DDR5
    consumo_watts = db.Column(db.Integer)    # consumo energético em W
    desempenho = db.Column(db.Integer)       # score de desempenho (0-100)
    frequencia = db.Column(db.String(50))    # ex: 3200MHz
    capacidade = db.Column(db.String(50))    # ex: 16GB, 1TB

    # Relacionamentos
    precos = db.relationship('Preco', backref='produto', lazy=True)
    avaliacoes = db.relationship('Avaliacao', backref='produto', lazy=True)

    def menor_preco(self):
        if not self.precos:
            return None
        return min(self.precos, key=lambda p: p.preco)

    def maior_preco(self):
        if not self.precos:
            return None
        return max(self.precos, key=lambda p: p.preco)

    def intervalo_precos(self):
        if not self.precos:
            return None
        valores = [p.preco for p in self.precos]
        return min(valores), max(valores)

    def __repr__(self):
        return f'<Produto {self.nome}>'