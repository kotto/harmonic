"""
English Response Templates for LM Arena
========================================
Usage: from en_templates import *
"""

EN_TEMPLATES = {
    'definition': {
        'open': [
            "{sujet} is defined as {objet}.",
            "{sujet} refers to {objet}.",
            "In simple terms, {sujet} means {objet}.",
            "By {sujet}, we mean {objet}.",
            "The term {sujet} designates {objet}.",
        ],
        'add': [
            "More specifically, it involves {objet}.",
            "In other words, {sujet} can be described as {objet}.",
            "To be precise, {sujet} corresponds to {objet}.",
        ],
        'close': [
            "In summary, {sujet} is fundamentally {objet}.",
            "The key takeaway: {sujet} is {objet}.",
        ],
    },
    'mechanism': {
        'open': [
            "{sujet} works through {objet}.",
            "The mechanism of {sujet} involves {objet}.",
            "At its core, {sujet} functions via {objet}.",
        ],
        'add': [
            "Additionally, {sujet} relies on {objet}.",
            "Furthermore, this process includes {objet}.",
        ],
        'close': [
            "Thus, {sujet} ultimately results in {objet}.",
        ],
    },
    'comparison': {
        'open': [
            "{sujet} and {objet} differ in that {sujet} is related to one aspect while {objet} relates to another.",
        ],
        'add': [
            "Another difference is that {sujet} involves {objet}.",
        ],
    },
    'general': {
        'open': ["Regarding {sujet}: {objet}."],
        'add': ["Furthermore, {sujet} relates to {objet}."],
        'close': ["In conclusion, {sujet} connects to {objet}."],
    },
    'unknown': [
        "I don't have enough information about that topic yet. My expertise covers sciences, mathematics, geography and history.",
        "That's outside my current knowledge base. I can help with science, math, geography and history questions.",
        "I'm not confident enough to answer that accurately.",
    ],
}

GREETING_EN = [
    "Hello. I'm KA, a harmonic AI. My expertise covers sciences, mathematics, geography and history. Ask me a question on these topics!",
    "Hi there. KA at your service. I can answer questions on physics, math, geography, history, and literature. What would you like to know?",
    "Greetings. I specialize in scientific reasoning. Feel free to ask me about science, geography, or history.",
]

IDENTITY_EN = (
    "I am KA (Knowledge Amplifier), a harmonic artificial intelligence. "
    "Unlike neural-network-based LLMs, I use wave interference for reasoning. "
    "I operate with 0 trained parameters, 0 GPU, and full determinism "
    "(same question always gives the same answer). "
    "My knowledge covers sciences, mathematics, geography, history, and literature."
)

OUT_OF_DOMAIN_EN = {
    'code': "I'm not a coding assistant. My architecture is wave-based, not neural. I can explain the scientific principles behind computing though.",
    'meteo': "I can't check the weather. My expertise is in fundamental sciences and knowledge.",
    'cuisine': "I don't have recipes. I cover physics, math, geography, history and related fields.",
    'actualite': "I'm not connected to current events. I deal with established knowledge.",
    'blague': "I don't tell jokes, but I can write a haiku or explain the physics of humor!",
}

DEFAULT_OUT_EN = "I specialize in sciences, geography, history and literature. I can't help with that specific request. Try asking me a science or knowledge question instead!"
