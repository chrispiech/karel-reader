import argparse
import os
import re

from javalang_fork import tokenizer
import translation_utils

from google.cloud import translate

SILENT = False




def translate_comment(comment, translation_client, target_language):
    MAX_LINE_LENGTH = 50

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
        translated_text = translation_client.translate(
                text, target_language=target_language, source_language="en", format_="text"
            )["translatedText"]
        return "{}{}{}".format(comment_starter, translated_text, comment_ender)

    # Otherwise, convert a multi-line comment to a one-liner and then re-split it
    sample_text_line = re.search(r"\n(\s+)(\*?)", text)
    comment_indentation = sample_text_line.group(1)
    leading_asterisk_if_present = sample_text_line.group(2)
    text = re.sub(r"\n\s+\*?", "", text) # Converts the whole comment to one line

    # Remove dashes before translating because sometimes the dashes cause translation to fail
    pre_and_post_dash_text = re.split(r" -----+", text)

    pre_and_post_dash_text = [translation_client.translate(
                token, target_language=target_language, source_language="en", format_="text"
            )["translatedText"] for token in pre_and_post_dash_text]

    text_lines = []
    if newline_after_starter:
        text_lines.append("")
        # Make sure first line gets the newline and possibly asterisk line separator during the
        # join call below if and only if it is not on the same line as the comment starter
    token_start = 0

    # If the filename is being separated from the comment body, put the filename on the first line
    # of the final comment body, insert an appropriately sized line of dashes as the next line,
    # and split the rest of the body across lines as needed
    if len(pre_and_post_dash_text) > 1:
        file_intro = pre_and_post_dash_text[0]
        text_lines.append(file_intro)
        new_dashes = " {}".format("-" * (len(file_intro) - 1)) # One char was a leading space
        text_lines.append(new_dashes)
        translated_text = pre_and_post_dash_text[1]
    else:
        translated_text = pre_and_post_dash_text[0]

    # Wrap lines based on a length constraint
    while token_start < len(translated_text):
        token_end = token_start + MAX_LINE_LENGTH
        if token_end >= len(translated_text):
            token_end = len(translated_text)
        elif not translated_text[token_end].isspace():
            token_end = translated_text.rfind(" ", token_start, token_end)
            if token_end == -1:
                token_end = len(translated_text)
        text_lines.append(translated_text[token_start:token_end])
        token_start = token_end # Note that this means tokens will start with spaces if there was a leading asterisk
    
    # Note that the first token is the comment starter, so every text line will have the newline separator inserted
    comment_body = "\n{}{}".format(comment_indentation, leading_asterisk_if_present).join(text_lines)
    return "{}{}{}".format(comment_starter, comment_body, comment_ender)

def translate_identifier(identifier, translation_client, target_language):
    known_translations = translation_utils.get_known_translations(target_language)
    if identifier in known_translations:
        print('known..')
        return known_translations[identifier]

    case_type, tokens = translation_utils.split_cased_tokens(identifier)
    is_multitoken = len(tokens) > 1

    print(case_type, tokens)
    phrase = " ".join(tokens).lower()
    print(phrase)
    translated_identifier_tokens = translation_client.translate(
                phrase, target_language=target_language, source_language="en", format_="text"
            )["translatedText"]
    if case_type == translation_utils.CaseType.UPPER_SNAKE:
        translated_identifier = "_".join(map(str.upper, translated_identifier_tokens.split(" ")))
    elif case_type == translation_utils.CaseType.LOWER_SNAKE:
        translated_identifier = "_".join(map(str.lower, translated_identifier_tokens.split(" ")))
    elif case_type == translation_utils.CaseType.UPPER_CAMEL:
        translated_identifier = "".join(map(str.title, translated_identifier_tokens.split(" ")))
    elif case_type == translation_utils.CaseType.LOWER_CAMEL:
        upper_camel = "".join(map(str.title, translated_identifier_tokens.split(" ")))
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
        is_id = isinstance(token, tokenizer.Identifier)
        if is_id and len(text) > 2:
            ids.add(text)
    return ids

def translate_code(code, target_lang):
    '''
    Translate code needs to do two passes. In the first pass we are going to translate
    all identifiers. Then in the second pass we can translate the remaining strings and
    comments.
    '''
    if not SILENT: print(code)

    

    tokens = tokenizer.tokenize(code)
    translated_tokens = []
    translation_client = translate.Client()

    identifiers = collect_identifiers(tokens)
    for id_name in identifiers:
        # testing...
        if id_name != 'BeeperLineBug': continue
        new_name = translate_identifier(id_name, translation_client, target_lang)
        print(id_name, new_name)

    # for token in tokens:
    #     text = token.value
    #     if isinstance(token, tokenizer.String):
    #         text = translation_client.translate(
    #             text, target_language=target_language, source_language="en", format_="text"
    #         )["translatedText"]
    #     elif isinstance(token, tokenizer.Comment):
    #         text = translate_comment(text, translation_client, target_language)
    #     elif isinstance(token, tokenizer.Identifier) and len(text) > 2:
    #         text = translate_identifier(text, translation_client, target_language)
    #     token.value = text
    #     translated_tokens.append(token)

    # toReturn = tokenizer.reformat_tokens(translated_tokens)
    # if not SILENT: 
    #     print('\n====\n')
    #     print(toReturn)
    # return toReturn
    raise Exception('test')

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
