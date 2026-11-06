from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from models.study_session import StudySessionModel
from models.task import TaskModel
from utils.decorators import login_required

sessions_bp = Blueprint("sessions", __name__, url_prefix="/sesiones")

@sessions_bp.route("", methods=["GET", "POST"])
@sessions_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """
    GET: Visualiza el historial de sesiones de estudio del usuario autenticado.
    POST: Permite registrar una nueva sesión de estudio.
    """
    user_id = session.get("user_id")

    if request.method == "POST":
        return crear()

    sesiones = StudySessionModel.get_all_by_user(user_id)
    tareas_usuario = TaskModel.get_all_by_user(user_id)
    return render_template(
        "sesiones/index.html",
        sesiones=sesiones,
        tareas=tareas_usuario,
        estados=StudySessionModel.ESTADOS
    )

@sessions_bp.route("/crear", methods=["POST"])
@login_required
def crear():
    """Crea una sesión de estudio asociada obligatoriamente al id_usuario autenticado."""
    user_id = session.get("user_id")

    duracion_raw = request.form.get("duracion_minutos", "25").strip()
    pausa_raw = request.form.get("tiempo_pausa_minutos", "5").strip()
    estado = request.form.get("estado", "completada").strip().lower()
    notas = request.form.get("notas", "").strip()
    id_tarea_raw = request.form.get("id_tarea", "").strip()

    # 1. Validación de duracion_minutos (> 0)
    try:
        duracion_minutos = int(duracion_raw)
        if duracion_minutos <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        flash("La duración debe ser un número entero mayor a 0 minutos.", "danger")
        sesiones = StudySessionModel.get_all_by_user(user_id)
        tareas_usuario = TaskModel.get_all_by_user(user_id)
        return render_template(
            "sesiones/index.html",
            sesiones=sesiones,
            tareas=tareas_usuario,
            estados=StudySessionModel.ESTADOS,
            form_data=request.form
        ), 400

    # 2. Validación de tiempo_pausa_minutos (>= 0)
    try:
        tiempo_pausa_minutos = int(pausa_raw) if pausa_raw else 5
        if tiempo_pausa_minutos < 0:
            raise ValueError()
    except (ValueError, TypeError):
        flash("El tiempo de pausa no puede ser negativo.", "danger")
        sesiones = StudySessionModel.get_all_by_user(user_id)
        tareas_usuario = TaskModel.get_all_by_user(user_id)
        return render_template(
            "sesiones/index.html",
            sesiones=sesiones,
            tareas=tareas_usuario,
            estados=StudySessionModel.ESTADOS,
            form_data=request.form
        ), 400

    # 3. Validación de estado
    if estado not in StudySessionModel.ESTADOS:
        flash(f"Estado de sesión no válido. Opciones: {', '.join(StudySessionModel.ESTADOS)}.", "danger")
        sesiones = StudySessionModel.get_all_by_user(user_id)
        tareas_usuario = TaskModel.get_all_by_user(user_id)
        return render_template(
            "sesiones/index.html",
            sesiones=sesiones,
            tareas=tareas_usuario,
            estados=StudySessionModel.ESTADOS,
            form_data=request.form
        ), 400

    # 4. Validación de id_tarea vinculada
    id_tarea = None
    if id_tarea_raw and id_tarea_raw.isdigit():
        t_id = int(id_tarea_raw)
        tarea = TaskModel.get_by_id(t_id)
        if tarea and tarea["id_usuario"] == user_id:
            id_tarea = t_id

    try:
        StudySessionModel.create(
            id_usuario=user_id,
            duracion_minutos=duracion_minutos,
            tiempo_pausa_minutos=tiempo_pausa_minutos,
            estado=estado,
            id_tarea=id_tarea,
            notas=notas
        )
        flash("Sesión de estudio registrada exitosamente.", "success")
        return redirect(url_for("sessions.index"))
    except Exception as e:
        flash("Error al registrar la sesión en la base de datos.", "danger")
        sesiones = StudySessionModel.get_all_by_user(user_id)
        tareas_usuario = TaskModel.get_all_by_user(user_id)
        return render_template(
            "sesiones/index.html",
            sesiones=sesiones,
            tareas=tareas_usuario,
            estados=StudySessionModel.ESTADOS,
            form_data=request.form
        ), 500

@sessions_bp.route("/<int:id_sesion>", methods=["GET"])
@login_required
def detalle(id_sesion: int):
    """Consulta el detalle de una sesión verificando la propiedad del usuario autenticado."""
    user_id = session.get("user_id")
    sesion = StudySessionModel.get_by_id(id_sesion)

    if not sesion:
        flash("La sesión de estudio no existe.", "warning")
        return redirect(url_for("sessions.index")), 404

    if sesion["id_usuario"] != user_id:
        abort(403)

    return render_template("sesiones/detalle.html", sesion=sesion)

@sessions_bp.route("/<int:id_sesion>/finalizar", methods=["POST"])
@login_required
def finalizar(id_sesion: int):
    """Finaliza una sesión activa garantizando que pertenezca al usuario autenticado."""
    user_id = session.get("user_id")
    sesion = StudySessionModel.get_by_id(id_sesion)

    if not sesion:
        flash("La sesión de estudio no existe.", "warning")
        return redirect(url_for("sessions.index")), 404

    if sesion["id_usuario"] != user_id:
        abort(403)

    notas = request.form.get("notas", "").strip()
    StudySessionModel.finish_session(id_sesion, user_id, notas if notas else None)
    flash("Sesión de estudio finalizada y marcada como completada.", "success")
    return redirect(url_for("sessions.index"))

@sessions_bp.route("/<int:id_sesion>/eliminar", methods=["POST"])
@login_required
def eliminar(id_sesion: int):
    """Elimina una sesión garantizando que pertenezca al usuario autenticado."""
    user_id = session.get("user_id")
    sesion = StudySessionModel.get_by_id(id_sesion)

    if not sesion:
        flash("La sesión de estudio no existe.", "warning")
        return redirect(url_for("sessions.index")), 404

    if sesion["id_usuario"] != user_id:
        abort(403)

    StudySessionModel.delete(id_sesion, user_id)
    flash("Sesión eliminada correctamente.", "info")
    return redirect(url_for("sessions.index"))
