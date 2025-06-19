import pytest
from submission import AF3Submission


def test_validate_missing_name():
    sub = AF3Submission()
    assert sub.validate() == "Job name is required."


def test_validate_missing_entities():
    sub = AF3Submission(name="job1")
    assert sub.validate() == "At least one entity is required."


def test_validate_protein_sequence():
    sub = AF3Submission(name="job1")
    p = sub.add_entity("protein")
    # no sequence yet
    assert sub.validate() == "Sequence required for protein."
    p.sequence = "MATT"
    # now valid
    assert sub.validate() is None


def test_validate_ligand_must_have_smiles_or_ccd():
    sub = AF3Submission(name="job1")
    l = sub.add_entity("ligand")
    assert sub.validate() == "Ligand must have SMILES or CCD codes."
    l.smiles = "C(C(=O)O)N"
    assert sub.validate() is None


def test_validate_ion_name_required():
    sub = AF3Submission(name="job1")
    i = sub.add_entity("ion")
    assert sub.validate() == "Ion name is required for ion entities."
    i.ion_name = "NA"
    assert sub.validate() is None


def test_to_json_structure():
    sub = AF3Submission(name="job1")
    p = sub.add_entity("protein", copies=1)
    p.sequence = "MATT"
    l = sub.add_entity("ligand", copies=2)
    l.smiles = "CCO"
    i = sub.add_entity("ion", copies=1)
    i.ion_name = "NA"
    data = sub.to_json()

    # top‐level keys
    assert data["name"] == "job1"
    assert "modelSeeds" in data and isinstance(data["modelSeeds"], list)
    assert data["dialect"] == "alphafold3"
    assert data["version"] == 2

    # sequences list length = 1 protein + 1 ligand + 1 ion
    assert len(data["sequences"]) == 3

    # check protein entry
    prot = data["sequences"][0]["protein"]
    assert prot["sequence"] == "MATT"
    assert "id" in prot

    # check ligand entry
    lig = data["sequences"][1]["ligand"]
    assert lig["smiles"] == "CCO"
    assert isinstance(lig["id"], list) and len(lig["id"]) == 2

    # check ion entry
    ion = data["sequences"][2]["ligand"]
    assert ion["ccdCodes"] == ["NA"]
