from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.build import BuildPC
from app.models.produto import Produto, Categoria
from app.services import compatibilidade, fps_estimator

builds_bp = Blueprint('builds', __name__, url_prefix='/builds')


@builds_bp.route('/publicas')
@login_required
def publicas():
    from sqlalchemy import func
    from app.models.avaliacao import AvaliacaoBuild

    ordenar = request.args.get('ordenar', 'recentes')
    pagina  = int(request.args.get('pagina', 1))
    por_pag = 12

    # Subquery de média de avaliação por build
    subq = db.session.query(
        AvaliacaoBuild.build_id,
        func.avg(AvaliacaoBuild.nota).label('media'),
        func.count(AvaliacaoBuild.id).label('total'),
    ).group_by(AvaliacaoBuild.build_id).subquery()

    q = db.session.query(BuildPC, subq.c.media, subq.c.total)\
        .outerjoin(subq, BuildPC.id == subq.c.build_id)\
        .filter(BuildPC.publica == True)

    if ordenar == 'avaliacao':
        q = q.order_by(subq.c.media.desc().nullslast(), subq.c.total.desc().nullslast())
    elif ordenar == 'preco_asc':
        q = q.order_by(BuildPC.id)   # fallback; preço real exige cálculo em Python
    elif ordenar == 'preco_desc':
        q = q.order_by(BuildPC.id.desc())
    else:
        q = q.order_by(BuildPC.criado_em.desc())

    total_count = q.count()
    builds = q.offset((pagina - 1) * por_pag).limit(por_pag).all()

    return render_template('builds/publicas.html',
        builds=builds,
        total=total_count,
        ordenar=ordenar,
        pagina=pagina,
        has_next=(pagina * por_pag) < total_count,
    )

@builds_bp.route('/listar')
@login_required
def listar():
    builds = BuildPC.query.filter_by(user_id=current_user.id)\
                    .order_by(BuildPC.criado_em.desc()).all()
    return render_template('builds/listar.html', builds=builds)


@builds_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    categorias = Categoria.query.order_by(Categoria.nome).all()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        if not nome:
            flash('Dê um nome para a build.', 'danger')
            return redirect(url_for('builds.nova'))

        def pid(campo):
            val = request.form.get(campo, '')
            return int(val) if val.isdigit() else None

        def loja(campo):
            return request.form.get(campo, '').strip() or None

        build = BuildPC(
            user_id      = current_user.id,
            nome         = nome,
            publica      = bool(request.form.get('publica')),
            cpu_id       = pid('cpu_id'),
            gpu_id       = pid('gpu_id'),
            ram_id       = pid('ram_id'),
            ram_quantidade = int(request.form.get('ram_quantidade') or 2),
            motherboard_id = pid('motherboard_id'),
            storage_id   = pid('storage_id'),
            fonte_id     = pid('fonte_id'),
            gabinete_id  = pid('gabinete_id'),
            cooler_id    = pid('cooler_id'),
            cpu_loja         = loja('cpu_loja'),
            gpu_loja         = loja('gpu_loja'),
            ram_loja         = loja('ram_loja'),
            motherboard_loja = loja('motherboard_loja'),
            storage_loja     = loja('storage_loja'),
            fonte_loja       = loja('fonte_loja'),
            gabinete_loja    = loja('gabinete_loja'),
            cooler_loja      = loja('cooler_loja'),
        )
        db.session.add(build)
        db.session.commit()
        flash('Build salva com sucesso! ✅', 'success')
        return redirect(url_for('builds.detalhe', build_id=build.id))

    return render_template('builds/montador.html', categorias=categorias)


@builds_bp.route('/<int:build_id>')
@login_required
def detalhe(build_id):
    build = BuildPC.query.get_or_404(build_id)

    if build.user_id != current_user.id and not build.publica:
        flash('Você não tem acesso a esta build.', 'danger')
        return redirect(url_for('builds.listar'))

    erros_compat = compatibilidade.verificar(build)
    status_compat = compatibilidade.status(erros_compat)
    fps_data      = fps_estimator.estimar(build)
    energia       = fps_estimator.consumo_mensal_kwh(build)

    # Comparação de preços por loja (total da build em cada loja)
    comparacao_lojas = _comparar_lojas(build)

    return render_template('builds/detalhe.html',
        build=build,
        erros_compat=erros_compat,
        status_compat=status_compat,
        fps_data=fps_data,
        energia=energia,
        comparacao_lojas=comparacao_lojas,
    )


@builds_bp.route('/<int:build_id>/deletar', methods=['POST'])
@login_required
def deletar(build_id):
    build = BuildPC.query.get_or_404(build_id)
    if build.user_id != current_user.id:
        flash('Ação não permitida.', 'danger')
        return redirect(url_for('builds.listar'))
    db.session.delete(build)
    db.session.commit()
    flash('Build deletada.', 'info')
    return redirect(url_for('builds.listar'))


@builds_bp.route('/api/compatibilidade', methods=['POST'])
@login_required
def api_compatibilidade():
    """Verificação de compatibilidade em tempo real (AJAX)."""
    data = request.get_json()

    # Monta objeto temporário (sem salvar no banco)
    class FakeBuild:
        pass
    fake = FakeBuild()

    def get_prod(field):
        pid = data.get(field)
        return Produto.query.get(int(pid)) if pid else None

    fake.cpu        = get_prod('cpu_id')
    fake.motherboard = get_prod('motherboard_id')
    fake.ram        = get_prod('ram_id')
    fake.gpu        = get_prod('gpu_id')
    fake.fonte      = get_prod('fonte_id')
    fake.storage = get_prod('storage_id')
    fake.gabinete = get_prod('gabinete_id')
    fake.consumo_total = lambda: sum(
        (p.consumo_watts or 0)
        for p in [fake.cpu, fake.gpu, fake.ram, fake.motherboard, fake.fonte]
        if p
    )

    erros  = compatibilidade.verificar(fake)
    status = compatibilidade.status(erros)
    fps    = fps_estimator.estimar(fake)
    consumo_total = fake.consumo_total()

    return jsonify({
        'compativel': status['ok'],
        'label':      status['label'],
        'icon':       status['icon'],
        'cor':        status.get('color', status.get('cor', '#64748b')),
        'erros':      erros,
        'fps':        fps,
        'consumo_watts': consumo_total,
    })


def _comparar_lojas(build) -> list[dict]:
    """Calcula o total da build para cada loja (usando menor preço disponível)."""
    from app.models.loja import Loja, Preco
    from collections import defaultdict

    pecas = [build.cpu, build.gpu, build.ram, build.motherboard,
             build.storage, build.fonte, build.gabinete, build.cooler]
    pecas = [p for p in pecas if p]

    lojas = Loja.query.all()
    resultado = []

    for loja in lojas:
        total = 0
        cobertura = 0
        for peca in pecas:
            preco_obj = Preco.query.filter_by(produto_id=peca.id, loja_id=loja.id).first()
            if preco_obj:
                total += preco_obj.preco
                cobertura += 1

        if cobertura > 0:
            resultado.append({
                'loja':      loja.nome,
                'total':     round(total, 2),
                'cobertura': cobertura,
                'total_pecas': len(pecas),
            })

    resultado.sort(key=lambda x: x['total'])
    return resultado