from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from models.exercise import ExerciseModel, ExerciseResultModel
from models.progress import ProgressModel
from models.achievement import AchievementModel
from utils.decorators import login_required

exercises_bp = Blueprint("exercises", __name__, url_prefix="/ejercicios")

@exercises_bp.route("", methods=["GET"])
@exercises_bp.route("/", methods=["GET"])
@login_required
def index():
    """Catálogo de ejercicios de concentración disponibles."""
    ejercicios = ExerciseModel.get_all()
    return render_template("ejercicios/index.html", ejercicios=ejercicios)

@exercises_bp.route("/<int:id_ejercicio>", methods=["GET"])
@login_required
def detalle(id_ejercicio: int):
    """Vista funcional para realizar un ejercicio cognitivo y registrar el desempeño."""
    ejercicio = ExerciseModel.get_by_id(id_ejercicio)
    if not ejercicio:
        flash("El ejercicio solicitado no existe.", "warning")
        return redirect(url_for("exercises.index")), 404

    return render_template("ejercicios/detalle.html", ejercicio=ejercicio)

@exercises_bp.route("/<int:id_ejercicio>/resultado", methods=["POST"])
@login_required
def registrar_resultado(id_ejercicio: int):
    """Registra el resultado obtenido por el usuario autenticado."""
    user_id = session.get("user_id")
    ejercicio = ExerciseModel.get_by_id(id_ejercicio)
    if not ejercicio:
        flash("El ejercicio no existe.", "warning")
        return redirect(url_for("exercises.index")), 404

    puntuacion_raw = request.form.get("puntuacion", "").strip()
    tiempo_raw = request.form.get("tiempo_segundos", "").strip()

    try:
        puntuacion = int(puntuacion_raw)
        if puntuacion < 0:
            raise ValueError()
    except (ValueError, TypeError):
        flash("La puntuación debe ser un número entero mayor o igual a 0.", "danger")
        return redirect(url_for("exercises.detalle", id_ejercicio=id_ejercicio)), 400

    tiempo_segundos = None
    if tiempo_raw:
        try:
            t = int(tiempo_raw)
            if t >= 0:
                tiempo_segundos = t
        except (ValueError, TypeError):
            pass

    # Guardar resultado asociado al usuario autenticado
    id_res = ExerciseResultModel.create(
        id_usuario=user_id,
        id_ejercicio=id_ejercicio,
        puntuacion=puntuacion,
        tiempo_segundos=tiempo_segundos
    )

    # Actualizar progreso diario automáticamente
    hoy = date.today()
    prog_actual = ProgressModel.get_by_user_and_date(user_id, hoy)
    if prog_actual:
        ProgressModel.upsert(
            id_usuario=user_id,
            fecha=hoy,
            tareas_completadas=prog_actual["tareas_completadas"],
            minutos_estudio=prog_actual["minutos_estudio"],
            ejercicios_completados=prog_actual["ejercicios_completados"] + 1
        )
    else:
        ProgressModel.upsert(
            id_usuario=user_id,
            fecha=hoy,
            tareas_completadas=0,
            minutos_estudio=0,
            ejercicios_completados=1
        )

    # Desbloquear logro de primer ejercicio
    AchievementModel.unlock(user_id, "primer_ejercicio")

    flash(f"¡Resultado de {puntuacion} puntos guardado con éxito!", "success")
    return redirect(url_for("exercises.mis_resultados"))

@exercises_bp.route("/mis-resultados", methods=["GET"])
@login_required
def mis_resultados():
    """Consulta exclusiva del historial de resultados del usuario en sesión."""
    user_id = session.get("user_id")
    resultados = ExerciseResultModel.get_all_by_user(user_id)
    return render_template("ejercicios/resultados.html", resultados=resultados)

@exercises_bp.route("/resultados/<int:id_resultado>", methods=["GET"])
@login_required
def detalle_resultado(id_resultado: int):
    """Consulta de detalle de un resultado específico con control estricto de propiedad (anti-IDOR)."""
    user_id = session.get("user_id")
    resultado = ExerciseResultModel.get_by_id(id_resultado)
    if not resultado:
        flash("El resultado no existe.", "warning")
        return redirect(url_for("exercises.mis_resultados")), 404

    if resultado["id_usuario"] != user_id:
        abort(403)

    return render_template("ejercicios/detalle_resultado.html", resultado=resultado)
