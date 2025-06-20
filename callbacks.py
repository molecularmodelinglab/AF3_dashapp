from datetime import datetime
from pathlib import Path
import json
import uuid
from subprocess import CalledProcessError

from dash import dcc, ctx, Input, Output, State, MATCH, ALL, Dash, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask import request

from layout import serve_history_table
from helpers import (
    build_submission, create_job_dir, 
    write_json_input, write_and_submit_script,
    list_job_entries
)

def register_callbacks(app: Dash):
    @app.callback(
        Output("entity-list", "children"),
        Input("add-entity-button", "n_clicks"),
        Input({"type": "remove-entity", "index": ALL}, "n_clicks"),
        State("entity-list", "children"),
        prevent_initial_call=True,
    )
    def update_entity_list(add_clicks, remove_clicks, children):
        # children is a list of existing cards
        children = children or []
        triggered = ctx.triggered_id

        # remove an entity card
        if isinstance(triggered, dict) and triggered.get("type") == "remove-entity":
            idx_to_remove = triggered["index"]
            return [
                card for card in children
                if card["props"]["id"]["index"] != idx_to_remove
            ]

        # add a new entity card
        if triggered == "add-entity-button":
            from layout import serve_entity_card
            new_uid = str(uuid.uuid4())
            children.append(serve_entity_card(new_uid))
            return children

        return children

    @app.callback(
        Output({"type": "entity-body", "index": MATCH}, "children"),
        Input({"type": "entity-type", "index": MATCH}, "value"),
        prevent_initial_call=True,
    )
    def render_fields(entity_type):
        uid = ctx.triggered_id["index"]
        if entity_type in ["protein", "rna", "dna"]:
            return [
                dbc.Textarea(id={"type": "sequence", "index": uid}, placeholder=">FASTA sequence", className="mb-2"),
                dbc.Input(id={"type": "bonded-ids", "index": uid}, placeholder="Bonded Atom Pairs (comma-separated)"),
            ]
        if entity_type == "ligand":
            return [
                dbc.Input(id={"type": "ligand-smiles", "index": uid}, placeholder="SMILES string", className="mb-2"),
                dbc.Input(id={"type": "ligand-ccd", "index": uid}, placeholder="CCD codes (comma-separated)"),
                dbc.Input(id={"type": "bonded-ids", "index": uid}, placeholder="Bonded Atom Pairs (comma-separated)"),
            ]
        if entity_type == "ion":
            return [
                dbc.Input(id={"type": "ion-name", "index": uid}, placeholder="Ion name", className="mb-2"),
                dbc.Input(id={"type": "bonded-ids", "index": uid}, placeholder="Bonded Atom Pairs (comma-separated)"),
            ]
        return []

    @app.callback(
        Output("json-preview-content", "children"),
        Output("json-collapse", "is_open"),
        Output("store-submission",        "data"),
        Input("generate-json-button", "n_clicks"),
        State("job-name", "value"),
        State({"type": "entity-card", "index": ALL}, "id"),
        State({"type": "entity-type", "index": ALL}, "value"),
        State({"type": "entity-copies", "index": ALL}, "value"),
        State({"type": "sequence",     "index": ALL}, "value"),
        State({"type": "ligand-smiles","index": ALL}, "value"),
        State({"type": "ligand-ccd",   "index": ALL}, "value"),
        State({"type": "ion-name",     "index": ALL}, "value"),
        State({"type": "bonded-ids",   "index": ALL}, "value"),
        prevent_initial_call=True,
    )
    def generate_json(
        n_clicks,
        job_name,
        card_ids,
        types,
        copies,
        seqs,
        smiles,
        ccds,
        ions,
        bonded
    ):
        if not job_name:
            return "Error: Job name is required.", True, None

        submission = build_submission(
            job_name,
            card_ids, types, copies,
            seqs, smiles, ccds,
            ions, bonded
        )

        submission_dict = submission.to_json()
        json_str = json.dumps(submission_dict, indent=2)
        return json_str, True, submission_dict

    @app.callback(
        Output("download-json", "data"),
        Input("download-json-button", "n_clicks"),
        State("job-name", "value"),
        State("json-preview-content", "children"),
        prevent_initial_call=True,
    )
    def download_json(n, job_name, json_str):
        safe_name = job_name.strip() or "af3_input"
        return dcc.send_string(json_str, filename=f"{safe_name}.json")

    @app.callback(
        Output("job-status", "children"),
        Output("job-status", "is_open"),
        Input("submit-job",          "n_clicks"),
        State("job-name",            "value"),
        State("email",               "value"),
        State("store-submission",    "data"),
        prevent_initial_call=True,
    )
    def submit_job(n_clicks, job_name, email, submission_dict):
        if not job_name:
            return "Error: Job name is required.", True
        if not email:
            return "Error: Email is required.", True
        if not submission_dict:
            return "Error: Generate JSON first.", True

        # create a timestamped job directory under ./jobs
        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        base = Path("jobs").resolve()
        job_dir = create_job_dir(base, job_name, ts)

        # write the AF3 input JSON
        json_path = write_json_input(job_dir, submission_dict)

        # write, submit the SLURM script, and capture the job ID
        try:
            job_id = write_and_submit_script(job_dir, email)
            msg = f"Job submitted (ID {job_id} TS {ts}). Notifications → {email}."
        except CalledProcessError as e:
            err = e.stderr.strip() or e.stdout.strip()
            msg = f"Submission failed: {err}"

        return msg, True

    @app.callback(
        Output("job-history-table", "children"),
        Output("store-history",       "data"),
        Input("tabs",                "value"),
    )
    def update_history(tab):
        if tab != "tab-history":
            return no_update, no_update

        # gather all completed job entries
        base = Path("jobs").resolve()
        entries = list_job_entries(base)

        # render the HTML table from those entries
        table = serve_history_table(entries)

        # return both the table and the raw entry list for later download callbacks
        return table, entries

    @app.callback(
        Output("download-results", "data"),
        Input({"type": "download-history", "index": ALL}, "n_clicks"),
        State("store-history", "data"),
        prevent_initial_call=True,
    )
    def download_results(n_clicks_list, history):
        """
        Streams back the ZIP file for the clicked row in the Job History table.
        """
        triggered = ctx.triggered_id
        if not (isinstance(triggered, dict) and triggered.get("type")=="download-history"):
            raise PreventUpdate
        idx = triggered["index"]

        if (n_clicks_list[idx] or 0) < 1:
            raise PreventUpdate

        # validate history entry
        if not history or idx >= len(history):
            raise PreventUpdate

        zip_path = Path(history[idx]["zip"])
        if not zip_path.is_file():
            raise PreventUpdate

        # send the file to the browser
        return dcc.send_file(str(zip_path))

    @app.callback(
        Output('uid-store', 'data'),
        Input('uid-store', 'data'),
        prevent_initial_call='initial_duplicate'
    )
    def fetch_user_uid(stored_data):
        if stored_data is None:
            http_uid = request.headers.get('HTTP_UID', 'USER_NOT_FOUND')
            return {'HTTP_UID': http_uid}
        return stored_data

    @app.callback(
        Output('display-uid', 'children'),
        Input('uid-store', 'data')
    )
    def display_uid(uid_data):
        if uid_data and 'HTTP_UID' in uid_data:
            return f"You are logged in as: {uid_data['HTTP_UID']}"
        return "Fetching your HTTP_UID..."
