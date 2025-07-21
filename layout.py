from dash import dcc, html
import dash_bootstrap_components as dbc

ENTITY_TYPES = ["protein", "rna", "dna", "ligand", "ion"]


def serve_entity_card(uid):
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Dropdown(
                                id={"type": "entity-type", "index": uid},
                                options=[{"label": t.title(), "value": t} for t in ENTITY_TYPES],
                                placeholder="Select entity type",
                            ),
                            width=4,
                        ),
                        dbc.Col(
                            dbc.Input(
                                id={"type": "entity-copies", "index": uid},
                                type="number",
                                min=1,
                                value=1,
                                placeholder="Copies",
                            ),
                            width=2,
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Remove",
                                id={"type": "remove-entity", "index": uid},
                                n_clicks=0,
                                color="danger",
                                size="sm",
                            ),
                            width="auto",
                        ),
                    ]
                )
            ),
            dbc.CardBody(id={"type": "entity-body", "index": uid}),
        ],
        class_name="mb-3",
        id={"type": "entity-card", "index": uid},
    )

def serve_submission_tab():
    """Serve the layout for the AlphaFold 3 submission tool."""
    return dbc.Container(
        [   
            # job metadata inputs
            dbc.Row(
                [
                    dbc.Col(dbc.Input(id="job-name", placeholder="Job name", type="text"), width=4),
                    dbc.Col(dbc.Input(id="email", placeholder="Your email", type="email"), width=4),
                ],
                class_name="mb-3",
            ),
            
            # entity cards
            html.Div(id="entity-list", children=[]),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Button("+ Add Entity", id="add-entity-button", n_clicks=0, color="success"),
                        width="auto",
                    ),
                ],
                class_name="mb-3",
            ),

            # submit buttons
            dbc.Row(
                [
                    dbc.Col(dbc.Button("Generate Input JSON", id="generate-json-button", color="info"), width="auto"),
                    dbc.Col(dbc.Button("Submit Job", id="submit-job", color="warning"), width="auto"),
                    dbc.Col(
                        dbc.Button(
                            "Download JSON", id="download-json-button", 
                            color="secondary", outline=True,
                            style={"display": "none"},
                        ), 
                        width="auto",
                    ),
                ],
                class_name="mb-3",
            ),

            # hidden stores for data passing
            dcc.Store(id="store-submission"),
            dcc.Download(id="download-json"),
            
            # JSON preview and status
            dbc.Collapse(
                dbc.Card(
                    [
                        dbc.CardHeader("Preview AF3 Input JSON"),
                        dbc.CardBody(html.Pre(id="json-preview-content", style={"whiteSpace": "pre-wrap", "textAlign": "left"})),
                    ]
                ),
                id="json-collapse",
                is_open=False,
            ),

            # job status alert
            dbc.Alert(id="job-status", is_open=False, color="danger"),
        ],
        style={"margin": "auto", "maxWidth": "960px"},
        fluid=False,
    )

def serve_history_table(entries):
    """
    Given a list of dicts each having keys:
      - name: the job folder name
      - timestamp: the TS string
      - email: the user email
      - zip: the absolute path to the .zip file
    return a Dash `dbc.Table` with one row per entry and a Download button.
    """
    header = html.Thead(html.Tr([
        html.Th("Job"),
        html.Th("Time (YYYY/MM/DD - HH:MM:SS)"),
        html.Th("User Email"),
        html.Th("Download"),
    ]))

    rows = []
    for idx, e in enumerate(entries):
        btn = dbc.Button(
            "Download",
            id={"type": "download-history", "index": idx},
            size="sm",
            color="primary",
            outline=True,
            class_name="btn-download",
        )
        rows.append(html.Tr([
            html.Td(e["name"]),
            html.Td(e["timestamp"]),
            html.Td(e["email"]),
            html.Td(btn),
        ]))

    body = html.Tbody(rows)
    return dbc.Table([header, body], bordered=True, hover=True, class_name="text-center align-middle")

def serve_layout():
    tab_style = {
        "padding": "10px 24px",
        "fontSize": "1.2rem",
        "width": "200px",
        "textAlign": "center",
    }
    selected_tab_style = {
        "padding": "10px 24px",
        "fontSize": "1.2rem",
        "width": "200px",
        "textAlign": "center",
        "fontWeight": "bold",
    }
    return dbc.Container([
        html.Link(id="theme-link", rel="stylesheet", href=dbc.themes.LUX),
        dcc.Store(id="theme-store", data={
            "light": dbc.themes.LUX,
            "dark":  dbc.themes.SUPERHERO,
        }),
        dbc.Row([
            dbc.Col(html.Div("Fetching your HTTP_UID...", id="display-uid"), width="auto"),
            dbc.Col(dbc.Switch(id="theme-switch",label="Dark Mode", value=False), width="auto",),
        ], style={"marginBottom": "12px"}, justify="between", align="center"),
        html.Div([
            html.Div(
                dcc.Tabs(
                    id="tabs",
                    value="tab-submit",
                    style={
                        "display": "inline-block", 
                        "margin": "0 auto",
                        "width": "fit-content", 
                    },
                    children=[
                        dcc.Tab(
                            label="Submit Job",
                            value="tab-submit",
                            style=tab_style,
                            selected_style=selected_tab_style,
                            children=[
                                html.Div([
                                    html.H2("AlphaFold 3 Submission Tool", style={"textAlign": "center", "marginTop": "1rem"}),
                                    html.P(
                                        "Prepare AF3-compatible input and submit a SLURM job. "
                                        "Once the job completes, you can download the results " 
                                        "from the Job History tab. You will receive an email "
                                        "notification when the job starts and finishes.",
                                        className="text-muted mb-4",
                                    ),
                                    serve_submission_tab(),
                                ], style={"padding": "1rem"})
                            ],
                        ),
                        dcc.Tab(
                            label="Job History",
                            value="tab-history",
                            style=tab_style,
                            selected_style=selected_tab_style,
                            children=[
                                html.Div([
                                    html.H2("Previously Run Jobs", style={"marginTop": "1rem", "textAlign": "center"}),
                                    html.P(
                                        "Below is a list of all previously run jobs. "
                                        "Click “Download” to retrieve the ZIP of results for that run. "
                                        "Download may take a few seconds to start, thank you for your patience. ",
                                        style={"marginBottom": "1rem"}
                                    ),
                                    html.Div(id="job-history-table"),
                                ], style={"padding": "1rem"})                                
                            ],
                        ),
                    ],
                ),
                style={
                    "marginBottom": "16px",
                    "textAlign": "center",
                },
            ),

            # hidden stores & downloads
            dcc.Store(id="uid-store"),
            dcc.Store(id="store-history"),
            dcc.Download(id="download-results"),
        ])
    ], fluid=False, class_name="pt-4")

