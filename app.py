import dash
import dash_bootstrap_components as dbc

from layout import serve_layout
from callbacks import register_callbacks


def create_app(title="AlphaFold 3 Submission"):
    app = dash.Dash(
        __name__,
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

app.clientside_callback(
    """
    function(isDark, urls) {
        // urls is an object: { light: "...lux.css", dark: "...solar.css" }
        return isDark ? urls.dark : urls.light;
    }
    """,
    dash.Output("theme-link", "href"),
    dash.Input("theme-switch", "value"),
    dash.Input("theme-store",  "data")
)


if __name__ == "__main__":
    app.run(debug=True, port=8050)
