from .grammar import elements

def format_element_tree(root_element):
    """
    Function which takes an element and creates a human-readable string showing the structure of the element tree it contains.

    Inputs: root_element - The element to use as the base of the element tree to construct the string representation of

    Outputs: A string containing a human-readable form of the given element
    """

    output_lines = []

    def _process_element(element, indentation):
        output_lines.append("%s%s" % (' ' * (4 * indentation), repr(element)))

        if isinstance(element, elements.BaseScopedElement):
            for sub_element in element.sub_elements:
                _process_element(sub_element, indentation + 1)

            if element.delimiter_grammar:
                _process_element(element.delimiter_grammar, indentation + 1)

    if getattr(root_element, "sub_elements", None):
        for sub_element in root_element.sub_elements:
            _process_element(sub_element, 0)

    return "\n".join(output_lines)


def format_subgrammar_tree(root_element):
    """
    Function which takes a sub grammar element and creates a human-readable string showing the
    structure of the sub grammar tree it contains.

    Inputs: root_element - The sub grammar element to use as the base of the element tree to construct the string representation of

    Outputs: A string containing a human-readable form of the given element
    """

    output_lines = []

    def _process_element(element, indentation):
        output_lines.append("%s%s" % (' ' * (4 * indentation), repr(element)))

        if isinstance(element, elements.SubGrammarDefinition):
            for sub_element in element.sub_elements:
                _process_element(sub_element, indentation + 1)

            for name, sub_grammar in sorted(element.sub_grammars.items()):
                _process_element(sub_grammar, indentation + 1)

    for name, sub_grammar in sorted(root_element.sub_grammars.items()):
        _process_element(sub_grammar, 0)

    return "\n".join(output_lines)
