from flask import Flask
from config.settings import Config
from utils.security import bcrypt
from routes.auth import auth_bp
from routes.main import main_bp
from routes.tasks import tasks_bp
from routes.calendar import calendar_bp
from routes.sessions import sessions_bp
from routes.exercises import exercises_bp
from routes.progress import progress_bp
from routes.achievements import achievements_bp

def create_app(config_class=Config):
    """
    Fábrica de aplicaciones (Application Factory) para NeuroFocus.
    Inicializa Flask, extensiones de seguridad y registra los blueprints.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensiones
    bcrypt.init_app(app)

    # Registrar Blueprints de módulos
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(exercises_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(achievements_bp)

    # Ruta de comprobación de salud técnica
    @app.route("/health")
    def health_check():
        return {
            "status": "ok",
            "app": "NeuroFocus",
            "database": config_class.DB_NAME
        }

    return app

# Instancia de aplicación
app = create_app()

if __name__ == "__main__":
    app.run(debug=Config.DEBUG)
