# -*- coding: utf-8 -*-

import re

import trac2down

TICKET_ATTRIBUTES_TO_LABEL = [
    'type', 'priority', 'resolution',
]

################################################################################
# Wiki format normalization
################################################################################

_pattern_changeset = r'(?sm)In \[changeset:"([^"/]+?)(?:/[^"]+)?"\]:\n\{\{\{(\n#![^\n]+)?\n(.*?)\n\}\}\}'
_matcher_changeset = re.compile(pattern_changeset)

_pattern_changeset2 = r'\[changeset:([a-zA-Z0-9]+)\]'
_matcher_changeset2 = re.compile(pattern_changeset2)


def _format_changeset_comment(m):
    return 'In changeset ' + m.group(1) + ':\n> ' + m.group(3).replace('\n', '\n> ')


def _wikifix(text):
    text = _matcher_changeset.sub(_format_changeset_comment, text)
    text = _matcher_changeset2.sub(r'\1', text)
    return text


def _wikiconvert(text, basepath, multiline=True):
    return trac2down.convert(_wikifix(text), basepath, multiline)

################################################################################
# Trac dict -> GitLab dict conversion
# The GitLab dict is a GitLab model-friendly representation, the GitLab dict
# can be unrolled as kwargs to the corresponding database model entity
# e.g.:
#  dbmodel.Milestone(**milestone_kwargs(trac_milestone))
################################################################################

def ticket_labels(ticket, attributes_to_labels=TICKET_ATTRIBUTES_TO_LABEL):
    labels = set([
        str(ticket['attributes'][attr]).strip() for attr in attributes_to_labels
    ])
    return filter(bool, labels)


def ticket_kwargs(ticket):
    return {
        'title': ticket['attributes']['summary'],
        'description': _wikiconvert(ticket['attributes']['description'], '/issues/', multiline=False),
        'state': new_state,
        'labels': ",".join(ticket_labels(ticket))
    }


def milestone_kwargs(milestone):
    return {
        'description': _wikiconvert(milestone['description'], '/milestones/', multiline=False),
        'title': milestone['name'],
        'state': 'closed' if milestone['completed'] else 'active',
        'due_date': milestone['due'],
    }
