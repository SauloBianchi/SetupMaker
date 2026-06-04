from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models.produto import Produto, Categoria
from app.models.loja import Preco, Loja
from app.extensions import db
from app.utils.lojas_urls import gerar_urls_busca, config_loja

produtos_bp = Blueprint('produtos', __name__, url_prefix='/pecas')


@produtos_bp.route('/')
@login_required
def listar():
    categorias = Categoria.query.order_by(Categoria.nome).all()

    cat_slug = request.args.get('categoria', '')
    marca    = request.args.get('marca', '')
    busca    = request.args.get('q', '')
    ordem    = request.args.get('ordem', 'nome')

    query = Produto.query

    if cat_slug:
        cat = Categoria.query.filter_by(slug=cat_slug).first()
        if cat:
            query = query.filter(Produto.categoria_id == cat.id)

    if marca:
        query = query.filter(Produto.marca.ilike(f'%{marca}%'))

    if busca:
        query = query.filter(
            Produto.nome.ilike(f'%{busca}%') |
            Produto.marca.ilike(f'%{busca}%')
        )

    produtos = query.all()

    if ordem == 'preco_asc':
        produtos.sort(key=lambda p: p.menor_preco().preco if p.menor_preco() else 99999)
    elif ordem == 'preco_desc':
        produtos.sort(key=lambda p: p.menor_preco().preco if p.menor_preco() else 0, reverse=True)
    elif ordem == 'desempenho':
        produtos.sort(key=lambda p: p.desempenho or 0, reverse=True)
    else:
        produtos.sort(key=lambda p: p.nome)

    marcas = sorted({p.marca for p in Produto.query.all() if p.marca})

    return render_template('produtos/listar.html',
        produtos=produtos,
        categorias=categorias,
        marcas=marcas,
        filtros={'categoria': cat_slug, 'marca': marca, 'q': busca, 'ordem': ordem}
    )


@produtos_bp.route('/<int:produto_id>')
@login_required
def detalhe(produto_id):
    produto   = Produto.query.get_or_404(produto_id)
    todos_precos = sorted(produto.precos, key=lambda p: p.preco)
    precos    = [p for p in todos_precos if p.fonte == 'usuario']
    similares = Produto.query.filter(
        Produto.categoria_id == produto.categoria_id,
        Produto.id != produto.id
    ).limit(4).all()

    urls_lojas      = gerar_urls_busca(produto.nome)
    lojas_com_preco = {pr.loja.nome: pr for pr in precos}
    todas_lojas     = ["Pichau", "KaBuM!", "TerabyteShop", "Amazon BR", "Mercado Livre", "AliExpress"]
    lojas_sem_preco = [l for l in todas_lojas if l not in lojas_com_preco]

    # Intervalo de preços baseado apenas em preços informados por usuários
    if precos:
        valores = [p.preco for p in precos]
        intervalo_usuario = (min(valores), max(valores))
    else:
        intervalo_usuario = None

    return render_template('produtos/detalhe.html',
        produto=produto,
        precos=precos,
        similares=similares,
        urls_lojas=urls_lojas,
        lojas_com_preco=lojas_com_preco,
        lojas_sem_preco=lojas_sem_preco,
        config_loja=config_loja,
        todas_lojas=todas_lojas,
        intervalo_usuario=intervalo_usuario,
    )


@produtos_bp.route('/<int:produto_id>/salvar-preco', methods=['POST'])
@login_required
def salvar_preco(produto_id):
    """Recebe o preço que o usuário encontrou na loja e salva como contribuição."""
    produto    = Produto.query.get_or_404(produto_id)
    data       = request.get_json()
    nome_loja  = data.get('loja', '').strip()
    preco_val  = data.get('preco')
    nome_modelo = data.get('modelo', '').strip()

    if not nome_loja or not preco_val:
        return jsonify({'ok': False, 'erro': 'Loja e preço são obrigatórios.'}), 400

    try:
        preco_val = float(str(preco_val).replace(',', '.').replace('R$', '').strip())
        if preco_val <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'ok': False, 'erro': 'Preço inválido.'}), 400

    # Busca ou cria a loja
    loja = Loja.query.filter(Loja.nome.ilike(f'%{nome_loja}%')).first()
    if not loja:
        loja = Loja(nome=nome_loja, url='#')
        db.session.add(loja)
        db.session.flush()

    # URL de busca do modelo específico se informado
    from app.utils.lojas_urls import gerar_urls_busca
    termo = nome_modelo if nome_modelo else produto.nome
    url   = gerar_urls_busca(termo).get(nome_loja, '#')

    # Atualiza preço se já existe, ou cria novo
    preco_existente = Preco.query.filter_by(
        produto_id=produto.id,
        loja_id=loja.id
    ).first()

    if preco_existente:
        preco_existente.preco       = preco_val
        preco_existente.url_produto = url
        preco_existente.fonte       = 'usuario'
    else:
        db.session.add(Preco(
            produto_id=produto.id,
            loja_id=loja.id,
            preco=preco_val,
            url_produto=url,
            fonte='usuario'
        ))

    db.session.commit()

    return jsonify({
        'ok':    True,
        'loja':  nome_loja,
        'preco': preco_val,
        'msg':   f'Preço R$ {preco_val:.2f} salvo para {nome_loja}!'
    })


@produtos_bp.route('/api/buscar')
@login_required
def api_buscar():
    """Endpoint AJAX para o montador de PC buscar peças por categoria."""
    cat_slug = request.args.get('categoria', '')
    q        = request.args.get('q', '')

    query = Produto.query
    if cat_slug:
        cat = Categoria.query.filter_by(slug=cat_slug).first()
        if cat:
            query = query.filter(Produto.categoria_id == cat.id)
    if q:
        query = query.filter(Produto.nome.ilike(f'%{q}%') | Produto.marca.ilike(f'%{q}%'))

    produtos = query.limit(20).all()
    return jsonify([{
        'id':         p.id,
        'nome':       p.nome,
        'marca':      p.marca,
        'preco':      float(p.menor_preco().preco) if p.menor_preco() else None,
        'desempenho': p.desempenho,
        'consumo':    p.consumo_watts,
        'socket':     p.socket,
        'tipo_ram':   p.tipo_ram,
        'categoria':  p.categoria.slug if p.categoria else '',
    } for p in produtos])


@produtos_bp.route('/<int:produto_id>/lojas')
@login_required
def api_lojas_produto(produto_id):
    """Retorna preços por loja de um produto (apenas preços informados por usuários)."""
    from app.utils.lojas_urls import gerar_urls_busca, config_loja as cfg_loja
    produto = Produto.query.get_or_404(produto_id)
    precos  = [p for p in produto.precos if p.fonte == 'usuario']
    precos  = sorted(precos, key=lambda p: p.preco)
    urls    = gerar_urls_busca(produto.nome)

    lojas_com_preco = [{
        'nome':  pr.loja.nome,
        'preco': float(pr.preco),
        'icon': cfg_loja(pr.loja.nome)['icon'],
        'url':   urls.get(pr.loja.nome, '#'),
    } for pr in precos]

    # Lojas sem preço cadastrado (para poder redirecionar mesmo assim)
    todas = ["Pichau", "KaBuM!", "TerabyteShop", "Amazon BR", "Mercado Livre", "AliExpress"]
    nomes_com = {l['nome'] for l in lojas_com_preco}
    lojas_sem_preco = [{
        'nome':  nome,
        'preco': None,
        'icon': cfg_loja(nome)['icon'],
        'url':   urls.get(nome, '#'),
    } for nome in todas if nome not in nomes_com]

    return jsonify({
        'produto': produto.nome,
        'lojas':   lojas_com_preco + lojas_sem_preco,
    })