from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from models.activity import ActivityModel
from models.task import TaskModel
from utils.decorators import login_required

calendar_bp = Blueprint("calendar", __name__, url_prefix="/calendario")

def _parse_timestamp(ts_str: str):
    """Convierte cadena de texto a objeto datetime validando múltiples formatos estándar."""
    if not ts_str or not ts_str.strip():
        return None
    cleaned = ts_str.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return "INVALIDO"

@calendar_bp.route("", methods=["GET", "POST"])
@calendar_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """
    GET: Visualiza las actividades del calendario del usuario autenticado.
    POST: Permite registrar una nueva actividad.
    """
    user_id = session.get("user_id")

    if request.method == "POST":
        return crear()

    actividades = ActivityModel.get_all_by_user(user_id)
    tareas_usuario = TaskModel.get_all_by_user(user_id)
    return render_template(
        "calendario/index.html",
        actividades=actividades,
        tareas=tareas_usuario,
        tipos=ActivityModel.TIPOS
    )

@calendar_bp.route("/crear", methods=["POST"])
@login_required
def crear():
    """Crea una nueva actividad en el calendario garantizando su asociación al usuario actual."""
    user_id = session.get("user_id")

    titulo = request.form.get("titulo", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    fecha_inicio_raw = request.form.get("fecha_inicio", "").strip()
    fecha_fin_raw = request.form.get("fecha_fin", "").strip()
    tipo = request.form.get("tipo", "estudio").strip().lower()
    id_tarea_raw = request.form.get("id_tarea", "").strip()

    # 1. Validación de título obligatorio
    if not titulo:
        flash("El título de la actividad es obligatorio.", "danger")
        actividades = ActivityModel.get_all_by_user(user_id)
        tareas_usuario = TaskModel.get_all_by_user(user_id)
        return render_template(
            "calendario/index.html",
            actividades=actividades,
            tareas=tareas_usuario,
            tipos=ActivityModel.TIPOS,
            form_data=request.form
        ), 400

    # 2. Validación de fecha_inicio obligatoria
    fecha_inicio = _parse_timestamp(fecha_inicio_raw)
    if not fecha_inicio or fecha_inicio == "INVALIDO":
        flash("La fecha y hora de inicio son obligatorias y deben tener un formato válido.", "danger")
        actividades = ActivityModel.get_all_by_user(user_id)
        tareas_usuario = TaskModel.get_all_by_user(user_id)
        return render_template(
            "calendario/index.html",
            actividades=actividades,
            tareas=tareas_usuario,
            tipos=ActivityModel.TIPOS,
            form_data=request.form
        ), 400

    # 3. Validación de fecha_fin (opcional pero coherente con restricción chk_actividad_fechas)
    fecha_fin = _parse_timestamp(fecha_fin_raw)
    if fecha_fin_raw and fecha_fin == "INVALIDO":
        flash("El formato de fecha de fin no es válido.", "danger")
        actividades = ActivityModel.get_all_by_user(user_id)
        tareas_usuario = TaskModel.get_all_by_user(user_id)
        return render_template(
            "calendario/index.html",
            actividades=actividades,
            tareas=tareas_usuario,
            tipos=ActivityModel.TIPOS,
            form_data=request.form
        ), 400

    if fecha_fin and fecha_fin < fecha_inicio:
        flash("La fecha de fin no puede ser anterior a la fecha de inicio.", "danger")
        actividades = ActivityModel.get_all_by_user(user_id)
        tareas_usuario = TaskModel.get_all_by_user(user_id)
        return render_template(
            "calendario/index.html",
            actividades=actividades,
            tareas=tareas_usuario,
            tipos=ActivityModel.TIPOS,
            form_data=request.form
        ), 400

    # 4. Validación de tipo
    if tipo not in ActivityModel.TIPOS:
        flash(f"Tipo no válido. Opciones permitidas: {', '.join(ActivityModel.TIPOS)}.", "danger")
        actividades = ActivityModel.get_all_by_user(user_id)
        tareas_usuario = TaskModel.get_all_by_user(user_id)
        return render_template(
            "calendario/index.html",
            actividades=actividades,
            tareas=tareas_usuario,
            tipos=ActivityModel.TIPOS,
            form_data=request.form
        ), 400

    # 5. Validación de tarea vinculada (respetando propiedad de tarea)
    id_tarea = None
    if id_tarea_raw and id_tarea_raw.isdigit():
        t_id = int(id_tarea_raw)
        tarea = TaskModel.get_by_id(t_id)
        if tarea and tarea["id_usuario"] == user_id:
            id_tarea = t_id

    try:
        ActivityModel.create(
            id_usuario=user_id,
            titulo=titulo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo=tipo,
            descripcion=descripcion,
            id_tarea=id_tarea
        )
        flash("Actividad agregada al calendario exitosamente.", "success")
        return redirect(url_for("calendar.index"))
    except Exception as e:
        flash("Error al registrar la actividad en la base de datos.", "danger")
        actividades = ActivityModel.get_all_by_user(user_id)
        tareas_usuario = TaskModel.get_all_by_user(user_id)
        return render_template(
            "calendario/index.html",
            actividades=actividades,
            tareas=tareas_usuario,
            tipos=ActivityModel.TIPOS,
            form_data=request.form
        ), 500

@calendar_bp.route("/<int:id_actividad>", methods=["GET"])
@login_required
def detalle(id_actividad: int):
    """Detalle de una actividad comprobando la propiedad del usuario autenticado."""
    user_id = session.get("user_id")
    actividad = ActivityModel.get_by_id(id_actividad)

    if not actividad:
        flash("La actividad no existe.", "warning")
        return redirect(url_for("calendar.index")), 404

    if actividad["id_usuario"] != user_id:
        abort(403)

    return render_template("calendario/detalle.html", actividad=actividad)

@calendar_bp.route("/<int:id_actividad>/editar", methods=["GET", "POST"])
@login_required
def editar(id_actividad: int):
    """Permite editar una actividad garantizando la propiedad del usuario autenticado."""
    user_id = session.get("user_id")
    actividad = ActivityModel.get_by_id(id_actividad)

    if not actividad:
        flash("La actividad no existe.", "warning")
        return redirect(url_for("calendar.index")), 404

    if actividad["id_usuario"] != user_id:
        abort(403)

    tareas_usuario = TaskModel.get_all_by_user(user_id)

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        fecha_inicio_raw = request.form.get("fecha_inicio", "").strip()
        fecha_fin_raw = request.form.get("fecha_fin", "").strip()
        tipo = request.form.get("tipo", "estudio").strip().lower()
        id_tarea_raw = request.form.get("id_tarea", "").strip()

        if not titulo:
            flash("El título es obligatorio.", "danger")
            return render_template(
                "calendario/editar.html",
                actividad=actividad,
                tareas=tareas_usuario,
                tipos=ActivityModel.TIPOS
            ), 400

        fecha_inicio = _parse_timestamp(fecha_inicio_raw)
        if not fecha_inicio or fecha_inicio == "INVALIDO":
            flash("Fecha de inicio inválida.", "danger")
            return render_template(
                "calendario/editar.html",
                actividad=actividad,
                tareas=tareas_usuario,
                tipos=ActivityModel.TIPOS
            ), 400

        fecha_fin = _parse_timestamp(fecha_fin_raw)
        if fecha_fin_raw and fecha_fin == "INVALIDO":
            flash("Fecha de fin inválida.", "danger")
            return render_template(
                "calendario/editar.html",
                actividad=actividad,
                tareas=tareas_usuario,
                tipos=ActivityModel.TIPOS
            ), 400

        if fecha_fin and fecha_fin < fecha_inicio:
            flash("La fecha de fin no puede ser anterior a la fecha de inicio.", "danger")
            return render_template(
                "calendario/editar.html",
                actividad=actividad,
                tareas=tareas_usuario,
                tipos=ActivityModel.TIPOS
            ), 400

        if tipo not in ActivityModel.TIPOS:
            flash("Tipo de actividad no válido.", "danger")
            return render_template(
                "calendario/editar.html",
                actividad=actividad,
                tareas=tareas_usuario,
                tipos=ActivityModel.TIPOS
            ), 400

        id_tarea = None
        if id_tarea_raw and id_tarea_raw.isdigit():
            t_id = int(id_tarea_raw)
            tarea = TaskModel.get_by_id(t_id)
            if tarea and tarea["id_usuario"] == user_id:
                id_tarea = t_id

        ActivityModel.update(
            id_actividad=id_actividad,
            id_usuario=user_id,
            titulo=titulo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo=tipo,
            descripcion=descripcion,
            id_tarea=id_tarea
        )
        flash("Actividad actualizada exitosamente.", "success")
        return redirect(url_for("calendar.index"))

    return render_template(
        "calendario/editar.html",
        actividad=actividad,
        tareas=tareas_usuario,
        tipos=ActivityModel.TIPOS
    )

@calendar_bp.route("/<int:id_actividad>/eliminar", methods=["POST"])
@login_required
def eliminar(id_actividad: int):
    """Elimina una actividad comprobando la propiedad del usuario autenticado."""
    user_id = session.get("user_id")
    actividad = ActivityModel.get_by_id(id_actividad)

    if not actividad:
        flash("La actividad no existe.", "warning")
        return redirect(url_for("calendar.index")), 404

    if actividad["id_usuario"] != user_id:
        abort(403)

    ActivityModel.delete(id_actividad, user_id)
    flash("Actividad eliminada exitosamente.", "info")
    return redirect(url_for("calendar.index"))
