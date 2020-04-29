from elementpath.xpath_context import XPathContext
from elementpath.xpath2_parser import XPath2Parser as XPath2Parser
from elementpath.xpath1_parser import is_document_node

def oselect_with_context(document_root, context_item, path, namespaces=None, parser=None, **kwargs):
    """
    XPath selector function that apply a *path* expression on *root* Element.

    :param root: An Element or ElementTree instance.
    :param path: The XPath expression.
    :param namespaces: A dictionary with mapping from namespace prefixes into URIs.
    :param parser: The parser class to use, that is :class:`XPath2Parser` for default.
    :param kwargs: Other optional parameters for the XPath parser instance.
    :return: A list with XPath nodes or a basic type for expressions based \
    on a function or literal.
    """
    parser = (parser or XPath2Parser)(namespaces, **kwargs)
    root_token = parser.parse(path)
    context = XPathContext(document_root, item=context_item)
    eval_result = root_token.evaluate(context)
    print("[XX] EVALUATE WOULD RESULT IN: %s (%s)" % (str(eval_result), str(type(eval_result))))
    results = root_token.get_results(context)
    print("[XX] RESULTS ARE: %s (%s)" % (str(results), str(type(results))))
    return results

def select_with_context(document, context_item, path, namespaces=None, parser=None, **kwargs):
    """
    XPath selector function that apply a *path* expression on *root* Element.

    :param root: An Element or ElementTree instance.
    :param path: The XPath expression.
    :param namespaces: A dictionary with mapping from namespace prefixes into URIs.
    :param parser: The parser class to use, that is :class:`XPath2Parser` for default.
    :param kwargs: Other optional parameters for the XPath parser instance.
    :return: A list with XPath nodes or a basic type for expressions based \
    on a function or literal.
    """
    if not is_document_node(document):
        raise Exception("select_with_context document parameter MUST be a full ElementTree")
    parser = (parser or XPath2Parser)(namespaces, **kwargs)
    root_token = parser.parse(path)
    context = XPathContext(document, item=context_item)
    result = root_token.get_results(context)
    return result

class SelectorWithContext(object):
    pass
