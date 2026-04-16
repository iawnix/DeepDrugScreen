import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem, Draw, rdmolops, DataStructs, rdFingerprintGenerator, rdDepictor, Descriptors
from rdkit.Chem.rdchem import Mol
from rdkit.DataStructs.cDataStructs import ExplicitBitVect
from rdkit.ML.Descriptors import MoleculeDescriptors

def load_mol(mol_f_type: str, mol_f: str, removeHs: bool = False, santize: bool = True) -> Mol:
    match mol_f_type:
        case "smi":
            mol = Chem.MolFromSmiles(mol_f, santize = santize, removeHs = removeHs)
        case "mol":
            mol = Chem.MolFromMolFile(mol_f, santize = santize, removeHs = removeHs)
        case "mol2":
            mol = Chem.MolFromMol2File(mol_f, santize = santize, removeHs = removeHs)
        case "sdf":
            mol = Chem.SDMolSupplier(mol_f, santize = santize, removeHs = removeHs)[0]
        case "pdb":
            mol = Chem.MolFromPDBFile(mol_f, santize = santize, removeHs = removeHs)
        case _:
            print("Error[iaw]:> UNsupport molecular type!")
            mol = None

    return mol


def calc_morgan_fp(mol: Mol, radius: int = 2, n_bits: int = 1024, use_features: bool = False) -> ExplicitBitVect:
    morgan_generator = rdFingerprintGenerator.GetMorganGenerator(radius = radius, fpSize = n_bits)
    fp = morgan_generator.GetFingerprint(mol)
    return fp




