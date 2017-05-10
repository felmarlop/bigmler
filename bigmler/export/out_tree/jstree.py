# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# Copyright 2017 BigML
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Tree level output for node/js

This module defines functions that generate node/js code to make local
predictions
"""

from bigml.tree_utils import (
    filter_nodes, missing_branch, java_string, none_value,
    INDENT, PYTHON_OPERATOR, MAX_ARGS_LENGTH)
from bigml.util import split
from bigml.tree import Tree


from bigmler.export.out_tree.pythontree import value_to_print


class JsTree(Tree):

    def missing_check_code(self, field, depth, prefix, cmv, metric):
        """Builds the code to predict when the field is missing

        """
        code = u"%sif (%s%s == null) {\n" % \
            (INDENT * depth,
             prefix,
             self.fields[field]['camelCase'])
        value = value_to_print(self.output,
                               self.fields[self.objective_id]['optype'])
        code += u"%sreturn {prediction: %s," \
            u" %s: %s}\n" % \
            (INDENT * (depth + 1), value, metric, self.confidence)
        cmv.append(self.fields[field]['camelCase'])
        return code

    def missing_prefix_code(self, field, prefix, cmv):
        """Part of the condition that checks for missings when missing_splits
        has been used

        """

        operator = u"==" if child.predicate.missing else u"!="
        connection = u"||" if child.predicate.missing else u"&&"
        if not child.predicate.missing:
            cmv.append(self.fields[field]['camelCase'])
        return u"%s%s %s null %s " % (prefix,
                                      self.fields[field]['camelCase'],
                                      operator,
                                      connection)

    def split_condition_code(self, field, depth, prefix, alternative,
                             pre_condition, term_analysis_fields,
                             item_analysis_fields):
        """Condition code for the split

        """
        """
        type_key = self.fields[field]['optype']
        if (type_key in ['numeric', 'text', 'items'] or
                child.predicate.value is None):
            value = "%s" % child.predicate.value
            operator = (" " +
                        PYTHON_OPERATOR[child.predicate.operator] +
                        " ")
        else:
            value = "\"%s\"" % java_string(child.predicate.value)
            operator = PYTHON_OPERATOR[child.predicate.operator]
        """
        optype = self.fields[field]['optype']
        operator = PYTHON_OPERATOR[self.predicate.operator]
        value = value_to_print(self.predicate.value, optype)

        if optype in ['text', 'items']:
            if optype == 'text':
                term_analysis_fields.append((field,
                                             self.predicate.term))
                matching_function = "term_matches"
            else:
                item_analysis_fields.append((field,
                                             self.predicate.term))
                matching_function = "item_matches"

            return u"%sif (%stermMatches(%s%s, %s, %s)%s%s) {\n" % \
                (INDENT * depth + alternative, pre_condition,
                 prefix,
                 self.fields[field]['camelCase'],
                 value_to_print(self.fields[field]['camelCase'], 'text'),
                 value_to_print(self.predicate.term, 'text'),
                 operator,
                 value)
        if self.predicate.value is None:
            cmv.append(self.fields[field]['camelCase'])
            value = 'null'
        return u"%sif (%s%s%s %s %s) {\n" % \
            (INDENT * depth + alternative, pre_condition,
             prefix,
             self.fields[field]['camelCase'],
             operator,
             value)

    def plug_in_body(self, depth=1, cmv=None, ids_path=None, subtree=True):
        """Translate the model into a set of "if" javascript statements.

        `depth` controls the size of indentation. As soon as a value is missing
        to evaluate a predicate the output at that node is returned without
        further evaluation.

        """
        metric = "error" if self.regression else "confidence"
        if cmv is None:
            cmv = []
        body = u""
        term_analysis_fields = []
        item_analysis_fields = []
        prefix = u""
        field_obj = self.fields[self.objective_id]

        if len(self.fields) > MAX_ARGS_LENGTH:
            prefix = u"data."
        children = filter_nodes(self.children, ids=ids_path,
                                subtree=subtree)

        if children:
            alternative = u""

            # field used in the split
            field = split(children)

            has_missing_branch = missing_branch(children)
            # the missing is singled out as a special case only when there's
            # no missing branch in the children list
            if (not has_missing_branch and
                    not self.fields[field]['camelCase'] in cmv):
                body += self.missing_check_code(field, depth, prefix, cmv,
                                                metric)
                alternative = u"else "

            for child in children:

                field = child.predicate.field

                pre_condition = u""
                # code when missing_splits has been used
                if has_missing_branch and child.predicate.value is not None:
                    pre_condition = missing_prefix_code(child, field,
                                                        prefix, cmv)

                # complete split condition code
                body += child.split_condition_code( \
                    field, depth, prefix, alternative, pre_condition,
                    term_analysis_fields, item_analysis_fields)

                # value to be determined in next node
                next_level = child.plug_in_body(depth + 1, cmv=cmv[:],
                                                ids_path=ids_path,
                                                subtree=subtree)
                body += next_level[0]
                body += u"%s}\n" % (INDENT * depth)
                term_analysis_fields.extend(next_level[1])
                item_analysis_fields.extend(next_level[2])
                alternative = u"else "

        else:
            value = value_to_print(self.output,
                                   self.fields[self.objective_id]['optype'])
            body = u"%sreturn {prediction: %s, %s: %s};\n" % ( \
                INDENT * depth,
                value,
                metric,
                self.confidence)
        return body, term_analysis_fields, item_analysis_fields
