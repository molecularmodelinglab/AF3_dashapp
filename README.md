# AlphaFold3 Dash App

A user-friendly web interface for submitting AlphaFold3 jobs to a Slurm-powered compute cluster. Built with [Dash](https://dash.plotly.com/) and Bootstrap, this app lets researchers with minimal computational background define protein, ligand, and ion entities, generate the necessary JSON input, and submit jobs—all without writing a single line of shell script.

---

## 🚀 Features

- **Intuitive UI**: Add and configure entities (protein, ligand, ion) through dynamic cards.
- **JSON Generation**: One-click generation and pretty-printing of the `input.json` for AlphaFold3.
- **Downloadable Inputs**: Download your JSON input named after your job.
- **SLURM Submission**: Automatically render and submit a Singularity-based Slurm script.
- **Job Tracking**: View a Job History table with timestamps and download result archives (`.zip`).
- **Responsive Design**: Mobile-friendly layout using Bootstrap and custom CSS effects.
- **Extensible Helpers**: Core logic factored into testable Python helpers and a pure `AF3Submission` model.

---

## 🛠️ Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/molecularmodelinglab/AF3_dashapp.git
   cd AF3_dashapp
   ```

2. **Create a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**

   ```bash
   python app.py
   ```

   Then open your browser to `http://localhost:8050`.

---

## 📂 Project Structure

```text
├── app.py                 # Entry point, wires layout + callbacks
├── layout.py              # Defines Dash layout and custom components
├── callbacks.py           # Dash callback registrations
├── helpers.py             # File I/O, Slurm script rendering, job-directory logic
├── submission.py          # AF3Submission model: validate & JSON serialization
├── assets/
│   └── style.css          # Custom CSS for button effects, layout tweaks
├── templates/
│   └── submit_template.sh # Slurm + Singularity submission script template
├── jobs/                  # (git-ignored) Per-job directories with inputs & results
├── tests/                 # pytest suite for submission & helper modules
└── requirements.txt       # Python dependencies
```

---

## 📝 Usage Guide

1. **Submit Job**

   - Enter a **Job Name** and your **Email** for notifications.
   - Click **Add Entity** to include proteins, ligands, or ions. Specify sequences or SMILES/CCD codes and bonded atom pairs.
   - Click **Generate JSON** to preview the `input.json`.
   - Click **Download JSON** to save the file if you need to.
   - Finally, click **Submit Job** to render and dispatch the Slurm script. You’ll see a confirmation with your Slurm Job ID.

2. **Job History**

   - Switch to the **Job History** tab.
   - A table lists all completed runs with their timestamps.
   - Click **Download** in any row to fetch the `<jobname>_<timestamp>.zip` archive of AlphaFold3 outputs.

---

## ✅ Testing

We use [pytest](https://docs.pytest.org/) for unit tests of both the core `AF3Submission` model and the helper utilities.

```bash
# from the repo root
pytest
```

All tests live under `tests/` and rely on built-in fixtures like `tmp_path` and `monkeypatch` for isolation.

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome! Please:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-idea`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/your-idea`)
5. Open a Pull Request

Please ensure new code is covered by tests and follows the existing style (run `black .` and `flake8`).

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

