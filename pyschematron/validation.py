class ValidationContext(object):
    """
    Holds all the relevant data for an assertion to be validated
    """
    def __init__(self, schema, xml_doc):
        self.xml_doc = xml_doc
        self.variables = {}
        self.schema = schema
        self.add_variables(schema.variables)

    def set_pattern(self, pattern):
        self.pattern = pattern
        self.add_variables(pattern.variables)

    def set_rule(self, rule):
        self.rule = rule
        self.add_variables(rule.variables)

    def add_variables(self, variables):
        for name, value in variables.items():
            self.variables[name] = self.schema.query_binding.interpret_let_statement(self.xml_doc, value, self.schema.ns_prefixes, self.variables)

    def copy(self):
        copy = ValidationContext(self.schema, self.xml_doc)
        copy.variables = self.variables.copy()
        return copy

    def get_rule_context_elements(self):
        """
        Returns all the elements in the xml doc that match the rule's context expression
        :return:
        """
        if self.rule.context == '/':
            return [None]
        else:
            return self.schema.query_binding.get_context_elements(self.xml_doc,
                                                                  self.rule.context,
                                                                  namespaces=self.schema.ns_prefixes,
                                                                  variables=self.variables)

    def validate_assertions(self):
        errors = []
        warnings = []

        return errors, warnings