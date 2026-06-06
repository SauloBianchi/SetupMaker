from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models.avaliacao import Avaliacao, AvaliacaoBuild
from app.models.produto import Produto
from app.models.build import BuildPC

avaliacoes_bp = Blueprint('avaliacoes', __name__, url_prefix='/avaliacoes')


# ── Helpers ──────────────────────────────────────────────────────────────────

def _media_produto(produto_id):
    r = db.session.query(func.avg(Avaliacao.nota), func.count(Avaliacao.id))\
          .filter(Avaliacao.produto_id == produto_id).first()
    return round(float(r[0]), 1) if r[0] else None, r[1] or 0


def _media_build(build_id):
    r = db.session.query(func.avg(AvaliacaoBuild.nota), func.count(AvaliacaoBuild.id))\
          .filter(AvaliacaoBuild.build_id == build_id).first()
    return round(float(r[0]), 1) if r[0] else None, r[1] or 0


def _stars_html(nota):
    """Retorna string com meia-estrela support."""
    if nota is None:
        return '—'
    full  = int(nota)
    half  = 1 if (nota - full) >= 0.4 else 0
    empty = 5 - full - half
    return ('★' * full) + ('½' if half else '') + ('☆' * empty)


# ── Página principal de avaliações / ranking ─────────────────────────────────

@avaliacoes_bp.route('/')
@login_required
def index():
    aba = request.args.get('aba', 'pecas')  # 'pecas', 'builds' ou 'minhas'

    # ── Minhas Avaliações ─────────────────────────────────────────────────
    minhas_pecas  = Avaliacao.query.filter_by(user_id=current_user.id)\
                      .order_by(Avaliacao.criado_em.desc()).all()
    minhas_builds = AvaliacaoBuild.query.filter_by(user_id=current_user.id)\
                      .order_by(AvaliacaoBuild.criado_em.desc()).all()

    # ── Ranking de Peças ──────────────────────────────────────────────────
    # Busca produtos com ao menos 1 avaliação, ordena por média desc
    subq = db.session.query(
        Avaliacao.produto_id,
        func.avg(Avaliacao.nota).label('media'),
        func.count(Avaliacao.id).label('total'),
    ).group_by(Avaliacao.produto_id).subquery()

    ranking_pecas = db.session.query(Produto, subq.c.media, subq.c.total)\
        .join(subq, Produto.id == subq.c.produto_id)\
        .order_by(subq.c.media.desc(), subq.c.total.desc())\
        .limit(50).all()

    # ── Ranking de Builds ─────────────────────────────────────────────────
    subq_b = db.session.query(
        AvaliacaoBuild.build_id,
        func.avg(AvaliacaoBuild.nota).label('media'),
        func.count(AvaliacaoBuild.id).label('total'),
    ).group_by(AvaliacaoBuild.build_id).subquery()

    ranking_builds = db.session.query(BuildPC, subq_b.c.media, subq_b.c.total)\
        .join(subq_b, BuildPC.id == subq_b.c.build_id)\
        .filter(BuildPC.publica == True)\
        .order_by(subq_b.c.media.desc(), subq_b.c.total.desc())\
        .limit(50).all()

    # Avaliação do user atual para highlight
    avaliadas_pelo_user_pecas = {
        a.produto_id for a in current_user.avaliacoes
    }
    avaliadas_pelo_user_builds = {
        a.build_id for a in current_user.avaliacoes_build
    }

    return render_template('avaliacoes/index.html',
        aba=aba,
        ranking_pecas=ranking_pecas,
        ranking_builds=ranking_builds,
        avaliadas_pecas=avaliadas_pelo_user_pecas,
        avaliadas_builds=avaliadas_pelo_user_builds,
        minhas_pecas=minhas_pecas,
        minhas_builds=minhas_builds,
        stars=_stars_html,
    )


# ── Avaliar peça (AJAX) ───────────────────────────────────────────────────────

@avaliacoes_bp.route('/peca/<int:produto_id>', methods=['POST'])
@login_required
def avaliar_peca(produto_id):
    Produto.query.get_or_404(produto_id)
    data = request.get_json()
    nota = int(data.get('nota', 0))
    comentario = data.get('comentario', '').strip()

    if not (1 <= nota <= 5):
        return jsonify({'ok': False, 'erro': 'Nota inválida.'}), 400

    av = Avaliacao.query.filter_by(user_id=current_user.id, produto_id=produto_id).first()
    if av:
        av.nota = nota
        av.comentario = comentario
    else:
        av = Avaliacao(user_id=current_user.id, produto_id=produto_id,
                       nota=nota, comentario=comentario)
        db.session.add(av)
    db.session.commit()

    media, total = _media_produto(produto_id)
    return jsonify({'ok': True, 'media': media, 'total': total,
                    'stars': _stars_html(media)})


# ── Avaliar build (AJAX) ──────────────────────────────────────────────────────

@avaliacoes_bp.route('/build/<int:build_id>', methods=['POST'])
@login_required
def avaliar_build(build_id):
    build = BuildPC.query.get_or_404(build_id)
    if not build.publica and build.user_id != current_user.id:
        return jsonify({'ok': False, 'erro': 'Build não encontrada.'}), 404

    data = request.get_json()
    nota = int(data.get('nota', 0))
    comentario = data.get('comentario', '').strip()

    if not (1 <= nota <= 5):
        return jsonify({'ok': False, 'erro': 'Nota inválida.'}), 400

    av = AvaliacaoBuild.query.filter_by(user_id=current_user.id, build_id=build_id).first()
    if av:
        av.nota = nota
        av.comentario = comentario
    else:
        av = AvaliacaoBuild(user_id=current_user.id, build_id=build_id,
                            nota=nota, comentario=comentario)
        db.session.add(av)
    db.session.commit()

    media, total = _media_build(build_id)
    return jsonify({'ok': True, 'media': media, 'total': total,
                    'stars': _stars_html(media)})


# ── Comentários de uma peça ───────────────────────────────────────────────────

@avaliacoes_bp.route('/peca/<int:produto_id>/comentarios')
@login_required
def comentarios_peca(produto_id):
    avs = Avaliacao.query.filter_by(produto_id=produto_id)\
            .order_by(Avaliacao.criado_em.desc()).limit(20).all()
    return jsonify([{
        'usuario':    av.usuario.username,
        'nota':       av.nota,
        'stars':      _stars_html(av.nota),
        'comentario': av.comentario or '',
        'data':       av.criado_em.strftime('%d/%m/%Y'),
    } for av in avs])


# ── Comentários de uma build ──────────────────────────────────────────────────

@avaliacoes_bp.route('/build/<int:build_id>/comentarios')
@login_required
def comentarios_build(build_id):
    avs = AvaliacaoBuild.query.filter_by(build_id=build_id)\
            .order_by(AvaliacaoBuild.criado_em.desc()).limit(20).all()
    return jsonify([{
        'usuario':    av.usuario.username,
        'nota':       av.nota,
        'stars':      _stars_html(av.nota),
        'comentario': av.comentario or '',
        'data':       av.criado_em.strftime('%d/%m/%Y'),
    } for av in avs])