"""Graphes RDF.

"""

from uuid import UUID, uuid4
from pathlib import Path

from rdflib import Graph, URIRef

from plume.rdf.namespaces import PlumeNamespaceManager, DCAT, RDF

class Metagraph(Graph):
    """Graphes de métadonnées.
    
    Un graphe de métadonnées décrit un et un seul jeu de données
    (dcat:Dataset).
    
    Notes
    -----   
    Tous les graphes de métadonnées sont initialisés avec
    l'espace de nommage standard de Plume
    (:py:class:`plume.rdf.namespaces.PlumeNamespaceManager`).
    
    """
    def __init__(self):
        super().__init__(namespace_manager=PlumeNamespaceManager())


def uuid_from_datasetid(datasetid):
    """Extrait l'UUID d'un identifiant de jeu de données.
    
    Parameters
    ----------
    datasetid : URIRef
        Un identifiant de jeu de données.
    
    Returns
    -------
    uuid.UUID
        L'UUID contenu dans l'identifiant. ``None`` si l'identifiant
        ne contenait pas d'UUID.
    
    """
    try:
        u = UUID(str(datasetid))
        return u
    except:
        r = re.search('[:]([a-z0-9-]{36})$', str(datasetid))
        if r:
            try:
                u = UUID(r[1])
                return u
            except:
                return

def datasetid_from_uuid(uuid):
    """Crée un identifiant de jeu de données à partir d'un UUID.
    
    Parameters
    ----------
    uuid : uuid.UUID or str
        Un UUID ou une chaîne de caractères présumée
        être un UUID.
    
    Returns
    -------
    URIRef
        Un identifiant de jeu de données. ``None`` si la valeur n'était
        pas un UUID.
    
    """
    if not isinstance(uuid, UUID):
        try:
            uuid = UUID(uuid)
        except:
            return
    return URIRef(uuid.urn)

def get_datasetid(anygraph):
    """Renvoie l'identifiant du jeu de données éventuellement contenu dans le graphe.
    
    Parameters
    ----------
    anygraph : Graph
        Un graphe quelconque, présumé contenir la description d'un
        jeu de données (``dcat:Dataset``).
    
    Returns
    -------
    URIRef
        L'identifiant du jeu de données. None si le graphe ne contenait
        pas de jeu de données.
    
    """
    for s in anygraph.subjects(RDF.type, DCAT.Dataset):
        return s

def graph_from_file(filepath, format=None):
    """Désérialise le contenu d'un fichier sous forme de graphe.
    
    Le fichier sera présumé être encodé en UTF-8 et mieux
    vaudrait qu'il le soit.
    
    Parameters
    ----------
    filepath : str
        Chemin complet du fichier source, supposé contenir des
        métadonnées dans un format RDF, sans quoi l'import échouera.
    format : str
        Le format des métadonnées. Si non renseigné, il est autant que
        possible déduit de l'extension du fichier, qui devra donc être
        cohérente avec son contenu. Valeurs acceptées : 'turtle',
        'json-ld', 'xml', 'n3', 'nt', 'trig'.
    
    Returns
    -------
    Graph
        Un graphe.
    """
    pfile = Path(filepath)
    
    if not pfile.exists():
        raise FileNotFoundError("Can't find file {}.".format(filepath))
        
    if not pfile.is_file():
        raise TypeError("{} is not a file.".format(filepath))
    
    if format and not format in import_formats():
        raise ValueError("Format '{}' is not supported.".format(format))
    
    if not format:
        if not pfile.suffix in import_extensions_from_format():
            raise TypeError("Couldn't guess RDF format from file extension." \
                            "Please use format to declare it manually.")
                            
        else:
            format = import_format_from_extension(pfile.suffix)
            # NB : en théorie, la fonction parse de RDFLib est censée
            # pouvoir reconnaître le format d'après l'extension, mais à
            # ce jour elle n'identifie même pas toute la liste ci-avant.
    
    with pfile.open(encoding='UTF-8') as src:
        g = Graph().parse(data=src.read(), format=format)
    return g

def import_formats():
    """Renvoie la liste de tous les formats disponibles pour l'import.
    
    Returns
    -------
    list of str
        La liste des formats reconnus par RDFLib à l'import.
    
    """
    return [ k for k, v in rdflib_formats.items() if v['import'] ]

def export_formats():
    """Renvoie la liste de tous les formats disponibles pour l'export.
    
    Returns
    -------
    list of str
        La liste des formats reconnus par RDFLib à l'export.
    
    """
    return [ k for k in rdflib_formats.keys() ]

def import_extensions_from_format(format=None):
    """Renvoie la liste des extensions associées à un format d'import.
    
    Parameters
    ----------
    format : str, optional
        Un format d'import présumé inclus dans la liste des formats
        reconnus par les fonctions de RDFLib (rdflib_formats avec
        import=True).
    
    Returns
    -------
    list of str
        La liste de toutes les extensions associées au format considéré,
        avec le point.
        Si `format` n'est pas renseigné, la fonction renvoie la liste
        de toutes les extensions reconnues pour l'import.
    
    Example
    -------
    >>> rdf_utils.import_extensions('xml')
    ['.rdf', '.xml']
    
    """
    if not format:
        l = []
        for k, d in rdflib_formats.items():
            if d['import']:
                l += d['extensions']
        return l
    
    d = rdflib_formats.get(format)
    if d and d['import']:
        return d['extensions']

def export_extension_from_format(format):
    """Renvoie l'extension utilisée pour les exports dans le format considéré.
    
    Parameters
    ----------
    format : str
        Un format d'export présumé inclus dans la liste des formats
        reconnus par les fonctions de RDFLib (rdflib_format).
    
    Returns
    -------
    str
        L'extension à utiliser pour le format considéré, avec le point.
    
    Example
    -------
    >>> rdf_utils.export_extension('pretty-xml')
    '.rdf'
    
    """
    d = rdflib_formats.get(format)
    if d:
        return d['extensions'][0]

def import_format_from_extension(extension):
    """Renvoie le format d'import correspondant à l'extension.
    
    Parameters
    ----------
    extension : str
        Une extension (avec point).
    
    Returns
    -------
    str
        Un nom de format. La fonction renvoie None si l'extension
        n'est pas reconnue.
    
    """
    for k, d in rdflib_formats.items():
        if d['import'] and extension in d['extensions']:
            return k

def export_format_from_extension(extension):
    """Renvoie le format d'export correspondant à l'extension.
    
     Parameters
    ----------
    extension : str
        Une extension (avec point).
    
    Returns
    -------
    str
        Un nom de format. La fonction renvoie None si l'extension
        n'est pas reconnue.
    
    """
    for k, d in rdflib_formats.items():
        if d['export default'] and extension in d['extensions']:
            return k

rdflib_formats = {
    'turtle': {
        'extensions': ['.ttl'],
        'import': True,
        'export default': True
        },
    'n3': {
        'extensions': ['.n3'],
        'import': True,
        'export default': True
        },
    'json-ld': {
        'extensions': ['.jsonld', '.json'],
        'import': True,
        'export default': True
        },
    'xml': {
        'extensions': ['.rdf', '.xml'],
        'import': True,
        'export default': False
        },
    'pretty-xml': {
        'extensions': ['.rdf', '.xml'],
        'import': False,
        'export default': True
        },
    'nt': {
        'extensions': ['.nt'],
        'import': True,
        'export default': True
        },
    'trig': {
        'extensions': ['.trig'],
        'import': True,
        'export default': True
        }
    }
"""Formats reconnus par les fonctions de RDFLib.

Si la clé `import` vaut False, le format n'est pas reconnu
à l'import. Si `export default` vaut True, il s'agit du
format d'export privilégié pour les extensions listées
par la clé `extension`.

"""
    
    