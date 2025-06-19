import json
from datetime import datetime
from pathlib import Path
from subprocess import run

from submission import AF3Submission


def create_job_dir(base: Path, job_name: str, ts: str) -> Path:
    """
    Create a timestamped job directory under `base` and ensure a logs subdirectory exists.
    """
    job_dir = base / f"{job_name}_{ts}"
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "logs").mkdir(exist_ok=True)
    return job_dir

def write_json_input(job_dir: Path, submission_dict: dict) -> Path:
    """
    Serialize the AF3 submission dict to `input.json` in the job directory.
    """
    path = job_dir / "input.json"
    path.write_text(json.dumps(submission_dict, indent=2))
    return path

def render_slurm_script(
    job_name: str,
    email: str,
    workdir: str,
    timestamp: str,
    template_path: Path = Path("templates") / "submit_template.sh"
) -> str:
    """
    Load SLURM template and replace placeholders:
      {{JOBNAME}}   → job name
      {{EMAIL}}     → user email for notifications
      {{WORKDIR}}   → working directory to cd into
      {{TIMESTAMP}} → timestamp used to name the results ZIP
    """
    tpl = template_path.read_text()
    script = (
        tpl
        .replace("{{JOBNAME}}", job_name)
        .replace("{{EMAIL}}", email)
        .replace("{{WORKDIR}}", workdir)
        .replace("{{TIMESTAMP}}", timestamp)
    )
    return script

def write_and_submit_script(
    job_dir: Path,
    email: str,
    template_path: Path = Path("templates") / "submit_template.sh"
) -> str:
    """
    Render the SLURM submission script (including zipping & cleanup steps),
    write it to disk, submit it via sbatch, and capture the job ID.

    Returns the Slurm job ID.
    """
    job_name, timestamp = job_dir.name.rsplit("_")[-2:]
    # render & write the submission script
    script_text = render_slurm_script(
        job_name,
        email,
        str(job_dir),
        timestamp,
        template_path
    )
    script_file = job_dir / "submit.sh"
    script_file.write_text(script_text)

    # submit the job
    result = run(
        ["sbatch", str(script_file)],
        capture_output=True,
        text=True,
        check=True
    )

    # write sbatch logs
    logs_dir = job_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    (logs_dir / "sbatch.out").write_text(result.stdout)
    (logs_dir / "sbatch.err").write_text(result.stderr)

    # return the job ID
    return result.stdout.strip().split()[-1]

def list_job_entries(base: Path) -> list[dict]:
    """
    Scan the `base` jobs directory for job subfolders.
    Returns a list of dicts with:
      - name: the folder name (jobname)
      - timestamp: the timestamp portion
      - zip: absolute path to results_<timestamp>.zip if it exists
    """
    entries = []
    if not base.exists():
        return entries
    
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        parts = d.name.rsplit("_", 1)
        if len(parts) != 2:
            continue
        job_name = parts[0]
        ts = parts[1]
        ts_readable = datetime.strptime(ts, "%Y%m%dT%H%M%S").strftime("%Y/%m/%d - %H:%M:%S")
        zip_file = d / f"{job_name}_{ts}.zip"
        if not zip_file.exists():
            continue
        entries.append({
            "name":      job_name,
            "timestamp": ts_readable,
            "zip":       str(zip_file)
        })
    return entries

def build_submission(
    job_name: str,
    card_ids: list[str],
    types: list[str],
    copies: list[str],
    seqs: list[str],
    smiles: list[str],
    ccds: list[str],
    ions: list[str],
    bonded: list[str]
) -> AF3Submission:
    """Build an AF3Submission object from the provided parameters."""

    seq_i = smile_i = ccd_i = ion_i = bonded_i = 0
    submission = AF3Submission(name=job_name)

    for i, card in enumerate(card_ids):
        t = types[i]
        if not t:
            continue

        cnt = int(copies[i] or 1)
        ent = submission.add_entity(t, cnt)

        if t in ["protein", "rna", "dna"]:
            ent.sequence = (seqs[seq_i] or "").strip()
            seq_i += 1

        elif t == "ligand":
            ent.smiles = (smiles[smile_i] or "").strip()
            smile_i += 1

            ent.ccd_codes = [
                c.strip() for c in (ccds[ccd_i] or "").split(",") if c.strip()
            ]
            ccd_i += 1

        else:  # ion
            ent.ion_name = (ions[ion_i] or "").strip()
            ion_i += 1

        raw_bond = bonded[bonded_i] or ""
        bonded_i += 1
        ent.bonded_atom_pairs = [
            b.strip() for b in raw_bond.split(",") if b.strip()
        ]

    return submission



