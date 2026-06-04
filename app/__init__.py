import click
from flask import Flask
from config import DevelopmentConfig
from app.extensions import db, login_manager, migrate, mail, csrf, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)
    jwt.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Faça login para acessar esta página.'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # ── Blueprints ────────────────────────────────────────────────
    from app.routes.auth      import auth
    from app.routes.main      import main
    from app.api.routes       import api
    from app.routes.produtos  import produtos_bp
    from app.routes.builds    import builds_bp
    from app.routes.avaliacoes import avaliacoes_bp
    from app.routes.admin      import admin_bp

    csrf.exempt(api)

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(api)
    app.register_blueprint(produtos_bp)
    app.register_blueprint(builds_bp)
    app.register_blueprint(avaliacoes_bp)
    app.register_blueprint(admin_bp)

    # ── CLI: flask seed ───────────────────────────────────────────
    @app.cli.command('seed')
    def seed_command():
        """Popula o banco com dados simulados de exemplo."""
        from app.services.seed import run
        run()

    # ── CLI: flask importar-hardware ──────────────────────────────
    @app.cli.command('importar-hardware')
    @click.option('--taxa', default=5.70, help='Taxa de conversão USD→BRL (padrão: 5.70)')
    def importar_hardware_command(taxa):
        """Importa produtos reais via API pc-part-dataset (GitHub)."""
        import app.services.importar_hardware as ih
        ih.TAXA_USD_BRL = taxa
        ih.run()

    return app