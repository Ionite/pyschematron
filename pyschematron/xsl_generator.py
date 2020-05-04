#
# Helper functions to generate xsl from a Schematron Schema class
#

# Copyright (c) 2020 Ionite
# See LICENSE for the license

# This module provides semi-hardcoded XML output for XSLT generation,
# based on the XSLT output of the schematron skeleton implementation

# For escaping
from html import escape

# Some static strings used at the start
MODE_SCHEMATRON_SELECT_FULL_PATH = """  <!--MODE: SCHEMATRON-SELECT-FULL-PATH-->
  <!--This mode can be used to generate an ugly though full XPath for locators-->
  <xsl:template match="*" mode="schematron-select-full-path">
    <xsl:apply-templates select="." mode="schematron-get-full-path"/>
  </xsl:template>"""

MODE_SCHEMATRON_FULL_PATH = """  <!--MODE: SCHEMATRON-FULL-PATH-->
  <!--This mode can be used to generate an ugly though full XPath for locators-->
  <xsl:template match="*" mode="schematron-get-full-path">
    <xsl:apply-templates select="parent::*" mode="schematron-get-full-path"/>
    <xsl:text>/</xsl:text>
    <xsl:choose>
      <xsl:when test="namespace-uri()=''">
        <xsl:value-of select="name()"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>*:</xsl:text>
        <xsl:value-of select="local-name()"/>
        <xsl:text>[namespace-uri()='</xsl:text>
        <xsl:value-of select="namespace-uri()"/>
        <xsl:text>']</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:variable name="preceding" select="count(preceding-sibling::*[local-name()=local-name(current())                                   and namespace-uri() = namespace-uri(current())])"/>
    <xsl:text>[</xsl:text>
    <xsl:value-of select="1+ $preceding"/>
    <xsl:text>]</xsl:text>
  </xsl:template>
  <xsl:template match="@*" mode="schematron-get-full-path">
    <xsl:apply-templates select="parent::*" mode="schematron-get-full-path"/>
    <xsl:text>/</xsl:text>
    <xsl:choose>
      <xsl:when test="namespace-uri()=''">
        @
        <xsl:value-of select="name()"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>@*[local-name()='</xsl:text>
        <xsl:value-of select="local-name()"/>
        <xsl:text>' and namespace-uri()='</xsl:text>
        <xsl:value-of select="namespace-uri()"/>
        <xsl:text>']</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>"""

MODE_SCHEMATRON_FULL_PATH2 = """  <!--MODE: SCHEMATRON-FULL-PATH-2-->
  <!--This mode can be used to generate prefixed XPath for humans-->
  <xsl:template match="node() | @*" mode="schematron-get-full-path-2">
    <xsl:for-each select="ancestor-or-self::*">
      <xsl:text>/</xsl:text>
      <xsl:value-of select="name(.)"/>
      <xsl:if test="preceding-sibling::*[name(.)=name(current())]">
        <xsl:text>[</xsl:text>
        <xsl:value-of select="count(preceding-sibling::*[name(.)=name(current())])+1"/>
        <xsl:text>]</xsl:text>
      </xsl:if>
    </xsl:for-each>
    <xsl:if test="not(self::*)"><xsl:text/>
      /@
      <xsl:value-of select="name(.)"/>
    </xsl:if>
  </xsl:template>"""

MODE_SCHEMATRON_FULL_PATH3 = """  <!--MODE: SCHEMATRON-FULL-PATH-3-->
  <!--This mode can be used to generate prefixed XPath for humans
       (Top-level element has index)-->
  <xsl:template match="node() | @*" mode="schematron-get-full-path-3">
    <xsl:for-each select="ancestor-or-self::*">
      <xsl:text>/</xsl:text>
      <xsl:value-of select="name(.)"/>
      <xsl:if test="parent::*">
        <xsl:text>[</xsl:text>
        <xsl:value-of select="count(preceding-sibling::*[name(.)=name(current())])+1"/>
        <xsl:text>]</xsl:text>
      </xsl:if>
    </xsl:for-each>
    <xsl:if test="not(self::*)"><xsl:text/>
      /@
      <xsl:value-of select="name(.)"/>
    </xsl:if>
  </xsl:template>"""

MODE_SCHEMATRON_GENERATE_ID_FROM_PATH = """  <!--MODE: GENERATE-ID-FROM-PATH -->
  <xsl:template match="/" mode="generate-id-from-path"/>
  <xsl:template match="text()" mode="generate-id-from-path">
    <xsl:apply-templates select="parent::*" mode="generate-id-from-path"/>
    <xsl:value-of select="concat('.text-', 1+count(preceding-sibling::text()), '-')"/>
  </xsl:template>
  <xsl:template match="comment()" mode="generate-id-from-path">
    <xsl:apply-templates select="parent::*" mode="generate-id-from-path"/>
    <xsl:value-of select="concat('.comment-', 1+count(preceding-sibling::comment()), '-')"/>
  </xsl:template>
  <xsl:template match="processing-instruction()" mode="generate-id-from-path">
    <xsl:apply-templates select="parent::*" mode="generate-id-from-path"/>
    <xsl:value-of select="concat('.processing-instruction-', 1+count(preceding-sibling::processing-instruction()), '-')"/>
  </xsl:template>
  <xsl:template match="@*" mode="generate-id-from-path">
    <xsl:apply-templates select="parent::*" mode="generate-id-from-path"/>
    <xsl:value-of select="concat('.@', name())"/>
  </xsl:template>
  <xsl:template match="*" mode="generate-id-from-path" priority="-0.5">
    <xsl:apply-templates select="parent::*" mode="generate-id-from-path"/>
    <xsl:text>.</xsl:text>
    <xsl:value-of select="concat('.',name(),'-',1+count(preceding-sibling::*[name()=name(current())]),'-')"/>
  </xsl:template>
"""

MODE_SCHEMATRON_GENERATE_ID2 = """  <!--MODE: GENERATE-ID-2 -->
  <xsl:template match="/" mode="generate-id-2">U</xsl:template>
  <xsl:template match="*" mode="generate-id-2" priority="2">
    <xsl:text>U</xsl:text>
    <xsl:number level="multiple" count="*"/>
  </xsl:template>
  <xsl:template match="node()" mode="generate-id-2">
    <xsl:text>U.</xsl:text>
    <xsl:number level="multiple" count="*"/>
    <xsl:text>n</xsl:text>
    <xsl:number count="node()"/>
  </xsl:template>
  <xsl:template match="@*" mode="generate-id-2">
    <xsl:text>U.</xsl:text>
    <xsl:number level="multiple" count="*"/>
    <xsl:text>_</xsl:text>
    <xsl:value-of select="string-length(local-name(.))"/>
    <xsl:text>_</xsl:text>
    <xsl:value-of select="translate(name(),':','.')"/>
  </xsl:template>
"""

def schema_to_xsl(schema):
    """
    Returns an XSL that can be used with any xslt processor
    :return:
    """
    result = []
    result.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
    result.append('<xsl:stylesheet xmlns:xs="http://www.w3.org/2001/XMLSchema"')
    result.append('                xmlns:xsd="http://www.w3.org/2001/XMLSchema"')
    result.append('                xmlns:saxon = "http://saxon.sf.net/"')
    result.append('                xmlns:xsl = "http://www.w3.org/1999/XSL/Transform"')
    result.append('                xmlns:schold = "http://www.ascc.net/xml/schematron"')
    result.append('                xmlns:iso = "http://purl.oclc.org/dsdl/schematron"')
    result.append('                xmlns:xhtml = "http://www.w3.org/1999/xhtml"')
    for k, v in schema.ns_prefixes.items():
        if k != 'xs':
            result.append('                xmlns:%s="%s"' % (k, v))
    result.append('                version="2.0"><!--Implementers: please note that overriding process-prolog or process-root is')
    result.append('       the preferred method for meta-stylesheets to use where possible. -->')

    result.append('  <xsl:param name="archiveDirParameter"/>')
    result.append('  <xsl:param name="archiveNameParameter"/>')
    result.append('  <xsl:param name="fileNameParameter"/>')
    result.append('  <xsl:param name="fileDirParameter"/>')
    result.append('  <xsl:variable name="document-uri">')
    result.append('    <xsl:value-of select="document-uri(/)"/>')
    result.append('  </xsl:variable>')
    result.append('  ')
    result.append('  <!--PHASES-->')
    # TODO PHASES
    result.append('  <!--PROLOG-->')
    result.append('  <xsl:output xmlns:svrl="http://purl.oclc.org/dsdl/svrl" method="xml" omit-xml-declaration="no" standalone="yes" indent="yes"/>')
    result.append('  <!--XSD TYPES FOR XSLT2-->')
    result.append('  <!--KEYS AND FUNCTIONS-->')
    result.append('  <!--DEFAULT RULES-->')
    result.append(MODE_SCHEMATRON_SELECT_FULL_PATH)
    result.append(MODE_SCHEMATRON_FULL_PATH)
    result.append(MODE_SCHEMATRON_FULL_PATH2)
    result.append(MODE_SCHEMATRON_FULL_PATH3)
    result.append(MODE_SCHEMATRON_GENERATE_ID_FROM_PATH)
    result.append(MODE_SCHEMATRON_GENERATE_ID2)
    result.append('  <!--Strip characters-->')
    result.append('  <xsl:template match="text()" priority="-1"/>')
    result.append('  <!--SCHEMA SETUP-->')
    result.append('  <xsl:template match="/">')
    result.append('    <svrl:schematron-output xmlns:svrl="http://purl.oclc.org/dsdl/svrl" title="%s" schemaVersion="">' % schema.title)
    result.append('      <xsl:comment><xsl:value-of select="$archiveDirParameter"/>')
    result.append('         ')
    result.append('        <xsl:value-of select="$archiveNameParameter"/>')
    result.append('         ')
    result.append('        <xsl:value-of select="$fileNameParameter"/>')
    result.append('         ')
    result.append('        <xsl:value-of select="$fileDirParameter"/>')
    result.append('      </xsl:comment>')

    for k,v in schema.ns_prefixes.items():
        result.append('<svrl:ns-prefix-in-attribute-values uri="%s" prefix="%s"/>' % (v, k))
    # Add xs again, just to be sure
    result.append('      <svrl:ns-prefix-in-attribute-values uri="http://www.w3.org/2001/XMLSchema" prefix="xs"/>')

    pattern_mode_id = 10
    for pattern in schema.patterns.values():
        if not pattern.abstract:
            result.append('      <svrl:active-pattern>')
            result.append('        <xsl:attribute name="document">')
            result.append('          <xsl:value-of select="document-uri(/)"/>')
            result.append('        </xsl:attribute>')
            result.append('        <xsl:attribute name="id">%s</xsl:attribute>' % pattern.id)
            result.append('        <xsl:attribute name="name">%s</xsl:attribute>' % pattern.id)
            result.append('        <xsl:apply-templates/>')
            result.append('      </svrl:active-pattern>')
            result.append('      <xsl:apply-templates select="/" mode="M%d"/>' % pattern_mode_id)
            # Store mode id in the pattern for the next loop
            pattern.mode_id = pattern_mode_id
            if pattern.isa:
                abstract = schema.get_pattern(pattern.isa)
                abstract.mode_id = pattern_mode_id
            pattern_mode_id += 1
    result.append('  ')
    result.append('    </svrl:schematron-output>')
    result.append('  </xsl:template>')
    result.append('  <!--SCHEMATRON PATTERNS-->')
    result.append('  <svrl:text xmlns:svrl="http://purl.oclc.org/dsdl/svrl">%s</svrl:text>' % schema.title)
    for pattern in schema.patterns.values():
        if not pattern.abstract:
            if pattern.isa:
                pattern = schema.get_pattern(pattern.isa)
                #raise Exception("pattern %s has rules but is an is-a" % pattern.id)
            result.append('  <!--PATTERN %s-->' % pattern.id)

            for name,value in pattern.variables.items():
                result.append('  <xsl:variable name="%s" select="%s"/>' % (name, value))

            number_of_rules = len(pattern.rules)
            rule_number = 1
            for rule in pattern.rules:
                # priority counts backwards to 1000
                priority = 1000 + number_of_rules - rule_number
                result.append('  <!--RULE -->')
                result.append('  <xsl:template match="%s" priority="%d" mode="M%d">' % (rule.context, priority, pattern.mode_id))
                result.append('    <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl" context="%s"/>' % rule.context)

                for assertion in rule.assertions:
                    result.append('    <!--ASSERT -->')
                    result.append('    <xsl:choose>')
                    result.append('      <xsl:when test="%s"/>' % escape(assertion.test))
                    result.append('      <xsl:otherwise>')
                    result.append('        <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl" test="%s">' % escape(assertion.test))
                    if assertion.id is not None and assertion.id != "unset":
                        result.append('        <xsl:attribute name="id">%s</xsl:attribute>' % assertion.id)
                    result.append('        <xsl:attribute name="flag">%s</xsl:attribute>' % assertion.flag)
                    result.append('        <xsl:attribute name="location">')
                    result.append('          <xsl:apply-templates select="." mode="schematron-select-full-path"/>')
                    result.append('        </xsl:attribute>')
                    result.append('        <svrl:text>%s</svrl:text>' % assertion.text)
                    result.append('        </svrl:failed-assert>')
                    result.append('      </xsl:otherwise>')
                    result.append('    </xsl:choose>')

                result.append('    <xsl:apply-templates select="@*|*" mode="M%d"/>' % pattern.mode_id)
                result.append('  </xsl:template>')
                rule_number += 1

            result.append("""  <xsl:template match="text()" priority="-1" mode="M%d"/>
  <xsl:template match="@*|node()" priority="-2" mode="M%d">
    <xsl:apply-templates select="@*|*" mode="M%d"/>
  </xsl:template>""" % (pattern.mode_id, pattern.mode_id, pattern.mode_id))
    result.append('</xsl:stylesheet>')

    return '\n'.join(result)
