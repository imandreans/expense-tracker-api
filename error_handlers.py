from flask import render_template, current_app

def register_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        app.logger.error(f"Page not Found!")    
        status =str(e).split(":")[0]
        return render_template("error.html", error="Page not Found!", status=status)

    @app.errorhandler(500)
    def server_internal_error(e):
        app.logger.error(f"Server error: {e}")
        status =str(e).split(":")[0]
        return render_template("error.html", error=e, status=status)