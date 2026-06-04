import random
import re
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, mail
from app.models import User
from flask_mail import Message

auth = Blueprint('auth', __name__)


def senha_forte(senha):
    if len(senha) < 8:
        return False, 'A senha deve ter pelo menos 8 caracteres.'
    if not re.search(r'[A-Z]', senha):
        return False, 'A senha deve ter pelo menos uma letra maiúscula.'
    if not re.search(r'[0-9]', senha):
        return False, 'A senha deve ter pelo menos um número.'
    return True, ''


def enviar_codigo(user, assunto, tipo):
    """Gera e envia código de 6 dígitos por e-mail. tipo: 'verificacao' ou '2fa'"""
    codigo = str(random.randint(100000, 999999))
    user.codigo_login = codigo
    db.session.commit()
    try:
        msg = Message(subject=assunto, recipients=[user.email])
        msg.html = f'''
        <div style="background:#0a0f1e;padding:40px 20px;font-family:Arial,sans-serif;">
        <div style="max-width:440px;margin:0 auto;background:#0f172a;border:1px solid #1e2d4a;
                    border-radius:16px;overflow:hidden;">

            <!-- Header com logo -->
            <div style="background:linear-gradient(135deg,#0d1b2e,#1a2f4e);
                        padding:28px 32px;border-bottom:1px solid #1e2d4a;
                        display:flex;align-items:center;gap:14px;">
            <img src="https://raw.githubusercontent.com/SauloBianchi/SetupMaker/main/app/static/img/logo.png"
                alt="SetupMaker"
                style="height:40px;width:auto;object-fit:contain;display:block;margin:0 auto;"
                onerror="this.style.display='none'">
            </div>

            <!-- Corpo -->
            <div style="padding:28px 32px;">
            <p style="color:#94a3b8;font-size:14px;margin-bottom:8px;">
                Olá, <strong style="color:#e2e8f0;">{user.username}</strong>!
            </p>
            <p style="color:#94a3b8;font-size:14px;margin-bottom:20px;">
                {"Confirme seu e-mail com o código abaixo:" if tipo == "verificacao" else "Seu código de acesso é:"}
            </p>

            <!-- Código -->
            <div style="background:#131d35;border:2px solid #3b82f6;border-radius:12px;
                        padding:24px;text-align:center;margin-bottom:20px;">
                <div style="font-size:11px;color:#64748b;text-transform:uppercase;
                            letter-spacing:2px;margin-bottom:8px;">Seu código</div>
                <span style="font-size:40px;font-weight:700;color:#3b82f6;
                            letter-spacing:10px;font-family:monospace;">{codigo}</span>
            </div>

            <p style="color:#475569;font-size:12px;line-height:1.6;margin:0;">
                Este código expira em 10 minutos.<br>
                Se não foi você, ignore este e-mail com segurança.
            </p>
            </div>

            <!-- Footer -->
            <div style="padding:16px 32px;border-top:1px solid #1e2d4a;text-align:center;">
            <p style="color:#334155;font-size:11px;margin:0;">
                © 2025 SetupMaker — Monte, compare e economize.
            </p>
            </div>
        </div>
        </div>
        '''
        mail.send(msg)
        return True
    except Exception:
        flash(f'[DEV] Código: {codigo}', 'info')
        return False


# ── Registro ──────────────────────────────────────────────────────────────────
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':

        # Etapa 2 — verificar token de e-mail
        if 'verificar_email' in request.form:
            codigo    = request.form.get('codigo', '').strip()
            user_id   = session.get('pending_register_id')

            if not user_id:
                flash('Sessão expirada. Tente se cadastrar novamente.', 'danger')
                return redirect(url_for('auth.register'))

            user = User.query.get(user_id)

            if not user:
                flash('Usuário não encontrado.', 'danger')
                return redirect(url_for('auth.register'))

            if user.codigo_login == codigo:
                user.codigo_login = None
                user.email_verificado = True
                db.session.commit()
                session.pop('pending_register_id', None)
                flash('E-mail verificado! Faça login para continuar.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Código incorreto. Tente novamente.', 'danger')
                return render_template('auth/verificar_email.html')

        # Etapa 1 — criar conta e enviar código
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        valida, msg = senha_forte(password)
        if not valida:
            flash(msg, 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Este nome de usuário já está em uso.', 'danger')
            return render_template('auth/register.html')

        # Cria usuário ainda não verificado
        user = User(username=username, email=email, email_verificado=False)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        enviar_codigo(user, 'Confirme seu e-mail — SetupMaker', 'verificacao')
        session['pending_register_id'] = user.id
        flash('Enviamos um código de verificação para seu e-mail.', 'info')
        return render_template('auth/verificar_email.html')

    return render_template('auth/register.html')


# ── Login (com 2FA) ────────────────────────────────────────────────────────────
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':

        # Etapa 2 — verificar código 2FA
        if 'verificar_codigo' in request.form:
            codigo  = request.form.get('codigo', '').strip()
            user_id = session.get('pending_user_id')

            if not user_id:
                flash('Sessão expirada. Faça login novamente.', 'danger')
                return redirect(url_for('auth.login'))

            user = User.query.get(user_id)

            if user and user.codigo_login == codigo:
                user.codigo_login = None
                db.session.commit()
                session.pop('pending_user_id', None)
                login_user(user)
                flash(f'Bem-vindo, {user.username}!', 'success')
                return redirect(request.args.get('next') or url_for('main.index'))
            else:
                flash('Código incorreto. Tente novamente.', 'danger')
                return render_template('auth/login_codigo.html')

        # Etapa 1 — verificar credenciais
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user     = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('E-mail ou senha incorretos.', 'danger')
            return render_template('auth/login.html')

        # Bloqueia login se e-mail não verificado
        if not user.email_verificado:
            enviar_codigo(user, 'Confirme seu e-mail — SetupMaker', 'verificacao')
            session['pending_register_id'] = user.id
            flash('Confirme seu e-mail antes de entrar. Reenviamos o código.', 'warning')
            return render_template('auth/verificar_email.html')

        # Admin entra diretamente — sem 2FA
        if user.is_admin:
            login_user(user)
            flash(f'Bem-vindo, {user.username}! (Administrador)', 'success')
            return redirect(request.args.get('next') or url_for('main.index'))

        enviar_codigo(user, 'Seu código de acesso — SetupMaker', '2fa')
        session['pending_user_id'] = user.id
        return render_template('auth/login_codigo.html')

    return render_template('auth/login.html')


# ── Logout ────────────────────────────────────────────────────────────────────
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.login'))


# ── Alterar senha ─────────────────────────────────────────────────────────────
@auth.route('/alterar-senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual', '')
        nova_senha  = request.form.get('nova_senha', '')
        confirmacao = request.form.get('confirmacao', '')

        if not current_user.check_password(senha_atual):
            flash('Senha atual incorreta.', 'danger')
            return render_template('auth/alterar_senha.html')

        if nova_senha != confirmacao:
            flash('A nova senha e a confirmação não coincidem.', 'danger')
            return render_template('auth/alterar_senha.html')

        valida, msg = senha_forte(nova_senha)
        if not valida:
            flash(msg, 'danger')
            return render_template('auth/alterar_senha.html')

        current_user.set_password(nova_senha)
        db.session.commit()
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('main.index'))

    return render_template('auth/alterar_senha.html')

@auth.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    from app.models.build import BuildPC
    from app.models.avaliacao import Avaliacao, AvaliacaoBuild

    if request.method == 'POST':
        acao = request.form.get('acao')

        if acao == 'perfil':
            novo_username = request.form.get('username', '').strip()
            novo_email    = request.form.get('email', '').strip()

            if not novo_username or not novo_email:
                flash('Username e e-mail são obrigatórios.', 'danger')
            elif novo_username != current_user.username and \
                 User.query.filter_by(username=novo_username).first():
                flash('Este nome de usuário já está em uso.', 'danger')
            elif novo_email != current_user.email and \
                 User.query.filter_by(email=novo_email).first():
                flash('Este e-mail já está cadastrado.', 'danger')
            else:
                current_user.username = novo_username
                current_user.email    = novo_email
                db.session.commit()
                flash('Perfil atualizado com sucesso!', 'success')

        elif acao == 'senha':
            senha_atual = request.form.get('senha_atual', '')
            nova_senha  = request.form.get('nova_senha', '')
            confirmacao = request.form.get('confirmacao', '')

            if not current_user.check_password(senha_atual):
                flash('Senha atual incorreta.', 'danger')
            elif nova_senha != confirmacao:
                flash('A nova senha e a confirmação não coincidem.', 'danger')
            else:
                valida, msg = senha_forte(nova_senha)
                if not valida:
                    flash(msg, 'danger')
                else:
                    current_user.set_password(nova_senha)
                    db.session.commit()
                    flash('Senha alterada com sucesso!', 'success')

        return redirect(url_for('auth.configuracoes'))

    # Estatísticas do usuário
    total_builds    = BuildPC.query.filter_by(user_id=current_user.id).count()
    builds_publicas = BuildPC.query.filter_by(user_id=current_user.id, publica=True).count()
    total_avals     = Avaliacao.query.filter_by(user_id=current_user.id).count()
    total_avals    += AvaliacaoBuild.query.filter_by(user_id=current_user.id).count()

    return render_template('auth/configuracoes.html',
        total_builds=total_builds,
        builds_publicas=builds_publicas,
        total_avals=total_avals,
    )
