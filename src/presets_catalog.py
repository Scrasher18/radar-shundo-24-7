"""
Catálogo escalable de Familias Evolutivas de Pokédex y Presets Inteligentes
para Eventos, Community Days, Master League/Raids, Mega Evoluciones y Meta PvP GBL.
"""

from typing import Any, Dict, List, Optional, Tuple
import requests

# Diccionario de especies frecuentes, Community Days, iniciales y Meta PvP (Nombre -> Familia de IDs Pokédex)
FAMILIAS_POKEDEX: Dict[str, List[int]] = {
    "bulbasaur": [1, 2, 3], "ivysaur": [1, 2, 3], "venusaur": [1, 2, 3],
    "charmander": [4, 5, 6], "charmeleon": [4, 5, 6], "charizard": [4, 5, 6],
    "squirtle": [7, 8, 9], "wartortle": [7, 8, 9], "blastoise": [7, 8, 9],
    "caterpie": [10, 11, 12], "weedle": [13, 14, 15], "beedrill": [13, 14, 15],
    "pidgey": [16, 17, 18], "pidgeot": [16, 17, 18],
    "pikachu": [25, 26, 172], "raichu": [25, 26, 172],
    "sandshrew": [27, 28], "sandslash": [27, 28],
    "nidoran": [29, 30, 31, 32, 33, 34], "nidoking": [32, 33, 34], "nidoqueen": [29, 30, 31],
    "clefairy": [35, 36, 173], "clefable": [35, 36, 173],
    "vulpix": [37, 38], "ninetales": [37, 38],
    "jigglypuff": [39, 40, 174], "wigglytuff": [39, 40, 174],
    "zubat": [41, 42, 169], "oddish": [43, 44, 45, 182],
    "diglett": [50, 51], "meowth": [52, 53, 863], "persian": [52, 53, 863],
    "psyduck": [54, 55], "mankey": [56, 57, 979], "primeape": [56, 57, 979], "annihilape": [56, 57, 979],
    "growlithe": [58, 59], "arcanine": [58, 59],
    "poliwag": [60, 61, 62, 186], "poliwrath": [60, 61, 62, 186], "politoed": [60, 61, 62, 186],
    "abra": [63, 64, 65], "alakazam": [63, 64, 65],
    "machop": [66, 67, 68], "machamp": [66, 67, 68],
    "bellsprout": [69, 70, 71], "victreebel": [69, 70, 71],
    "tentacool": [72, 73], "tentacruel": [72, 73],
    "geodude": [74, 75, 76], "golem": [74, 75, 76],
    "ponyta": [77, 78], "rapidash": [77, 78],
    "slowpoke": [79, 80, 199], "slowbro": [79, 80, 199], "slowking": [79, 80, 199],
    "magnemite": [81, 82, 462], "magnezone": [81, 82, 462],
    "seel": [86, 87], "dewgong": [86, 87],
    "grimer": [88, 89], "muk": [88, 89],
    "gastly": [92, 93, 94], "haunter": [92, 93, 94], "gengar": [92, 93, 94],
    "onix": [95, 208], "steelix": [95, 208],
    "cubone": [104, 105], "marowak": [104, 105],
    "hitmonlee": [106, 236], "hitmonchan": [107, 236],
    "lickitung": [108, 463], "lickilicky": [108, 463],
    "koffing": [109, 110], "weezing": [109, 110],
    "rhyhorn": [111, 112, 464], "rhyperior": [111, 112, 464],
    "chansey": [113, 242, 440], "blissey": [113, 242, 440],
    "kangaskhan": [115], "horsea": [116, 117, 230], "kingdra": [116, 117, 230],
    "scyther": [123, 212, 900], "scizor": [123, 212, 900],
    "electabuzz": [125, 239, 466], "electivire": [125, 239, 466],
    "magmar": [126, 240, 467], "magmortar": [126, 240, 467],
    "pinsir": [127], "magikarp": [129, 130], "gyarados": [129, 130],
    "lapras": [131], "eevee": [133, 134, 135, 136, 196, 197, 470, 471, 700],
    "umbreon": [133, 197], "sylveon": [133, 700],
    "porygon": [137, 233, 474], "aerodactyl": [142], "snorlax": [143, 446],
    "dratini": [147, 148, 149], "dragonair": [147, 148, 149], "dragonite": [147, 148, 149],
    "chikorita": [152, 153, 154], "meganium": [152, 153, 154],
    "cyndaquil": [155, 156, 157], "typhlosion": [155, 156, 157],
    "totodile": [158, 159, 160], "feraligatr": [158, 159, 160],
    "sentret": [161, 162], "hoothoot": [163, 164], "noctowl": [163, 164],
    "chinchou": [170, 171], "lanturn": [170, 171],
    "togetic": [175, 176, 468], "togekiss": [175, 176, 468],
    "mareep": [179, 180, 181], "ampharos": [179, 180, 181],
    "marill": [183, 184, 298], "azumarill": [183, 184, 298],
    "hoppip": [187, 188, 189], "jumpluff": [187, 188, 189],
    "wooper": [194, 195, 980], "quagsire": [194, 195, 980], "clodsire": [194, 195, 980],
    "dunsparce": [206, 982], "gligar": [207, 472], "gliscor": [207, 472],
    "heracross": [214], "sneasel": [215, 461, 903], "weavile": [215, 461], "sneasler": [215, 903],
    "teddiursa": [216, 217, 901], "ursaluna": [216, 217, 901],
    "swinub": [220, 221, 473], "mamoswine": [220, 221, 473],
    "skarmory": [227], "houndour": [228, 229], "houndoom": [228, 229],
    "larvitar": [246, 247, 248], "tyranitar": [246, 247, 248],
    "treecko": [252, 253, 254], "sceptile": [252, 253, 254],
    "torchic": [255, 256, 257], "blaziken": [255, 256, 257],
    "mudkip": [258, 259, 260], "swampert": [258, 259, 260],
    "zigzagoon": [263, 264, 862], "obstagoon": [263, 264, 862],
    "lotad": [270, 271, 272], "seedot": [273, 274, 275], "wingull": [278, 279], "pelipper": [278, 279],
    "ralts": [280, 281, 282, 475], "gardevoir": [280, 281, 282, 475], "gallade": [280, 281, 282, 475],
    "slakoth": [287, 288, 289], "vigoroth": [287, 288, 289],
    "whismur": [293, 294, 295], "exploud": [293, 294, 295],
    "makuhita": [296, 297], "hariyama": [296, 297],
    "sableye": [302], "mawile": [303], "aron": [304, 305, 306], "aggron": [304, 305, 306],
    "meditite": [307, 308], "medicham": [307, 308],
    "electrike": [309, 310], "manectric": [309, 310],
    "roselia": [315, 406, 407], "roserade": [315, 406, 407],
    "carvanha": [318, 319], "sharpedo": [318, 319],
    "numel": [322, 323], "camerupt": [322, 323],
    "trapinch": [328, 329, 330], "flygon": [328, 329, 330],
    "swablu": [333, 334], "altaria": [333, 334],
    "barboach": [339, 340], "whiscash": [339, 340],
    "feebas": [349, 350], "milotic": [349, 350],
    "shuppet": [353, 354], "banette": [353, 354],
    "duskull": [355, 356, 477], "dusknoir": [355, 356, 477],
    "absol": [359], "snorunt": [361, 362, 478], "glalie": [361, 362, 478],
    "spheal": [363, 364, 365], "walrein": [363, 364, 365],
    "bagon": [371, 372, 373], "salamence": [371, 372, 373],
    "beldum": [374, 375, 376], "metang": [374, 375, 376], "metagross": [374, 375, 376],
    "turtwig": [387, 388, 389], "torterra": [387, 388, 389],
    "chimchar": [390, 391, 392], "infernape": [390, 391, 392],
    "piplup": [393, 394, 395], "empoleon": [393, 394, 395],
    "starly": [396, 397, 398], "shinx": [403, 404, 405], "luxray": [403, 404, 405],
    "cranidos": [408, 409], "rampardos": [408, 409],
    "shieldon": [410, 411], "bastiodon": [410, 411],
    "shellos": [422, 423], "gastrodon": [422, 423],
    "drifloon": [425, 426], "drifblim": [425, 426],
    "buneary": [427, 428], "lopunny": [427, 428],
    "gible": [443, 444, 445], "garchomp": [443, 444, 445],
    "riolu": [447, 448], "lucario": [447, 448],
    "skorupi": [451, 452], "drapion": [451, 452],
    "snover": [459, 460], "abomasnow": [459, 460],
    "snivy": [495, 496, 497], "serperior": [495, 496, 497],
    "tepig": [498, 499, 500], "emboar": [498, 499, 500],
    "oshawott": [501, 502, 503], "samurott": [501, 502, 503],
    "lillipup": [506, 507, 508], "roggenrola": [524, 525, 526], "gigalith": [524, 525, 526],
    "audino": [531], "timburr": [532, 533, 534], "conkeldurr": [532, 533, 534],
    "tympole": [535, 536, 537], "seismitoad": [535, 536, 537],
    "sewaddle": [540, 541, 542], "leavanny": [540, 541, 542],
    "venipede": [543, 544, 545], "cottonee": [546, 547], "whimsicott": [546, 547],
    "sandile": [551, 552, 553], "scraggy": [559, 560], "scrafty": [559, 560],
    "yamask": [562, 563, 867], "cofagrigus": [562, 563, 867], "runerigus": [562, 563, 867],
    "frillish": [592, 593], "jellicent": [592, 593],
    "ferroseed": [597, 598], "ferrothorn": [597, 598],
    "tynamo": [602, 603, 604], "litwick": [607, 608, 609], "chandelure": [607, 608, 609],
    "axew": [610, 611, 612], "haxorus": [610, 611, 612],
    "shelmet": [616, 617], "accelgor": [616, 617],
    "stunfisk": [618], "mienfoo": [619, 620], "mienshao": [619, 620],
    "vullaby": [629, 630], "mandibuzz": [629, 630],
    "deino": [633, 634, 635], "hydreigon": [633, 634, 635],
    "chespin": [650, 651, 652], "chesnaught": [650, 651, 652],
    "fennekin": [653, 654, 655], "delphox": [653, 654, 655],
    "froakie": [656, 657, 658], "greninja": [656, 657, 658],
    "bunnelby": [659, 660], "diggersby": [659, 660],
    "fletchling": [661, 662, 663], "talonflame": [661, 662, 663],
    "pancham": [674, 675], "pangoro": [674, 675],
    "inkay": [686, 687], "malamar": [686, 687],
    "carbink": [703], "goomy": [704, 705, 706], "goodra": [704, 705, 706],
    "phantump": [708, 709], "trevenant": [708, 709],
    "noibat": [714, 715], "noivern": [714, 715],
    "rowlet": [722, 723, 724], "decidueye": [722, 723, 724],
    "litten": [725, 726, 727], "incineroar": [725, 726, 727],
    "popplio": [728, 729, 730], "primarina": [728, 729, 730],
    "grubbin": [736, 737, 738], "charjabug": [736, 737, 738], "vikavolt": [736, 737, 738],
    "mareanie": [747, 748], "toxapex": [747, 748],
    "stufful": [759, 760], "bewear": [759, 760],
    "bounsweet": [761, 762, 763], "tsareena": [761, 762, 763],
    "jangmo-o": [782, 783, 784], "kommo-o": [782, 783, 784],
    "rookidee": [821, 822, 823], "corviknight": [821, 822, 823],
    "dreepy": [885, 886, 887], "dragapult": [885, 886, 887],
    "sprigatito": [906, 907, 908], "fuecoco": [909, 910, 911], "quaxly": [912, 913, 914],
    "lechonk": [915, 916], "smoliv": [928, 929, 930], "frigibax": [996, 997, 998],
}

# Catálogo de Presets de 1 comando para #🎉-evento-cd
PRESETS_EVENTO: Dict[str, Dict[str, Any]] = {
    "master": {
        "titulo": "👑 Preset: Top Master League & Raids (Pseudo-Legendarios)",
        "pokemones": [
            "Dratini", "Larvitar", "Bagon", "Beldum", "Gible", "Deino",
            "Axew", "Goomy", "Jangmo-o", "Dreepy", "Frigibax", "Rhyhorn",
            "Swinub", "Machop", "Timburr", "Ralts", "Cranidos", "Litwick",
            "Magnemite", "Togetic", "Chansey", "Snorlax",
        ],
        "incluir_shundos_100": True,
        "incluir_pvp_gl": False,
        "incluir_pvp_ul": False,
    },
    "mega": {
        "titulo": "🧬 Preset: Todos los Pokémon con Mega Evolución",
        "pokemones": [
            "Charmander", "Bulbasaur", "Squirtle", "Beldum", "Bagon", "Gible",
            "Larvitar", "Ralts", "Magikarp", "Gastly", "Abra", "Scyther",
            "Swablu", "Aron", "Meditite", "Mareep", "Houndour", "Carvanha",
            "Numel", "Snover", "Buneary", "Riolu", "Pidgey", "Weedle",
            "Slowpoke", "Onix", "Pinsir", "Aerodactyl", "Kangaskhan", "Heracross",
            "Sableye", "Mawile", "Electrike", "Shuppet", "Absol", "Snorunt",
        ],
        "incluir_shundos_100": True,
        "incluir_pvp_gl": False,
        "incluir_pvp_ul": False,
    },
    "meta": {
        "titulo": "🔥 Preset: Top Meta PvP GBL (Great & Ultra League)",
        "pokemones": [
            "Mankey", "Wooper", "Totodile", "Marill", "Mudkip", "Froakie",
            "Fuecoco", "Snivy", "Fletchling", "Rookidee", "Bunnelby", "Jigglypuff",
            "Clefairy", "Hoppip", "Gligar", "Barboach", "Shieldon", "Lickitung",
            "Yamask", "Frillish", "Ferroseed", "Phantump", "Mareanie", "Spheal",
            "Swinub", "Poliwag", "Grimer", "Tentacool", "Onix", "Eevee",
            "Skarmory", "Shellos", "Skorupi", "Vullaby", "Inkay", "Carbink", "Dunsparce",
        ],
        "incluir_shundos_100": False,
        "incluir_pvp_gl": True,
        "incluir_pvp_ul": True,
    },
    "iniciales": {
        "titulo": "🌱🔥💧 Preset: Todos los Iniciales (Gen 1 a Gen 9)",
        "pokemones": [
            "Bulbasaur", "Charmander", "Squirtle", "Chikorita", "Cyndaquil", "Totodile",
            "Treecko", "Torchic", "Mudkip", "Turtwig", "Chimchar", "Piplup",
            "Snivy", "Tepig", "Oshawott", "Chespin", "Fennekin", "Froakie",
            "Rowlet", "Litten", "Popplio", "Sprigatito", "Fuecoco", "Quaxly",
        ],
        "incluir_shundos_100": True,
        "incluir_pvp_gl": True,
        "incluir_pvp_ul": True,
    },
}


def obtener_preset(nombre_clave: str) -> Optional[Dict[str, Any]]:
    """Busca un preset por nombre o alias."""
    clave = nombre_clave.strip().lower()
    alias_map = {
        "raids": "master",
        "raid": "master",
        "ml": "master",
        "megas": "mega",
        "gbl": "meta",
        "pvp": "meta",
        "starters": "iniciales",
    }
    clave_real = alias_map.get(clave, clave)
    return PRESETS_EVENTO.get(clave_real)


def resolver_nombres_e_ids(entradas_crudas: List[str]) -> Tuple[List[str], List[int]]:
    """Convierte una lista de nombres o IDs (ej. ['Mankey', '374']) en nombres limpios e IDs de Pokédex."""
    nombres_finales: List[str] = []
    ids_finales: List[int] = []

    for item in entradas_crudas:
        limpio = item.strip().lower()
        if not limpio:
            continue
        if limpio.isdigit():
            pid = int(limpio)
            if pid not in ids_finales:
                ids_finales.append(pid)
            etiqueta = f"#{pid}"
            for nom_k, fam_ids in FAMILIAS_POKEDEX.items():
                if pid == fam_ids[0]:
                    etiqueta = nom_k.capitalize()
                    for fid in fam_ids:
                        if fid not in ids_finales:
                            ids_finales.append(fid)
                    break
            if etiqueta not in nombres_finales:
                nombres_finales.append(etiqueta)
        else:
            nom_cap = limpio.capitalize()
            if nom_cap not in nombres_finales:
                nombres_finales.append(nom_cap)
            if limpio in FAMILIAS_POKEDEX:
                for fid in FAMILIAS_POKEDEX[limpio]:
                    if fid not in ids_finales:
                        ids_finales.append(fid)
            else:
                try:
                    r_poke = requests.get(f"https://pokeapi.co/api/v2/pokemon/{limpio}", timeout=4)
                    if r_poke.status_code == 200:
                        pid_api = int(r_poke.json().get("id") or 0)
                        if pid_api > 0 and pid_api not in ids_finales:
                            ids_finales.append(pid_api)
                except Exception:
                    pass

    return nombres_finales, ids_finales
