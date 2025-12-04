from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, current_app
from database import db
from models.models import Usuario, Pedido, BoloPersonalizado, ItemPedido, ItemPedidoPersonalizado, Produto, Token
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from utils.helpers import allowed_file
from datetime import datetime, timedelta
import os
import json
import io
import uuid
import re
from functools import wraps
from utils.helpers import funcionario_bloqueado

user_bp = Blueprint('user', __name__)

# Decorator para proteger rotas que exigem autenticação
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa fazer login para acessar esta página', 'warning')
            return redirect(url_for('auth.login'))
        
        # Bloquear funcionários de acessar perfil de usuário
        usuario = Usuario.query.get(session['usuario_id'])
        if usuario and usuario.is_funcionario:
            flash('Funcionários não têm acesso ao perfil de usuário.', 'warning')
            return redirect(url_for('funcionario.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

# routes/user.py - MODIFICAÇÃO NA ROTA /perfil

@user_bp.route('/perfil')
@login_required
def perfil():
    usuario = db.session.get(Usuario, session['usuario_id'])
    tokens = Token.query.filter_by(usuario_id=usuario.id, is_revogado=False).all()
    
    # ADICIONE APENAS ESTAS 2 LINHAS:
    pedidos_pendentes = Pedido.query.filter(
        Pedido.usuario_id == usuario.id,
        Pedido.status.in_(['Pendente', 'Em Preparação', 'Aprovado', 'Pronto para Retirada', 'Em Transporte'])
    ).all()
    
    return render_template('perfil.html', usuario=usuario, tokens=tokens, pedidos_pendentes=pedidos_pendentes)

@user_bp.route('/perfil/atualizar', methods=['POST'])
@login_required
def atualizar_perfil():
    usuario = db.session.get(Usuario, session['usuario_id'])
    
    # Debug: Imprimir todos os dados do formulário
    print("=== DEBUG: Dados recebidos do formulário ===")
    for key, value in request.form.items():
        print(f"{key}: '{value}'")
    print("==========================================")
    
    # Identificar qual formulário foi enviado
    if 'nome' in request.form:
        # Formulário de dados básicos
        # Obter dados do formulário com validação mais robusta
        nome = request.form.get('nome')
        email = request.form.get('email')
        
        # Verificar se os campos existem no formulário antes de processar
        if nome is None:
            flash('Campo nome não foi encontrado no formulário', 'danger')
            return redirect(url_for('user.perfil'))
        
        if email is None:
            flash('Campo email não foi encontrado no formulário', 'danger')
            return redirect(url_for('user.perfil'))
        
        # Limpar e validar os dados
        nome = nome.strip() if nome else ''
        email = email.strip() if email else ''
        
        # Debug específico para nome e email
        print(f"Nome após processamento: '{nome}' (length: {len(nome)})")
        print(f"Email após processamento: '{email}' (length: {len(email)})")
        
        # Validar campos obrigatórios
        if not nome or len(nome) == 0:
            flash('O nome é obrigatório e não pode estar vazio', 'danger')
            return redirect(url_for('user.perfil'))
        
        if not email or len(email) == 0:
            flash('O e-mail é obrigatório e não pode estar vazio', 'danger')
            return redirect(url_for('user.perfil'))
        
        # Validar comprimento mínimo do nome
        if len(nome) < 2:
            flash('O nome deve ter pelo menos 2 caracteres', 'danger')
            return redirect(url_for('user.perfil'))
        
        # Validar formato do email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Por favor, insira um e-mail válido', 'danger')
            return redirect(url_for('user.perfil'))
        
        # Verificar se o email já existe para outro usuário
        if email != usuario.email:
            usuario_existente = Usuario.query.filter_by(email=email).first()
            if usuario_existente:
                flash('Este e-mail já está sendo utilizado por outra conta', 'danger')
                return redirect(url_for('user.perfil'))
        
        # Atualizar dados básicos
        usuario.nome = nome
        usuario.email = email
        
    elif 'endereco_cep' in request.form:
        # Formulário de endereço
        # Dados de endereço com validação de existência
        endereco_cep = request.form.get('endereco_cep', '').strip()
        endereco_rua = request.form.get('endereco_rua', '').strip()
        endereco_numero = request.form.get('endereco_numero', '').strip()
        endereco_complemento = request.form.get('endereco_complemento', '').strip()
        endereco_bairro = request.form.get('endereco_bairro', '').strip()
        endereco_cidade = request.form.get('endereco_cidade', '').strip()
        endereco_estado = request.form.get('endereco_estado', '').strip()
        
        # Atualizar dados de endereço (apenas se não estiverem vazios)
        if endereco_cep:
            usuario.endereco_cep = endereco_cep
        if endereco_rua:
            usuario.endereco_rua = endereco_rua
        if endereco_numero:
            usuario.endereco_numero = endereco_numero
        if endereco_complemento:
            usuario.endereco_complemento = endereco_complemento
        if endereco_bairro:
            usuario.endereco_bairro = endereco_bairro
        if endereco_cidade:
            usuario.endereco_cidade = endereco_cidade
        if endereco_estado:
            usuario.endereco_estado = endereco_estado
            
    elif 'mascarar_email' in request.form or 'receber_newsletter' in request.form:
        # Formulário de preferências
        # Preferências de privacidade com verificação de existência
        mascarar_email = request.form.get('mascarar_email') == 'on'
        mascarar_cpf = request.form.get('mascarar_cpf') == 'on'
        mascarar_endereco = request.form.get('mascarar_endereco') == 'on'
        receber_newsletter = request.form.get('receber_newsletter') == 'on'
        receber_sms = request.form.get('receber_sms') == 'on'
        receber_whatsapp = request.form.get('receber_whatsapp') == 'on'
        
        # Atualizar preferências de privacidade (se os campos existirem no modelo)
        if hasattr(usuario, 'mascarar_email'):
            usuario.mascarar_email = mascarar_email
        if hasattr(usuario, 'mascarar_cpf'):
            usuario.mascarar_cpf = mascarar_cpf
        if hasattr(usuario, 'mascarar_endereco'):
            usuario.mascarar_endereco = mascarar_endereco
        if hasattr(usuario, 'receber_newsletter'):
            usuario.receber_newsletter = receber_newsletter
        if hasattr(usuario, 'receber_sms'):
            usuario.receber_sms = receber_sms
        if hasattr(usuario, 'receber_whatsapp'):
            usuario.receber_whatsapp = receber_whatsapp
            
    elif 'cpf' in request.form:
        # Formulário de CPF
        cpf = request.form.get('cpf', '').strip()
        
        # Atualizar CPF se fornecido
        if cpf:
            # Limpar CPF (remover pontos e traços)
            cpf_limpo = cpf.replace('.', '').replace('-', '').replace(' ', '')
            
            # Validar CPF (básico - 11 dígitos)
            if len(cpf_limpo) == 11 and cpf_limpo.isdigit():
                # Salvar CPF diretamente no campo correto
                usuario.cpf = cpf_limpo
            else:
                flash('CPF inválido. Por favor, insira um CPF válido', 'danger')
                return redirect(url_for('user.perfil'))
    else:
        flash('Formulário não reconhecido', 'danger')
        return redirect(url_for('user.perfil'))
    
    try:
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar perfil: {str(e)}', 'danger')
    
    return redirect(url_for('user.perfil'))

@user_bp.route('/perfil/foto', methods=['POST'])
@login_required
def atualizar_foto():
    try:
        usuario = db.session.get(Usuario, session['usuario_id'])
        
        # Verificar se há um arquivo de foto no formulário
        if 'foto_perfil' not in request.files:
            flash('Nenhuma foto foi enviada', 'danger')
            return redirect(url_for('user.perfil'))
        
        arquivo = request.files['foto_perfil']
        
        if arquivo.filename == '':
            flash('Nenhuma foto foi selecionada', 'danger')
            return redirect(url_for('user.perfil'))
        
        if not allowed_file(arquivo.filename):
            flash('Formato de arquivo não permitido. Use JPG, JPEG, PNG ou GIF', 'danger')
            return redirect(url_for('user.perfil'))
        
        # Limitar tamanho do arquivo (5MB)
        arquivo.seek(0, os.SEEK_END)
        tamanho = arquivo.tell()
        arquivo.seek(0)
        
        if tamanho > 5 * 1024 * 1024:
            flash('O arquivo é muito grande. O tamanho máximo permitido é 5MB', 'danger')
            return redirect(url_for('user.perfil'))
        
        # Criar uma pasta para fotos de perfil se não existir
        diretorio_uploads = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_pics')
        os.makedirs(diretorio_uploads, exist_ok=True)
        
        # Salvar a foto com um nome mais curto
        extensao = secure_filename(arquivo.filename).rsplit('.', 1)[1].lower()
        filename = f"user_{usuario.id}_{uuid.uuid4().hex[:12]}.{extensao}"
        caminho_completo = os.path.join(diretorio_uploads, filename)
        arquivo.save(caminho_completo)
        
        # Excluir foto antiga se existir
        if usuario.foto_perfil and usuario.foto_perfil != 'default.jpg':
            try:
                if usuario.foto_perfil.startswith('/static/'):
                    caminho_foto_antiga = os.path.join(current_app.root_path, usuario.foto_perfil.lstrip('/'))
                else:
                    caminho_foto_antiga = os.path.join(diretorio_uploads, usuario.foto_perfil)
                
                if os.path.exists(caminho_foto_antiga):
                    os.remove(caminho_foto_antiga)
            except Exception as e:
                print(f"Erro ao excluir foto antiga: {e}")
        
        # Atualizar o caminho da foto no banco de dados
        usuario.foto_perfil = f'/static/uploads/profile_pics/{filename}'
        
        db.session.commit()
        flash('Foto de perfil atualizada com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        # Log do erro completo para debug (não mostrar ao usuário)
        print(f"Erro ao atualizar foto: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Mensagem amigável para o usuário
        flash('Ocorreu um erro ao atualizar sua foto. Por favor, tente novamente com uma imagem menor ou com nome mais curto.', 'danger')
    
    return redirect(url_for('user.perfil'))

# Modificação em alterar_senha
@user_bp.route('/perfil/alterar-senha', methods=['POST'])
@login_required
def alterar_senha():
    usuario = db.session.get(Usuario, session['usuario_id'])
    
    senha_atual = request.form.get('senha_atual', '').strip()
    nova_senha = request.form.get('nova_senha', '').strip()
    confirmar_nova_senha = request.form.get('confirmar_nova_senha', '').strip()
    
    # Validar campos obrigatórios
    if not senha_atual:
        flash('A senha atual é obrigatória', 'danger')
        return redirect(url_for('user.perfil'))
    
    if not nova_senha:
        flash('A nova senha é obrigatória', 'danger')
        return redirect(url_for('user.perfil'))
    
    if not confirmar_nova_senha:
        flash('A confirmação da nova senha é obrigatória', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Verificar se a senha atual está correta
    if not check_password_hash(usuario.senha, senha_atual):
        flash('Senha atual incorreta', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Verificar se as novas senhas coincidem
    if nova_senha != confirmar_nova_senha:
        flash('As novas senhas não coincidem', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Verificar requisitos de segurança da senha
    if len(nova_senha) < 8:
        flash('A senha deve ter pelo menos 8 caracteres', 'danger')
        return redirect(url_for('user.perfil'))
    if not re.search("[a-z]", nova_senha):
        flash('A senha deve conter pelo menos uma letra minúscula', 'danger')
        return redirect(url_for('user.perfil'))
    if not re.search("[A-Z]", nova_senha):
        flash('A senha deve conter pelo menos uma letra maiúscula', 'danger')
        return redirect(url_for('user.perfil'))
    if not re.search("[0-9]", nova_senha):
        flash('A senha deve conter pelo menos um número', 'danger')
        return redirect(url_for('user.perfil'))
    if not re.search("[_@$!%*?&]", nova_senha):
        flash('A senha deve conter pelo menos um caractere especial', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Atualizar a senha
    usuario.senha = generate_password_hash(nova_senha)
    
    try:
        # Revogar todos os tokens existentes por segurança
        tokens = Token.query.filter_by(usuario_id=usuario.id, is_revogado=False).all()
        for token in tokens:
            token.is_revogado = True
        
        db.session.commit()
        
        # Gerar novo token de autenticação se o método existir
        if hasattr(usuario, 'gerar_auth_token'):
            token = usuario.gerar_auth_token()
            session['auth_token'] = token
            
            # Salvar novo token no banco - removendo o IP
            novo_token = Token(
                usuario_id=usuario.id,
                token=token,
                device_info=request.user_agent.string,
                data_expiracao=datetime.utcnow() + timedelta(hours=24)
            )
            db.session.add(novo_token)
            db.session.commit()
        
        flash('Senha alterada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar senha: {str(e)}', 'danger')
    
    return redirect(url_for('user.perfil'))


@user_bp.route('/perfil/revogar-token/<int:token_id>', methods=['POST'])
@login_required
def revogar_token(token_id):
    token = Token.query.get_or_404(token_id)
    
    # Verificar se o token pertence ao usuário atual
    if token.usuario_id != session['usuario_id']:
        flash('Acesso negado', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Não permitir revogar o token atual
    if token.token == session.get('auth_token'):
        flash('Não é possível revogar a sessão atual', 'danger')
        return redirect(url_for('user.perfil'))
    
    try:
        token.is_revogado = True
        db.session.commit()
        flash('Sessão encerrada com sucesso', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao encerrar sessão: {str(e)}', 'danger')
    
    return redirect(url_for('user.perfil'))

# routes/user.py - MODIFICAÇÃO NA FUNÇÃO excluir_conta

@user_bp.route('/perfil/excluir', methods=['POST'])
@login_required
def excluir_conta():
    usuario = db.session.get(Usuario, session['usuario_id'])
    
    # Verificar confirmação
    confirmar_exclusao = request.form.get('confirmar_exclusao')
    if not confirmar_exclusao:
        flash('Você precisa confirmar a exclusão da conta', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Verificar senha
    senha = request.form.get('confirmar_senha', '').strip()
    if not senha:
        flash('A senha é obrigatória para confirmar a exclusão', 'danger')
        return redirect(url_for('user.perfil'))
    
    if not check_password_hash(usuario.senha, senha):
        flash('Senha incorreta', 'danger')
        return redirect(url_for('user.perfil'))
    
    # VALIDAÇÃO: Verificar se há pedidos não entregues
    pedidos_pendentes = Pedido.query.filter(
        Pedido.usuario_id == usuario.id,
        Pedido.status.in_(['Pendente', 'Em Preparação', 'Aprovado', 'Pronto para Retirada', 'Em Transporte'])
    ).all()
    
    if pedidos_pendentes:
        # Construir mensagem detalhada sobre os pedidos pendentes
        status_pedidos = {}
        for pedido in pedidos_pendentes:
            status = pedido.status
            if status not in status_pedidos:
                status_pedidos[status] = []
            status_pedidos[status].append(pedido.id)
        
        mensagem_detalhes = []
        for status, ids in status_pedidos.items():
            if len(ids) == 1:
                mensagem_detalhes.append(f"1 pedido com status '{status}' (#{ids[0]})")
            else:
                mensagem_detalhes.append(f"{len(ids)} pedidos com status '{status}' (#{', #'.join(map(str, ids))})")
        
        flash(
            f'Não é possível excluir sua conta pois você possui {len(pedidos_pendentes)} '
            f'pedido(s) pendente(s): {"; ".join(mensagem_detalhes)}. '
            f'Aguarde a conclusão de todos os pedidos (status "Entregue" ou "Cancelado") antes de excluir sua conta.',
            'danger'
        )
        return redirect(url_for('user.perfil'))
    
    # Excluir foto de perfil se existir
    if usuario.foto_perfil and usuario.foto_perfil.startswith('/static/uploads/profile_pics/'):
        try:
            caminho_foto = os.path.join(current_app.root_path, usuario.foto_perfil.lstrip('/'))
            if os.path.exists(caminho_foto):
                os.remove(caminho_foto)
        except Exception as e:
            print(f"Erro ao excluir foto de perfil: {e}")
    
    # Implementação de anonimização/exclusão conforme LGPD
    try:
        # Anonimizar dados do usuário em vez de excluir completamente
        usuario.nome = f"Usuário Excluído {usuario.id}"
        usuario.email = f"excluido_{uuid.uuid4()}@anonimo.com"
        usuario.senha = generate_password_hash(str(uuid.uuid4()))
        usuario.foto_perfil = None
        usuario.cpf = None
        usuario.endereco_cep = None
        usuario.endereco_rua = None
        usuario.endereco_numero = None
        usuario.endereco_complemento = None
        usuario.endereco_bairro = None
        usuario.endereco_cidade = None
        usuario.endereco_estado = None
        if hasattr(usuario, 'status'):
            usuario.status = 'excluido'
        
        # Revogar todos os tokens
        tokens = Token.query.filter_by(usuario_id=usuario.id).all()
        for token in tokens:
            token.is_revogado = True
        
        # Encerrar a sessão do usuário
        session.pop('usuario_id', None)
        session.pop('auth_token', None)
        session.pop('carrinho', None)
        session.pop('carrinho_personalizado', None)
        
        db.session.commit()
        flash('Sua conta foi excluída com sucesso. Esperamos vê-lo novamente em breve!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir conta: {str(e)}', 'danger')
        return redirect(url_for('user.perfil'))
    
    # Limpar cookie
    resposta = redirect(url_for('index'))
    resposta.delete_cookie('auth_token')
    
    return resposta

@user_bp.route('/perfil/dados-pessoais')
@login_required
def dados_pessoais():
    usuario = db.session.get(Usuario, session['usuario_id'])
    
    # Buscar pedidos do usuário
    pedidos = Pedido.query.filter_by(usuario_id=usuario.id).order_by(Pedido.data.desc()).all()
    
    # Buscar bolos personalizados do usuário
    bolos_personalizados = BoloPersonalizado.query.filter_by(usuario_id=usuario.id, ativo=True).all()
    
    return render_template('dados_pessoais.html', usuario=usuario, pedidos=pedidos, bolos_personalizados=bolos_personalizados)

@user_bp.route('/perfil/exportar-dados')
@login_required
def exportar_dados():
    import csv
    
    usuario = db.session.get(Usuario, session['usuario_id'])
    
    # Criar CSV único em memória
    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)
    
    # ===== SEÇÃO 1: DADOS DO USUÁRIO =====
    csv_writer.writerow(['===== DADOS DO USUÁRIO =====', '', '', '', ''])
    csv_writer.writerow([])
    
    csv_writer.writerow(['ID:', usuario.id, '', '', ''])
    csv_writer.writerow(['Nome:', usuario.nome, '', '', ''])
    csv_writer.writerow(['Email:', usuario.email, '', '', ''])
    csv_writer.writerow(['Data de Registro:', usuario.data_registro.strftime('%Y-%m-%d %H:%M:%S'), '', '', ''])
  
    
    # CPF
    if usuario.cpf_hash:
        if hasattr(usuario, 'get_cpf_masked'):
            csv_writer.writerow(['CPF:', usuario.get_cpf_masked(), '', '', ''])
        else:
            csv_writer.writerow(['CPF:', '***.***.***-**', '', '', ''])
    
    # Endereço
    if usuario.endereco_cep:
        csv_writer.writerow([])
        csv_writer.writerow(['ENDEREÇO:', '', '', '', ''])
        csv_writer.writerow(['CEP:', usuario.endereco_cep, '', '', ''])
        csv_writer.writerow(['Rua:', usuario.endereco_rua, '', '', ''])
        csv_writer.writerow(['Número:', usuario.endereco_numero, '', '', ''])
        if usuario.endereco_complemento:
            csv_writer.writerow(['Complemento:', usuario.endereco_complemento, '', '', ''])
        csv_writer.writerow(['Bairro:', usuario.endereco_bairro, '', '', ''])
        csv_writer.writerow(['Cidade:', usuario.endereco_cidade, '', '', ''])
        csv_writer.writerow(['Estado:', usuario.endereco_estado, '', '', ''])
    
    # ===== SEÇÃO 2: PEDIDOS =====
    csv_writer.writerow([])
    csv_writer.writerow([])
    csv_writer.writerow(['===== PEDIDOS =====', '', '', '', ''])
    csv_writer.writerow([])
    
    pedidos = Pedido.query.filter_by(usuario_id=usuario.id).all()
    
    if pedidos:
        for idx, pedido in enumerate(pedidos, 1):
            csv_writer.writerow([f'--- PEDIDO #{pedido.id} ---', '', '', '', ''])
            csv_writer.writerow(['Data:', pedido.data.strftime('%Y-%m-%d %H:%M:%S'), '', '', ''])
            csv_writer.writerow(['Status:', pedido.status, '', '', ''])
            csv_writer.writerow(['Total:', f'R$ {float(pedido.total):.2f}', '', '', ''])
            csv_writer.writerow([])
            
            # Itens regulares
            itens_regulares = ItemPedido.query.filter_by(pedido_id=pedido.id).all()
            if itens_regulares:
                csv_writer.writerow(['Produto', 'Quantidade', 'Preço Unitário', 'Subtotal', ''])
                for item in itens_regulares:
                    produto = Produto.query.get(item.produto_id)
                    if produto:
                        csv_writer.writerow([
                            produto.nome,
                            item.quantidade,
                            f'R$ {float(item.preco_unitario):.2f}',
                            f'R$ {float(item.preco_unitario * item.quantidade):.2f}',
                            ''
                        ])
                csv_writer.writerow([])
            
            # Itens personalizados
            itens_personalizados = ItemPedidoPersonalizado.query.filter_by(pedido_id=pedido.id).all()
            if itens_personalizados:
                csv_writer.writerow(['Bolo Personalizado', 'Massa', 'Quantidade', 'Preço Unitário', 'Subtotal'])
                for item in itens_personalizados:
                    bolo = BoloPersonalizado.query.get(item.bolo_personalizado_id)
                    if bolo:
                        csv_writer.writerow([
                            bolo.nome,
                            bolo.massa,
                            item.quantidade,
                            f'R$ {float(item.preco_unitario):.2f}',
                            f'R$ {float(item.preco_unitario * item.quantidade):.2f}'
                        ])
                csv_writer.writerow([])
            
            csv_writer.writerow([])
    else:
        csv_writer.writerow(['Nenhum pedido encontrado', '', '', '', ''])
        csv_writer.writerow([])
    
    # ===== SEÇÃO 3: BOLOS PERSONALIZADOS =====
    csv_writer.writerow([])
    csv_writer.writerow(['===== BOLOS PERSONALIZADOS CRIADOS =====', '', '', '', '', '', '', '', ''])
    csv_writer.writerow([])
    
    bolos = BoloPersonalizado.query.filter_by(usuario_id=usuario.id).all()
    
    if bolos:
        csv_writer.writerow(['ID', 'Nome', 'Massa', 'Recheios', 'Cobertura', 'Finalização', 'Observações', 'Preço', 'Data Criação', 'Ativo'])
        
        for bolo in bolos:
            try:
                recheios = json.loads(bolo.recheios) if bolo.recheios else []
                finalizacao = json.loads(bolo.finalizacao) if bolo.finalizacao else []
            except json.JSONDecodeError:
                recheios = []
                finalizacao = []
            
            csv_writer.writerow([
                bolo.id,
                bolo.nome,
                bolo.massa,
                ', '.join(recheios) if recheios else 'Nenhum',
                bolo.cobertura,
                ', '.join(finalizacao) if finalizacao else 'Nenhuma',
                bolo.observacoes or 'Sem observações',
                f'R$ {float(bolo.preco):.2f}',
                bolo.data_criacao.strftime('%Y-%m-%d %H:%M:%S'),
                'Sim' if bolo.ativo else 'Não'
            ])
    else:
        csv_writer.writerow(['Nenhum bolo personalizado encontrado', '', '', '', '', '', '', '', '', ''])
    
    # Rodapé
    csv_writer.writerow([])
    csv_writer.writerow([])
    csv_writer.writerow(['===== FIM DO RELATÓRIO =====', '', '', '', ''])
    csv_writer.writerow(['Data de Exportação:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), '', '', ''])
    
    # Converter para bytes
    csv_bytes = io.BytesIO()
    csv_bytes.write(csv_buffer.getvalue().encode('utf-8-sig'))
    csv_bytes.seek(0)
    
    try:
        return send_file(
            csv_bytes,
            as_attachment=True,
            download_name=f'dados_doce_sonho_usuario_{usuario.id}.csv',
            mimetype='text/csv'
        )
    except Exception as e:
        flash(f'Erro ao exportar dados: {str(e)}', 'danger')
        return redirect(url_for('user.perfil'))