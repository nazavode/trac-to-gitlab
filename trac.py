# -*- coding: utf-8 -*-

import ssl

from six.moves import xmlrpc_client as xmlrpc


def ticket_get_changelog(ticket_id, source):
    changelog = list(source.ticket.changeLog(ticket_id))
    # TODO attachments
    return changelog


def ticket_get_all(source):
    tickets = {
        id: ticket
        for id, created, updated, ticket in source.ticket.getAll()
    }


def milestone_get_all(source):
    return {
        milestone: source.ticket.milestone.get(milestone)
        for milestone in milestone_get_all_names(source)
    }


def milestone_get(milestone_name, source):
    return source.ticket.milestone.get(milestone_name)


def milestone_get_all_names(source):
    return list(source.ticket.milestone.getAll())


def wiki_get_all_pages(source):
    return {
        pagename: wiki_get_page(pagename, source)
        for pagename in wiki_get_all_page_names(source)
    }


def wiki_get_page(pagename, source):
    info = source.wiki.getPageInfo(pagename)
    page = source.wiki.getPage(pagename)
    attachments = {
        filename: source.wiki.getAttachment(filename).data
            for filename in source.wiki.listAttachments(pagename)
    }
    return {'info': info, 'page': page, 'attachments': attachments}


def wiki_get_all_page_names(source):
    return list(source.wiki.getAllPages())


def project_get(source):
    return {
        'wiki': wiki_get_all_pages(source),
        'tickets': ticket_get_all(source),
        'milestones': milestone_get_all(source),
    }


def connect(url, encoding='UTF-8', use_datetime=True, ssl_verify=True):
    context = None if ssl_verify else ssl._create_unverified_context()
    return xmlrpc.MultiCall(
        xmlrpc.ServerProxy(url, encoding=encoding, use_datetime=use_datetime, context=context)
    )
