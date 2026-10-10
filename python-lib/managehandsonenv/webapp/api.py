"""Flask routes of the console webapp.

``register_routes(app, manager, context_factory)`` adds the ``/api/...`` endpoints
to the Flask ``app`` DSS hands to a standard webapp backend. The module imports
Flask lazily inside that function so the rest of the library stays importable
without it.
"""
from typing import Any, Callable, Dict, Optional

from managehandsonenv.context import Context
from managehandsonenv.features import FEATURES, FeatureNotFound, by_category, get_feature
from managehandsonenv.webapp.forms import coerce_params, form_schema
from managehandsonenv.webapp.jobs import JobManager, JobRunning


def context_payload(ctx: Context) -> Dict[str, Any]:
    """What the page needs to draw the button bar and decide whether it may run anything."""
    return {
        "project_key": ctx.project_key,
        "admin_project_key": ctx.settings.admin_project_key,
        "allowed": ctx.is_admin_project,
        "settings": ctx.settings.public_dict(),
        "categories": [
            {
                "name": category,
                "features": [
                    {
                        "id": feature.id,
                        "label": feature.label,
                        "description": feature.description,
                        "destructive": feature.destructive,
                        "confirm": feature.confirm,
                    }
                    for feature in features
                ],
            }
            for category, features in by_category()
        ],
    }


def register_routes(app, manager: JobManager, context_factory: Callable[[], Context],
                    descriptor_loader: Optional[Callable[[str], Dict[str, Any]]] = None) -> None:
    from flask import jsonify, request

    def schema_for(feature):
        descriptor = descriptor_loader(feature.macro_folder) if descriptor_loader else None
        return form_schema(feature, descriptor)

    def error(status: int, message: str, **extra):
        payload = {"error": message}
        payload.update(extra)
        return jsonify(payload), status

    @app.route("/api/context", methods=["GET"], endpoint="hands_on_context")
    def api_context():
        return jsonify(context_payload(context_factory()))

    @app.route("/api/features", methods=["GET"], endpoint="hands_on_features")
    def api_features():
        return jsonify({"features": [schema_for(feature) for feature in FEATURES.values()]})

    @app.route("/api/features/<feature_id>/form", methods=["GET"], endpoint="hands_on_feature_form")
    def api_feature_form(feature_id):
        try:
            feature = get_feature(feature_id)
        except FeatureNotFound as e:
            return error(404, str(e))
        return jsonify(schema_for(feature))

    @app.route("/api/jobs", methods=["GET"], endpoint="hands_on_jobs")
    def api_jobs():
        limit = request.args.get("limit", default=20, type=int)
        current = manager.current()
        return jsonify({
            "current": current.to_dict() if current else None,
            "jobs": [job.to_dict(log_from=len(job.log)) for job in manager.history(limit)],
        })

    @app.route("/api/jobs", methods=["POST"], endpoint="hands_on_start_job")
    def api_start_job():
        ctx = context_factory()
        if not ctx.is_admin_project:
            return error(403, "This webapp only runs inside project {} (this is {})".format(
                ctx.settings.admin_project_key, ctx.project_key))
        body = request.get_json(silent=True) or {}
        try:
            feature = get_feature(str(body.get("feature_id", "")))
        except FeatureNotFound as e:
            return error(400, str(e))
        try:
            params = coerce_params(schema_for(feature), body.get("params") or {})
        except (TypeError, ValueError) as e:
            return error(400, "Invalid parameters: {}".format(e))
        try:
            job = manager.start(feature, params)
        except JobRunning as e:
            return error(409, str(e), job=e.job.to_dict(log_from=len(e.job.log)))
        return jsonify({"job": job.to_dict()}), 202

    @app.route("/api/jobs/<job_id>", methods=["GET"], endpoint="hands_on_job")
    def api_job(job_id):
        job = manager.get(job_id)
        if job is None:
            return error(404, "Unknown job {}".format(job_id))
        log_from = request.args.get("log_from", default=0, type=int)
        return jsonify({"job": job.to_dict(log_from=log_from)})
