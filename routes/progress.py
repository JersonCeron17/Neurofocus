from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from models.progress import ProgressModel
from models.achievement import AchievementModel
from utils.decorators import login_required

progress_bp = Blueprint("progress", __name__, url_prefix="/progreso")

@progress_bp.route("", methods=["GET"])
@progress_bp.route("/", methods=["GET"])
@login_required
def index():
    """Visualización del historial de progreso diario del usuario autenticado."""
    user_id = session.get("user_id")
    hoy = date.today()
    progreso_hoy = ProgressModel.get_by_user_and_date(user_id, hoy)
    historial = ProgressModel.get_all_by_user(user_id)
    return render_template(
        "progreso/index.html",
        progreso_hoy=progreso_hoy,
        historial=historial,
        fecha_hoy=hoy.isoformat()
    )

@progress_bp.route("/actualizar", methods=["POST"])
@login_required
def actualizar():
    """Registra o actualiza el progreso diario del usuario para una fecha determinada."""
    user_id = session.get("user_id")

    fecha_raw = request.form.get("fecha", "").strip()
    tareas_raw = request.form.get("tareas_completadas", "0").strip()
    minutos_raw = request.form.get("minutos_estudio", "0").strip()
    ejercicios_raw = request.form.get("ejercicios_completados", "0").strip()

    # Validación de fecha
    if not fecha_raw:
        fecha = date.today()
    else:
        try:
            fecha = datetime.strptime(fecha_raw, "%Y-%m-%d").date()
        except ValueError:
            flash("El formato de fecha debe ser AAAA-MM-DD.", "danger")
            return redirect(url_for("progress.index")), 400

    # Validación de métricas no negativas
    try:
        tareas_completadas = int(tareas_raw)
        minutos_estudio = int(minutos_raw)
        ejercicios_completados = int(ejercicios_raw)
        if tareas_completadas < 0 or minutos_estudio < 0 or ejercicios_completados < 0:
            raise ValueError()
    except (ValueError, TypeError):
        flash("Las métricas de progreso deben ser números enteros mayores o iguales a 0.", "danger")
        return redirect(url_for("progress.index")), 400

    ProgressModel.upsert(
        id_usuario=user_id,
        fecha=fecha,
        tareas_completadas=tareas_completadas,
        minutos_estudio=minutos_estudio,
        ejercicios_completados=ejercicios_completados
    )

    # Desbloquear logro de constancia diaria
    AchievementModel.unlock(user_id, "progreso_diario")

    flash(f"Progreso para el {fecha.isoformat()} registrado exitosamente.", "success")
    return redirect(url_for("progress.index"))

@progress_bp.route("/<int:id_progreso>", methods=["GET"])
@login_required
def detalle(id_progreso: int):
    """Consulta de detalle de un registro de progreso garantizando la propiedad del usuario (anti-IDOR)."""
    user_id = session.get("user_id")
    prog = ProgressModel.get_by_id(id_progreso)
    if not prog:
        flash("El registro de progreso no existe.", "warning")
        return redirect(url_for("progress.index")), 404

    if prog["id_usuario"] != user_id:
        abort(403)

    return render_template("progreso/detalle.html", prog=prog)
