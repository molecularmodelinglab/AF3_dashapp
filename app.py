import dash
import dash_bootstrap_components as dbc

from layout import serve_layout
from callbacks import register_callbacks


def create_app(title="AlphaFold 3 Submission"):
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.LUX],
        suppress_callback_exceptions=True,
    )
    app.title = title

    # Expose Flask server for deployment
    app.server = app.server  # noqa: F841

    # Set up the layout and callbacks
    app.layout = serve_layout()
    register_callbacks(app)

    return app

app = create_app()


if __name__ == "__main__":
    app.run_server(debug=True)
