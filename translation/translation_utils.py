import os
import pickle
import re
import json
from enum import Enum


CaseType = Enum("CaseType", "UPPER_SNAKE LOWER_SNAKE UPPER_CAMEL LOWER_CAMEL")


def split_cased_tokens(identifier):
    if identifier.islower():
        return (CaseType.LOWER_SNAKE, identifier.split("_"))
    elif identifier.isupper():
        return (CaseType.UPPER_SNAKE, identifier.split("_"))

    # If neither, then either lower or upper camel case
    # TODO document more
    tokens = []
    token_start = 0
    for i, letter in enumerate(identifier[1:], start=1):
        if letter.isupper():
            tokens.append(identifier[token_start:i])
            token_start = i
    tokens.append(identifier[token_start:])
    case_type = (
        CaseType.LOWER_CAMEL if identifier[0].islower() else CaseType.UPPER_CAMEL
    )
    return (case_type, tokens)

# TODO make caps / plural stuff better based on: 
# r"([Ff])or ([Ll])oop(s?)": lambda match: "{}ucle{} {}or".format(
#     "B" if match.group(2).isupper() else "b",
#     match.group(3),
#     "F" if match.group(1).isupper() else "f"),
# r"([Ww])hile ([Ll])oop(s?)": lambda match: "{}ucle{} {}hile".format(
#     "B" if match.group(2).isupper() else "b",
#     match.group(3),
#     "W" if match.group(1).isupper() else "w")

HARDCODED_TRANSLATIONS = {
    "no_translate": {"run": "run", "main": "main"}
}

def get_api_json_filename(target_language):
    translation_dir = os.path.dirname(__file__)
    known_translations = os.path.join(translation_dir, "api")
    filename = target_language + '.json'
    return os.path.join(known_translations, filename)

def get_json_filename(target_language):
    translation_dir = os.path.dirname(__file__)
    known_translations = os.path.join(translation_dir, "forced_translations")
    filename = target_language + '.json'
    return os.path.join(known_translations, filename)

def get_pickle_filename(target_language):
    # directory is empty if the function is called by this module or
    # an absolute path if called by another module (works correctly either way)
    translation_dir = os.path.dirname(__file__)
    pickle_dir = os.path.join(translation_dir, "known_translations")
    if not os.path.exists(pickle_dir):
        os.makedirs(pickle_dir)
    filename = "{}.pkl".format(target_language)
    return os.path.join(pickle_dir, filename)

def get_api_translations(target_language):
    json_path = get_api_json_filename(target_language)
    if os.path.exists(json_path):
        return json.load(open(json_path))

def get_known_translations(target_language, is_pickle = True):
    if is_pickle:
        return get_known_translations_pkl(target_language)
    json_path = get_json_filename(target_language)
    if os.path.exists(json_path):
        return json.load(open(json_path))

    raise Exception('missing known translations. TODO: add default')

def get_known_translations_pkl(target_language):
    pickle_filename = get_pickle_filename(target_language)
    if os.path.exists(pickle_filename):
        with open(pickle_filename, "rb") as pickle_file:
            return pickle.load(pickle_file)

    if target_language in HARDCODED_TRANSLATIONS:
        return {
            **HARDCODED_TRANSLATIONS["no_translate"],
            **HARDCODED_TRANSLATIONS[target_language],
        }

    return HARDCODED_TRANSLATIONS["no_translate"]


def add_known_translation(target_language, english_identifier, translated_identifier):
    current_translations = get_known_translations(target_language)
    current_translations[english_identifier] = translated_identifier
    pickle_filename = get_pickle_filename(target_language)
    with open(pickle_filename, "wb+") as pickle_file:
        pickle.dump(current_translations, pickle_file)


def make_known_translations(target_language, text):
    known_translations = get_known_translations(target_language)
    # For each match, look up the corresponding value in the dictionary (approach from Python Cookbook)
    identifier_regex = re.compile(
        "({}){}".format("|".join(known_translations.keys()), r"(\W|$)")
    )
    return identifier_regex.sub(
        lambda match: "{}{}".format(
            known_translations[match.group(1)], match.group(2)
        ),
        text,
    )

TRANSLATION_OVERRIDES = {"es":
    {
    # Match the translatios of "for loop" and "while loop" that we specified in preprocessing
    # Allow an optional extra word between the two words in case there was an adjective describing
    # the loop (e.g., basic for loop --> bucle básico para should become bucle básico for)
    # Note that this strategy will cause incorrect behavior if the words "while" or "for" appear
    # adjacent to "for loop" or "while loop" (e.g., in "re-enter the for loop while the condition is true,"
    # you end up with "... el bucle para mientras ...," which will be incorrectly parsed as:
    # "el bucle para while ..." when it should be "el bucle for mientras ...")
    r"([Bb]ucles?(?: \w+)?) ([Pp])ara": lambda match: "{} {}or".format(
        match.group(1),
        "F" if match.group(2).isupper() else "f"),
    r"([Bb]ucles?(?: \w+)?) ([Mm])ientras": lambda match: "{} {}hile".format(
        match.group(1),
        "W" if match.group(2).isupper() else "w"),
    }
}

def override_translations(target_language, text):
    if target_language not in TRANSLATION_OVERRIDES:
        return text
    for incorrect_translation, replacement in TRANSLATION_OVERRIDES[target_language].items():
        text = re.sub(incorrect_translation, replacement, text)
    return text

# TODO move common translate_file functionality in here?
# No probably make translate.py for that since both main and translate_file have similarity