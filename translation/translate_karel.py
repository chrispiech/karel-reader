import argparse
import os
import re

from javalang_fork import tokenizer
import translation_utils
from translator import translateWithForced

SILENT = True
SPACE_SENTINEL = '&nbsp;'

# default is 50
MAX_LINE_DEFAULT = 50
MAX_LINE_LENGTH_MAP = {
    'zh':25,
    'ja':25,
}

def translate_comment(id_map, comment, target_language):
    

    # First replace all identifiers with their common translation
    comment = translation_utils.make_known_translations(target_language, comment)

    # Preserve /*, /**, or // if present
    comment_starter_match = re.search(r"^((?:/\*+|//) *)(\n?)", comment)
    comment_starter = "" if comment_starter_match is None else comment_starter_match.group(1)
    text_start = len(comment_starter) # The starter should be the first characters of the comment
    newline_after_starter = comment_starter_match is not None and len(comment_starter_match.group(2)) > 0
    
    # Preserve */ if present. Also capture preceding whitespace because Google Translate will
    # discard the text segment's trailing whitespace
    comment_ender_match = re.search(r"(\s*\*/)$", comment)
    comment_ender = "" if comment_ender_match is None else comment_ender_match.group(1)
    text_end = len(comment) - len(comment_ender)

    text = comment[text_start:text_end].rstrip() # rstrip is optional; translate discards anyway

    if text.find("\n") == -1: # One-liners stay one-liners, even if the line ends up being longer than we'd like
        translated_text = translateWithForced(text, target_language)
        return "{}{}{}".format(comment_starter, translated_text, comment_ender)

    # Otherwise, convert a multi-line comment to a one-liner and then re-split it
    sample_text_line = re.search(r"\n(\s+)(\*?)", text)
    comment_indentation = sample_text_line.group(1)
    leading_asterisk_if_present = sample_text_line.group(2)
    text = re.sub(r"\n\s+\*?", "", text) # Converts the whole comment to one line

    # Remove dashes before translating because sometimes the dashes cause translation to fail
    pre_and_post_dash_text = re.split(r" -----+", text)

    pre_and_post_dash_text = [translateWithForced(token, target_language) for token in pre_and_post_dash_text]
    text_lines = []
    if newline_after_starter:
        text_lines.append("")
        # Make sure first line gets the newline and possibly asterisk line separator during the
        # join call below if and only if it is not on the same line as the comment starter
    

    # If the filename is being separated from the comment body, put the filename on the first line
    # of the final comment body, insert an appropriately sized line of dashes as the next line,
    # and split the rest of the body across lines as needed
    if len(pre_and_post_dash_text) > 1:
        file_intro = pre_and_post_dash_text[0]
        text_lines.append(' ' + file_intro.strip())
        new_dashes = " {}".format("-" * (len(file_intro) - 1)) # One char was a leading space
        text_lines.append(new_dashes)
        translated_text = pre_and_post_dash_text[1]
    else:
        translated_text = pre_and_post_dash_text[0]


    ''' 
    WARNING: for some languages like chinese there are no
    spaces between words and the characters are twice as large
    '''
    maxLineLength = getMaxLineLength(target_language)
    token_start = 0
    while token_start < len(translated_text):
        token_end = token_start + maxLineLength
        if token_end >= len(translated_text):
            token_end = len(translated_text)
        elif not translated_text[token_end].isspace():
            phrase = translated_text[token_start:token_end]
            phrase_end = phrase.rfind(" ")
            if phrase_end == -1:
                token_end = len(translated_text)
            else:
                token_end + token_start + phrase_end

        next_line = translated_text[token_start:token_end]
        text_lines.append(' ' + next_line.strip())
        # input('wait: ')
        token_start = token_end # Note that this means tokens will start with spaces if there was a leading asterisk
    
    # Note that the first token is the comment starter, so every text line will have the newline separator inserted
    comment_body = "\n{}{}".format(comment_indentation, leading_asterisk_if_present).join(text_lines)
    formatted = "{}{}{}".format(comment_starter, comment_body, comment_ender)

    # Now, replace any untranslated IDs in the comment text
    for identifier in id_map:
        translated = id_map[identifier]
        formatted = formatted.replace(identifier, translated)
    return formatted

def getMaxLineLength(target_language):
    if target_language in MAX_LINE_LENGTH_MAP:
        return MAX_LINE_LENGTH_MAP[target_language]
    return MAX_LINE_DEFAULT

def sanitize_translation_token(token):
    # you can assume that the input is lowercase
    if token == 'beeper': return 'cono'
    if token == 'beepers': return 'conos'
    return token

def sanitize_translation_tokens(split_translation):
    to_return = []
    for token in split_translation:
        sanitized = sanitize_translation_token(token)
        to_return.append(sanitized)
    return to_return

'''
Warning: this still leaves in punctuation
'''
def translate_identifier(identifier, target_language):
    api_translations = translation_utils.get_api_translations(target_language)
    if identifier in api_translations:
        return api_translations[identifier]
    # if identifier in known_translations:
    #     return known_translations[identifier]

    # dont translate 1 char ids like "i"
    if len(identifier) <= 1: return identifier

    case_type, tokens = translation_utils.split_cased_tokens(identifier)
    is_multitoken = len(tokens) > 1

    phrase = " ".join(tokens).lower()

    translated_identifier_tokens = translateWithForced(phrase, target_language)
    split_translation = translated_identifier_tokens.split(" ")

    split_sanitized = sanitize_translation_tokens(split_translation)

    if case_type == translation_utils.CaseType.UPPER_SNAKE:
        translated_identifier = "_".join(map(str.upper, split_sanitized))
    elif case_type == translation_utils.CaseType.LOWER_SNAKE:
        translated_identifier = "_".join(map(str.lower, split_sanitized))
    elif case_type == translation_utils.CaseType.UPPER_CAMEL:
        translated_identifier = "".join(map(str.title, split_sanitized))
    elif case_type == translation_utils.CaseType.LOWER_CAMEL:
        upper_camel = "".join(map(str.title, split_sanitized))
        translated_identifier = upper_camel[0].lower() + upper_camel[1:]
    else:
        print("Error determining identifier {}'s case type".format(identifier))
        # TODO make this error case more robust

    # Only store translations for tokens that vanilla text translation will not be able to handle
    if identifier != translated_identifier and is_multitoken:
        translation_utils.add_known_translation(target_language, identifier, translated_identifier)

    return translated_identifier


def collect_identifiers(tokens):
    ids = set([])
    for token in tokens:
        text = token.value
        if isinstance(token, tokenizer.Identifier):
            ids.add(text)
    return ids

def translate_token(id_map, token, target_lang):
    # id_map stores pre-translation of identifiers
    old_text = token.value
    new_text = old_text # default to copying the old text

    # We need to special case the NBSP tokens
    if isNBSP(token):
        return token

    if isinstance(token, tokenizer.String):
        new_text = translateWithForced(old_text, target_lang)
    elif isinstance(token, tokenizer.Comment):
        new_text = translate_comment(id_map, old_text, target_lang)
    elif isinstance(token, tokenizer.Identifier):
        new_text = id_map[old_text]
    token.value = new_text
    return token

def isNBSP(token):
    # this was solved by translating as "html"
    return False


def translate_code(code, target_lang):
    '''
    Translate code needs to do two passes. In the first pass we are going to translate
    all identifiers. Then in the second pass we can translate the remaining strings and
    comments.
    '''
    if not SILENT: print(code)
    tokens = tokenizer.tokenize(code)

    # first pass, translate identifiers
    identifiers = collect_identifiers(tokens)
    id_map = {}
    for id_name in identifiers:
        new_name = translate_identifier(id_name, target_lang)
        id_map[id_name] = new_name

    # second pass, translate the rest of the code
    translated_tokens = []
    tokens = tokenizer.tokenize(code)
    for token in tokens:
        translated = translate_token(id_map, token, target_lang)
        translated_tokens.append(translated)
    # input('pause')

    # reformat all the tokens
    to_return = tokenizer.reformat_tokens(translated_tokens)
    if not SILENT: 
        print('\n====\n')
        print(to_return)
    return to_return

def translate_program(filename, target_language):
    """Translates the code in a Java file from English to another language.
    Excludes identifiers that need to be in English for the code's syntactic correctness.

    Keyword arguments:
    filename -- the local path to a Java source file
    target_language -- the natural language to which text should be translated
    """
    path_segments = filename.split("/")
    page_name = path_segments[-1]
    # Currently assumes path is to a file in a folder for English versions
    output_dir = "/".join(
        [
            segment if segment != "en" else target_language
            for segment in path_segments[:-1]
        ]
    )
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    with open(filename, "r") as file:
        translated_file = translate_code(file.read(), target_language)
        with open(os.path.join(output_dir, page_name), "w") as outfile:
            outfile.write(translated_file)
    # TODO eliminate this code reuse by using better module structure


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "language", help="Two-letter (ISO 639-1) code for the target language"
    )
    parser.add_argument(
        "files",
        help="File(s) to be translated (use globbing to translate whole directories)",
        nargs="+",
    )
    args = parser.parse_args()
    for filename in args.files:
        print("Translating {}...".format(filename))
        translate_program(filename, args.language)
        print(" done.\n")


if __name__ == "__main__":
    main()
