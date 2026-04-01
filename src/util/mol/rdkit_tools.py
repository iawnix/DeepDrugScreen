import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem, Draw, rdmolops, DataStructs, rdFingerprintGenerator, rdDepictor, Descriptors
from rdkit.Chem.rdchem import Mol
from rdkit.DataStructs.cDataStructs import ExplicitBitVect
from rdkit.ML.Descriptors import MoleculeDescriptors




def load_mol(mol_f_type: str, mol_f: str) -> Mol:
    match mol_f_type:
        case "smi":
            mol = Chem.MolFromSmiles(smi, santize = True)
        case "mol":
            mol = 
        case "mol2":
            mol = Chem.MolFromMol2File()
        case "sdf":
            mol = 
        case "pdb":
            mol = Chem.MolFromPDBFile()
        case "pdbqt":

    return mol


def calc_morgan_fp(mol: Mol, radius: int = 2, n_bits: int = 1024, use_features: bool = False) -> ExplicitBitVect:
    morgan_generator = rdFingerprintGenerator.GetMorganGenerator(radius = radius, fpSize = n_bits)
    fp = morgan_generator.GetFingerprint(mol)
    return fp




