from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from models.task import TaskModel
from utils.decorators import login_required

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tareas")

def _parse_and_validate_date(date_str: str, default_date: str = None):
    """
    Valida formato AAAA-MM-DD.
    Si la fecha es provista, debe ser válida.
    Si no se proporciona, retorna default_date o la fecha actual.
    """
    if not date_str or not date_str.strip():
        return default_date or date.today().isoformat(), True

    try:
        parsed = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        return parsed.isoformat(), True
    except ValueError:
        return None, False

@tasks_bp.route("", methods=["GET", "POST"])
@tasks_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """
    GET: Lista las tareas exclusivas del usuario autenticado.
    POST: Permite la creación directa de una tarea desde el formulario principal.
    """
    user_id = session.get("user_id")

    if request.method == "POST":
        return crear()

    tareas = TaskModel.get_all_by_user(user_id)
    return render_template(
        "tareas/index.html",
        tareas=tareas,
        prioridades=TaskModel.PRIORIDADES,
        estados=TaskModel.ESTADOS
    )

@tasks_bp.route("/crear", methods=["POST"])
@login_required
def crear():
    """Crea una nueva tarea vinculada obligatoriamente al id_usuario de la sesión."""
    user_id = session.get("user_id")

    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    fecha_input = request.form.get("fecha_entrega", "").strip()
    prioridad = request.form.get("prioridad", "media").strip().lower()
    estado = request.form.get("estado", "pendiente").strip().lower()

    # 1. Validación de nombre obligatorio
    if not nombre:
        flash("El nombre de la tarea es obligatorio.", "danger")
        tareas = TaskModel.get_all_by_user(user_id)
        return render_template(
            "tareas/index.html",
            tareas=tareas,
            prioridades=TaskModel.PRIORIDADES,
            estados=TaskModel.ESTADOS,
            form_data=request.form
        ), 400

    # 2. Validación de fecha
    fecha_entrega, es_valida = _parse_and_validate_date(fecha_input)
    if not es_valida:
        flash("La fecha de entrega debe tener un formato válido (AAAA-MM-DD).", "danger")
        tareas = TaskModel.get_all_by_user(user_id)
        return render_template(
            "tareas/index.html",
            tareas=tareas,
            prioridades=TaskModel.PRIORIDADES,
            estados=TaskModel.ESTADOS,
            form_data=request.form
        ), 400

    # 3. Validación de prioridad
    if prioridad not in TaskModel.PRIORIDADES:
        flash(f"Prioridad inválida. Debe ser: {', '.join(TaskModel.PRIORIDADES)}.", "danger")
        tareas = TaskModel.get_all_by_user(user_id)
        return render_template(
            "tareas/index.html",
            tareas=tareas,
            prioridades=TaskModel.PRIORIDADES,
            estados=TaskModel.ESTADOS,
            form_data=request.form
        ), 400

    # 4. Validación de estado
    if estado not in TaskModel.ESTADOS:
        flash(f"Estado inválido. Debe ser: {', '.join(TaskModel.ESTADOS)}.", "danger")
        tareas = TaskModel.get_all_by_user(user_id)
        return render_template(
            "tareas/index.html",
            tareas=tareas,
            prioridades=TaskModel.PRIORIDADES,
            estados=TaskModel.ESTADOS,
            form_data=request.form
        ), 400

    try:
        TaskModel.create(
            id_usuario=user_id,
            nombre=nombre,
            descripcion=descripcion,
            fecha_entrega=fecha_entrega,
            prioridad=prioridad,
            estado=estado
        )
        flash("Tarea creada exitosamente.", "success")
        return redirect(url_for("tasks.index"))
    except Exception as e:
        flash("Ocurrió un error al guardar la tarea en la base de datos.", "danger")
        tareas = TaskModel.get_all_by_user(user_id)
        return render_template(
            "tareas/index.html",
            tareas=tareas,
            prioridades=TaskModel.PRIORIDADES,
            estados=TaskModel.ESTADOS,
            form_data=request.form
        ), 500

@tasks_bp.route("/<int:id_tarea>", methods=["GET"])
@login_required
def detalle(id_tarea: int):
    """Consulta los detalles de una tarea verificando la propiedad del usuario."""
    user_id = session.get("user_id")
    tarea = TaskModel.get_by_id(id_tarea)

    if not tarea:
        flash("La tarea solicitada no existe.", "warning")
        return redirect(url_for("tasks.index")), 404

    # Verificación de propiedad (seguridad IDOR)
    if tarea["id_usuario"] != user_id:
        abort(403)

    return render_template("tareas/detalle.html", tarea=tarea)

@tasks_bp.route("/<int:id_tarea>/editar", methods=["GET", "POST"])
@login_required
def editar(id_tarea: int):
    """Permite ver el formulario de edición y guardar modificaciones de una tarea propia."""
    user_id = session.get("user_id")
    tarea = TaskModel.get_by_id(id_tarea)

    if not tarea:
        flash("La tarea solicitada no existe.", "warning")
        return redirect(url_for("tasks.index")), 404

    # Verificación de propiedad (seguridad IDOR)
    if tarea["id_usuario"] != user_id:
        abort(403)

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        fecha_input = request.form.get("fecha_entrega", "").strip()
        prioridad = request.form.get("prioridad", "").strip().lower()
        estado = request.form.get("estado", "").strip().lower()

        # Validación de nombre
        if not nombre:
            flash("El nombre de la tarea es obligatorio.", "danger")
            return render_template(
                "tareas/editar.html",
                tarea=tarea,
                prioridades=TaskModel.PRIORIDADES,
                estados=TaskModel.ESTADOS
            ), 400

        # Validación de fecha
        fecha_default = tarea["fecha_entrega"].isoformat() if hasattr(tarea["fecha_entrega"], "isoformat") else str(tarea["fecha_entrega"])
        fecha_entrega, es_valida = _parse_and_validate_date(fecha_input, default_date=fecha_default)
        if not es_valida:
            flash("La fecha de entrega debe tener un formato válido (AAAA-MM-DD).", "danger")
            return render_template(
                "tareas/editar.html",
                tarea=tarea,
                prioridades=TaskModel.PRIORIDADES,
                estados=TaskModel.ESTADOS
            ), 400

        # Validación de prioridad
        if prioridad not in TaskModel.PRIORIDADES:
            flash(f"Prioridad inválida. Debe ser: {', '.join(TaskModel.PRIORIDADES)}.", "danger")
            return render_template(
                "tareas/editar.html",
                tarea=tarea,
                prioridades=TaskModel.PRIORIDADES,
                estados=TaskModel.ESTADOS
            ), 400

        # Validación de estado
        if estado not in TaskModel.ESTADOS:
            flash(f"Estado inválido. Debe ser: {', '.join(TaskModel.ESTADOS)}.", "danger")
            return render_template(
                "tareas/editar.html",
                tarea=tarea,
                prioridades=TaskModel.PRIORIDADES,
                estados=TaskModel.ESTADOS
            ), 400

        # Actualizar en base de datos
        TaskModel.update(
            id_tarea=id_tarea,
            id_usuario=user_id,
            nombre=nombre,
            descripcion=descripcion,
            fecha_entrega=fecha_entrega,
            prioridad=prioridad,
            estado=estado
        )
        flash("Tarea actualizada exitosamente.", "success")
        return redirect(url_for("tasks.index"))

    return render_template(
        "tareas/editar.html",
        tarea=tarea,
        prioridades=TaskModel.PRIORIDADES,
        estados=TaskModel.ESTADOS
    )

@tasks_bp.route("/<int:id_tarea>/completar", methods=["POST"])
@login_required
def completar(id_tarea: int):
    """Marca una tarea como completada garantizando que pertenezca al usuario autenticado."""
    user_id = session.get("user_id")
    tarea = TaskModel.get_by_id(id_tarea)

    if not tarea:
        flash("La tarea solicitada no existe.", "warning")
        return redirect(url_for("tasks.index")), 404

    # Verificación de propiedad (seguridad IDOR)
    if tarea["id_usuario"] != user_id:
        abort(403)

    TaskModel.mark_completed(id_tarea, user_id)
    flash(f"Tarea '{tarea['nombre']}' completada exitosamente.", "success")
    return redirect(url_for("tasks.index"))

@tasks_bp.route("/<int:id_tarea>/eliminar", methods=["POST"])
@login_required
def eliminar(id_tarea: int):
    """Elimina una tarea garantizando que pertenezca al usuario autenticado."""
    user_id = session.get("user_id")
    tarea = TaskModel.get_by_id(id_tarea)

    if not tarea:
        flash("La tarea solicitada no existe.", "warning")
        return redirect(url_for("tasks.index")), 404

    # Verificación de propiedad (seguridad IDOR)
    if tarea["id_usuario"] != user_id:
        abort(403)

    TaskModel.delete(id_tarea, user_id)
    flash("Tarea eliminada exitosamente.", "info")
    return redirect(url_for("tasks.index"))
