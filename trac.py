# -*- coding: utf-8 -*-

import ssl
import logging

import six
from six.moves import xmlrpc_client as xmlrpc


LOG = logging.getLogger(__name__)


def _safe_encode(data, encoding='base64'):
    try:
        six.u(data.decode(encoding))
    except Exception as e:
        LOG.exception('error while decoding data from %s', encoding)
        return six.u(str(e))


def _authors_collect(wiki=None, tickets=None):
    wiki = wiki or []
    tickets = tickets or []
    return list(set(
        [page['attributes']['author'] for page in six.itervalues(wiki)] + \
        [ticket['attributes']['reporter'] for ticket in six.itervalues(tickets)] + \
        [ticket['attributes']['owner'] for ticket in six.itervalues(tickets)] + \
        [change['author'] for ticket in six.itervalues(tickets) for change in ticket['changelog']]
        # TODO crawl wiki attachments for additional authors
    ))


def ticket_get_changelog(ticket_id, source):
    LOG.debug('ticket_get_changelog of ticket %s', ticket_id)
    return [
        {
            'time': c[0],
            'author': c[1],
            'field': c[2],
            'oldvalue': c[3],
            'newvalue': c[4],
            'permanent': bool(c[5])
        }
        for c in source.ticket.changeLog(ticket_id)
    ]


def ticket_get_attachments(ticket_id, source):
    LOG.debug('ticket_get_attachments of ticket %s', ticket_id)
    return {
        meta[0]: {
            'attributes': {
                'filename': meta[0],
                'description': meta[1],
                'size': meta[2],
                'time': meta[3],
                'author': meta[4],
            },
            'data': _safe_encode(source.ticket.getAttachment(ticket_id, meta[0]).data)
        }
        for meta in source.ticket.listAttachments(ticket_id)
    }


def ticket_get_all(source):
    LOG.debug('ticket_get_all')
    return {
        tid: {
            'attributes': attrs,
            'changelog': ticket_get_changelog(tid, source),
            'attachments': ticket_get_attachments(tid, source),
        }
        for tid in source.ticket.query("max=0")
            for attrs in source.ticket.get(tid)
    }


def milestone_get_all(source):
    LOG.debug('milestone_get_all')
    return {
        milestone: source.ticket.milestone.get(milestone)
            for milestone in milestone_get_all_names(source)
    }


def milestone_get(milestone_name, source):
    LOG.debug('milestone_get of milestone %s', milestone_name)
    return source.ticket.milestone.get(milestone_name)


def milestone_get_all_names(source):
    LOG.debug('milestone_get_all_names')
    return list(source.ticket.milestone.getAll())


def wiki_get_all_pages(source, exclude_authors=None, exclude_trac_pages=True):
    LOG.debug('wiki_get_all_pages')
    exclude_authors = set(exclude_authors or [])
    if exclude_trac_pages:
        exclude_authors.add('trac')
    LOG.debug('wiki_get_all_pages is retrieving metadata for all pages')
    pages = {
        name: {'attributes': source.wiki.getPageInfo(name)}
            for name in source.wiki.getAllPages()
    }
    if exclude_authors:
        LOG.debug('wiki_get_all_pages is excluding authors: %s', exclude_authors)
        pages = {
            k: v for k, v in six.iteritems(pages)
                if v['attributes']['author'] not in exclude_authors
        }
    for pagename, pagedict in six.iteritems(pages):
        LOG.debug('wiki_get_all_pages is retrieving contents for wiki page %s', pagename)
        pagedict['page'] = source.wiki.getPage(pagename)
        LOG.debug('wiki_get_all_pages is retrieving attachments for wiki page %s', pagename)
        pagedict['attachments'] = {
            filename: _safe_encode(source.wiki.getAttachment(filename).data)
                for filename in source.wiki.listAttachments(pagename)
        }
    return pages


def project_get(source, collect_authors=True):
    LOG.debug('project_get')
    project = {
        'wiki': wiki_get_all_pages(source),
        'tickets': ticket_get_all(source),
        'milestones': milestone_get_all(source),
    }
    if collect_authors:
        LOG.debug('project_get is collecting authors from project')
        project['authors'] = _authors_collect(wiki=project['wiki'], tickets=project['tickets'])
    return project


def authors_get(source, from_wiki=True, from_tickets=True):
    wiki = wiki_get_all_pages(source) if from_wiki else None
    tickets = ticket_get_all(source) if from_tickets else None
    return _authors_collect(wiki=wiki, tickets=tickets)


def connect(url, encoding='UTF-8', use_datetime=True, ssl_verify=True):
    context = None if ssl_verify else ssl._create_unverified_context()
    return xmlrpc.ServerProxy(url, encoding=encoding, use_datetime=use_datetime, context=context)
