from flask import Blueprint, render_template, session
from models.achievement import AchievementModel
from utils.decorators import login_required

achievements_bp = Blueprint("achievements", __name__, url_prefix="/logros")

@achievements_bp.route("", methods=["GET"])
@achievements_bp.route("/", methods=["GET"])
@login_required
def index():
    """Muestra el catálogo de logros disponibles y el estado de desbloqueo del usuario autenticado."""
    user_id = session.get("user_id")
    logros = AchievementModel.get_user_achievements(user_id)
    desbloqueados_count = sum(1 for l in logros if l["desbloqueado"])
    return render_template(
        "logros/index.html",
        logros=logros,
        total=len(logros),
        desbloqueados_count=desbloqueados_count
    )
