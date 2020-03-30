import re

import js2py

from google.cloud import translate


"""
For now, assumes code is written in Javascript
"""


def get_comments(tree):
    result = set([])
    comment_entries = tree["comments"]
    for entry in comment_entries:
        result.add(entry["value"])
    return result


def get_children(tree):
    children = []
    for v in tree.values():
        if isinstance(v, list):
            children = children + v
        elif isinstance(v, dict):
            children.append(v)
    return children


def get_translatables(tree, id_list, str_lit_list):
    if tree["type"] == "Identifier":
        if len(tree["name"]) > 2:
            id_list.add(tree["name"])
    elif tree["type"] == "Literal":
        if isinstance(tree["value"], str):
            str_lit_list.add(tree["value"])
    else:
        for child in get_children(tree):
            get_translatables(child, id_list, str_lit_list)


def get_target(id_list, str_lit_list, comment_list, target_language):
    src_target_map = dict([])
    translation_client = translate.Client()

    for source in id_list:
        unconcat_src = unconcat(source)
        target = translation_client.translate(
            unconcat_src, target_language=target_language
        )["translatedText"]
        target = concat(target)
        src_target_map[source] = target

    for source in str_lit_list | comment_list:
        target = translation_client.translate(source, target_language=target_language)[
            "translatedText"
        ]
        src_target_map[source] = target

    return src_target_map


def src_to_target(code_src, src_target_map):
    code_target = code_src
    for src, target in src_target_map.items():
        # code_target = code_target.replace(src, target)
        pattern = r"(?:((?<=\W)|(?<=\b)))" + src + r"(?=\W)"  # (?<=\W)
        code_target = re.sub(pattern, target, code_target)
    return code_target


def unconcat(string):
    length = len(string)
    substrings = []

    start_index = 0
    for i in range(1, length):
        if string[i].isupper():
            end_index = i
            substrings.append(string[start_index:end_index])
            start_index = i
    substrings.append(string[start_index:])

    separator = " "
    return separator.join(substrings)


def concat(string):
    substrings = string.split(" ")
    substrings[0] = substrings[0].lower()
    for i in range(1, len(substrings)):
        substrings[i] = substrings[i].capitalize()
    return "".join(substrings)


def translate_code(code, target_language):
    syntax_tree = (
        js2py.require("esprima").parseScript(code, {"comment": True}).to_dict()
    )
    import pdb
    pdb.set_trace()
    id_list, str_lit_list = set([]), set([])
    get_translatables(syntax_tree, id_list, str_lit_list)
    comment_list = get_comments(syntax_tree)
    src_target_map = get_target(id_list, str_lit_list, comment_list, target_language)
    translated_code = src_to_target(code, src_target_map)

    return translated_code

def main():
    code = u"""
    // Here's a leading comment.
    var greeting = "Hello, my friends!"
    function fillPothole() {
       turnRight();
       move();
       moveToWall();
       if (noBeepersPresent()) {
          putBeeper();
       }
       turnAround();
       move();
       turnRight();
    }
    /* Here's a trailing comment. */
    """
    target_language = "es"

    translated_code = translate_code(code, target_language)
    print("Original code: {}".format(code))
    print("Translated code: {}".format(translated_code))


if __name__ == "__main__":
    main()
