from elementpath.xpath_context import XPathContext


class XPathContextXSLT(XPathContext):
    """
    This class extends the standard XPathContext with some additional functionality to support
    XSLT functions, such as current().
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_item = self.item

    def __copy__(self):
        result = super().__copy__()
        result.current_item = self.current_item
        return result
