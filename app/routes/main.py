from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models.produto import Produto, Categoria
from app.models.build import BuildPC

main = Blueprint('main', __name__)


@main.route('/')
@login_required
def index():
    total_produtos = Produto.query.count()
    total_builds   = BuildPC.query.count()
    categorias     = Categoria.query.all()
    destaques      = Produto.query.order_by(Produto.desempenho.desc()).limit(8).all() # quantidade de produtos em destaque
    builds_pub     = BuildPC.query.filter_by(publica=True).order_by(BuildPC.criado_em.desc()).limit(3).all()

    return render_template('main/index.html',
        total_produtos=total_produtos,
        total_builds=total_builds,
        categorias=categorias,
        destaques=destaques,
        builds_pub=builds_pub,
    )


@main.route('/comparar')
@login_required
def comparar():
    from app.utils.lojas_urls import LOJAS_CONFIG, gerar_urls_busca

    categorias = Categoria.query.order_by(Categoria.nome).all()
    cat_slug   = request.args.get('categoria', '')
    busca      = request.args.get('q', '').strip()

    query = Produto.query
    if cat_slug:
        cat = Categoria.query.filter_by(slug=cat_slug).first()
        if cat:
            query = query.filter(Produto.categoria_id == cat.id)
    if busca:
        query = query.filter(
            Produto.nome.ilike(f'%{busca}%') |
            Produto.marca.ilike(f'%{busca}%')
        )

    produtos = query.order_by(Produto.nome).all()

    # Monta tabela: apenas produtos com ao menos 1 preço informado por usuário
    todas_lojas = list(LOJAS_CONFIG.keys())
    tabela = []
    for p in produtos:
        precos_usuario = {pr.loja.nome: pr for pr in p.precos if pr.fonte == 'usuario'}
        if not precos_usuario:
            continue
        linha = {
            'produto': p,
            'urls':    gerar_urls_busca(p.nome),
            'precos':  precos_usuario,
            'menor':   min(precos_usuario.values(), key=lambda pr: pr.preco),
        }
        tabela.append(linha)

    tabela.sort(key=lambda x: x['produto'].nome)

    return render_template('main/comparar.html',
        tabela=tabela,
        todas_lojas=todas_lojas,
        lojas_config=LOJAS_CONFIG,
        categorias=categorias,
        filtros={'categoria': cat_slug, 'q': busca},
    )
