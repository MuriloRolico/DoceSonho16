from database import db
from datetime import datetime, timedelta
import jwt
from flask import current_app
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib

class Usuario(db.Model):
    __tablename__ = 'usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    foto_perfil = db.Column(db.String(100), nullable=True)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    concordou_politica = db.Column(db.Boolean, default=False)
    
    # Campos de endereço e segurança
    cpf_hash = db.Column(db.String(200), nullable=True)
    endereco_cep = db.Column(db.String(10), nullable=True)
    endereco_rua = db.Column(db.String(200), nullable=True)
    endereco_numero = db.Column(db.String(20), nullable=True)
    endereco_complemento = db.Column(db.String(100), nullable=True)
    endereco_bairro = db.Column(db.String(100), nullable=True)
    endereco_cidade = db.Column(db.String(100), nullable=True)
    endereco_estado = db.Column(db.String(2), nullable=True)
    
    # Campos para recuperação de senha
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiracao = db.Column(db.DateTime, nullable=True)
    ultimo_acesso = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='ativo')
    
    # Campos de privacidade
    mascarar_email = db.Column(db.Boolean, default=True)
    mascarar_cpf = db.Column(db.Boolean, default=True)
    mascarar_endereco = db.Column(db.Boolean, default=True)
  
    
    # Relationships
    pedidos = db.relationship('Pedido', backref='cliente', lazy=True)
    bolos_personalizados = db.relationship('BoloPersonalizado', backref='usuario', lazy=True)
    logs = db.relationship('Log', backref='usuario', lazy=True)
    tokens = db.relationship('Token', backref='usuario', lazy=True)
    
    def set_password(self, password):
        """Define a senha do usuário usando hash"""
        self.senha = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return check_password_hash(self.senha, password)
    
    def set_cpf(self, cpf):
        """Criptografa o CPF antes de armazenar"""
        if cpf:
            salt = current_app.config.get('HASH_SALT', 'default-salt')
            self.cpf_hash = hashlib.sha256((cpf + salt).encode()).hexdigest()
    
    def check_cpf(self, cpf):
        """Verifica se o CPF fornecido corresponde ao armazenado"""
        if not cpf or not self.cpf_hash:
            return False
        salt = current_app.config.get('HASH_SALT', 'default-salt')
        return self.cpf_hash == hashlib.sha256((cpf + salt).encode()).hexdigest()
    
    def get_cpf_masked(self):
        """Retorna o CPF mascarado para exibição"""
        if self.cpf_hash:
            return "***.***.***-**"
        return None
    
    def gerar_token_recuperacao(self):
        """Gera um token para recuperação de senha"""
        token = str(uuid.uuid4())
        self.reset_token = token
        self.reset_token_expiracao = datetime.utcnow() + timedelta(hours=1)
        return token
    
    def verificar_token_recuperacao(self, token):
        """Verifica se o token de recuperação é válido"""
        return (self.reset_token == token and 
                self.reset_token_expiracao and 
                self.reset_token_expiracao > datetime.utcnow())
    
    def gerar_auth_token(self, expira_em=24):
        """Gera um token JWT para autenticação"""
        payload = {
            'id': self.id,
            'exp': datetime.utcnow() + timedelta(hours=expira_em)
        }
        return jwt.encode(
            payload,
            current_app.config.get('SECRET_KEY', 'default-secret-key'),
            algorithm='HS256'
        )
    
    @staticmethod
    def verificar_auth_token(token):
        """Verifica e retorna o usuário do token JWT"""
        try:
            payload = jwt.decode(
                token,
                current_app.config.get('SECRET_KEY', 'default-secret-key'),
                algorithms=['HS256']
            )
            return Usuario.query.get(payload['id'])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
    
    def __repr__(self):
        return f'<Usuario {self.email}>'

class Produto(db.Model):
    __tablename__ = 'produto'
    
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
    
    # Campo para soft delete
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    itens_pedido = db.relationship('ItemPedido', backref='produto', lazy=True)
    carrinho_itens = db.relationship('CarrinhoItem', backref='produto', lazy=True)
    
    def desativar(self):
        """Soft delete - marca o produto como inativo"""
        self.ativo = False
        self.data_atualizacao = datetime.utcnow()
        db.session.commit()
    
    def reativar(self):
        """Reativa um produto desativado"""
        self.ativo = True
        self.data_atualizacao = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def ativos(cls):
        """Retorna query apenas de produtos ativos"""
        return cls.query.filter_by(ativo=True)
    
    @classmethod
    def inativos(cls):
        """Retorna query apenas de produtos inativos"""
        return cls.query.filter_by(ativo=False)
    
    def __repr__(self):
        return f'<Produto {self.nome} (Ativo: {self.ativo})>'

class BoloPersonalizado(db.Model):
    __tablename__ = 'bolo_personalizado'
    
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
    # Relationships
    pedidos = db.relationship('ItemPedidoPersonalizado', backref='bolo', lazy=True)
    carrinho_itens_bolo = db.relationship('CarrinhoBoloPersonalizado', backref='bolo', lazy=True)
    def __repr__(self):
        return f'<BoloPersonalizado {self.nome}>'

class Pedido(db.Model):
    __tablename__ = 'pedido'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pendente')
    total = db.Column(db.Float, default=0.0)
    tipo_entrega = db.Column(db.String(20), nullable=True)
    valor_frete = db.Column(db.Float, default=0.0)
    endereco_entrega = db.Column(db.Text, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    mercado_pago_transaction_id = db.Column(db.String(255), nullable=True)
    
    # Relationships
    itens = db.relationship('ItemPedido', backref='pedido', lazy=True)
    itens_personalizados = db.relationship('ItemPedidoPersonalizado', backref='pedido', lazy=True)
    
    def calcular_total(self):
        """Calcula o total do pedido"""
        total = 0
        for item in self.itens:
            total += item.preco_unitario * item.quantidade
        for item in self.itens_personalizados:
            total += item.preco_unitario * item.quantidade
        self.total = total
        return total
    
    def __repr__(self):
        return f'<Pedido {self.id} - {self.status}>'

class ItemPedido(db.Model):
    __tablename__ = 'item_pedido'
    
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    preco_unitario = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<ItemPedido {self.id} - Produto: {self.produto_id}>'

class ItemPedidoPersonalizado(db.Model):
    __tablename__ = 'item_pedido_personalizado'
    
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    bolo_personalizado_id = db.Column(db.Integer, db.ForeignKey('bolo_personalizado.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    preco_unitario = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<ItemPedidoPersonalizado {self.id} - Bolo: {self.bolo_personalizado_id}>'

class Log(db.Model):
    __tablename__ = 'log'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    data = db.Column(db.DateTime, default=datetime.utcnow)
  
    
    def __repr__(self):
        return f'<Log {self.id} - {self.tipo}>'

class Token(db.Model):
    __tablename__ = 'token'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    token = db.Column(db.String(500), nullable=False)
    tipo = db.Column(db.String(20), default='access')
    device_info = db.Column(db.String(200), nullable=True)
    # A coluna IP foi removida
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_expiracao = db.Column(db.DateTime, nullable=False)
    is_revogado = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Token {self.id} - {self.tipo}>'

class CarrinhoItem(db.Model):
    __tablename__ = 'carrinho'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    data_adicao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    usuario = db.relationship('Usuario', backref=db.backref('carrinho_itens', lazy=True))
    
    def __repr__(self):
        return f'<CarrinhoItem {self.id}: {self.quantidade}x produto {self.produto_id}>'

class CarrinhoBoloPersonalizado(db.Model):
    __tablename__ = 'carrinho_personalizado'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    bolo_personalizado_id = db.Column(db.Integer, db.ForeignKey('bolo_personalizado.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    data_adicao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    usuario = db.relationship('Usuario', backref=db.backref('carrinho_bolos', lazy=True))
    
    def __repr__(self):
        return f'<CarrinhoBoloPersonalizado {self.id}: {self.quantidade}x bolo {self.bolo_personalizado_id}>'