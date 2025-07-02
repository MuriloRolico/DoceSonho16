from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    foto_perfil = db.Column(db.String(100), nullable=True)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    concordou_politica = db.Column(db.Boolean, default=False)
    pedidos = db.relationship('Pedido', backref='cliente', lazy=True)
    bolos_personalizados = db.relationship('BoloPersonalizado', backref='usuario', lazy=True)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    preco = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    imagem = db.Column(db.String(100), nullable=True)
    peso = db.Column(db.Float, nullable=True)
    ingredientes = db.Column(db.Text, nullable=True)
    data_validade = db.Column(db.DateTime, nullable=True)
    informacoes_nutricionais = db.Column(db.Text, nullable=True)
    itens_pedido = db.relationship('ItemPedido', backref='produto', lazy=True)

class BoloPersonalizado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False, default="Bolo Personalizado")
    massa = db.Column(db.String(50), nullable=False)
    recheios = db.Column(db.Text, nullable=False)
    cobertura = db.Column(db.String(50), nullable=False)
    finalizacao = db.Column(db.Text, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    preco = db.Column(db.Float, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    pedidos = db.relationship('ItemPedidoPersonalizado', backref='bolo', lazy=True)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pendente')
    total = db.Column(db.Float, default=0.0)
    itens = db.relationship('ItemPedido', backref='pedido', lazy=True)
    itens_personalizados = db.relationship('ItemPedidoPersonalizado', backref='pedido', lazy=True)

class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    preco_unitario = db.Column(db.Float, nullable=False)

class ItemPedidoPersonalizado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    bolo_personalizado_id = db.Column(db.Integer, db.ForeignKey('bolo_personalizado.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    preco_unitario = db.Column(db.Float, nullable=False)

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    ip = db.Column(db.String(50), nullable=True)
    usuario = db.relationship('Usuario', backref='logs', lazy=True)

class Carrinho(db.Model):
    __tablename__ = 'carrinho'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, default=1, nullable=False)
    data_adicao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario', backref=db.backref('itens_carrinho', lazy=True))
    produto = db.relationship('Produto', backref=db.backref('itens_carrinho', lazy=True))

class CarrinhoPersonalizado(db.Model):
    __tablename__ = 'carrinho_personalizado'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    bolo_personalizado_id = db.Column(db.Integer, db.ForeignKey('bolo_personalizado.id'), nullable=False)
    quantidade = db.Column(db.Integer, default=1, nullable=False)
    data_adicao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario', backref=db.backref('itens_carrinho_personalizado', lazy=True))
    bolo_personalizado = db.relationship('BoloPersonalizado', backref=db.backref('itens_carrinho', lazy=True))