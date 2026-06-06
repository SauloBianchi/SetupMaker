from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import timedelta
from app.models import User
from app.extensions import db

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/docs')
@login_required
def docs():
    """Página de documentação interativa da API."""
    return render_template('api/docs.html')


# ── Helpers ───────────────────────────────────────────────────────────────────

def _produto_json(p):
    return {
        'id':           p.id,
        'nome':         p.nome,
        'marca':        p.marca,
        'categoria':    p.categoria.nome if p.categoria else None,
        'socket':       p.socket,
        'tipo_ram':     p.tipo_ram,
        'consumo_watts':p.consumo_watts,
        'desempenho':   p.desempenho,
        'menor_preco':  float(p.menor_preco().preco) if p.menor_preco() else None,
    }

def _build_json(b):
    return {
        'id':           b.id,
        'nome':         b.nome,
        'publica':      b.publica,
        'preco_total':  b.preco_total(),
        'consumo_watts':b.consumo_total(),
        'criado_em':    b.criado_em.isoformat(),
        'componentes': {
            'cpu':         b.cpu.nome        if b.cpu        else None,
            'gpu':         b.gpu.nome        if b.gpu        else None,
            'ram':         b.ram.nome        if b.ram        else None,
            'ram_qtd':     b.ram_quantidade,
            'motherboard': b.motherboard.nome if b.motherboard else None,
            'storage':     b.storage.nome    if b.storage    else None,
            'fonte':       b.fonte.nome      if b.fonte      else None,
            'gabinete':    b.gabinete.nome   if b.gabinete   else None,
            'cooler':      b.cooler.nome     if b.cooler     else None,
        }
    }


# ── AUTH ──────────────────────────────────────────────────────────────────────

@api.route('/auth/login', methods=['POST'])
def api_login():
    """
    Autentica o usuário e retorna um JWT de acesso e um de refresh.

    Body JSON:
        { "email": "...", "password": "..." }

    Retorna:
        access_token  — válido por 1 hora
        refresh_token — válido por 30 dias
    """
    data = request.get_json(silent=True) or {}

    if not data.get('email') or not data.get('password'):
        return jsonify({'erro': 'E-mail e senha são obrigatórios.'}), 400

    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'erro': 'Credenciais inválidas.'}), 401

    access_token  = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(hours=1)
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        expires_delta=timedelta(days=30)
    )

    return jsonify({
        'access_token':  access_token,
        'refresh_token': refresh_token,
        'token_type':    'Bearer',
        'expires_in':    3600,
        'usuario': {
            'id':       user.id,
            'username': user.username,
            'email':    user.email,
            'is_admin': user.is_admin,
        }
    }), 200


@api.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def api_refresh():
    """Gera um novo access_token usando o refresh_token."""
    user_id      = get_jwt_identity()
    access_token = create_access_token(
        identity=user_id,
        expires_delta=timedelta(hours=1)
    )
    return jsonify({'access_token': access_token, 'token_type': 'Bearer'}), 200


@api.route('/auth/me', methods=['GET'])
@jwt_required()
def api_me():
    """Retorna os dados do usuário autenticado pelo JWT."""
    user_id = get_jwt_identity()
    user    = User.query.get(int(user_id))
    if not user:
        return jsonify({'erro': 'Usuário não encontrado.'}), 404

    return jsonify({
        'id':        user.id,
        'username':  user.username,
        'email':     user.email,
        'is_admin':  user.is_admin,
        'criado_em': user.criado_em.isoformat(),
    }), 200


# ── PRODUTOS ──────────────────────────────────────────────────────────────────

@api.route('/produtos', methods=['GET'])
@jwt_required()
def api_produtos():
    """
    Lista produtos com filtros opcionais.

    Query params:
        categoria — slug da categoria (ex: cpu, gpu)
        q         — busca por nome ou marca
        limit     — máximo de resultados (padrão 50)
    """
    from app.models import Produto, Categoria

    categoria_slug = request.args.get('categoria', '')
    busca          = request.args.get('q', '').strip()
    limit          = min(int(request.args.get('limit', 50)), 200)

    query = Produto.query
    if categoria_slug:
        cat = Categoria.query.filter_by(slug=categoria_slug).first()
        if cat:
            query = query.filter(Produto.categoria_id == cat.id)
    if busca:
        query = query.filter(
            Produto.nome.ilike(f'%{busca}%') |
            Produto.marca.ilike(f'%{busca}%')
        )

    produtos = query.order_by(Produto.nome).limit(limit).all()
    return jsonify({
        'total':    len(produtos),
        'produtos': [_produto_json(p) for p in produtos],
    }), 200


@api.route('/produtos/<int:produto_id>', methods=['GET'])
@jwt_required()
def api_produto_detalhe(produto_id):
    """Retorna detalhes completos de um produto, incluindo preços por loja."""
    from app.models import Produto
    produto = Produto.query.get_or_404(produto_id)

    precos = [{
        'loja':  pr.loja.nome,
        'preco': float(pr.preco),
        'fonte': pr.fonte,
    } for pr in sorted(produto.precos, key=lambda x: x.preco)]

    return jsonify({
        **_produto_json(produto),
        'precos_por_loja': precos,
    }), 200


@api.route('/produtos/<int:produto_id>/precos', methods=['GET'])
@jwt_required()
def api_comparador(produto_id):
    """Comparação de preços de um produto entre todas as lojas."""
    from app.models import Produto
    produto = Produto.query.get_or_404(produto_id)

    precos = [{
        'loja':  pr.loja.nome,
        'preco': float(pr.preco),
        'fonte': pr.fonte,
    } for pr in sorted(produto.precos, key=lambda x: x.preco)]

    return jsonify({
        'produto':      produto.nome,
        'precos':       precos,
        'menor_preco':  precos[0]  if precos else None,
        'maior_preco':  precos[-1] if precos else None,
        'economia_max': round(precos[-1]['preco'] - precos[0]['preco'], 2) if len(precos) > 1 else 0,
    }), 200


# ── BUILDS ────────────────────────────────────────────────────────────────────

@api.route('/builds', methods=['GET'])
@jwt_required()
def api_builds():
    """Lista as builds do usuário autenticado."""
    from app.models import BuildPC
    user_id = get_jwt_identity()
    builds  = BuildPC.query.filter_by(user_id=int(user_id))\
                     .order_by(BuildPC.criado_em.desc()).all()

    return jsonify({
        'total':  len(builds),
        'builds': [_build_json(b) for b in builds],
    }), 200


@api.route('/builds/<int:build_id>', methods=['GET'])
@jwt_required()
def api_build_detalhe(build_id):
    """Retorna detalhes de uma build (própria ou pública)."""
    from app.models import BuildPC
    user_id = int(get_jwt_identity())
    build   = BuildPC.query.get_or_404(build_id)

    if build.user_id != user_id and not build.publica:
        return jsonify({'erro': 'Acesso negado.'}), 403

    return jsonify(_build_json(build)), 200


@api.route('/builds/publicas', methods=['GET'])
@jwt_required()
def api_builds_publicas():
    """Lista todas as builds públicas."""
    from app.models import BuildPC
    limit  = min(int(request.args.get('limit', 20)), 100)
    builds = BuildPC.query.filter_by(publica=True)\
                    .order_by(BuildPC.criado_em.desc()).limit(limit).all()

    return jsonify({
        'total':  len(builds),
        'builds': [_build_json(b) for b in builds],
    }), 200


# ── AVALIAÇÕES ────────────────────────────────────────────────────────────────

@api.route('/avaliacoes/produtos', methods=['GET'])
@jwt_required()
def api_ranking_produtos():
    """Ranking dos produtos mais bem avaliados."""
    from sqlalchemy import func
    from app.models import Produto
    from app.models.avaliacao import Avaliacao

    resultados = db.session.query(
        Produto,
        func.avg(Avaliacao.nota).label('media'),
        func.count(Avaliacao.id).label('total'),
    ).join(Avaliacao, Produto.id == Avaliacao.produto_id)\
     .group_by(Produto.id)\
     .order_by(func.avg(Avaliacao.nota).desc())\
     .limit(20).all()

    return jsonify([{
        'produto': _produto_json(p),
        'media':   round(float(m), 1),
        'total_avaliacoes': t,
    } for p, m, t in resultados]), 200


@api.route('/avaliacoes/builds', methods=['GET'])
@jwt_required()
def api_ranking_builds():
    """Ranking das builds públicas mais bem avaliadas."""
    from sqlalchemy import func
    from app.models import BuildPC
    from app.models.avaliacao import AvaliacaoBuild

    resultados = db.session.query(
        BuildPC,
        func.avg(AvaliacaoBuild.nota).label('media'),
        func.count(AvaliacaoBuild.id).label('total'),
    ).join(AvaliacaoBuild, BuildPC.id == AvaliacaoBuild.build_id)\
     .filter(BuildPC.publica == True)\
     .group_by(BuildPC.id)\
     .order_by(func.avg(AvaliacaoBuild.nota).desc())\
     .limit(20).all()

    return jsonify([{
        'build': _build_json(b),
        'media': round(float(m), 1),
        'total_avaliacoes': t,
    } for b, m, t in resultados]), 200


# ── COMPATIBILIDADE ───────────────────────────────────────────────────────────

@api.route('/compatibilidade', methods=['POST'])
@jwt_required()
def api_compatibilidade():
    """
    Verifica compatibilidade de uma build via API.

    Body JSON:
        { "build_id": 1 }
    """
    from app.models import BuildPC
    from app.services import compatibilidade as compat

    user_id = int(get_jwt_identity())
    data    = request.get_json(silent=True) or {}
    build_id = data.get('build_id')

    if not build_id:
        return jsonify({'erro': 'build_id é obrigatório.'}), 400

    build = BuildPC.query.get_or_404(build_id)
    if build.user_id != user_id and not build.publica:
        return jsonify({'erro': 'Acesso negado.'}), 403

    erros  = compat.verificar(build)
    status = compat.status(erros)

    return jsonify({
        'compativel': status['ok'],
        'label':      status['label'],
        'erros':      erros,
    }), 200