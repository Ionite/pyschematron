from lxml import etree

class ValidationContext(object):
    """
    Holds all the relevant data for an assertion to be validated
    """
    def __init__(self, schema, xml_doc):
        self.xml_doc = xml_doc
        self.variables = {}
        self.schema = schema
        self.pattern = None
        self.rule = None

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
        copy.pattern = self.pattern
        copy.rule = self.rule
        return copy

    def msg(self, level, msg):
        if self.schema.verbosity >= level:
            print(msg)

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

    def validate_assertions(self, element):
        errors = []
        warnings = []
        r = self.rule
        for a in r.assertions:
            self.msg(3, "Start test: %s" % a.id)
            self.msg(4, "Test context: %s" % str(r.context))
            self.msg(4, "Test expression: %s" % a.test)
            result = self.schema.query_binding.evaluate_assertion(self.xml_doc, element, self.schema.ns_prefixes, self.variables,
                                                           a.test)
            if not result:
                self.msg(5, "Failed assertion")
                self.msg(5, "Pattern: %s" % self.pattern.id)
                self.msg(5, "Variables:")
                for k, v in self.variables.items():
                    self.msg(5, "  %s: %s" % (k, v))
                self.msg(5, "Context root: %s" % str(self.xml_doc.getroot()))
                self.msg(5, "Context item: %s" % r.context)
                self.msg(5, "CONTEXT ELEMENT: " + etree.tostring(element, pretty_print=True).decode('utf-8'))
                if 'id' in a.__dict__:
                    self.msg(5, "Id: " + a.id)
                self.msg(5, "Test: '%s'" % a.test)
                self.msg(5, "Result: %s" % str(result))

                if a.flag == "warning":
                    warnings.append(a)
                else:
                    # raise Exception(self.file_path)
                    errors.append(a)

        return errors, warnings