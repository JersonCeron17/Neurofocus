from datetime import date
from flask import Blueprint, render_template, session
from utils.decorators import login_required, role_required
from models.task import TaskModel
from models.activity import ActivityModel
from models.study_session import StudySessionModel
from models.progress import ProgressModel
from models.achievement import AchievementModel

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    """Página de inicio sencilla con enlaces de acceso."""
    return render_template("index.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Vista protegida del centro principal de NeuroFocus para el usuario autenticado."""
    user_id = session.get("user_id")

    tareas = TaskModel.get_all_by_user(user_id) if user_id else []
    tareas_pendientes = sum(1 for t in tareas if t["estado"] != "completada")
    tareas_completadas = sum(1 for t in tareas if t["estado"] == "completada")

    actividades = ActivityModel.get_all_by_user(user_id) if user_id else []
    total_actividades = len(actividades)

    sesiones = StudySessionModel.get_all_by_user(user_id) if user_id else []
    total_sesiones = len(sesiones)
    minutos_estudio_total = sum(s["duracion_minutos"] for s in sesiones if s["estado"] == "completada")

    progreso_hoy = ProgressModel.get_by_user_and_date(user_id, date.today()) if user_id else None

    logros = AchievementModel.get_user_achievements(user_id) if user_id else []
    logros_desbloqueados = sum(1 for l in logros if l["desbloqueado"])
    total_logros = len(logros)

    return render_template(
        "dashboard.html",
        nombre=session.get("user_nombre"),
        correo=session.get("user_correo"),
        rol=session.get("user_rol"),
        tareas=tareas[:5],
        tareas_pendientes=tareas_pendientes,
        tareas_completadas=tareas_completadas,
        actividades=actividades[:5],
        total_actividades=total_actividades,
        sesiones=sesiones[:5],
        total_sesiones=total_sesiones,
        minutos_estudio_total=minutos_estudio_total,
        progreso_hoy=progreso_hoy,
        logros_desbloqueados=logros_desbloqueados,
        total_logros=total_logros
    )

@main_bp.route("/estudiante/panel")
@role_required("estudiante")
def panel_estudiante():
    """Ruta de prueba para acceso exclusivo con rol estudiante."""
    return "Panel Estudiante - Acceso Autorizado", 200

@main_bp.route("/docente/panel")
@role_required("docente")
def panel_docente():
    """Ruta de prueba para acceso exclusivo con rol docente."""
    return "Panel Docente - Acceso Autorizado", 200

@main_bp.route("/admin/panel")
@role_required("administrador")
def panel_admin():
    """Ruta de prueba para acceso exclusivo con rol administrador."""
    return "Panel Administrador - Acceso Autorizado", 200

