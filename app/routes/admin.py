from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.produto import Produto, Categoria
from app.models.build import BuildPC
from app.models.loja import Loja, Preco

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ── Proteção: só admins ───────────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash('Acesso restrito a administradores.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ─────────────────────────────────────────────────────────────────
@admin_bp.route('/')
@admin_required
def index():
    total_users    = User.query.count()
    total_produtos = Produto.query.count()
    total_builds   = BuildPC.query.count()
    total_lojas    = Loja.query.count()
    total_precos   = Preco.query.count()

    usuarios_recentes = User.query.order_by(User.criado_em.desc()).limit(5).all()
    builds_recentes   = BuildPC.query.order_by(BuildPC.criado_em.desc()).limit(5).all()

    return render_template('admin/index.html',
        total_users=total_users,
        total_produtos=total_produtos,
        total_builds=total_builds,
        total_lojas=total_lojas,
        total_precos=total_precos,
        usuarios_recentes=usuarios_recentes,
        builds_recentes=builds_recentes,
    )


# ══════════════════════════════════════════════════════════════════════════════
# USUÁRIOS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/usuarios')
@admin_required
def usuarios():
    busca = request.args.get('q', '')
    query = User.query
    if busca:
        query = query.filter(
            User.username.ilike(f'%{busca}%') |
            User.email.ilike(f'%{busca}%')
        )
    users = query.order_by(User.criado_em.desc()).all()
    return render_template('admin/usuarios.html', users=users, busca=busca)


@admin_bp.route('/usuarios/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode alterar sua própria permissão de admin.', 'warning')
        return redirect(url_for('admin.usuarios'))
    user.is_admin = not user.is_admin
    db.session.commit()
    acao = 'promovido a admin' if user.is_admin else 'removido do admin'
    flash(f'{user.username} foi {acao}.', 'success')
    return redirect(url_for('admin.usuarios'))


@admin_bp.route('/usuarios/<int:user_id>/toggle-verificado', methods=['POST'])
@admin_required
def toggle_verificado(user_id):
    user = User.query.get_or_404(user_id)
    user.email_verificado = not user.email_verificado
    db.session.commit()
    status = 'verificado' if user.email_verificado else 'não verificado'
    flash(f'E-mail de {user.username} marcado como {status}.', 'success')
    return redirect(url_for('admin.usuarios'))


@admin_bp.route('/usuarios/<int:user_id>/deletar', methods=['POST'])
@admin_required
def deletar_usuario(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode deletar sua própria conta pelo painel.', 'danger')
        return redirect(url_for('admin.usuarios'))
    # Remove builds do usuário antes
    BuildPC.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f'Usuário {user.username} deletado.', 'info')
    return redirect(url_for('admin.usuarios'))


# ══════════════════════════════════════════════════════════════════════════════
# PRODUTOS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/produtos')
@admin_required
def produtos():
    busca    = request.args.get('q', '')
    cat_slug = request.args.get('categoria', '')
    categorias = Categoria.query.order_by(Categoria.nome).all()

    query = Produto.query
    if busca:
        query = query.filter(
            Produto.nome.ilike(f'%{busca}%') |
            Produto.marca.ilike(f'%{busca}%')
        )
    if cat_slug:
        cat = Categoria.query.filter_by(slug=cat_slug).first()
        if cat:
            query = query.filter(Produto.categoria_id == cat.id)

    produtos = query.order_by(Produto.categoria_id, Produto.nome).all()
    return render_template('admin/produtos.html',
        produtos=produtos, categorias=categorias,
        busca=busca, cat_slug=cat_slug
    )


@admin_bp.route('/produtos/novo', methods=['GET', 'POST'])
@admin_required
def produto_novo():
    categorias = Categoria.query.order_by(Categoria.nome).all()
    lojas      = Loja.query.order_by(Loja.nome).all()

    if request.method == 'POST':
        nome     = request.form.get('nome', '').strip()
        marca    = request.form.get('marca', '').strip()
        cat_id   = request.form.get('categoria_id', type=int)
        descricao= request.form.get('descricao', '').strip()
        imagem   = request.form.get('imagem_url', '').strip()
        socket   = request.form.get('socket', '').strip() or None
        tipo_ram = request.form.get('tipo_ram', '').strip() or None
        consumo  = request.form.get('consumo_watts', type=int)
        desempenho = request.form.get('desempenho', type=int)
        frequencia = request.form.get('frequencia', '').strip() or None
        capacidade = request.form.get('capacidade', '').strip() or None

        if not nome or not cat_id:
            flash('Nome e categoria são obrigatórios.', 'danger')
            return render_template('admin/produto_form.html',
                categorias=categorias, lojas=lojas, produto=None)

        produto = Produto(
            nome=nome, marca=marca, categoria_id=cat_id,
            descricao=descricao, imagem_url=imagem or None,
            socket=socket, tipo_ram=tipo_ram,
            consumo_watts=consumo, desempenho=desempenho,
            frequencia=frequencia, capacidade=capacidade,
        )
        db.session.add(produto)
        db.session.flush()

        # Preços por loja
        for loja in lojas:
            val = request.form.get(f'preco_{loja.id}', '').strip()
            if val:
                try:
                    preco_val = float(val.replace(',', '.'))
                    db.session.add(Preco(
                        produto_id=produto.id,
                        loja_id=loja.id,
                        preco=preco_val,
                        fonte='admin'
                    ))
                except ValueError:
                    pass

        db.session.commit()
        flash(f'Produto "{nome}" criado com sucesso!', 'success')
        return redirect(url_for('admin.produtos'))

    return render_template('admin/produto_form.html',
        categorias=categorias, lojas=lojas, produto=None)


@admin_bp.route('/produtos/<int:produto_id>/editar', methods=['GET', 'POST'])
@admin_required
def produto_editar(produto_id):
    produto    = Produto.query.get_or_404(produto_id)
    categorias = Categoria.query.order_by(Categoria.nome).all()
    lojas      = Loja.query.order_by(Loja.nome).all()

    if request.method == 'POST':
        produto.nome        = request.form.get('nome', '').strip()
        produto.marca       = request.form.get('marca', '').strip()
        produto.categoria_id= request.form.get('categoria_id', type=int)
        produto.descricao   = request.form.get('descricao', '').strip()
        produto.imagem_url  = request.form.get('imagem_url', '').strip() or None
        produto.socket      = request.form.get('socket', '').strip() or None
        produto.tipo_ram    = request.form.get('tipo_ram', '').strip() or None
        produto.consumo_watts = request.form.get('consumo_watts', type=int)
        produto.desempenho  = request.form.get('desempenho', type=int)
        produto.frequencia  = request.form.get('frequencia', '').strip() or None
        produto.capacidade  = request.form.get('capacidade', '').strip() or None

        # Atualiza preços
        for loja in lojas:
            val = request.form.get(f'preco_{loja.id}', '').strip()
            preco_obj = Preco.query.filter_by(
                produto_id=produto.id, loja_id=loja.id).first()
            if val:
                try:
                    preco_val = float(val.replace(',', '.'))
                    if preco_obj:
                        preco_obj.preco = preco_val
                    else:
                        db.session.add(Preco(
                            produto_id=produto.id,
                            loja_id=loja.id,
                            preco=preco_val,
                            fonte='admin'
                        ))
                except ValueError:
                    pass
            elif preco_obj:
                db.session.delete(preco_obj)

        db.session.commit()
        flash(f'Produto "{produto.nome}" atualizado!', 'success')
        return redirect(url_for('admin.produtos'))

    # Monta dict loja_id → preco para preencher o form
    precos_dict = {p.loja_id: p.preco for p in produto.precos}
    return render_template('admin/produto_form.html',
        produto=produto, categorias=categorias,
        lojas=lojas, precos_dict=precos_dict)


@admin_bp.route('/produtos/<int:produto_id>/deletar', methods=['POST'])
@admin_required
def produto_deletar(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    Preco.query.filter_by(produto_id=produto.id).delete()
    db.session.delete(produto)
    db.session.commit()
    flash(f'Produto "{produto.nome}" deletado.', 'info')
    return redirect(url_for('admin.produtos'))


# ══════════════════════════════════════════════════════════════════════════════
# BUILDS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/builds')
@admin_required
def builds():
    busca = request.args.get('q', '')
    query = BuildPC.query
    if busca:
        query = query.join(User).filter(
            BuildPC.nome.ilike(f'%{busca}%') |
            User.username.ilike(f'%{busca}%')
        )
    builds = query.order_by(BuildPC.criado_em.desc()).all()
    return render_template('admin/builds.html', builds=builds, busca=busca)


@admin_bp.route('/builds/nova', methods=['GET', 'POST'])
@admin_required
def build_nova():
    usuarios   = User.query.order_by(User.username).all()
    categorias = Categoria.query.order_by(Categoria.nome).all()
    produtos_por_cat = {}
    for cat in categorias:
        produtos_por_cat[cat.slug] = Produto.query.filter_by(
            categoria_id=cat.id).order_by(Produto.nome).all()

    if request.method == 'POST':
        nome    = request.form.get('nome', '').strip()
        user_id = request.form.get('user_id', type=int)
        publica = bool(request.form.get('publica'))

        if not nome or not user_id:
            flash('Nome e usuário são obrigatórios.', 'danger')
            return render_template('admin/build_form.html',
                build=None, usuarios=usuarios,
                produtos_por_cat=produtos_por_cat)

        def pid(campo):
            v = request.form.get(campo, '')
            return int(v) if v and v.isdigit() else None

        build = BuildPC(
            user_id=user_id, nome=nome, publica=publica,
            cpu_id=pid('cpu_id'), gpu_id=pid('gpu_id'),
            ram_id=pid('ram_id'), motherboard_id=pid('motherboard_id'),
            storage_id=pid('storage_id'), fonte_id=pid('fonte_id'),
            gabinete_id=pid('gabinete_id'), cooler_id=pid('cooler_id'),
            ram_quantidade=request.form.get('ram_quantidade', 2, type=int),
        )
        db.session.add(build)
        db.session.commit()
        flash(f'Build "{nome}" criada com sucesso!', 'success')
        return redirect(url_for('admin.builds'))

    return render_template('admin/build_form.html',
        build=None, usuarios=usuarios,
        produtos_por_cat=produtos_por_cat)


@admin_bp.route('/builds/<int:build_id>/editar', methods=['GET', 'POST'])
@admin_required
def build_editar(build_id):
    build      = BuildPC.query.get_or_404(build_id)
    usuarios   = User.query.order_by(User.username).all()
    categorias = Categoria.query.order_by(Categoria.nome).all()
    produtos_por_cat = {}
    for cat in categorias:
        produtos_por_cat[cat.slug] = Produto.query.filter_by(
            categoria_id=cat.id).order_by(Produto.nome).all()

    if request.method == 'POST':
        build.nome    = request.form.get('nome', '').strip()
        build.user_id = request.form.get('user_id', type=int)
        build.publica = bool(request.form.get('publica'))

        def pid(campo):
            v = request.form.get(campo, '')
            return int(v) if v and v.isdigit() else None

        build.cpu_id         = pid('cpu_id')
        build.gpu_id         = pid('gpu_id')
        build.ram_id         = pid('ram_id')
        build.motherboard_id = pid('motherboard_id')
        build.storage_id     = pid('storage_id')
        build.fonte_id       = pid('fonte_id')
        build.gabinete_id    = pid('gabinete_id')
        build.cooler_id      = pid('cooler_id')
        build.ram_quantidade = request.form.get('ram_quantidade', 2, type=int)

        db.session.commit()
        flash(f'Build "{build.nome}" atualizada!', 'success')
        return redirect(url_for('admin.builds'))

    return render_template('admin/build_form.html',
        build=build, usuarios=usuarios,
        produtos_por_cat=produtos_por_cat)


@admin_bp.route('/builds/<int:build_id>/toggle-publica', methods=['POST'])
@admin_required
def build_toggle_publica(build_id):
    build = BuildPC.query.get_or_404(build_id)
    build.publica = not build.publica
    db.session.commit()
    status = 'pública' if build.publica else 'privada'
    flash(f'Build "{build.nome}" agora é {status}.', 'success')
    return redirect(url_for('admin.builds'))


@admin_bp.route('/builds/<int:build_id>/deletar', methods=['POST'])
@admin_required
def build_deletar(build_id):
    build = BuildPC.query.get_or_404(build_id)
    nome  = build.nome
    db.session.delete(build)
    db.session.commit()
    flash(f'Build "{nome}" deletada.', 'info')
    return redirect(url_for('admin.builds'))
