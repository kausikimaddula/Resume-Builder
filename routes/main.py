"""Main public routes for the application."""

from __future__ import annotations

from flask import Blueprint, current_app, render_template


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    """Show the landing page."""
    current_app.logger.info("Home page requested")
    return render_template("index.html")
