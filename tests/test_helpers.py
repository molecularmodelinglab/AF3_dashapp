import json

import helpers


def test_create_job_dir(tmp_path):
    base = tmp_path
    job_dir = helpers.create_job_dir(base, "jobA", "20250101T000000")
    assert job_dir.exists() and job_dir.is_dir()
    assert (job_dir / "logs").exists() and (job_dir / "logs").is_dir()


def test_write_json_input(tmp_path):
    job_dir = tmp_path / "jobB"
    job_dir.mkdir()
    data = {"foo": 123, "bar": [1, 2, 3]}
    out = helpers.write_json_input(job_dir, data)
    assert out.exists()
    loaded = json.loads(out.read_text())
    assert loaded == data


def test_render_slurm_script(tmp_path):
    tpl = tmp_path / "tpl.sh"
    tpl.write_text(
        "Name={{JOBNAME}}\nEmail={{EMAIL}}\nWD={{WORKDIR}}\nTS={{TIMESTAMP}}"
    )
    script = helpers.render_slurm_script(
        job_name="myjob",
        email="me@x.com",
        workdir="/tmp/myjob",
        timestamp="20250101T000000",
        template_path=tpl,
    )
    assert "myjob" in script
    assert "me@x.com" in script
    assert "/tmp/myjob" in script
    assert "20250101T000000" in script


def test_list_job_entries(tmp_path):
    # create two valid job dirs
    for name, ts in [("run1", "20250101T010101"), ("run2", "20250102T020202")]:
        d = tmp_path / f"{name}_{ts}"
        d.mkdir()
        # create a ZIP fixture
        z = d / f"{name}_{ts}.zip"
        z.write_text("dummy")
    entries = helpers.list_job_entries(tmp_path)
    assert len(entries) == 2
    # Check format of timestamp
    assert entries[0]["timestamp"].startswith("2025/01/")
    assert entries[1]["timestamp"].startswith("2025/01/")


class DummyResult:
    def __init__(self, out="Submitted batch job 4242\n", err=""):
        self.stdout = out
        self.stderr = err


def test_write_and_submit_script(tmp_path, monkeypatch):
    # prepare job_dir
    job_dir = tmp_path / "myjob_20250103T030303"
    (job_dir / "logs").mkdir(parents=True)
    # monkey‐patch run (in helpers) and render_slurm_script
    monkeypatch.setattr(helpers, "run", lambda *args, **kwargs: DummyResult())
    monkeypatch.setattr(
        helpers,
        "render_slurm_script",
        lambda job_name, email, workdir, timestamp, template_path=None: "#!/bin/bash\necho hi\n",
    )

    # call the function
    job_id = helpers.write_and_submit_script(job_dir, email="me@x.com")
    assert job_id == "4242"

    # verify logs were written
    out = (job_dir / "logs" / "sbatch.out").read_text()
    err = (job_dir / "logs" / "sbatch.err").read_text()
    assert "Submitted batch job 4242" in out
    assert err == ""
