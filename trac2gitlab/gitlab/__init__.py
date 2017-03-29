# -*- coding: utf-8 -*-

import re

from trac2gitlab import trac2down

TICKET_PRIORITY_TO_ISSUE_LABEL = {
    'high': 'prio:high',
    'medium': None,
    'low': 'prio:low',
}

TICKET_RESOLUTION_TO_ISSUE_LABEL = {
    'high': 'prio:high',
    'medium': None,
    'low': 'prio:low',
}

TICKET_STATE_TO_ISSUE_STATE = {
    'new': 'opened',
    'assigned': 'opened',
    'reopened': 'reopened',
    'closed': 'closed',
}

################################################################################
# Wiki format normalization
################################################################################

_pattern_changeset = r'(?sm)In \[changeset:"([^"/]+?)(?:/[^"]+)?"\]:\n\{\{\{(\n#![^\n]+)?\n(.*?)\n\}\}\}'
_matcher_changeset = re.compile(_pattern_changeset)

_pattern_changeset2 = r'\[changeset:([a-zA-Z0-9]+)\]'
_matcher_changeset2 = re.compile(_pattern_changeset2)


def _format_changeset_comment(m):
    return 'In changeset ' + m.group(1) + ':\n> ' + m.group(3).replace('\n', '\n> ')


def _wikifix(text):
    text = _matcher_changeset.sub(_format_changeset_comment, text)
    text = _matcher_changeset2.sub(r'\1', text)
    return text


def _wikiconvert(text, basepath, multiline=True):
    return trac2down.convert(_wikifix(text), basepath, multiline)

################################################################################
# Trac ticket metadata conversion
################################################################################

def ticket_priority(ticket, priority_to_label=TICKET_PRIORITY_TO_ISSUE_LABEL):
    priority = ticket['attributes']['priority']
    if priority in priority_to_label:
        return set([priority_to_label[priority]])
    else:
        return set()


def ticket_resolution(ticket, resolution_to_label=TICKET_RESOLUTION_TO_ISSUE_LABEL):
    resolution = ticket['attributes']['resolution']
    if resolution in resolution_to_label:
        return set([resolution_to_label[resolution]])
    else:
        return set()


def ticket_version(ticket):
    version = ticket['attributes']['version']
    if version:
        return set(['ver:{}'.format(version)])
    else:
        return set()


def ticket_components(ticket):
    components = ticket['attributes']['component'].split(',')
    return set('comp:{}'.format(comp.strip()) for comp in components)


def ticket_type(ticket):
    type = ticket['attributes']['type']
    return set(['type:{}'.format(type.strip())])


def ticket_state(ticket, issue, state_to_state=TICKET_STATE_TO_ISSUE_STATE):
    state = ticket['attributes']['state']
    if state in state_to_state:
        return state_to_state[state], None
    else:
        return None, set(['state:{}'.format(state)])

################################################################################
# Trac dict -> GitLab dict conversion
# The GitLab dict is a GitLab model-friendly representation, the GitLab dict
# can be unrolled as kwargs to the corresponding database model entity
# e.g.:
#  dbmodel.Milestone(**milestone_kwargs(trac_milestone))
################################################################################

def ticket_kwargs(ticket):
    priority_labels = ticket_priority(ticket)
    resolution_labels = ticket_resolution(ticket)
    version_labels = ticket_version(ticket)
    component_labels = ticket_components(ticket)
    type_labels = ticket_type(ticket)
    state, state_labels = ticket_state(ticket)
    
    labels = priority_labels | resolution_labels | version_labels | \
             component_labels | type_labels | state_labels

    return {
        'title': ticket['attributes']['summary'],
        'description': _wikiconvert(ticket['attributes']['description'], '/issues/', multiline=False),
        'state': state,
        'labels': ','.join(labels),
        'assignee': ticket['attributes']['owner'],
        'created_at': ticket['attributes']['time'],
        'updated_at': ticket['attributes']['changetime'],
        # 'project': None,
        'author': ticket['attributes']['reporter'],
        # 'iid': None,
        'milestone': ticket['attributes']['milestone'],
    }


def milestone_kwargs(milestone):
    return {
        'description': _wikiconvert(milestone['description'], '/milestones/', multiline=False),
        'title': milestone['name'],
        'state': 'closed' if milestone['completed'] else 'active',
        'due_date': milestone['due'],
    }
