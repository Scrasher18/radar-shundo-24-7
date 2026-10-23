"""
Catálogo completo de la Pokédex Nacional (Gen 1 a Gen 9 - 1025 especies)
para Autocompletado de Slash Commands en Discord.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

POKEDEX_1025 = [
  {
    "id": 1,
    "slug": "bulbasaur",
    "name": "Bulbasaur"
  },
  {
    "id": 2,
    "slug": "ivysaur",
    "name": "Ivysaur"
  },
  {
    "id": 3,
    "slug": "venusaur",
    "name": "Venusaur"
  },
  {
    "id": 4,
    "slug": "charmander",
    "name": "Charmander"
  },
  {
    "id": 5,
    "slug": "charmeleon",
    "name": "Charmeleon"
  },
  {
    "id": 6,
    "slug": "charizard",
    "name": "Charizard"
  },
  {
    "id": 7,
    "slug": "squirtle",
    "name": "Squirtle"
  },
  {
    "id": 8,
    "slug": "wartortle",
    "name": "Wartortle"
  },
  {
    "id": 9,
    "slug": "blastoise",
    "name": "Blastoise"
  },
  {
    "id": 10,
    "slug": "caterpie",
    "name": "Caterpie"
  },
  {
    "id": 11,
    "slug": "metapod",
    "name": "Metapod"
  },
  {
    "id": 12,
    "slug": "butterfree",
    "name": "Butterfree"
  },
  {
    "id": 13,
    "slug": "weedle",
    "name": "Weedle"
  },
  {
    "id": 14,
    "slug": "kakuna",
    "name": "Kakuna"
  },
  {
    "id": 15,
    "slug": "beedrill",
    "name": "Beedrill"
  },
  {
    "id": 16,
    "slug": "pidgey",
    "name": "Pidgey"
  },
  {
    "id": 17,
    "slug": "pidgeotto",
    "name": "Pidgeotto"
  },
  {
    "id": 18,
    "slug": "pidgeot",
    "name": "Pidgeot"
  },
  {
    "id": 19,
    "slug": "rattata",
    "name": "Rattata"
  },
  {
    "id": 20,
    "slug": "raticate",
    "name": "Raticate"
  },
  {
    "id": 21,
    "slug": "spearow",
    "name": "Spearow"
  },
  {
    "id": 22,
    "slug": "fearow",
    "name": "Fearow"
  },
  {
    "id": 23,
    "slug": "ekans",
    "name": "Ekans"
  },
  {
    "id": 24,
    "slug": "arbok",
    "name": "Arbok"
  },
  {
    "id": 25,
    "slug": "pikachu",
    "name": "Pikachu"
  },
  {
    "id": 26,
    "slug": "raichu",
    "name": "Raichu"
  },
  {
    "id": 27,
    "slug": "sandshrew",
    "name": "Sandshrew"
  },
  {
    "id": 28,
    "slug": "sandslash",
    "name": "Sandslash"
  },
  {
    "id": 29,
    "slug": "nidoran-f",
    "name": "Nidoran F"
  },
  {
    "id": 30,
    "slug": "nidorina",
    "name": "Nidorina"
  },
  {
    "id": 31,
    "slug": "nidoqueen",
    "name": "Nidoqueen"
  },
  {
    "id": 32,
    "slug": "nidoran-m",
    "name": "Nidoran M"
  },
  {
    "id": 33,
    "slug": "nidorino",
    "name": "Nidorino"
  },
  {
    "id": 34,
    "slug": "nidoking",
    "name": "Nidoking"
  },
  {
    "id": 35,
    "slug": "clefairy",
    "name": "Clefairy"
  },
  {
    "id": 36,
    "slug": "clefable",
    "name": "Clefable"
  },
  {
    "id": 37,
    "slug": "vulpix",
    "name": "Vulpix"
  },
  {
    "id": 38,
    "slug": "ninetales",
    "name": "Ninetales"
  },
  {
    "id": 39,
    "slug": "jigglypuff",
    "name": "Jigglypuff"
  },
  {
    "id": 40,
    "slug": "wigglytuff",
    "name": "Wigglytuff"
  },
  {
    "id": 41,
    "slug": "zubat",
    "name": "Zubat"
  },
  {
    "id": 42,
    "slug": "golbat",
    "name": "Golbat"
  },
  {
    "id": 43,
    "slug": "oddish",
    "name": "Oddish"
  },
  {
    "id": 44,
    "slug": "gloom",
    "name": "Gloom"
  },
  {
    "id": 45,
    "slug": "vileplume",
    "name": "Vileplume"
  },
  {
    "id": 46,
    "slug": "paras",
    "name": "Paras"
  },
  {
    "id": 47,
    "slug": "parasect",
    "name": "Parasect"
  },
  {
    "id": 48,
    "slug": "venonat",
    "name": "Venonat"
  },
  {
    "id": 49,
    "slug": "venomoth",
    "name": "Venomoth"
  },
  {
    "id": 50,
    "slug": "diglett",
    "name": "Diglett"
  },
  {
    "id": 51,
    "slug": "dugtrio",
    "name": "Dugtrio"
  },
  {
    "id": 52,
    "slug": "meowth",
    "name": "Meowth"
  },
  {
    "id": 53,
    "slug": "persian",
    "name": "Persian"
  },
  {
    "id": 54,
    "slug": "psyduck",
    "name": "Psyduck"
  },
  {
    "id": 55,
    "slug": "golduck",
    "name": "Golduck"
  },
  {
    "id": 56,
    "slug": "mankey",
    "name": "Mankey"
  },
  {
    "id": 57,
    "slug": "primeape",
    "name": "Primeape"
  },
  {
    "id": 58,
    "slug": "growlithe",
    "name": "Growlithe"
  },
  {
    "id": 59,
    "slug": "arcanine",
    "name": "Arcanine"
  },
  {
    "id": 60,
    "slug": "poliwag",
    "name": "Poliwag"
  },
  {
    "id": 61,
    "slug": "poliwhirl",
    "name": "Poliwhirl"
  },
  {
    "id": 62,
    "slug": "poliwrath",
    "name": "Poliwrath"
  },
  {
    "id": 63,
    "slug": "abra",
    "name": "Abra"
  },
  {
    "id": 64,
    "slug": "kadabra",
    "name": "Kadabra"
  },
  {
    "id": 65,
    "slug": "alakazam",
    "name": "Alakazam"
  },
  {
    "id": 66,
    "slug": "machop",
    "name": "Machop"
  },
  {
    "id": 67,
    "slug": "machoke",
    "name": "Machoke"
  },
  {
    "id": 68,
    "slug": "machamp",
    "name": "Machamp"
  },
  {
    "id": 69,
    "slug": "bellsprout",
    "name": "Bellsprout"
  },
  {
    "id": 70,
    "slug": "weepinbell",
    "name": "Weepinbell"
  },
  {
    "id": 71,
    "slug": "victreebel",
    "name": "Victreebel"
  },
  {
    "id": 72,
    "slug": "tentacool",
    "name": "Tentacool"
  },
  {
    "id": 73,
    "slug": "tentacruel",
    "name": "Tentacruel"
  },
  {
    "id": 74,
    "slug": "geodude",
    "name": "Geodude"
  },
  {
    "id": 75,
    "slug": "graveler",
    "name": "Graveler"
  },
  {
    "id": 76,
    "slug": "golem",
    "name": "Golem"
  },
  {
    "id": 77,
    "slug": "ponyta",
    "name": "Ponyta"
  },
  {
    "id": 78,
    "slug": "rapidash",
    "name": "Rapidash"
  },
  {
    "id": 79,
    "slug": "slowpoke",
    "name": "Slowpoke"
  },
  {
    "id": 80,
    "slug": "slowbro",
    "name": "Slowbro"
  },
  {
    "id": 81,
    "slug": "magnemite",
    "name": "Magnemite"
  },
  {
    "id": 82,
    "slug": "magneton",
    "name": "Magneton"
  },
  {
    "id": 83,
    "slug": "farfetchd",
    "name": "Farfetchd"
  },
  {
    "id": 84,
    "slug": "doduo",
    "name": "Doduo"
  },
  {
    "id": 85,
    "slug": "dodrio",
    "name": "Dodrio"
  },
  {
    "id": 86,
    "slug": "seel",
    "name": "Seel"
  },
  {
    "id": 87,
    "slug": "dewgong",
    "name": "Dewgong"
  },
  {
    "id": 88,
    "slug": "grimer",
    "name": "Grimer"
  },
  {
    "id": 89,
    "slug": "muk",
    "name": "Muk"
  },
  {
    "id": 90,
    "slug": "shellder",
    "name": "Shellder"
  },
  {
    "id": 91,
    "slug": "cloyster",
    "name": "Cloyster"
  },
  {
    "id": 92,
    "slug": "gastly",
    "name": "Gastly"
  },
  {
    "id": 93,
    "slug": "haunter",
    "name": "Haunter"
  },
  {
    "id": 94,
    "slug": "gengar",
    "name": "Gengar"
  },
  {
    "id": 95,
    "slug": "onix",
    "name": "Onix"
  },
  {
    "id": 96,
    "slug": "drowzee",
    "name": "Drowzee"
  },
  {
    "id": 97,
    "slug": "hypno",
    "name": "Hypno"
  },
  {
    "id": 98,
    "slug": "krabby",
    "name": "Krabby"
  },
  {
    "id": 99,
    "slug": "kingler",
    "name": "Kingler"
  },
  {
    "id": 100,
    "slug": "voltorb",
    "name": "Voltorb"
  },
  {
    "id": 101,
    "slug": "electrode",
    "name": "Electrode"
  },
  {
    "id": 102,
    "slug": "exeggcute",
    "name": "Exeggcute"
  },
  {
    "id": 103,
    "slug": "exeggutor",
    "name": "Exeggutor"
  },
  {
    "id": 104,
    "slug": "cubone",
    "name": "Cubone"
  },
  {
    "id": 105,
    "slug": "marowak",
    "name": "Marowak"
  },
  {
    "id": 106,
    "slug": "hitmonlee",
    "name": "Hitmonlee"
  },
  {
    "id": 107,
    "slug": "hitmonchan",
    "name": "Hitmonchan"
  },
  {
    "id": 108,
    "slug": "lickitung",
    "name": "Lickitung"
  },
  {
    "id": 109,
    "slug": "koffing",
    "name": "Koffing"
  },
  {
    "id": 110,
    "slug": "weezing",
    "name": "Weezing"
  },
  {
    "id": 111,
    "slug": "rhyhorn",
    "name": "Rhyhorn"
  },
  {
    "id": 112,
    "slug": "rhydon",
    "name": "Rhydon"
  },
  {
    "id": 113,
    "slug": "chansey",
    "name": "Chansey"
  },
  {
    "id": 114,
    "slug": "tangela",
    "name": "Tangela"
  },
  {
    "id": 115,
    "slug": "kangaskhan",
    "name": "Kangaskhan"
  },
  {
    "id": 116,
    "slug": "horsea",
    "name": "Horsea"
  },
  {
    "id": 117,
    "slug": "seadra",
    "name": "Seadra"
  },
  {
    "id": 118,
    "slug": "goldeen",
    "name": "Goldeen"
  },
  {
    "id": 119,
    "slug": "seaking",
    "name": "Seaking"
  },
  {
    "id": 120,
    "slug": "staryu",
    "name": "Staryu"
  },
  {
    "id": 121,
    "slug": "starmie",
    "name": "Starmie"
  },
  {
    "id": 122,
    "slug": "mr-mime",
    "name": "Mr Mime"
  },
  {
    "id": 123,
    "slug": "scyther",
    "name": "Scyther"
  },
  {
    "id": 124,
    "slug": "jynx",
    "name": "Jynx"
  },
  {
    "id": 125,
    "slug": "electabuzz",
    "name": "Electabuzz"
  },
  {
    "id": 126,
    "slug": "magmar",
    "name": "Magmar"
  },
  {
    "id": 127,
    "slug": "pinsir",
    "name": "Pinsir"
  },
  {
    "id": 128,
    "slug": "tauros",
    "name": "Tauros"
  },
  {
    "id": 129,
    "slug": "magikarp",
    "name": "Magikarp"
  },
  {
    "id": 130,
    "slug": "gyarados",
    "name": "Gyarados"
  },
  {
    "id": 131,
    "slug": "lapras",
    "name": "Lapras"
  },
  {
    "id": 132,
    "slug": "ditto",
    "name": "Ditto"
  },
  {
    "id": 133,
    "slug": "eevee",
    "name": "Eevee"
  },
  {
    "id": 134,
    "slug": "vaporeon",
    "name": "Vaporeon"
  },
  {
    "id": 135,
    "slug": "jolteon",
    "name": "Jolteon"
  },
  {
    "id": 136,
    "slug": "flareon",
    "name": "Flareon"
  },
  {
    "id": 137,
    "slug": "porygon",
    "name": "Porygon"
  },
  {
    "id": 138,
    "slug": "omanyte",
    "name": "Omanyte"
  },
  {
    "id": 139,
    "slug": "omastar",
    "name": "Omastar"
  },
  {
    "id": 140,
    "slug": "kabuto",
    "name": "Kabuto"
  },
  {
    "id": 141,
    "slug": "kabutops",
    "name": "Kabutops"
  },
  {
    "id": 142,
    "slug": "aerodactyl",
    "name": "Aerodactyl"
  },
  {
    "id": 143,
    "slug": "snorlax",
    "name": "Snorlax"
  },
  {
    "id": 144,
    "slug": "articuno",
    "name": "Articuno"
  },
  {
    "id": 145,
    "slug": "zapdos",
    "name": "Zapdos"
  },
  {
    "id": 146,
    "slug": "moltres",
    "name": "Moltres"
  },
  {
    "id": 147,
    "slug": "dratini",
    "name": "Dratini"
  },
  {
    "id": 148,
    "slug": "dragonair",
    "name": "Dragonair"
  },
  {
    "id": 149,
    "slug": "dragonite",
    "name": "Dragonite"
  },
  {
    "id": 150,
    "slug": "mewtwo",
    "name": "Mewtwo"
  },
  {
    "id": 151,
    "slug": "mew",
    "name": "Mew"
  },
  {
    "id": 152,
    "slug": "chikorita",
    "name": "Chikorita"
  },
  {
    "id": 153,
    "slug": "bayleef",
    "name": "Bayleef"
  },
  {
    "id": 154,
    "slug": "meganium",
    "name": "Meganium"
  },
  {
    "id": 155,
    "slug": "cyndaquil",
    "name": "Cyndaquil"
  },
  {
    "id": 156,
    "slug": "quilava",
    "name": "Quilava"
  },
  {
    "id": 157,
    "slug": "typhlosion",
    "name": "Typhlosion"
  },
  {
    "id": 158,
    "slug": "totodile",
    "name": "Totodile"
  },
  {
    "id": 159,
    "slug": "croconaw",
    "name": "Croconaw"
  },
  {
    "id": 160,
    "slug": "feraligatr",
    "name": "Feraligatr"
  },
  {
    "id": 161,
    "slug": "sentret",
    "name": "Sentret"
  },
  {
    "id": 162,
    "slug": "furret",
    "name": "Furret"
  },
  {
    "id": 163,
    "slug": "hoothoot",
    "name": "Hoothoot"
  },
  {
    "id": 164,
    "slug": "noctowl",
    "name": "Noctowl"
  },
  {
    "id": 165,
    "slug": "ledyba",
    "name": "Ledyba"
  },
  {
    "id": 166,
    "slug": "ledian",
    "name": "Ledian"
  },
  {
    "id": 167,
    "slug": "spinarak",
    "name": "Spinarak"
  },
  {
    "id": 168,
    "slug": "ariados",
    "name": "Ariados"
  },
  {
    "id": 169,
    "slug": "crobat",
    "name": "Crobat"
  },
  {
    "id": 170,
    "slug": "chinchou",
    "name": "Chinchou"
  },
  {
    "id": 171,
    "slug": "lanturn",
    "name": "Lanturn"
  },
  {
    "id": 172,
    "slug": "pichu",
    "name": "Pichu"
  },
  {
    "id": 173,
    "slug": "cleffa",
    "name": "Cleffa"
  },
  {
    "id": 174,
    "slug": "igglybuff",
    "name": "Igglybuff"
  },
  {
    "id": 175,
    "slug": "togepi",
    "name": "Togepi"
  },
  {
    "id": 176,
    "slug": "togetic",
    "name": "Togetic"
  },
  {
    "id": 177,
    "slug": "natu",
    "name": "Natu"
  },
  {
    "id": 178,
    "slug": "xatu",
    "name": "Xatu"
  },
  {
    "id": 179,
    "slug": "mareep",
    "name": "Mareep"
  },
  {
    "id": 180,
    "slug": "flaaffy",
    "name": "Flaaffy"
  },
  {
    "id": 181,
    "slug": "ampharos",
    "name": "Ampharos"
  },
  {
    "id": 182,
    "slug": "bellossom",
    "name": "Bellossom"
  },
  {
    "id": 183,
    "slug": "marill",
    "name": "Marill"
  },
  {
    "id": 184,
    "slug": "azumarill",
    "name": "Azumarill"
  },
  {
    "id": 185,
    "slug": "sudowoodo",
    "name": "Sudowoodo"
  },
  {
    "id": 186,
    "slug": "politoed",
    "name": "Politoed"
  },
  {
    "id": 187,
    "slug": "hoppip",
    "name": "Hoppip"
  },
  {
    "id": 188,
    "slug": "skiploom",
    "name": "Skiploom"
  },
  {
    "id": 189,
    "slug": "jumpluff",
    "name": "Jumpluff"
  },
  {
    "id": 190,
    "slug": "aipom",
    "name": "Aipom"
  },
  {
    "id": 191,
    "slug": "sunkern",
    "name": "Sunkern"
  },
  {
    "id": 192,
    "slug": "sunflora",
    "name": "Sunflora"
  },
  {
    "id": 193,
    "slug": "yanma",
    "name": "Yanma"
  },
  {
    "id": 194,
    "slug": "wooper",
    "name": "Wooper"
  },
  {
    "id": 195,
    "slug": "quagsire",
    "name": "Quagsire"
  },
  {
    "id": 196,
    "slug": "espeon",
    "name": "Espeon"
  },
  {
    "id": 197,
    "slug": "umbreon",
    "name": "Umbreon"
  },
  {
    "id": 198,
    "slug": "murkrow",
    "name": "Murkrow"
  },
  {
    "id": 199,
    "slug": "slowking",
    "name": "Slowking"
  },
  {
    "id": 200,
    "slug": "misdreavus",
    "name": "Misdreavus"
  },
  {
    "id": 201,
    "slug": "unown",
    "name": "Unown"
  },
  {
    "id": 202,
    "slug": "wobbuffet",
    "name": "Wobbuffet"
  },
  {
    "id": 203,
    "slug": "girafarig",
    "name": "Girafarig"
  },
  {
    "id": 204,
    "slug": "pineco",
    "name": "Pineco"
  },
  {
    "id": 205,
    "slug": "forretress",
    "name": "Forretress"
  },
  {
    "id": 206,
    "slug": "dunsparce",
    "name": "Dunsparce"
  },
  {
    "id": 207,
    "slug": "gligar",
    "name": "Gligar"
  },
  {
    "id": 208,
    "slug": "steelix",
    "name": "Steelix"
  },
  {
    "id": 209,
    "slug": "snubbull",
    "name": "Snubbull"
  },
  {
    "id": 210,
    "slug": "granbull",
    "name": "Granbull"
  },
  {
    "id": 211,
    "slug": "qwilfish",
    "name": "Qwilfish"
  },
  {
    "id": 212,
    "slug": "scizor",
    "name": "Scizor"
  },
  {
    "id": 213,
    "slug": "shuckle",
    "name": "Shuckle"
  },
  {
    "id": 214,
    "slug": "heracross",
    "name": "Heracross"
  },
  {
    "id": 215,
    "slug": "sneasel",
    "name": "Sneasel"
  },
  {
    "id": 216,
    "slug": "teddiursa",
    "name": "Teddiursa"
  },
  {
    "id": 217,
    "slug": "ursaring",
    "name": "Ursaring"
  },
  {
    "id": 218,
    "slug": "slugma",
    "name": "Slugma"
  },
  {
    "id": 219,
    "slug": "magcargo",
    "name": "Magcargo"
  },
  {
    "id": 220,
    "slug": "swinub",
    "name": "Swinub"
  },
  {
    "id": 221,
    "slug": "piloswine",
    "name": "Piloswine"
  },
  {
    "id": 222,
    "slug": "corsola",
    "name": "Corsola"
  },
  {
    "id": 223,
    "slug": "remoraid",
    "name": "Remoraid"
  },
  {
    "id": 224,
    "slug": "octillery",
    "name": "Octillery"
  },
  {
    "id": 225,
    "slug": "delibird",
    "name": "Delibird"
  },
  {
    "id": 226,
    "slug": "mantine",
    "name": "Mantine"
  },
  {
    "id": 227,
    "slug": "skarmory",
    "name": "Skarmory"
  },
  {
    "id": 228,
    "slug": "houndour",
    "name": "Houndour"
  },
  {
    "id": 229,
    "slug": "houndoom",
    "name": "Houndoom"
  },
  {
    "id": 230,
    "slug": "kingdra",
    "name": "Kingdra"
  },
  {
    "id": 231,
    "slug": "phanpy",
    "name": "Phanpy"
  },
  {
    "id": 232,
    "slug": "donphan",
    "name": "Donphan"
  },
  {
    "id": 233,
    "slug": "porygon2",
    "name": "Porygon2"
  },
  {
    "id": 234,
    "slug": "stantler",
    "name": "Stantler"
  },
  {
    "id": 235,
    "slug": "smeargle",
    "name": "Smeargle"
  },
  {
    "id": 236,
    "slug": "tyrogue",
    "name": "Tyrogue"
  },
  {
    "id": 237,
    "slug": "hitmontop",
    "name": "Hitmontop"
  },
  {
    "id": 238,
    "slug": "smoochum",
    "name": "Smoochum"
  },
  {
    "id": 239,
    "slug": "elekid",
    "name": "Elekid"
  },
  {
    "id": 240,
    "slug": "magby",
    "name": "Magby"
  },
  {
    "id": 241,
    "slug": "miltank",
    "name": "Miltank"
  },
  {
    "id": 242,
    "slug": "blissey",
    "name": "Blissey"
  },
  {
    "id": 243,
    "slug": "raikou",
    "name": "Raikou"
  },
  {
    "id": 244,
    "slug": "entei",
    "name": "Entei"
  },
  {
    "id": 245,
    "slug": "suicune",
    "name": "Suicune"
  },
  {
    "id": 246,
    "slug": "larvitar",
    "name": "Larvitar"
  },
  {
    "id": 247,
    "slug": "pupitar",
    "name": "Pupitar"
  },
  {
    "id": 248,
    "slug": "tyranitar",
    "name": "Tyranitar"
  },
  {
    "id": 249,
    "slug": "lugia",
    "name": "Lugia"
  },
  {
    "id": 250,
    "slug": "ho-oh",
    "name": "Ho Oh"
  },
  {
    "id": 251,
    "slug": "celebi",
    "name": "Celebi"
  },
  {
    "id": 252,
    "slug": "treecko",
    "name": "Treecko"
  },
  {
    "id": 253,
    "slug": "grovyle",
    "name": "Grovyle"
  },
  {
    "id": 254,
    "slug": "sceptile",
    "name": "Sceptile"
  },
  {
    "id": 255,
    "slug": "torchic",
    "name": "Torchic"
  },
  {
    "id": 256,
    "slug": "combusken",
    "name": "Combusken"
  },
  {
    "id": 257,
    "slug": "blaziken",
    "name": "Blaziken"
  },
  {
    "id": 258,
    "slug": "mudkip",
    "name": "Mudkip"
  },
  {
    "id": 259,
    "slug": "marshtomp",
    "name": "Marshtomp"
  },
  {
    "id": 260,
    "slug": "swampert",
    "name": "Swampert"
  },
  {
    "id": 261,
    "slug": "poochyena",
    "name": "Poochyena"
  },
  {
    "id": 262,
    "slug": "mightyena",
    "name": "Mightyena"
  },
  {
    "id": 263,
    "slug": "zigzagoon",
    "name": "Zigzagoon"
  },
  {
    "id": 264,
    "slug": "linoone",
    "name": "Linoone"
  },
  {
    "id": 265,
    "slug": "wurmple",
    "name": "Wurmple"
  },
  {
    "id": 266,
    "slug": "silcoon",
    "name": "Silcoon"
  },
  {
    "id": 267,
    "slug": "beautifly",
    "name": "Beautifly"
  },
  {
    "id": 268,
    "slug": "cascoon",
    "name": "Cascoon"
  },
  {
    "id": 269,
    "slug": "dustox",
    "name": "Dustox"
  },
  {
    "id": 270,
    "slug": "lotad",
    "name": "Lotad"
  },
  {
    "id": 271,
    "slug": "lombre",
    "name": "Lombre"
  },
  {
    "id": 272,
    "slug": "ludicolo",
    "name": "Ludicolo"
  },
  {
    "id": 273,
    "slug": "seedot",
    "name": "Seedot"
  },
  {
    "id": 274,
    "slug": "nuzleaf",
    "name": "Nuzleaf"
  },
  {
    "id": 275,
    "slug": "shiftry",
    "name": "Shiftry"
  },
  {
    "id": 276,
    "slug": "taillow",
    "name": "Taillow"
  },
  {
    "id": 277,
    "slug": "swellow",
    "name": "Swellow"
  },
  {
    "id": 278,
    "slug": "wingull",
    "name": "Wingull"
  },
  {
    "id": 279,
    "slug": "pelipper",
    "name": "Pelipper"
  },
  {
    "id": 280,
    "slug": "ralts",
    "name": "Ralts"
  },
  {
    "id": 281,
    "slug": "kirlia",
    "name": "Kirlia"
  },
  {
    "id": 282,
    "slug": "gardevoir",
    "name": "Gardevoir"
  },
  {
    "id": 283,
    "slug": "surskit",
    "name": "Surskit"
  },
  {
    "id": 284,
    "slug": "masquerain",
    "name": "Masquerain"
  },
  {
    "id": 285,
    "slug": "shroomish",
    "name": "Shroomish"
  },
  {
    "id": 286,
    "slug": "breloom",
    "name": "Breloom"
  },
  {
    "id": 287,
    "slug": "slakoth",
    "name": "Slakoth"
  },
  {
    "id": 288,
    "slug": "vigoroth",
    "name": "Vigoroth"
  },
  {
    "id": 289,
    "slug": "slaking",
    "name": "Slaking"
  },
  {
    "id": 290,
    "slug": "nincada",
    "name": "Nincada"
  },
  {
    "id": 291,
    "slug": "ninjask",
    "name": "Ninjask"
  },
  {
    "id": 292,
    "slug": "shedinja",
    "name": "Shedinja"
  },
  {
    "id": 293,
    "slug": "whismur",
    "name": "Whismur"
  },
  {
    "id": 294,
    "slug": "loudred",
    "name": "Loudred"
  },
  {
    "id": 295,
    "slug": "exploud",
    "name": "Exploud"
  },
  {
    "id": 296,
    "slug": "makuhita",
    "name": "Makuhita"
  },
  {
    "id": 297,
    "slug": "hariyama",
    "name": "Hariyama"
  },
  {
    "id": 298,
    "slug": "azurill",
    "name": "Azurill"
  },
  {
    "id": 299,
    "slug": "nosepass",
    "name": "Nosepass"
  },
  {
    "id": 300,
    "slug": "skitty",
    "name": "Skitty"
  },
  {
    "id": 301,
    "slug": "delcatty",
    "name": "Delcatty"
  },
  {
    "id": 302,
    "slug": "sableye",
    "name": "Sableye"
  },
  {
    "id": 303,
    "slug": "mawile",
    "name": "Mawile"
  },
  {
    "id": 304,
    "slug": "aron",
    "name": "Aron"
  },
  {
    "id": 305,
    "slug": "lairon",
    "name": "Lairon"
  },
  {
    "id": 306,
    "slug": "aggron",
    "name": "Aggron"
  },
  {
    "id": 307,
    "slug": "meditite",
    "name": "Meditite"
  },
  {
    "id": 308,
    "slug": "medicham",
    "name": "Medicham"
  },
  {
    "id": 309,
    "slug": "electrike",
    "name": "Electrike"
  },
  {
    "id": 310,
    "slug": "manectric",
    "name": "Manectric"
  },
  {
    "id": 311,
    "slug": "plusle",
    "name": "Plusle"
  },
  {
    "id": 312,
    "slug": "minun",
    "name": "Minun"
  },
  {
    "id": 313,
    "slug": "volbeat",
    "name": "Volbeat"
  },
  {
    "id": 314,
    "slug": "illumise",
    "name": "Illumise"
  },
  {
    "id": 315,
    "slug": "roselia",
    "name": "Roselia"
  },
  {
    "id": 316,
    "slug": "gulpin",
    "name": "Gulpin"
  },
  {
    "id": 317,
    "slug": "swalot",
    "name": "Swalot"
  },
  {
    "id": 318,
    "slug": "carvanha",
    "name": "Carvanha"
  },
  {
    "id": 319,
    "slug": "sharpedo",
    "name": "Sharpedo"
  },
  {
    "id": 320,
    "slug": "wailmer",
    "name": "Wailmer"
  },
  {
    "id": 321,
    "slug": "wailord",
    "name": "Wailord"
  },
  {
    "id": 322,
    "slug": "numel",
    "name": "Numel"
  },
  {
    "id": 323,
    "slug": "camerupt",
    "name": "Camerupt"
  },
  {
    "id": 324,
    "slug": "torkoal",
    "name": "Torkoal"
  },
  {
    "id": 325,
    "slug": "spoink",
    "name": "Spoink"
  },
  {
    "id": 326,
    "slug": "grumpig",
    "name": "Grumpig"
  },
  {
    "id": 327,
    "slug": "spinda",
    "name": "Spinda"
  },
  {
    "id": 328,
    "slug": "trapinch",
    "name": "Trapinch"
  },
  {
    "id": 329,
    "slug": "vibrava",
    "name": "Vibrava"
  },
  {
    "id": 330,
    "slug": "flygon",
    "name": "Flygon"
  },
  {
    "id": 331,
    "slug": "cacnea",
    "name": "Cacnea"
  },
  {
    "id": 332,
    "slug": "cacturne",
    "name": "Cacturne"
  },
  {
    "id": 333,
    "slug": "swablu",
    "name": "Swablu"
  },
  {
    "id": 334,
    "slug": "altaria",
    "name": "Altaria"
  },
  {
    "id": 335,
    "slug": "zangoose",
    "name": "Zangoose"
  },
  {
    "id": 336,
    "slug": "seviper",
    "name": "Seviper"
  },
  {
    "id": 337,
    "slug": "lunatone",
    "name": "Lunatone"
  },
  {
    "id": 338,
    "slug": "solrock",
    "name": "Solrock"
  },
  {
    "id": 339,
    "slug": "barboach",
    "name": "Barboach"
  },
  {
    "id": 340,
    "slug": "whiscash",
    "name": "Whiscash"
  },
  {
    "id": 341,
    "slug": "corphish",
    "name": "Corphish"
  },
  {
    "id": 342,
    "slug": "crawdaunt",
    "name": "Crawdaunt"
  },
  {
    "id": 343,
    "slug": "baltoy",
    "name": "Baltoy"
  },
  {
    "id": 344,
    "slug": "claydol",
    "name": "Claydol"
  },
  {
    "id": 345,
    "slug": "lileep",
    "name": "Lileep"
  },
  {
    "id": 346,
    "slug": "cradily",
    "name": "Cradily"
  },
  {
    "id": 347,
    "slug": "anorith",
    "name": "Anorith"
  },
  {
    "id": 348,
    "slug": "armaldo",
    "name": "Armaldo"
  },
  {
    "id": 349,
    "slug": "feebas",
    "name": "Feebas"
  },
  {
    "id": 350,
    "slug": "milotic",
    "name": "Milotic"
  },
  {
    "id": 351,
    "slug": "castform",
    "name": "Castform"
  },
  {
    "id": 352,
    "slug": "kecleon",
    "name": "Kecleon"
  },
  {
    "id": 353,
    "slug": "shuppet",
    "name": "Shuppet"
  },
  {
    "id": 354,
    "slug": "banette",
    "name": "Banette"
  },
  {
    "id": 355,
    "slug": "duskull",
    "name": "Duskull"
  },
  {
    "id": 356,
    "slug": "dusclops",
    "name": "Dusclops"
  },
  {
    "id": 357,
    "slug": "tropius",
    "name": "Tropius"
  },
  {
    "id": 358,
    "slug": "chimecho",
    "name": "Chimecho"
  },
  {
    "id": 359,
    "slug": "absol",
    "name": "Absol"
  },
  {
    "id": 360,
    "slug": "wynaut",
    "name": "Wynaut"
  },
  {
    "id": 361,
    "slug": "snorunt",
    "name": "Snorunt"
  },
  {
    "id": 362,
    "slug": "glalie",
    "name": "Glalie"
  },
  {
    "id": 363,
    "slug": "spheal",
    "name": "Spheal"
  },
  {
    "id": 364,
    "slug": "sealeo",
    "name": "Sealeo"
  },
  {
    "id": 365,
    "slug": "walrein",
    "name": "Walrein"
  },
  {
    "id": 366,
    "slug": "clamperl",
    "name": "Clamperl"
  },
  {
    "id": 367,
    "slug": "huntail",
    "name": "Huntail"
  },
  {
    "id": 368,
    "slug": "gorebyss",
    "name": "Gorebyss"
  },
  {
    "id": 369,
    "slug": "relicanth",
    "name": "Relicanth"
  },
  {
    "id": 370,
    "slug": "luvdisc",
    "name": "Luvdisc"
  },
  {
    "id": 371,
    "slug": "bagon",
    "name": "Bagon"
  },
  {
    "id": 372,
    "slug": "shelgon",
    "name": "Shelgon"
  },
  {
    "id": 373,
    "slug": "salamence",
    "name": "Salamence"
  },
  {
    "id": 374,
    "slug": "beldum",
    "name": "Beldum"
  },
  {
    "id": 375,
    "slug": "metang",
    "name": "Metang"
  },
  {
    "id": 376,
    "slug": "metagross",
    "name": "Metagross"
  },
  {
    "id": 377,
    "slug": "regirock",
    "name": "Regirock"
  },
  {
    "id": 378,
    "slug": "regice",
    "name": "Regice"
  },
  {
    "id": 379,
    "slug": "registeel",
    "name": "Registeel"
  },
  {
    "id": 380,
    "slug": "latias",
    "name": "Latias"
  },
  {
    "id": 381,
    "slug": "latios",
    "name": "Latios"
  },
  {
    "id": 382,
    "slug": "kyogre",
    "name": "Kyogre"
  },
  {
    "id": 383,
    "slug": "groudon",
    "name": "Groudon"
  },
  {
    "id": 384,
    "slug": "rayquaza",
    "name": "Rayquaza"
  },
  {
    "id": 385,
    "slug": "jirachi",
    "name": "Jirachi"
  },
  {
    "id": 386,
    "slug": "deoxys-normal",
    "name": "Deoxys Normal"
  },
  {
    "id": 387,
    "slug": "turtwig",
    "name": "Turtwig"
  },
  {
    "id": 388,
    "slug": "grotle",
    "name": "Grotle"
  },
  {
    "id": 389,
    "slug": "torterra",
    "name": "Torterra"
  },
  {
    "id": 390,
    "slug": "chimchar",
    "name": "Chimchar"
  },
  {
    "id": 391,
    "slug": "monferno",
    "name": "Monferno"
  },
  {
    "id": 392,
    "slug": "infernape",
    "name": "Infernape"
  },
  {
    "id": 393,
    "slug": "piplup",
    "name": "Piplup"
  },
  {
    "id": 394,
    "slug": "prinplup",
    "name": "Prinplup"
  },
  {
    "id": 395,
    "slug": "empoleon",
    "name": "Empoleon"
  },
  {
    "id": 396,
    "slug": "starly",
    "name": "Starly"
  },
  {
    "id": 397,
    "slug": "staravia",
    "name": "Staravia"
  },
  {
    "id": 398,
    "slug": "staraptor",
    "name": "Staraptor"
  },
  {
    "id": 399,
    "slug": "bidoof",
    "name": "Bidoof"
  },
  {
    "id": 400,
    "slug": "bibarel",
    "name": "Bibarel"
  },
  {
    "id": 401,
    "slug": "kricketot",
    "name": "Kricketot"
  },
  {
    "id": 402,
    "slug": "kricketune",
    "name": "Kricketune"
  },
  {
    "id": 403,
    "slug": "shinx",
    "name": "Shinx"
  },
  {
    "id": 404,
    "slug": "luxio",
    "name": "Luxio"
  },
  {
    "id": 405,
    "slug": "luxray",
    "name": "Luxray"
  },
  {
    "id": 406,
    "slug": "budew",
    "name": "Budew"
  },
  {
    "id": 407,
    "slug": "roserade",
    "name": "Roserade"
  },
  {
    "id": 408,
    "slug": "cranidos",
    "name": "Cranidos"
  },
  {
    "id": 409,
    "slug": "rampardos",
    "name": "Rampardos"
  },
  {
    "id": 410,
    "slug": "shieldon",
    "name": "Shieldon"
  },
  {
    "id": 411,
    "slug": "bastiodon",
    "name": "Bastiodon"
  },
  {
    "id": 412,
    "slug": "burmy",
    "name": "Burmy"
  },
  {
    "id": 413,
    "slug": "wormadam-plant",
    "name": "Wormadam Plant"
  },
  {
    "id": 414,
    "slug": "mothim",
    "name": "Mothim"
  },
  {
    "id": 415,
    "slug": "combee",
    "name": "Combee"
  },
  {
    "id": 416,
    "slug": "vespiquen",
    "name": "Vespiquen"
  },
  {
    "id": 417,
    "slug": "pachirisu",
    "name": "Pachirisu"
  },
  {
    "id": 418,
    "slug": "buizel",
    "name": "Buizel"
  },
  {
    "id": 419,
    "slug": "floatzel",
    "name": "Floatzel"
  },
  {
    "id": 420,
    "slug": "cherubi",
    "name": "Cherubi"
  },
  {
    "id": 421,
    "slug": "cherrim",
    "name": "Cherrim"
  },
  {
    "id": 422,
    "slug": "shellos",
    "name": "Shellos"
  },
  {
    "id": 423,
    "slug": "gastrodon",
    "name": "Gastrodon"
  },
  {
    "id": 424,
    "slug": "ambipom",
    "name": "Ambipom"
  },
  {
    "id": 425,
    "slug": "drifloon",
    "name": "Drifloon"
  },
  {
    "id": 426,
    "slug": "drifblim",
    "name": "Drifblim"
  },
  {
    "id": 427,
    "slug": "buneary",
    "name": "Buneary"
  },
  {
    "id": 428,
    "slug": "lopunny",
    "name": "Lopunny"
  },
  {
    "id": 429,
    "slug": "mismagius",
    "name": "Mismagius"
  },
  {
    "id": 430,
    "slug": "honchkrow",
    "name": "Honchkrow"
  },
  {
    "id": 431,
    "slug": "glameow",
    "name": "Glameow"
  },
  {
    "id": 432,
    "slug": "purugly",
    "name": "Purugly"
  },
  {
    "id": 433,
    "slug": "chingling",
    "name": "Chingling"
  },
  {
    "id": 434,
    "slug": "stunky",
    "name": "Stunky"
  },
  {
    "id": 435,
    "slug": "skuntank",
    "name": "Skuntank"
  },
  {
    "id": 436,
    "slug": "bronzor",
    "name": "Bronzor"
  },
  {
    "id": 437,
    "slug": "bronzong",
    "name": "Bronzong"
  },
  {
    "id": 438,
    "slug": "bonsly",
    "name": "Bonsly"
  },
  {
    "id": 439,
    "slug": "mime-jr",
    "name": "Mime Jr"
  },
  {
    "id": 440,
    "slug": "happiny",
    "name": "Happiny"
  },
  {
    "id": 441,
    "slug": "chatot",
    "name": "Chatot"
  },
  {
    "id": 442,
    "slug": "spiritomb",
    "name": "Spiritomb"
  },
  {
    "id": 443,
    "slug": "gible",
    "name": "Gible"
  },
  {
    "id": 444,
    "slug": "gabite",
    "name": "Gabite"
  },
  {
    "id": 445,
    "slug": "garchomp",
    "name": "Garchomp"
  },
  {
    "id": 446,
    "slug": "munchlax",
    "name": "Munchlax"
  },
  {
    "id": 447,
    "slug": "riolu",
    "name": "Riolu"
  },
  {
    "id": 448,
    "slug": "lucario",
    "name": "Lucario"
  },
  {
    "id": 449,
    "slug": "hippopotas",
    "name": "Hippopotas"
  },
  {
    "id": 450,
    "slug": "hippowdon",
    "name": "Hippowdon"
  },
  {
    "id": 451,
    "slug": "skorupi",
    "name": "Skorupi"
  },
  {
    "id": 452,
    "slug": "drapion",
    "name": "Drapion"
  },
  {
    "id": 453,
    "slug": "croagunk",
    "name": "Croagunk"
  },
  {
    "id": 454,
    "slug": "toxicroak",
    "name": "Toxicroak"
  },
  {
    "id": 455,
    "slug": "carnivine",
    "name": "Carnivine"
  },
  {
    "id": 456,
    "slug": "finneon",
    "name": "Finneon"
  },
  {
    "id": 457,
    "slug": "lumineon",
    "name": "Lumineon"
  },
  {
    "id": 458,
    "slug": "mantyke",
    "name": "Mantyke"
  },
  {
    "id": 459,
    "slug": "snover",
    "name": "Snover"
  },
  {
    "id": 460,
    "slug": "abomasnow",
    "name": "Abomasnow"
  },
  {
    "id": 461,
    "slug": "weavile",
    "name": "Weavile"
  },
  {
    "id": 462,
    "slug": "magnezone",
    "name": "Magnezone"
  },
  {
    "id": 463,
    "slug": "lickilicky",
    "name": "Lickilicky"
  },
  {
    "id": 464,
    "slug": "rhyperior",
    "name": "Rhyperior"
  },
  {
    "id": 465,
    "slug": "tangrowth",
    "name": "Tangrowth"
  },
  {
    "id": 466,
    "slug": "electivire",
    "name": "Electivire"
  },
  {
    "id": 467,
    "slug": "magmortar",
    "name": "Magmortar"
  },
  {
    "id": 468,
    "slug": "togekiss",
    "name": "Togekiss"
  },
  {
    "id": 469,
    "slug": "yanmega",
    "name": "Yanmega"
  },
  {
    "id": 470,
    "slug": "leafeon",
    "name": "Leafeon"
  },
  {
    "id": 471,
    "slug": "glaceon",
    "name": "Glaceon"
  },
  {
    "id": 472,
    "slug": "gliscor",
    "name": "Gliscor"
  },
  {
    "id": 473,
    "slug": "mamoswine",
    "name": "Mamoswine"
  },
  {
    "id": 474,
    "slug": "porygon-z",
    "name": "Porygon Z"
  },
  {
    "id": 475,
    "slug": "gallade",
    "name": "Gallade"
  },
  {
    "id": 476,
    "slug": "probopass",
    "name": "Probopass"
  },
  {
    "id": 477,
    "slug": "dusknoir",
    "name": "Dusknoir"
  },
  {
    "id": 478,
    "slug": "froslass",
    "name": "Froslass"
  },
  {
    "id": 479,
    "slug": "rotom",
    "name": "Rotom"
  },
  {
    "id": 480,
    "slug": "uxie",
    "name": "Uxie"
  },
  {
    "id": 481,
    "slug": "mesprit",
    "name": "Mesprit"
  },
  {
    "id": 482,
    "slug": "azelf",
    "name": "Azelf"
  },
  {
    "id": 483,
    "slug": "dialga",
    "name": "Dialga"
  },
  {
    "id": 484,
    "slug": "palkia",
    "name": "Palkia"
  },
  {
    "id": 485,
    "slug": "heatran",
    "name": "Heatran"
  },
  {
    "id": 486,
    "slug": "regigigas",
    "name": "Regigigas"
  },
  {
    "id": 487,
    "slug": "giratina-altered",
    "name": "Giratina Altered"
  },
  {
    "id": 488,
    "slug": "cresselia",
    "name": "Cresselia"
  },
  {
    "id": 489,
    "slug": "phione",
    "name": "Phione"
  },
  {
    "id": 490,
    "slug": "manaphy",
    "name": "Manaphy"
  },
  {
    "id": 491,
    "slug": "darkrai",
    "name": "Darkrai"
  },
  {
    "id": 492,
    "slug": "shaymin-land",
    "name": "Shaymin Land"
  },
  {
    "id": 493,
    "slug": "arceus",
    "name": "Arceus"
  },
  {
    "id": 494,
    "slug": "victini",
    "name": "Victini"
  },
  {
    "id": 495,
    "slug": "snivy",
    "name": "Snivy"
  },
  {
    "id": 496,
    "slug": "servine",
    "name": "Servine"
  },
  {
    "id": 497,
    "slug": "serperior",
    "name": "Serperior"
  },
  {
    "id": 498,
    "slug": "tepig",
    "name": "Tepig"
  },
  {
    "id": 499,
    "slug": "pignite",
    "name": "Pignite"
  },
  {
    "id": 500,
    "slug": "emboar",
    "name": "Emboar"
  },
  {
    "id": 501,
    "slug": "oshawott",
    "name": "Oshawott"
  },
  {
    "id": 502,
    "slug": "dewott",
    "name": "Dewott"
  },
  {
    "id": 503,
    "slug": "samurott",
    "name": "Samurott"
  },
  {
    "id": 504,
    "slug": "patrat",
    "name": "Patrat"
  },
  {
    "id": 505,
    "slug": "watchog",
    "name": "Watchog"
  },
  {
    "id": 506,
    "slug": "lillipup",
    "name": "Lillipup"
  },
  {
    "id": 507,
    "slug": "herdier",
    "name": "Herdier"
  },
  {
    "id": 508,
    "slug": "stoutland",
    "name": "Stoutland"
  },
  {
    "id": 509,
    "slug": "purrloin",
    "name": "Purrloin"
  },
  {
    "id": 510,
    "slug": "liepard",
    "name": "Liepard"
  },
  {
    "id": 511,
    "slug": "pansage",
    "name": "Pansage"
  },
  {
    "id": 512,
    "slug": "simisage",
    "name": "Simisage"
  },
  {
    "id": 513,
    "slug": "pansear",
    "name": "Pansear"
  },
  {
    "id": 514,
    "slug": "simisear",
    "name": "Simisear"
  },
  {
    "id": 515,
    "slug": "panpour",
    "name": "Panpour"
  },
  {
    "id": 516,
    "slug": "simipour",
    "name": "Simipour"
  },
  {
    "id": 517,
    "slug": "munna",
    "name": "Munna"
  },
  {
    "id": 518,
    "slug": "musharna",
    "name": "Musharna"
  },
  {
    "id": 519,
    "slug": "pidove",
    "name": "Pidove"
  },
  {
    "id": 520,
    "slug": "tranquill",
    "name": "Tranquill"
  },
  {
    "id": 521,
    "slug": "unfezant",
    "name": "Unfezant"
  },
  {
    "id": 522,
    "slug": "blitzle",
    "name": "Blitzle"
  },
  {
    "id": 523,
    "slug": "zebstrika",
    "name": "Zebstrika"
  },
  {
    "id": 524,
    "slug": "roggenrola",
    "name": "Roggenrola"
  },
  {
    "id": 525,
    "slug": "boldore",
    "name": "Boldore"
  },
  {
    "id": 526,
    "slug": "gigalith",
    "name": "Gigalith"
  },
  {
    "id": 527,
    "slug": "woobat",
    "name": "Woobat"
  },
  {
    "id": 528,
    "slug": "swoobat",
    "name": "Swoobat"
  },
  {
    "id": 529,
    "slug": "drilbur",
    "name": "Drilbur"
  },
  {
    "id": 530,
    "slug": "excadrill",
    "name": "Excadrill"
  },
  {
    "id": 531,
    "slug": "audino",
    "name": "Audino"
  },
  {
    "id": 532,
    "slug": "timburr",
    "name": "Timburr"
  },
  {
    "id": 533,
    "slug": "gurdurr",
    "name": "Gurdurr"
  },
  {
    "id": 534,
    "slug": "conkeldurr",
    "name": "Conkeldurr"
  },
  {
    "id": 535,
    "slug": "tympole",
    "name": "Tympole"
  },
  {
    "id": 536,
    "slug": "palpitoad",
    "name": "Palpitoad"
  },
  {
    "id": 537,
    "slug": "seismitoad",
    "name": "Seismitoad"
  },
  {
    "id": 538,
    "slug": "throh",
    "name": "Throh"
  },
  {
    "id": 539,
    "slug": "sawk",
    "name": "Sawk"
  },
  {
    "id": 540,
    "slug": "sewaddle",
    "name": "Sewaddle"
  },
  {
    "id": 541,
    "slug": "swadloon",
    "name": "Swadloon"
  },
  {
    "id": 542,
    "slug": "leavanny",
    "name": "Leavanny"
  },
  {
    "id": 543,
    "slug": "venipede",
    "name": "Venipede"
  },
  {
    "id": 544,
    "slug": "whirlipede",
    "name": "Whirlipede"
  },
  {
    "id": 545,
    "slug": "scolipede",
    "name": "Scolipede"
  },
  {
    "id": 546,
    "slug": "cottonee",
    "name": "Cottonee"
  },
  {
    "id": 547,
    "slug": "whimsicott",
    "name": "Whimsicott"
  },
  {
    "id": 548,
    "slug": "petilil",
    "name": "Petilil"
  },
  {
    "id": 549,
    "slug": "lilligant",
    "name": "Lilligant"
  },
  {
    "id": 550,
    "slug": "basculin-red-striped",
    "name": "Basculin Red Striped"
  },
  {
    "id": 551,
    "slug": "sandile",
    "name": "Sandile"
  },
  {
    "id": 552,
    "slug": "krokorok",
    "name": "Krokorok"
  },
  {
    "id": 553,
    "slug": "krookodile",
    "name": "Krookodile"
  },
  {
    "id": 554,
    "slug": "darumaka",
    "name": "Darumaka"
  },
  {
    "id": 555,
    "slug": "darmanitan-standard",
    "name": "Darmanitan Standard"
  },
  {
    "id": 556,
    "slug": "maractus",
    "name": "Maractus"
  },
  {
    "id": 557,
    "slug": "dwebble",
    "name": "Dwebble"
  },
  {
    "id": 558,
    "slug": "crustle",
    "name": "Crustle"
  },
  {
    "id": 559,
    "slug": "scraggy",
    "name": "Scraggy"
  },
  {
    "id": 560,
    "slug": "scrafty",
    "name": "Scrafty"
  },
  {
    "id": 561,
    "slug": "sigilyph",
    "name": "Sigilyph"
  },
  {
    "id": 562,
    "slug": "yamask",
    "name": "Yamask"
  },
  {
    "id": 563,
    "slug": "cofagrigus",
    "name": "Cofagrigus"
  },
  {
    "id": 564,
    "slug": "tirtouga",
    "name": "Tirtouga"
  },
  {
    "id": 565,
    "slug": "carracosta",
    "name": "Carracosta"
  },
  {
    "id": 566,
    "slug": "archen",
    "name": "Archen"
  },
  {
    "id": 567,
    "slug": "archeops",
    "name": "Archeops"
  },
  {
    "id": 568,
    "slug": "trubbish",
    "name": "Trubbish"
  },
  {
    "id": 569,
    "slug": "garbodor",
    "name": "Garbodor"
  },
  {
    "id": 570,
    "slug": "zorua",
    "name": "Zorua"
  },
  {
    "id": 571,
    "slug": "zoroark",
    "name": "Zoroark"
  },
  {
    "id": 572,
    "slug": "minccino",
    "name": "Minccino"
  },
  {
    "id": 573,
    "slug": "cinccino",
    "name": "Cinccino"
  },
  {
    "id": 574,
    "slug": "gothita",
    "name": "Gothita"
  },
  {
    "id": 575,
    "slug": "gothorita",
    "name": "Gothorita"
  },
  {
    "id": 576,
    "slug": "gothitelle",
    "name": "Gothitelle"
  },
  {
    "id": 577,
    "slug": "solosis",
    "name": "Solosis"
  },
  {
    "id": 578,
    "slug": "duosion",
    "name": "Duosion"
  },
  {
    "id": 579,
    "slug": "reuniclus",
    "name": "Reuniclus"
  },
  {
    "id": 580,
    "slug": "ducklett",
    "name": "Ducklett"
  },
  {
    "id": 581,
    "slug": "swanna",
    "name": "Swanna"
  },
  {
    "id": 582,
    "slug": "vanillite",
    "name": "Vanillite"
  },
  {
    "id": 583,
    "slug": "vanillish",
    "name": "Vanillish"
  },
  {
    "id": 584,
    "slug": "vanilluxe",
    "name": "Vanilluxe"
  },
  {
    "id": 585,
    "slug": "deerling",
    "name": "Deerling"
  },
  {
    "id": 586,
    "slug": "sawsbuck",
    "name": "Sawsbuck"
  },
  {
    "id": 587,
    "slug": "emolga",
    "name": "Emolga"
  },
  {
    "id": 588,
    "slug": "karrablast",
    "name": "Karrablast"
  },
  {
    "id": 589,
    "slug": "escavalier",
    "name": "Escavalier"
  },
  {
    "id": 590,
    "slug": "foongus",
    "name": "Foongus"
  },
  {
    "id": 591,
    "slug": "amoonguss",
    "name": "Amoonguss"
  },
  {
    "id": 592,
    "slug": "frillish-male",
    "name": "Frillish Male"
  },
  {
    "id": 593,
    "slug": "jellicent-male",
    "name": "Jellicent Male"
  },
  {
    "id": 594,
    "slug": "alomomola",
    "name": "Alomomola"
  },
  {
    "id": 595,
    "slug": "joltik",
    "name": "Joltik"
  },
  {
    "id": 596,
    "slug": "galvantula",
    "name": "Galvantula"
  },
  {
    "id": 597,
    "slug": "ferroseed",
    "name": "Ferroseed"
  },
  {
    "id": 598,
    "slug": "ferrothorn",
    "name": "Ferrothorn"
  },
  {
    "id": 599,
    "slug": "klink",
    "name": "Klink"
  },
  {
    "id": 600,
    "slug": "klang",
    "name": "Klang"
  },
  {
    "id": 601,
    "slug": "klinklang",
    "name": "Klinklang"
  },
  {
    "id": 602,
    "slug": "tynamo",
    "name": "Tynamo"
  },
  {
    "id": 603,
    "slug": "eelektrik",
    "name": "Eelektrik"
  },
  {
    "id": 604,
    "slug": "eelektross",
    "name": "Eelektross"
  },
  {
    "id": 605,
    "slug": "elgyem",
    "name": "Elgyem"
  },
  {
    "id": 606,
    "slug": "beheeyem",
    "name": "Beheeyem"
  },
  {
    "id": 607,
    "slug": "litwick",
    "name": "Litwick"
  },
  {
    "id": 608,
    "slug": "lampent",
    "name": "Lampent"
  },
  {
    "id": 609,
    "slug": "chandelure",
    "name": "Chandelure"
  },
  {
    "id": 610,
    "slug": "axew",
    "name": "Axew"
  },
  {
    "id": 611,
    "slug": "fraxure",
    "name": "Fraxure"
  },
  {
    "id": 612,
    "slug": "haxorus",
    "name": "Haxorus"
  },
  {
    "id": 613,
    "slug": "cubchoo",
    "name": "Cubchoo"
  },
  {
    "id": 614,
    "slug": "beartic",
    "name": "Beartic"
  },
  {
    "id": 615,
    "slug": "cryogonal",
    "name": "Cryogonal"
  },
  {
    "id": 616,
    "slug": "shelmet",
    "name": "Shelmet"
  },
  {
    "id": 617,
    "slug": "accelgor",
    "name": "Accelgor"
  },
  {
    "id": 618,
    "slug": "stunfisk",
    "name": "Stunfisk"
  },
  {
    "id": 619,
    "slug": "mienfoo",
    "name": "Mienfoo"
  },
  {
    "id": 620,
    "slug": "mienshao",
    "name": "Mienshao"
  },
  {
    "id": 621,
    "slug": "druddigon",
    "name": "Druddigon"
  },
  {
    "id": 622,
    "slug": "golett",
    "name": "Golett"
  },
  {
    "id": 623,
    "slug": "golurk",
    "name": "Golurk"
  },
  {
    "id": 624,
    "slug": "pawniard",
    "name": "Pawniard"
  },
  {
    "id": 625,
    "slug": "bisharp",
    "name": "Bisharp"
  },
  {
    "id": 626,
    "slug": "bouffalant",
    "name": "Bouffalant"
  },
  {
    "id": 627,
    "slug": "rufflet",
    "name": "Rufflet"
  },
  {
    "id": 628,
    "slug": "braviary",
    "name": "Braviary"
  },
  {
    "id": 629,
    "slug": "vullaby",
    "name": "Vullaby"
  },
  {
    "id": 630,
    "slug": "mandibuzz",
    "name": "Mandibuzz"
  },
  {
    "id": 631,
    "slug": "heatmor",
    "name": "Heatmor"
  },
  {
    "id": 632,
    "slug": "durant",
    "name": "Durant"
  },
  {
    "id": 633,
    "slug": "deino",
    "name": "Deino"
  },
  {
    "id": 634,
    "slug": "zweilous",
    "name": "Zweilous"
  },
  {
    "id": 635,
    "slug": "hydreigon",
    "name": "Hydreigon"
  },
  {
    "id": 636,
    "slug": "larvesta",
    "name": "Larvesta"
  },
  {
    "id": 637,
    "slug": "volcarona",
    "name": "Volcarona"
  },
  {
    "id": 638,
    "slug": "cobalion",
    "name": "Cobalion"
  },
  {
    "id": 639,
    "slug": "terrakion",
    "name": "Terrakion"
  },
  {
    "id": 640,
    "slug": "virizion",
    "name": "Virizion"
  },
  {
    "id": 641,
    "slug": "tornadus-incarnate",
    "name": "Tornadus Incarnate"
  },
  {
    "id": 642,
    "slug": "thundurus-incarnate",
    "name": "Thundurus Incarnate"
  },
  {
    "id": 643,
    "slug": "reshiram",
    "name": "Reshiram"
  },
  {
    "id": 644,
    "slug": "zekrom",
    "name": "Zekrom"
  },
  {
    "id": 645,
    "slug": "landorus-incarnate",
    "name": "Landorus Incarnate"
  },
  {
    "id": 646,
    "slug": "kyurem",
    "name": "Kyurem"
  },
  {
    "id": 647,
    "slug": "keldeo-ordinary",
    "name": "Keldeo Ordinary"
  },
  {
    "id": 648,
    "slug": "meloetta-aria",
    "name": "Meloetta Aria"
  },
  {
    "id": 649,
    "slug": "genesect",
    "name": "Genesect"
  },
  {
    "id": 650,
    "slug": "chespin",
    "name": "Chespin"
  },
  {
    "id": 651,
    "slug": "quilladin",
    "name": "Quilladin"
  },
  {
    "id": 652,
    "slug": "chesnaught",
    "name": "Chesnaught"
  },
  {
    "id": 653,
    "slug": "fennekin",
    "name": "Fennekin"
  },
  {
    "id": 654,
    "slug": "braixen",
    "name": "Braixen"
  },
  {
    "id": 655,
    "slug": "delphox",
    "name": "Delphox"
  },
  {
    "id": 656,
    "slug": "froakie",
    "name": "Froakie"
  },
  {
    "id": 657,
    "slug": "frogadier",
    "name": "Frogadier"
  },
  {
    "id": 658,
    "slug": "greninja",
    "name": "Greninja"
  },
  {
    "id": 659,
    "slug": "bunnelby",
    "name": "Bunnelby"
  },
  {
    "id": 660,
    "slug": "diggersby",
    "name": "Diggersby"
  },
  {
    "id": 661,
    "slug": "fletchling",
    "name": "Fletchling"
  },
  {
    "id": 662,
    "slug": "fletchinder",
    "name": "Fletchinder"
  },
  {
    "id": 663,
    "slug": "talonflame",
    "name": "Talonflame"
  },
  {
    "id": 664,
    "slug": "scatterbug",
    "name": "Scatterbug"
  },
  {
    "id": 665,
    "slug": "spewpa",
    "name": "Spewpa"
  },
  {
    "id": 666,
    "slug": "vivillon",
    "name": "Vivillon"
  },
  {
    "id": 667,
    "slug": "litleo",
    "name": "Litleo"
  },
  {
    "id": 668,
    "slug": "pyroar-male",
    "name": "Pyroar Male"
  },
  {
    "id": 669,
    "slug": "flabebe",
    "name": "Flabebe"
  },
  {
    "id": 670,
    "slug": "floette",
    "name": "Floette"
  },
  {
    "id": 671,
    "slug": "florges",
    "name": "Florges"
  },
  {
    "id": 672,
    "slug": "skiddo",
    "name": "Skiddo"
  },
  {
    "id": 673,
    "slug": "gogoat",
    "name": "Gogoat"
  },
  {
    "id": 674,
    "slug": "pancham",
    "name": "Pancham"
  },
  {
    "id": 675,
    "slug": "pangoro",
    "name": "Pangoro"
  },
  {
    "id": 676,
    "slug": "furfrou",
    "name": "Furfrou"
  },
  {
    "id": 677,
    "slug": "espurr",
    "name": "Espurr"
  },
  {
    "id": 678,
    "slug": "meowstic-male",
    "name": "Meowstic Male"
  },
  {
    "id": 679,
    "slug": "honedge",
    "name": "Honedge"
  },
  {
    "id": 680,
    "slug": "doublade",
    "name": "Doublade"
  },
  {
    "id": 681,
    "slug": "aegislash-shield",
    "name": "Aegislash Shield"
  },
  {
    "id": 682,
    "slug": "spritzee",
    "name": "Spritzee"
  },
  {
    "id": 683,
    "slug": "aromatisse",
    "name": "Aromatisse"
  },
  {
    "id": 684,
    "slug": "swirlix",
    "name": "Swirlix"
  },
  {
    "id": 685,
    "slug": "slurpuff",
    "name": "Slurpuff"
  },
  {
    "id": 686,
    "slug": "inkay",
    "name": "Inkay"
  },
  {
    "id": 687,
    "slug": "malamar",
    "name": "Malamar"
  },
  {
    "id": 688,
    "slug": "binacle",
    "name": "Binacle"
  },
  {
    "id": 689,
    "slug": "barbaracle",
    "name": "Barbaracle"
  },
  {
    "id": 690,
    "slug": "skrelp",
    "name": "Skrelp"
  },
  {
    "id": 691,
    "slug": "dragalge",
    "name": "Dragalge"
  },
  {
    "id": 692,
    "slug": "clauncher",
    "name": "Clauncher"
  },
  {
    "id": 693,
    "slug": "clawitzer",
    "name": "Clawitzer"
  },
  {
    "id": 694,
    "slug": "helioptile",
    "name": "Helioptile"
  },
  {
    "id": 695,
    "slug": "heliolisk",
    "name": "Heliolisk"
  },
  {
    "id": 696,
    "slug": "tyrunt",
    "name": "Tyrunt"
  },
  {
    "id": 697,
    "slug": "tyrantrum",
    "name": "Tyrantrum"
  },
  {
    "id": 698,
    "slug": "amaura",
    "name": "Amaura"
  },
  {
    "id": 699,
    "slug": "aurorus",
    "name": "Aurorus"
  },
  {
    "id": 700,
    "slug": "sylveon",
    "name": "Sylveon"
  },
  {
    "id": 701,
    "slug": "hawlucha",
    "name": "Hawlucha"
  },
  {
    "id": 702,
    "slug": "dedenne",
    "name": "Dedenne"
  },
  {
    "id": 703,
    "slug": "carbink",
    "name": "Carbink"
  },
  {
    "id": 704,
    "slug": "goomy",
    "name": "Goomy"
  },
  {
    "id": 705,
    "slug": "sliggoo",
    "name": "Sliggoo"
  },
  {
    "id": 706,
    "slug": "goodra",
    "name": "Goodra"
  },
  {
    "id": 707,
    "slug": "klefki",
    "name": "Klefki"
  },
  {
    "id": 708,
    "slug": "phantump",
    "name": "Phantump"
  },
  {
    "id": 709,
    "slug": "trevenant",
    "name": "Trevenant"
  },
  {
    "id": 710,
    "slug": "pumpkaboo-average",
    "name": "Pumpkaboo Average"
  },
  {
    "id": 711,
    "slug": "gourgeist-average",
    "name": "Gourgeist Average"
  },
  {
    "id": 712,
    "slug": "bergmite",
    "name": "Bergmite"
  },
  {
    "id": 713,
    "slug": "avalugg",
    "name": "Avalugg"
  },
  {
    "id": 714,
    "slug": "noibat",
    "name": "Noibat"
  },
  {
    "id": 715,
    "slug": "noivern",
    "name": "Noivern"
  },
  {
    "id": 716,
    "slug": "xerneas",
    "name": "Xerneas"
  },
  {
    "id": 717,
    "slug": "yveltal",
    "name": "Yveltal"
  },
  {
    "id": 718,
    "slug": "zygarde-50",
    "name": "Zygarde 50"
  },
  {
    "id": 719,
    "slug": "diancie",
    "name": "Diancie"
  },
  {
    "id": 720,
    "slug": "hoopa",
    "name": "Hoopa"
  },
  {
    "id": 721,
    "slug": "volcanion",
    "name": "Volcanion"
  },
  {
    "id": 722,
    "slug": "rowlet",
    "name": "Rowlet"
  },
  {
    "id": 723,
    "slug": "dartrix",
    "name": "Dartrix"
  },
  {
    "id": 724,
    "slug": "decidueye",
    "name": "Decidueye"
  },
  {
    "id": 725,
    "slug": "litten",
    "name": "Litten"
  },
  {
    "id": 726,
    "slug": "torracat",
    "name": "Torracat"
  },
  {
    "id": 727,
    "slug": "incineroar",
    "name": "Incineroar"
  },
  {
    "id": 728,
    "slug": "popplio",
    "name": "Popplio"
  },
  {
    "id": 729,
    "slug": "brionne",
    "name": "Brionne"
  },
  {
    "id": 730,
    "slug": "primarina",
    "name": "Primarina"
  },
  {
    "id": 731,
    "slug": "pikipek",
    "name": "Pikipek"
  },
  {
    "id": 732,
    "slug": "trumbeak",
    "name": "Trumbeak"
  },
  {
    "id": 733,
    "slug": "toucannon",
    "name": "Toucannon"
  },
  {
    "id": 734,
    "slug": "yungoos",
    "name": "Yungoos"
  },
  {
    "id": 735,
    "slug": "gumshoos",
    "name": "Gumshoos"
  },
  {
    "id": 736,
    "slug": "grubbin",
    "name": "Grubbin"
  },
  {
    "id": 737,
    "slug": "charjabug",
    "name": "Charjabug"
  },
  {
    "id": 738,
    "slug": "vikavolt",
    "name": "Vikavolt"
  },
  {
    "id": 739,
    "slug": "crabrawler",
    "name": "Crabrawler"
  },
  {
    "id": 740,
    "slug": "crabominable",
    "name": "Crabominable"
  },
  {
    "id": 741,
    "slug": "oricorio-baile",
    "name": "Oricorio Baile"
  },
  {
    "id": 742,
    "slug": "cutiefly",
    "name": "Cutiefly"
  },
  {
    "id": 743,
    "slug": "ribombee",
    "name": "Ribombee"
  },
  {
    "id": 744,
    "slug": "rockruff",
    "name": "Rockruff"
  },
  {
    "id": 745,
    "slug": "lycanroc-midday",
    "name": "Lycanroc Midday"
  },
  {
    "id": 746,
    "slug": "wishiwashi-solo",
    "name": "Wishiwashi Solo"
  },
  {
    "id": 747,
    "slug": "mareanie",
    "name": "Mareanie"
  },
  {
    "id": 748,
    "slug": "toxapex",
    "name": "Toxapex"
  },
  {
    "id": 749,
    "slug": "mudbray",
    "name": "Mudbray"
  },
  {
    "id": 750,
    "slug": "mudsdale",
    "name": "Mudsdale"
  },
  {
    "id": 751,
    "slug": "dewpider",
    "name": "Dewpider"
  },
  {
    "id": 752,
    "slug": "araquanid",
    "name": "Araquanid"
  },
  {
    "id": 753,
    "slug": "fomantis",
    "name": "Fomantis"
  },
  {
    "id": 754,
    "slug": "lurantis",
    "name": "Lurantis"
  },
  {
    "id": 755,
    "slug": "morelull",
    "name": "Morelull"
  },
  {
    "id": 756,
    "slug": "shiinotic",
    "name": "Shiinotic"
  },
  {
    "id": 757,
    "slug": "salandit",
    "name": "Salandit"
  },
  {
    "id": 758,
    "slug": "salazzle",
    "name": "Salazzle"
  },
  {
    "id": 759,
    "slug": "stufful",
    "name": "Stufful"
  },
  {
    "id": 760,
    "slug": "bewear",
    "name": "Bewear"
  },
  {
    "id": 761,
    "slug": "bounsweet",
    "name": "Bounsweet"
  },
  {
    "id": 762,
    "slug": "steenee",
    "name": "Steenee"
  },
  {
    "id": 763,
    "slug": "tsareena",
    "name": "Tsareena"
  },
  {
    "id": 764,
    "slug": "comfey",
    "name": "Comfey"
  },
  {
    "id": 765,
    "slug": "oranguru",
    "name": "Oranguru"
  },
  {
    "id": 766,
    "slug": "passimian",
    "name": "Passimian"
  },
  {
    "id": 767,
    "slug": "wimpod",
    "name": "Wimpod"
  },
  {
    "id": 768,
    "slug": "golisopod",
    "name": "Golisopod"
  },
  {
    "id": 769,
    "slug": "sandygast",
    "name": "Sandygast"
  },
  {
    "id": 770,
    "slug": "palossand",
    "name": "Palossand"
  },
  {
    "id": 771,
    "slug": "pyukumuku",
    "name": "Pyukumuku"
  },
  {
    "id": 772,
    "slug": "type-null",
    "name": "Type Null"
  },
  {
    "id": 773,
    "slug": "silvally",
    "name": "Silvally"
  },
  {
    "id": 774,
    "slug": "minior-red-meteor",
    "name": "Minior Red Meteor"
  },
  {
    "id": 775,
    "slug": "komala",
    "name": "Komala"
  },
  {
    "id": 776,
    "slug": "turtonator",
    "name": "Turtonator"
  },
  {
    "id": 777,
    "slug": "togedemaru",
    "name": "Togedemaru"
  },
  {
    "id": 778,
    "slug": "mimikyu-disguised",
    "name": "Mimikyu Disguised"
  },
  {
    "id": 779,
    "slug": "bruxish",
    "name": "Bruxish"
  },
  {
    "id": 780,
    "slug": "drampa",
    "name": "Drampa"
  },
  {
    "id": 781,
    "slug": "dhelmise",
    "name": "Dhelmise"
  },
  {
    "id": 782,
    "slug": "jangmo-o",
    "name": "Jangmo O"
  },
  {
    "id": 783,
    "slug": "hakamo-o",
    "name": "Hakamo O"
  },
  {
    "id": 784,
    "slug": "kommo-o",
    "name": "Kommo O"
  },
  {
    "id": 785,
    "slug": "tapu-koko",
    "name": "Tapu Koko"
  },
  {
    "id": 786,
    "slug": "tapu-lele",
    "name": "Tapu Lele"
  },
  {
    "id": 787,
    "slug": "tapu-bulu",
    "name": "Tapu Bulu"
  },
  {
    "id": 788,
    "slug": "tapu-fini",
    "name": "Tapu Fini"
  },
  {
    "id": 789,
    "slug": "cosmog",
    "name": "Cosmog"
  },
  {
    "id": 790,
    "slug": "cosmoem",
    "name": "Cosmoem"
  },
  {
    "id": 791,
    "slug": "solgaleo",
    "name": "Solgaleo"
  },
  {
    "id": 792,
    "slug": "lunala",
    "name": "Lunala"
  },
  {
    "id": 793,
    "slug": "nihilego",
    "name": "Nihilego"
  },
  {
    "id": 794,
    "slug": "buzzwole",
    "name": "Buzzwole"
  },
  {
    "id": 795,
    "slug": "pheromosa",
    "name": "Pheromosa"
  },
  {
    "id": 796,
    "slug": "xurkitree",
    "name": "Xurkitree"
  },
  {
    "id": 797,
    "slug": "celesteela",
    "name": "Celesteela"
  },
  {
    "id": 798,
    "slug": "kartana",
    "name": "Kartana"
  },
  {
    "id": 799,
    "slug": "guzzlord",
    "name": "Guzzlord"
  },
  {
    "id": 800,
    "slug": "necrozma",
    "name": "Necrozma"
  },
  {
    "id": 801,
    "slug": "magearna",
    "name": "Magearna"
  },
  {
    "id": 802,
    "slug": "marshadow",
    "name": "Marshadow"
  },
  {
    "id": 803,
    "slug": "poipole",
    "name": "Poipole"
  },
  {
    "id": 804,
    "slug": "naganadel",
    "name": "Naganadel"
  },
  {
    "id": 805,
    "slug": "stakataka",
    "name": "Stakataka"
  },
  {
    "id": 806,
    "slug": "blacephalon",
    "name": "Blacephalon"
  },
  {
    "id": 807,
    "slug": "zeraora",
    "name": "Zeraora"
  },
  {
    "id": 808,
    "slug": "meltan",
    "name": "Meltan"
  },
  {
    "id": 809,
    "slug": "melmetal",
    "name": "Melmetal"
  },
  {
    "id": 810,
    "slug": "grookey",
    "name": "Grookey"
  },
  {
    "id": 811,
    "slug": "thwackey",
    "name": "Thwackey"
  },
  {
    "id": 812,
    "slug": "rillaboom",
    "name": "Rillaboom"
  },
  {
    "id": 813,
    "slug": "scorbunny",
    "name": "Scorbunny"
  },
  {
    "id": 814,
    "slug": "raboot",
    "name": "Raboot"
  },
  {
    "id": 815,
    "slug": "cinderace",
    "name": "Cinderace"
  },
  {
    "id": 816,
    "slug": "sobble",
    "name": "Sobble"
  },
  {
    "id": 817,
    "slug": "drizzile",
    "name": "Drizzile"
  },
  {
    "id": 818,
    "slug": "inteleon",
    "name": "Inteleon"
  },
  {
    "id": 819,
    "slug": "skwovet",
    "name": "Skwovet"
  },
  {
    "id": 820,
    "slug": "greedent",
    "name": "Greedent"
  },
  {
    "id": 821,
    "slug": "rookidee",
    "name": "Rookidee"
  },
  {
    "id": 822,
    "slug": "corvisquire",
    "name": "Corvisquire"
  },
  {
    "id": 823,
    "slug": "corviknight",
    "name": "Corviknight"
  },
  {
    "id": 824,
    "slug": "blipbug",
    "name": "Blipbug"
  },
  {
    "id": 825,
    "slug": "dottler",
    "name": "Dottler"
  },
  {
    "id": 826,
    "slug": "orbeetle",
    "name": "Orbeetle"
  },
  {
    "id": 827,
    "slug": "nickit",
    "name": "Nickit"
  },
  {
    "id": 828,
    "slug": "thievul",
    "name": "Thievul"
  },
  {
    "id": 829,
    "slug": "gossifleur",
    "name": "Gossifleur"
  },
  {
    "id": 830,
    "slug": "eldegoss",
    "name": "Eldegoss"
  },
  {
    "id": 831,
    "slug": "wooloo",
    "name": "Wooloo"
  },
  {
    "id": 832,
    "slug": "dubwool",
    "name": "Dubwool"
  },
  {
    "id": 833,
    "slug": "chewtle",
    "name": "Chewtle"
  },
  {
    "id": 834,
    "slug": "drednaw",
    "name": "Drednaw"
  },
  {
    "id": 835,
    "slug": "yamper",
    "name": "Yamper"
  },
  {
    "id": 836,
    "slug": "boltund",
    "name": "Boltund"
  },
  {
    "id": 837,
    "slug": "rolycoly",
    "name": "Rolycoly"
  },
  {
    "id": 838,
    "slug": "carkol",
    "name": "Carkol"
  },
  {
    "id": 839,
    "slug": "coalossal",
    "name": "Coalossal"
  },
  {
    "id": 840,
    "slug": "applin",
    "name": "Applin"
  },
  {
    "id": 841,
    "slug": "flapple",
    "name": "Flapple"
  },
  {
    "id": 842,
    "slug": "appletun",
    "name": "Appletun"
  },
  {
    "id": 843,
    "slug": "silicobra",
    "name": "Silicobra"
  },
  {
    "id": 844,
    "slug": "sandaconda",
    "name": "Sandaconda"
  },
  {
    "id": 845,
    "slug": "cramorant",
    "name": "Cramorant"
  },
  {
    "id": 846,
    "slug": "arrokuda",
    "name": "Arrokuda"
  },
  {
    "id": 847,
    "slug": "barraskewda",
    "name": "Barraskewda"
  },
  {
    "id": 848,
    "slug": "toxel",
    "name": "Toxel"
  },
  {
    "id": 849,
    "slug": "toxtricity-amped",
    "name": "Toxtricity Amped"
  },
  {
    "id": 850,
    "slug": "sizzlipede",
    "name": "Sizzlipede"
  },
  {
    "id": 851,
    "slug": "centiskorch",
    "name": "Centiskorch"
  },
  {
    "id": 852,
    "slug": "clobbopus",
    "name": "Clobbopus"
  },
  {
    "id": 853,
    "slug": "grapploct",
    "name": "Grapploct"
  },
  {
    "id": 854,
    "slug": "sinistea",
    "name": "Sinistea"
  },
  {
    "id": 855,
    "slug": "polteageist",
    "name": "Polteageist"
  },
  {
    "id": 856,
    "slug": "hatenna",
    "name": "Hatenna"
  },
  {
    "id": 857,
    "slug": "hattrem",
    "name": "Hattrem"
  },
  {
    "id": 858,
    "slug": "hatterene",
    "name": "Hatterene"
  },
  {
    "id": 859,
    "slug": "impidimp",
    "name": "Impidimp"
  },
  {
    "id": 860,
    "slug": "morgrem",
    "name": "Morgrem"
  },
  {
    "id": 861,
    "slug": "grimmsnarl",
    "name": "Grimmsnarl"
  },
  {
    "id": 862,
    "slug": "obstagoon",
    "name": "Obstagoon"
  },
  {
    "id": 863,
    "slug": "perrserker",
    "name": "Perrserker"
  },
  {
    "id": 864,
    "slug": "cursola",
    "name": "Cursola"
  },
  {
    "id": 865,
    "slug": "sirfetchd",
    "name": "Sirfetchd"
  },
  {
    "id": 866,
    "slug": "mr-rime",
    "name": "Mr Rime"
  },
  {
    "id": 867,
    "slug": "runerigus",
    "name": "Runerigus"
  },
  {
    "id": 868,
    "slug": "milcery",
    "name": "Milcery"
  },
  {
    "id": 869,
    "slug": "alcremie",
    "name": "Alcremie"
  },
  {
    "id": 870,
    "slug": "falinks",
    "name": "Falinks"
  },
  {
    "id": 871,
    "slug": "pincurchin",
    "name": "Pincurchin"
  },
  {
    "id": 872,
    "slug": "snom",
    "name": "Snom"
  },
  {
    "id": 873,
    "slug": "frosmoth",
    "name": "Frosmoth"
  },
  {
    "id": 874,
    "slug": "stonjourner",
    "name": "Stonjourner"
  },
  {
    "id": 875,
    "slug": "eiscue-ice",
    "name": "Eiscue Ice"
  },
  {
    "id": 876,
    "slug": "indeedee-male",
    "name": "Indeedee Male"
  },
  {
    "id": 877,
    "slug": "morpeko-full-belly",
    "name": "Morpeko Full Belly"
  },
  {
    "id": 878,
    "slug": "cufant",
    "name": "Cufant"
  },
  {
    "id": 879,
    "slug": "copperajah",
    "name": "Copperajah"
  },
  {
    "id": 880,
    "slug": "dracozolt",
    "name": "Dracozolt"
  },
  {
    "id": 881,
    "slug": "arctozolt",
    "name": "Arctozolt"
  },
  {
    "id": 882,
    "slug": "dracovish",
    "name": "Dracovish"
  },
  {
    "id": 883,
    "slug": "arctovish",
    "name": "Arctovish"
  },
  {
    "id": 884,
    "slug": "duraludon",
    "name": "Duraludon"
  },
  {
    "id": 885,
    "slug": "dreepy",
    "name": "Dreepy"
  },
  {
    "id": 886,
    "slug": "drakloak",
    "name": "Drakloak"
  },
  {
    "id": 887,
    "slug": "dragapult",
    "name": "Dragapult"
  },
  {
    "id": 888,
    "slug": "zacian",
    "name": "Zacian"
  },
  {
    "id": 889,
    "slug": "zamazenta",
    "name": "Zamazenta"
  },
  {
    "id": 890,
    "slug": "eternatus",
    "name": "Eternatus"
  },
  {
    "id": 891,
    "slug": "kubfu",
    "name": "Kubfu"
  },
  {
    "id": 892,
    "slug": "urshifu-single-strike",
    "name": "Urshifu Single Strike"
  },
  {
    "id": 893,
    "slug": "zarude",
    "name": "Zarude"
  },
  {
    "id": 894,
    "slug": "regieleki",
    "name": "Regieleki"
  },
  {
    "id": 895,
    "slug": "regidrago",
    "name": "Regidrago"
  },
  {
    "id": 896,
    "slug": "glastrier",
    "name": "Glastrier"
  },
  {
    "id": 897,
    "slug": "spectrier",
    "name": "Spectrier"
  },
  {
    "id": 898,
    "slug": "calyrex",
    "name": "Calyrex"
  },
  {
    "id": 899,
    "slug": "wyrdeer",
    "name": "Wyrdeer"
  },
  {
    "id": 900,
    "slug": "kleavor",
    "name": "Kleavor"
  },
  {
    "id": 901,
    "slug": "ursaluna",
    "name": "Ursaluna"
  },
  {
    "id": 902,
    "slug": "basculegion-male",
    "name": "Basculegion Male"
  },
  {
    "id": 903,
    "slug": "sneasler",
    "name": "Sneasler"
  },
  {
    "id": 904,
    "slug": "overqwil",
    "name": "Overqwil"
  },
  {
    "id": 905,
    "slug": "enamorus-incarnate",
    "name": "Enamorus Incarnate"
  },
  {
    "id": 906,
    "slug": "sprigatito",
    "name": "Sprigatito"
  },
  {
    "id": 907,
    "slug": "floragato",
    "name": "Floragato"
  },
  {
    "id": 908,
    "slug": "meowscarada",
    "name": "Meowscarada"
  },
  {
    "id": 909,
    "slug": "fuecoco",
    "name": "Fuecoco"
  },
  {
    "id": 910,
    "slug": "crocalor",
    "name": "Crocalor"
  },
  {
    "id": 911,
    "slug": "skeledirge",
    "name": "Skeledirge"
  },
  {
    "id": 912,
    "slug": "quaxly",
    "name": "Quaxly"
  },
  {
    "id": 913,
    "slug": "quaxwell",
    "name": "Quaxwell"
  },
  {
    "id": 914,
    "slug": "quaquaval",
    "name": "Quaquaval"
  },
  {
    "id": 915,
    "slug": "lechonk",
    "name": "Lechonk"
  },
  {
    "id": 916,
    "slug": "oinkologne-male",
    "name": "Oinkologne Male"
  },
  {
    "id": 917,
    "slug": "tarountula",
    "name": "Tarountula"
  },
  {
    "id": 918,
    "slug": "spidops",
    "name": "Spidops"
  },
  {
    "id": 919,
    "slug": "nymble",
    "name": "Nymble"
  },
  {
    "id": 920,
    "slug": "lokix",
    "name": "Lokix"
  },
  {
    "id": 921,
    "slug": "pawmi",
    "name": "Pawmi"
  },
  {
    "id": 922,
    "slug": "pawmo",
    "name": "Pawmo"
  },
  {
    "id": 923,
    "slug": "pawmot",
    "name": "Pawmot"
  },
  {
    "id": 924,
    "slug": "tandemaus",
    "name": "Tandemaus"
  },
  {
    "id": 925,
    "slug": "maushold-family-of-four",
    "name": "Maushold Family Of Four"
  },
  {
    "id": 926,
    "slug": "fidough",
    "name": "Fidough"
  },
  {
    "id": 927,
    "slug": "dachsbun",
    "name": "Dachsbun"
  },
  {
    "id": 928,
    "slug": "smoliv",
    "name": "Smoliv"
  },
  {
    "id": 929,
    "slug": "dolliv",
    "name": "Dolliv"
  },
  {
    "id": 930,
    "slug": "arboliva",
    "name": "Arboliva"
  },
  {
    "id": 931,
    "slug": "squawkabilly-green-plumage",
    "name": "Squawkabilly Green Plumage"
  },
  {
    "id": 932,
    "slug": "nacli",
    "name": "Nacli"
  },
  {
    "id": 933,
    "slug": "naclstack",
    "name": "Naclstack"
  },
  {
    "id": 934,
    "slug": "garganacl",
    "name": "Garganacl"
  },
  {
    "id": 935,
    "slug": "charcadet",
    "name": "Charcadet"
  },
  {
    "id": 936,
    "slug": "armarouge",
    "name": "Armarouge"
  },
  {
    "id": 937,
    "slug": "ceruledge",
    "name": "Ceruledge"
  },
  {
    "id": 938,
    "slug": "tadbulb",
    "name": "Tadbulb"
  },
  {
    "id": 939,
    "slug": "bellibolt",
    "name": "Bellibolt"
  },
  {
    "id": 940,
    "slug": "wattrel",
    "name": "Wattrel"
  },
  {
    "id": 941,
    "slug": "kilowattrel",
    "name": "Kilowattrel"
  },
  {
    "id": 942,
    "slug": "maschiff",
    "name": "Maschiff"
  },
  {
    "id": 943,
    "slug": "mabosstiff",
    "name": "Mabosstiff"
  },
  {
    "id": 944,
    "slug": "shroodle",
    "name": "Shroodle"
  },
  {
    "id": 945,
    "slug": "grafaiai",
    "name": "Grafaiai"
  },
  {
    "id": 946,
    "slug": "bramblin",
    "name": "Bramblin"
  },
  {
    "id": 947,
    "slug": "brambleghast",
    "name": "Brambleghast"
  },
  {
    "id": 948,
    "slug": "toedscool",
    "name": "Toedscool"
  },
  {
    "id": 949,
    "slug": "toedscruel",
    "name": "Toedscruel"
  },
  {
    "id": 950,
    "slug": "klawf",
    "name": "Klawf"
  },
  {
    "id": 951,
    "slug": "capsakid",
    "name": "Capsakid"
  },
  {
    "id": 952,
    "slug": "scovillain",
    "name": "Scovillain"
  },
  {
    "id": 953,
    "slug": "rellor",
    "name": "Rellor"
  },
  {
    "id": 954,
    "slug": "rabsca",
    "name": "Rabsca"
  },
  {
    "id": 955,
    "slug": "flittle",
    "name": "Flittle"
  },
  {
    "id": 956,
    "slug": "espathra",
    "name": "Espathra"
  },
  {
    "id": 957,
    "slug": "tinkatink",
    "name": "Tinkatink"
  },
  {
    "id": 958,
    "slug": "tinkatuff",
    "name": "Tinkatuff"
  },
  {
    "id": 959,
    "slug": "tinkaton",
    "name": "Tinkaton"
  },
  {
    "id": 960,
    "slug": "wiglett",
    "name": "Wiglett"
  },
  {
    "id": 961,
    "slug": "wugtrio",
    "name": "Wugtrio"
  },
  {
    "id": 962,
    "slug": "bombirdier",
    "name": "Bombirdier"
  },
  {
    "id": 963,
    "slug": "finizen",
    "name": "Finizen"
  },
  {
    "id": 964,
    "slug": "palafin-zero",
    "name": "Palafin Zero"
  },
  {
    "id": 965,
    "slug": "varoom",
    "name": "Varoom"
  },
  {
    "id": 966,
    "slug": "revavroom",
    "name": "Revavroom"
  },
  {
    "id": 967,
    "slug": "cyclizar",
    "name": "Cyclizar"
  },
  {
    "id": 968,
    "slug": "orthworm",
    "name": "Orthworm"
  },
  {
    "id": 969,
    "slug": "glimmet",
    "name": "Glimmet"
  },
  {
    "id": 970,
    "slug": "glimmora",
    "name": "Glimmora"
  },
  {
    "id": 971,
    "slug": "greavard",
    "name": "Greavard"
  },
  {
    "id": 972,
    "slug": "houndstone",
    "name": "Houndstone"
  },
  {
    "id": 973,
    "slug": "flamigo",
    "name": "Flamigo"
  },
  {
    "id": 974,
    "slug": "cetoddle",
    "name": "Cetoddle"
  },
  {
    "id": 975,
    "slug": "cetitan",
    "name": "Cetitan"
  },
  {
    "id": 976,
    "slug": "veluza",
    "name": "Veluza"
  },
  {
    "id": 977,
    "slug": "dondozo",
    "name": "Dondozo"
  },
  {
    "id": 978,
    "slug": "tatsugiri-curly",
    "name": "Tatsugiri Curly"
  },
  {
    "id": 979,
    "slug": "annihilape",
    "name": "Annihilape"
  },
  {
    "id": 980,
    "slug": "clodsire",
    "name": "Clodsire"
  },
  {
    "id": 981,
    "slug": "farigiraf",
    "name": "Farigiraf"
  },
  {
    "id": 982,
    "slug": "dudunsparce-two-segment",
    "name": "Dudunsparce Two Segment"
  },
  {
    "id": 983,
    "slug": "kingambit",
    "name": "Kingambit"
  },
  {
    "id": 984,
    "slug": "great-tusk",
    "name": "Great Tusk"
  },
  {
    "id": 985,
    "slug": "scream-tail",
    "name": "Scream Tail"
  },
  {
    "id": 986,
    "slug": "brute-bonnet",
    "name": "Brute Bonnet"
  },
  {
    "id": 987,
    "slug": "flutter-mane",
    "name": "Flutter Mane"
  },
  {
    "id": 988,
    "slug": "slither-wing",
    "name": "Slither Wing"
  },
  {
    "id": 989,
    "slug": "sandy-shocks",
    "name": "Sandy Shocks"
  },
  {
    "id": 990,
    "slug": "iron-treads",
    "name": "Iron Treads"
  },
  {
    "id": 991,
    "slug": "iron-bundle",
    "name": "Iron Bundle"
  },
  {
    "id": 992,
    "slug": "iron-hands",
    "name": "Iron Hands"
  },
  {
    "id": 993,
    "slug": "iron-jugulis",
    "name": "Iron Jugulis"
  },
  {
    "id": 994,
    "slug": "iron-moth",
    "name": "Iron Moth"
  },
  {
    "id": 995,
    "slug": "iron-thorns",
    "name": "Iron Thorns"
  },
  {
    "id": 996,
    "slug": "frigibax",
    "name": "Frigibax"
  },
  {
    "id": 997,
    "slug": "arctibax",
    "name": "Arctibax"
  },
  {
    "id": 998,
    "slug": "baxcalibur",
    "name": "Baxcalibur"
  },
  {
    "id": 999,
    "slug": "gimmighoul",
    "name": "Gimmighoul"
  },
  {
    "id": 1000,
    "slug": "gholdengo",
    "name": "Gholdengo"
  },
  {
    "id": 1001,
    "slug": "wo-chien",
    "name": "Wo Chien"
  },
  {
    "id": 1002,
    "slug": "chien-pao",
    "name": "Chien Pao"
  },
  {
    "id": 1003,
    "slug": "ting-lu",
    "name": "Ting Lu"
  },
  {
    "id": 1004,
    "slug": "chi-yu",
    "name": "Chi Yu"
  },
  {
    "id": 1005,
    "slug": "roaring-moon",
    "name": "Roaring Moon"
  },
  {
    "id": 1006,
    "slug": "iron-valiant",
    "name": "Iron Valiant"
  },
  {
    "id": 1007,
    "slug": "koraidon",
    "name": "Koraidon"
  },
  {
    "id": 1008,
    "slug": "miraidon",
    "name": "Miraidon"
  },
  {
    "id": 1009,
    "slug": "walking-wake",
    "name": "Walking Wake"
  },
  {
    "id": 1010,
    "slug": "iron-leaves",
    "name": "Iron Leaves"
  },
  {
    "id": 1011,
    "slug": "dipplin",
    "name": "Dipplin"
  },
  {
    "id": 1012,
    "slug": "poltchageist",
    "name": "Poltchageist"
  },
  {
    "id": 1013,
    "slug": "sinistcha",
    "name": "Sinistcha"
  },
  {
    "id": 1014,
    "slug": "okidogi",
    "name": "Okidogi"
  },
  {
    "id": 1015,
    "slug": "munkidori",
    "name": "Munkidori"
  },
  {
    "id": 1016,
    "slug": "fezandipiti",
    "name": "Fezandipiti"
  },
  {
    "id": 1017,
    "slug": "ogerpon",
    "name": "Ogerpon"
  },
  {
    "id": 1018,
    "slug": "archaludon",
    "name": "Archaludon"
  },
  {
    "id": 1019,
    "slug": "hydrapple",
    "name": "Hydrapple"
  },
  {
    "id": 1020,
    "slug": "gouging-fire",
    "name": "Gouging Fire"
  },
  {
    "id": 1021,
    "slug": "raging-bolt",
    "name": "Raging Bolt"
  },
  {
    "id": 1022,
    "slug": "iron-boulder",
    "name": "Iron Boulder"
  },
  {
    "id": 1023,
    "slug": "iron-crown",
    "name": "Iron Crown"
  },
  {
    "id": 1024,
    "slug": "terapagos",
    "name": "Terapagos"
  },
  {
    "id": 1025,
    "slug": "pecharunt",
    "name": "Pecharunt"
  }
]

SLUG_TO_ID = {p["slug"]: p["id"] for p in POKEDEX_1025}
ID_TO_NAME = {p["id"]: p["name"] for p in POKEDEX_1025}

FORMAS_REGIONALES: List[Dict[str, Any]] = [
    # --- HISUI ---
    {"id": 704, "name": "Goomy (Hisui)", "slug": "goomy-hisui", "region": "Hisui", "family": [704, 705, 706]},
    {"id": 705, "name": "Sliggoo (Hisui)", "slug": "sliggoo-hisui", "region": "Hisui", "family": [704, 705, 706]},
    {"id": 706, "name": "Goodra (Hisui)", "slug": "goodra-hisui", "region": "Hisui", "family": [704, 705, 706]},
    {"id": 58, "name": "Growlithe (Hisui)", "slug": "growlithe-hisui", "region": "Hisui", "family": [58, 59]},
    {"id": 59, "name": "Arcanine (Hisui)", "slug": "arcanine-hisui", "region": "Hisui", "family": [58, 59]},
    {"id": 100, "name": "Voltorb (Hisui)", "slug": "voltorb-hisui", "region": "Hisui", "family": [100, 101]},
    {"id": 101, "name": "Electrode (Hisui)", "slug": "electrode-hisui", "region": "Hisui", "family": [100, 101]},
    {"id": 157, "name": "Typhlosion (Hisui)", "slug": "typhlosion-hisui", "region": "Hisui", "family": [155, 156, 157]},
    {"id": 211, "name": "Qwilfish (Hisui)", "slug": "qwilfish-hisui", "region": "Hisui", "family": [211, 904]},
    {"id": 215, "name": "Sneasel (Hisui)", "slug": "sneasel-hisui", "region": "Hisui", "family": [215, 903]},
    {"id": 503, "name": "Samurott (Hisui)", "slug": "samurott-hisui", "region": "Hisui", "family": [501, 502, 503]},
    {"id": 549, "name": "Lilligant (Hisui)", "slug": "lilligant-hisui", "region": "Hisui", "family": [548, 549]},
    {"id": 570, "name": "Zorua (Hisui)", "slug": "zorua-hisui", "region": "Hisui", "family": [570, 571]},
    {"id": 571, "name": "Zoroark (Hisui)", "slug": "zoroark-hisui", "region": "Hisui", "family": [570, 571]},
    {"id": 628, "name": "Braviary (Hisui)", "slug": "braviary-hisui", "region": "Hisui", "family": [627, 628]},
    {"id": 713, "name": "Avalugg (Hisui)", "slug": "avalugg-hisui", "region": "Hisui", "family": [712, 713]},
    {"id": 724, "name": "Decidueye (Hisui)", "slug": "decidueye-hisui", "region": "Hisui", "family": [722, 723, 724]},
    {"id": 901, "name": "Ursaluna (Hisui)", "slug": "ursaluna-hisui", "region": "Hisui", "family": [216, 217, 901]},
    {"id": 900, "name": "Kleavor", "slug": "kleavor", "region": "Hisui", "family": [123, 212, 900]},
    {"id": 904, "name": "Overqwil", "slug": "overqwil", "region": "Hisui", "family": [211, 904]},
    {"id": 903, "name": "Sneasler", "slug": "sneasler", "region": "Hisui", "family": [215, 903]},
    {"id": 899, "name": "Wyrdeer", "slug": "wyrdeer", "region": "Hisui", "family": [234, 899]},
    {"id": 902, "name": "Basculegion", "slug": "basculegion", "region": "Hisui", "family": [550, 902]},

    # --- ALOLA ---
    {"id": 19, "name": "Rattata (Alola)", "slug": "rattata-alola", "region": "Alola", "family": [19, 20]},
    {"id": 20, "name": "Raticate (Alola)", "slug": "raticate-alola", "region": "Alola", "family": [19, 20]},
    {"id": 26, "name": "Raichu (Alola)", "slug": "raichu-alola", "region": "Alola", "family": [172, 25, 26]},
    {"id": 27, "name": "Sandshrew (Alola)", "slug": "sandshrew-alola", "region": "Alola", "family": [27, 28]},
    {"id": 28, "name": "Sandslash (Alola)", "slug": "sandslash-alola", "region": "Alola", "family": [27, 28]},
    {"id": 37, "name": "Vulpix (Alola)", "slug": "vulpix-alola", "region": "Alola", "family": [37, 38]},
    {"id": 38, "name": "Ninetales (Alola)", "slug": "ninetales-alola", "region": "Alola", "family": [37, 38]},
    {"id": 50, "name": "Diglett (Alola)", "slug": "diglett-alola", "region": "Alola", "family": [50, 51]},
    {"id": 51, "name": "Dugtrio (Alola)", "slug": "dugtrio-alola", "region": "Alola", "family": [50, 51]},
    {"id": 52, "name": "Meowth (Alola)", "slug": "meowth-alola", "region": "Alola", "family": [52, 53]},
    {"id": 53, "name": "Persian (Alola)", "slug": "persian-alola", "region": "Alola", "family": [52, 53]},
    {"id": 74, "name": "Geodude (Alola)", "slug": "geodude-alola", "region": "Alola", "family": [74, 75, 76]},
    {"id": 75, "name": "Graveler (Alola)", "slug": "graveler-alola", "region": "Alola", "family": [74, 75, 76]},
    {"id": 76, "name": "Golem (Alola)", "slug": "golem-alola", "region": "Alola", "family": [74, 75, 76]},
    {"id": 88, "name": "Grimer (Alola)", "slug": "grimer-alola", "region": "Alola", "family": [88, 89]},
    {"id": 89, "name": "Muk (Alola)", "slug": "muk-alola", "region": "Alola", "family": [88, 89]},
    {"id": 103, "name": "Exeggutor (Alola)", "slug": "exeggutor-alola", "region": "Alola", "family": [102, 103]},
    {"id": 105, "name": "Marowak (Alola)", "slug": "marowak-alola", "region": "Alola", "family": [104, 105]},

    # --- GALAR ---
    {"id": 52, "name": "Meowth (Galar)", "slug": "meowth-galar", "region": "Galar", "family": [52, 863]},
    {"id": 863, "name": "Perrserker", "slug": "perrserker", "region": "Galar", "family": [52, 863]},
    {"id": 77, "name": "Ponyta (Galar)", "slug": "ponyta-galar", "region": "Galar", "family": [77, 78]},
    {"id": 78, "name": "Rapidash (Galar)", "slug": "rapidash-galar", "region": "Galar", "family": [77, 78]},
    {"id": 79, "name": "Slowpoke (Galar)", "slug": "slowpoke-galar", "region": "Galar", "family": [79, 80, 199]},
    {"id": 80, "name": "Slowbro (Galar)", "slug": "slowbro-galar", "region": "Galar", "family": [79, 80, 199]},
    {"id": 199, "name": "Slowking (Galar)", "slug": "slowking-galar", "region": "Galar", "family": [79, 80, 199]},
    {"id": 83, "name": "Farfetch'd (Galar)", "slug": "farfetchd-galar", "region": "Galar", "family": [83, 865]},
    {"id": 865, "name": "Sirfetch'd", "slug": "sirfetchd", "region": "Galar", "family": [83, 865]},
    {"id": 110, "name": "Weezing (Galar)", "slug": "weezing-galar", "region": "Galar", "family": [109, 110]},
    {"id": 122, "name": "Mr. Mime (Galar)", "slug": "mr-mime-galar", "region": "Galar", "family": [439, 122, 866]},
    {"id": 866, "name": "Mr. Rime", "slug": "mr-rime", "region": "Galar", "family": [439, 122, 866]},
    {"id": 144, "name": "Articuno (Galar)", "slug": "articuno-galar", "region": "Galar", "family": [144]},
    {"id": 145, "name": "Zapdos (Galar)", "slug": "zapdos-galar", "region": "Galar", "family": [145]},
    {"id": 146, "name": "Moltres (Galar)", "slug": "moltres-galar", "region": "Galar", "family": [146]},
    {"id": 222, "name": "Corsola (Galar)", "slug": "corsola-galar", "region": "Galar", "family": [222, 864]},
    {"id": 864, "name": "Cursola", "slug": "cursola", "region": "Galar", "family": [222, 864]},
    {"id": 263, "name": "Zigzagoon (Galar)", "slug": "zigzagoon-galar", "region": "Galar", "family": [263, 264, 862]},
    {"id": 264, "name": "Linoone (Galar)", "slug": "linoone-galar", "region": "Galar", "family": [263, 264, 862]},
    {"id": 862, "name": "Obstagoon", "slug": "obstagoon", "region": "Galar", "family": [263, 264, 862]},
    {"id": 554, "name": "Darumaka (Galar)", "slug": "darumaka-galar", "region": "Galar", "family": [554, 555]},
    {"id": 555, "name": "Darmanitan (Galar)", "slug": "darmanitan-galar", "region": "Galar", "family": [554, 555]},
    {"id": 562, "name": "Yamask (Galar)", "slug": "yamask-galar", "region": "Galar", "family": [562, 867]},
    {"id": 867, "name": "Runerigus", "slug": "runerigus", "region": "Galar", "family": [562, 867]},
    {"id": 618, "name": "Stunfisk (Galar)", "slug": "stunfisk-galar", "region": "Galar", "family": [618]},

    # --- PALDEA ---
    {"id": 194, "name": "Wooper (Paldea)", "slug": "wooper-paldea", "region": "Paldea", "family": [194, 195, 980]},
    {"id": 980, "name": "Clodsire", "slug": "clodsire", "region": "Paldea", "family": [194, 195, 980]},
    {"id": 128, "name": "Tauros (Paldea)", "slug": "tauros-paldea", "region": "Paldea", "family": [128]},
]

LOOKUP_REGIONAL_NORMALIZADO: Dict[str, Dict[str, Any]] = {}
for _r in FORMAS_REGIONALES:
    def _add_lk(k: str, obj: Dict[str, Any]) -> None:
        c = re.sub(r"[^a-z0-9]", "", k.lower())
        if c:
            LOOKUP_REGIONAL_NORMALIZADO[c] = obj

    _add_lk(_r["slug"], _r)
    _add_lk(_r["name"], _r)
    _base = re.sub(r"\(.*?\)", "", _r["name"]).strip()
    _reg = _r["region"]
    _add_lk(f"{_base} {_reg}", _r)
    _add_lk(f"{_base} de {_reg}", _r)
    _add_lk(f"{_reg} {_base}", _r)
    _add_lk(f"{_reg}an {_base}", _r)


def buscar_pokemon_autocomplete(query: str, limite: int = 25) -> List[Tuple[str, str]]:
    """
    Busca en tiempo real entre los 1025 Pokémon oficiales y las formas regionales (Hisui, Alola, Galar, Paldea)
    para el dropdown interactivo de Discord.
    Devuelve tuplas (etiqueta_visible, valor_a_enviar).
    """
    q = (query or "").strip().lower()
    q_slug = q.replace(" ", "-")
    q_num = re.sub(r"[^\d]", "", q)

    # Catálogo unificado
    catalogo = []
    for p in POKEDEX_1025:
        catalogo.append({
            "id": p["id"],
            "name": p["name"],
            "slug": p["slug"],
            "label": f"#{p['id']:03d} {p['name']}",
            "region": ""
        })
    for r in FORMAS_REGIONALES:
        catalogo.append({
            "id": r["id"],
            "name": r["name"],
            "slug": r["slug"],
            "label": f"#{r['id']:03d} {r['name']}",
            "region": r["region"].lower()
        })

    if not q:
        return [(x["label"], x["label"]) for x in catalogo[:limite]]

    coincidencias_exactas = []
    coincidencias_inicio = []
    coincidencias_contiene = []

    for item in catalogo:
        label = item["label"]
        name_low = item["name"].lower()
        slug = item["slug"]
        num_str = str(item["id"])
        reg = item["region"]

        if q_num and q_num == num_str:
            coincidencias_exactas.append((label, label))
        elif name_low.startswith(q) or slug.startswith(q_slug) or (reg and reg.startswith(q)):
            coincidencias_inicio.append((label, label))
        elif q in name_low or q in slug or (reg and q in reg):
            coincidencias_contiene.append((label, label))

    resultado = coincidencias_exactas + coincidencias_inicio + coincidencias_contiene
    vistos = set()
    dedup = []
    for l, val in resultado:
        if l not in vistos:
            vistos.add(l)
            dedup.append((l, val))
        if len(dedup) >= limite:
            break
    return dedup


def resolver_cadena_pokemon(
    entradas: Any,
    incluir_familia: bool = True,
    familias_dict: Optional[Dict[str, List[int]]] = None
) -> Dict[str, Any]:
    """
    Motor universal ultra-robusto para interpretar cualquier entrada de Pokémon:
    - Selección de autocomplete ('#704 Goomy', '#705 Sliggoo (Hisui)')
    - ID numérico ('#704', '704', '4', '#004')
    - Formas regionales ('Sliggoo Hisui', 'Goodra de Hisui', 'Goomy Hisui', 'Vulpix Alola', 'Zigzagoon Galar')
    - Nombres en texto simple ('Charmander', 'Beldum', 'Ralts')
    - Múltiples especies separadas por coma ('#705 Sliggoo (Hisui), Charmander, Squirtle')
    """
    if isinstance(entradas, str):
        entradas = [entradas]
    elif not isinstance(entradas, (list, tuple)):
        entradas = [str(entradas)]

    items: List[str] = []
    for e in entradas:
        if not e:
            continue
        parts = [p.strip() for p in re.split(r"[,;]+", str(e)) if p.strip()]
        items.extend(parts)

    nombres_elegidos: List[str] = []
    ids_totales: List[int] = []

    fams = familias_dict or {}

    for item in items:
        s = item.strip()
        if not s:
            continue
        clean_key = re.sub(r"[^a-z0-9]", "", s.lower())

        # 1. Búsqueda directa en Formas Regionales
        if clean_key in LOOKUP_REGIONAL_NORMALIZADO:
            reg = LOOKUP_REGIONAL_NORMALIZADO[clean_key]
            nom = reg["name"]
            if nom not in nombres_elegidos:
                nombres_elegidos.append(nom)
            fam = reg["family"] if incluir_familia else [reg["id"]]
            for fid in fam:
                if fid not in ids_totales:
                    ids_totales.append(fid)
            continue

        # 2. Coincidencia con formato '#704 Goomy' o '#705 Sliggoo (Hisui)' o '#704' o '704'
        m = re.match(r"^#?(\d+)(?:\s+(.*))?$", s)
        num = None
        if m:
            cand = int(m.group(1))
            resto = (m.group(2) or "").strip().lower()
            if 1 <= cand <= 1025:
                # Comprobar si el resto indica una variante regional
                matched_regional = False
                for reg_name in ("hisui", "alola", "galar", "paldea"):
                    if reg_name in resto:
                        for r in FORMAS_REGIONALES:
                            if r["id"] == cand and r["region"].lower() == reg_name:
                                nom = r["name"]
                                if nom not in nombres_elegidos:
                                    nombres_elegidos.append(nom)
                                fam = r["family"] if incluir_familia else [cand]
                                for fid in fam:
                                    if fid not in ids_totales:
                                        ids_totales.append(fid)
                                matched_regional = True
                                break
                        if matched_regional:
                            break
                if not matched_regional:
                    num = cand

        # 3. Búsqueda por slug o nombre exacto
        if num is None and clean_key not in LOOKUP_REGIONAL_NORMALIZADO:
            clean_slug = s.lower().replace(" ", "-")
            if clean_slug in SLUG_TO_ID:
                num = SLUG_TO_ID[clean_slug]
            elif clean_key in SLUG_TO_ID:
                num = SLUG_TO_ID[clean_key]

        if num:
            nom_base = ID_TO_NAME.get(num, f"#{num}")
            if nom_base not in nombres_elegidos:
                nombres_elegidos.append(nom_base)
            fam = fams.get(nom_base.lower(), [num]) if incluir_familia else [num]
            for fid in fam:
                if fid not in ids_totales:
                    ids_totales.append(fid)

    nombres_completos = [ID_TO_NAME.get(i, f"#{i}") for i in ids_totales]
    titulo = "Evento: " + ", ".join(nombres_elegidos[:3])
    if len(nombres_elegidos) > 3:
        titulo += f" (+{len(nombres_elegidos) - 3})"

    return {
        "nombres_principales": nombres_elegidos,
        "nombres_completos": nombres_completos,
        "ids_totales": ids_totales,
        "titulo_evento": titulo,
        "exito": bool(ids_totales),
    }
