#! /usr/bin/env python
# encoding: utf-8

from __future__ import unicode_literals
import logging
import re
from antlr4.error.ErrorListener import ErrorListener
from antlr4.tree.Tree import TerminalNodeImpl as TerminalNode

from tutorons.common.java.gateway import java_isinstance
from tutorons.common.java.simplenlg import factory as nlg_factory,\
    Feature, NumberAgreement, NPPhraseSpec, realiser
from parsers.xpath.xpathLexer import xpathLexer
from parsers.xpath.xpathParser import xpathParser
from parsers.xpath.xpathListener import xpathListener
from parsers.common.util import parse_plaintext, walk_tree


logging.basicConfig(level=logging.INFO, format="%(message)s")


# Convenience function for finding the parent of a terminal node, or where the tree branches
def get_interesting_nodes(node):
    while node.getChildCount() == 1 and not isinstance(node.getChild(0), TerminalNode):
        node = node.getChild(0)
    return node

def explain(xpath):
    explainer = xpathExplainer()
    try:
        parse_tree = parse_plaintext(xpath, xpathLexer, xpathParser, 'main')
        walk_tree(parse_tree, explainer)
        explanations = {}
        for xpath, clause in explainer.result.items():
            explanations[xpath] =\
                "The '" + xpath + "'xpath chooses " +\
                str(realiser.realise(clause)) + "."
        return explanations
    except Exception as exception:
        # Although this is a pretty broad catch, we want the default
        # behavior of explanation to be that the program continues to
        # run, even if one xpath was not properly explained.
        logging.error("Error generating examples: %s", str(exception))
        return None

def explain_location_path(location_path):
    # phrase = None

    # for child in path.getChildren():
    #     if isinstance(child, xpathParser.absoluteLocationPathNoroot):
    #         # add 'from the root node'
    #     else:
    #         explanation = explain_relative_location_path(child)
    #         # explain relative location path
    #         # 
    pass

def explain_relative_location_path(relative_location_path):
    pass

def explain_step(step):
    print('in step')
    # a step consists of an (axis specifier), node test and (predicate)
    clause = nlg_factory.createNounPhrase()

    preModifier = explain_axis_specifier(step.children[0])
    print('preModifier: ' + preModifier)
    clause.addPreModifier(preModifier)

    # alter noun if it's an attribute deal
    noun = explain_node_test(step.children[1])
    clause.setNoun(noun)

    if step.getChildCount() == 3:
        modifier = explain_predicate(step.children[2])
        clause.addModifier(modifier)

    return clause

def explain_axis_specifier(axis_specifier):
    print(type(axis_specifier))
    if axis_specifier.getChildCount() == 0:
        return 'children of'
    else:
        AXIS_NAMES = {
            'ancestor': 'ancestors of' ,
            'ancestor-or-self': ' [self_name] and ancestors of', ## fix
            'attribute': 'attributes of', ## fix
            '@': 'attributes of', ## fix
            'child': 'children of',
            'descendant': 'descendants of',
            'descendant-or-self': '[self_name] and descendants of', ## fix
            'following': 'nodes after',
            'following-sibling': 'siblings that appear before',
            'namespace': 'nodes in the namespace of',
            'parent': 'the parent of',
            'preceding': 'nodes before',
            'preceding-sibling': 'siblings that appear before',
            'self': '[self_name]', ## fix
        }
        return AXIS_NAMES[axis_specifier.children[0].getText()]

def explain_node_test(node_test):

    noun = nlg_factory.createNounPhrase('node')

    # simple NodeType case
    # print(type(node_test.children[0]))
    if isinstance(node_test.children[0], TerminalNode):
        node_type = node_test.children[0].getText()
        print 'I found a simple nodetype!: ' + node_type
        if node_type == 'node':
            node_type = 'all '
        type_adjective = nlg_factory.createAdjectivePhrase(node_type)
        noun.addPreModifier(type_adjective)
        noun.setFeature(Feature.NUMBER, NumberAgreement.PLURAL)
        return noun

    else:
        def _lookup_type_name(type_):
            TYPE_NAMES = {
                'p': 'paragraph',
                'div': 'container',
                'strong': 'bolded text segment',
                'a': 'link',
                'img': 'image',
                'pre': 'preformatted text block',
                'table': 'table',
                'tr': 'row',
                'td': 'cell',
            }
            return TYPE_NAMES.get(type_, type_)

        # Look up a 'fancier' name for this node, if we can
        type_ = node_test.children[0].getText()
        type_name = _lookup_type_name(type_)

        # Only reset the type of noun ('node') to the type name
        # if we were able to find a more specific name during lookup.
        if type_name != type_:
            noun.setNoun(type_name)
        else:
            type_adjective = nlg_factory.createAdjectivePhrase('\'' + _lookup_type_name(type_) + '\'')
            noun.addPreModifier(type_adjective)

        # Make sure to pluralize the count
        noun.setFeature(Feature.NUMBER, NumberAgreement.PLURAL)

        return noun

def explain_predicate(predicate):

    clause = nlg_factory.createClause()
    explain_expr(predicate.getChild(1))
    pass

def explain_expr(expr):

    expr = get_interesting_nodes(expr)

    if isinstance(expr, xpathParser.OrExprContext):
        modifier = explain_orExpr(expr)
    elif isinstance(expr, xpathParser.AndExprContext):
        modifier = explain_andExpr(expr)
    elif isinstance(expr, xpathParser.EqualityExprContext):
        modifier = explain_equalityExpr(expr)
    elif isinstance(expr, xpathParser.RelationalExprContext):
        modifier = explain_relationalExpr(expr)
    elif isinstance(expr, xpathParser.AdditiveExprContext):
        modifier = explain_additiveExpr(expr)
    elif isinstance(expr, xpathParser.MultiplicativeExprContext):
        modifier = explain_multiplicativeExpr(expr)
    return clause

def explain_orExpr(or_expr):
    coordinated_phrase = nlg_factory.createCoordinatedPhrase()
    coordinated_phrase.setFeature(Feature.CONJUNCTION, "or")
    coordinated_phrase.addCoordinate(explain_expr(getChild(0)))
    coordinated_phrase.addCoordinate(explain_expr(getChild(2)))
    return coordinated_phrase

def explain_andExpr(and_expr):
    coordinated_phrase = nlg_factory.createCoordinatedPhrase()
    coordinated_phrase.setFeature(Feature.CONJUNCTION, "or")
    coordinated_phrase.addCoordinate(explain_expr(getChild(0)))
    coordinated_phrase.addCoordinate(explain_expr(getChild(2)))
    return coordinated_phrase

def explain_equalityExpr(equality_expr):
    coordinated_phrase = nlg_factory.createCoordinatedPhrase()
    if equality_expr.getChild(1).getText() == '=':
        coordinated_phrase.setFeature(Feature.CONJUNCTION, "equals")
    else:
        coordinated_phrase.setFeature(Feature.CONJUNCTION, "does not equal")
    coordinated_phrase.addCoordinate(explain_expr(getChild(0)))
    coordinated_phrase.addCoordinate(explain_expr(getChild(2)))
    return coordinated_phrase

def explain_relationalExpr(relational_expr):
    coordinated_phrase = nlg_factory.createCoordinatedPhrase()
    if equality_expr.getChild(1).symbol.type == xpathLexer.LESS:
        coordinated_phrase.setFeature(Feature.CONJUNCTION, "less than")
    elif equality_expr.getChild(1).symbol.type == xpathLexer.MORE:
        coordinated_phrase.setFeature(Feature.CONJUNCTION, "greater than")
    elif equality_expr.getChild(1).symbol.type == xpathLexer.LE:
        coordinated_phrase.setFeature(Feature.CONJUNCTION, "less than or equal to")
    elif equality_expr.getChild(1).symbol.type == xpathLexer.GE:
        coordinated_phrase.setFeature(Feature.CONJUNCTION, "greater than or equal to")
    coordinated_phrase.addCoordinate(explain_expr(getChild(0)))
    coordinated_phrase.addCoordinate(explain_expr(getChild(2)))
    return coordinated_phrase

def explain_additiveExpr(additive_expr):
    pass

def explain_multiplicative_expr(multiplicative_expr):
    pass

def explain_unaryExprNoRoot():
    pass

def explain_xpath(xpath):

    phrase = None

    for index, child in enumerate(xpath.getChildren()):

        # If this is a simple xpath sequence, explain what is choosing.
        # Add prepositions that describe how the combinator relates this sequence
        # to the last visited sequence.
        if isinstance(child, xpathParser.Simple_selector_sequenceContext):
            focus = (index == len(xpath.children) - 1)  # it's in focus if it's the last one.
            simple_selector_sequence_phrase =\
                explain_simple_selector_sequence(child, focus)
            if phrase is not None:
                simple_selector_sequence_phrase.addComplement(phrase)
            phrase = simple_selector_sequence_phrase

        # If this is a combinator, form a preposition that will link the next
        # encountered sequence to the last one by describing the relationship
        # between the two sequences.
        elif isinstance(child, xpathParser.CombinatorContext):

            # Get the name of the symbol that defines this combinator
            combinator_symbol = child.children[0].symbol.type

            # A space is just selecting one sequence "from" another
            if combinator_symbol == xpathLexer.SPACE:
                preposition = nlg_factory.createPrepositionPhrase('from')
                preposition.addComplement(phrase)
                phrase = preposition

            # A greater-than sign tells us that a later sequence chooses
            # "children of" a later sequence.
            elif combinator_symbol == xpathLexer.GREATER:

                complement = nlg_factory.createClause()
                complement.setFeature(Feature.NUMBER, NumberAgreement.PLURAL)

                verb = nlg_factory.createVerbPhrase('be')
                complement.setVerb(verb)

                object_ = nlg_factory.createNounPhrase('child')
                object_.setFeature(Feature.NUMBER, NumberAgreement.PLURAL)
                complement.setObject(object_)

                # Here's where we connect this sequence to the past one,
                # through and 'of' preposition.
                preposition = nlg_factory.createPrepositionPhrase('of')
                preposition.addComplement(phrase)
                object_.addComplement(preposition)
                phrase = complement

            # A tilde sign tells us that a later sequence chooses elements that
            # are siblings of and eventually appear after those specified
            # by an earlier sequence.
            elif combinator_symbol == xpathLexer.TILDE:

                complement = nlg_factory.createCoordinatedPhrase()
                complement.setFeature(Feature.NUMBER, NumberAgreement.PLURAL)

                siblings_clause = nlg_factory.createClause()
                verb = nlg_factory.createVerbPhrase('be')
                siblings_clause.setVerb(verb)
                object_ = nlg_factory.createNounPhrase('sibling')
                object_.setFeature(Feature.NUMBER, NumberAgreement.PLURAL)
                siblings_clause.setObject(object_)
                preposition = nlg_factory.createPrepositionPhrase('of')
                object_.addComplement(preposition)
                complement.addCoordinate(siblings_clause)

                appearance_clause = nlg_factory.createClause()
                verb = nlg_factory.createVerbPhrase('appear')
                verb.addPreModifier('eventually')
                appearance_clause.setVerb(verb)
                preposition = nlg_factory.createPrepositionPhrase('after')
                preposition.addComplement(phrase)
                verb.addComplement(preposition)
                complement.addCoordinate(appearance_clause)

                phrase = complement

            # The plus symbol is used when the elements specified by a second sequence
            # are siblings of and appear right after the elements specified by a first sequence.
            # The construction here is practically the same as that for the ~ symbol,
            # as it uses almost the same phrasing to describe the relationship.
            elif combinator_symbol == xpathLexer.PLUS:

                "are siblings of and appear right after elements"
                complement = nlg_factory.createCoordinatedPhrase()
                complement.setFeature(Feature.NUMBER, NumberAgreement.PLURAL)

                siblings_clause = nlg_factory.createClause()
                verb = nlg_factory.createVerbPhrase('be')
                siblings_clause.setVerb(verb)
                object_ = nlg_factory.createNounPhrase('sibling')
                object_.setFeature(Feature.NUMBER, NumberAgreement.PLURAL)
                siblings_clause.setObject(object_)
                preposition = nlg_factory.createPrepositionPhrase('of')
                object_.addComplement(preposition)
                complement.addCoordinate(siblings_clause)

                appearance_clause = nlg_factory.createClause()
                verb = nlg_factory.createVerbPhrase('appear')
                appearance_clause.setVerb(verb)
                preposition = nlg_factory.createPrepositionPhrase('after')
                preposition.addPreModifier('right')
                preposition.addComplement(phrase)
                verb.addComplement(preposition)
                complement.addCoordinate(appearance_clause)

                phrase = complement

    return phrase


def explain_main(main):

    return explain_expr(main.getChild(0))


class xpathExplainer(xpathListener, ErrorListener):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

    def exitMain(self, context):
        self.result = explain_main(context)
