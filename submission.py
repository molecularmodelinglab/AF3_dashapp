import random
import string

class Entity:
    def __init__(self, entity_type, copies=1):
        self.type = entity_type
        self.copies = copies
        self.sequence = None
        self.smiles = None
        self.ccd_codes = []
        self.ion_name = None
        self.bonded_atom_pairs = []

class AF3Submission:
    def __init__(self, name='', email=None):
        self.name = name
        self.email = email
        self.entities = []
        self._id_counter = 0

    def _next_label(self):
        """Generate labels: A, B, ..., Z, AA, AB, ..."""
        n = self._id_counter
        label = ''
        while True:
            label = string.ascii_uppercase[n % 26] + label
            n = n // 26 - 1
            if n < 0:
                break
        self._id_counter += 1
        return label

    def add_entity(self, entity_type, copies=1):
        ent = Entity(entity_type, copies)
        self.entities.append(ent)
        return ent

    def validate(self):
        if not self.name:
            return 'Job name is required.'
        if not self.entities:
            return 'At least one entity is required.'
        for ent in self.entities:
            if ent.type in ['protein', 'rna', 'dna']:
                if not ent.sequence:
                    return f'Sequence required for {ent.type}.'
            if ent.type == 'ligand':
                if not (ent.smiles or ent.ccd_codes):
                    return 'Ligand must have SMILES or CCD codes.'
            if ent.type == 'ion':
                if not ent.ion_name:
                    return 'Ion name is required for ion entities.'
        return None

    def to_json(self):
        sequences = []
        for ent in self.entities:
            # generate unique labels per copy
            labels = [self._next_label() for _ in range(ent.copies)]
            entity_id = labels[0] if ent.copies == 1 else labels

            if ent.type in ['protein', 'rna', 'dna']:
                entry = {
                    ent.type: {
                        'id': entity_id,
                        'sequence': ent.sequence
                    }
                }
                if ent.bonded_atom_pairs:
                    entry[ent.type]['bondedAtomPairs'] = ent.bonded_atom_pairs
                sequences.append(entry)

            elif ent.type == 'ligand':
                lig = {'id': entity_id}
                if ent.smiles:
                    lig['smiles'] = ent.smiles
                if ent.ccd_codes:
                    lig['ccdCodes'] = ent.ccd_codes
                if ent.bonded_atom_pairs:
                    lig['bondedAtomPairs'] = ent.bonded_atom_pairs
                sequences.append({'ligand': lig})

            elif ent.type == 'ion':
                lig = {'id': entity_id, 'ccdCodes': [ent.ion_name]}
                if ent.bonded_atom_pairs:
                    lig['bondedAtomPairs'] = ent.bonded_atom_pairs
                sequences.append({'ligand': lig})

        return {
            'name': self.name,
            'modelSeeds': [random.randint(1, 100)],
            'sequences': sequences,
            'dialect': 'alphafold3',
            'version': 2
        }
    
    