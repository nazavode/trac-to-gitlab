# -*- coding: utf-8 -*-

import functools
import urlparse
import logging
from collections import defaultdict
from pprint import pformat
from six.moves.urllib import parse as urllib

import click
import click_spinner
import toml
import json

from . import trac


CONTEXT_SETTINGS = {
    'max_content_width': 120,
    'auto_envvar_prefix': 'TRAC2GITLAB',
    'default_map': {},
}

def _dumps(obj, format=None):
    if format == 'toml':
        return toml.dumps(obj)
    elif format == 'json':
        return json.dumps(obj, sort_keys=True, indent=2)
    elif format == 'python':
        return pformat(obj, indent=2)
    else:
        return str(obj)

def sanitize_url(url):
    """Strip out username and password if included in URL"""
    username = None
    password = None
    if '@' in url:
        parts = urllib.urlparse(url)
        username = parts.username
        password = parts.password
        hostname = parts.hostname
        if parts.port:
            hostname += ":%s" % parts.port
        url = urllib.urlunparse((parts.scheme, hostname, parts.path,
                          parts.params, parts.query, parts.fragment))
    return url

################################################################################
# common parameter groups
################################################################################

def trac_params(func):
    @click.option(
        '--trac-uri',
        metavar='<uri>',
        default='http://localhost/xmlrpc',
        show_default=True,
        help='uri of the Trac instance XMLRpc endpoint',
    )
    @click.option(
        '--ssl-verify / --no-ssl-verify',
        default=True,
        show_default=True,
        help='Enable/disable SSL certificate verification'
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def gitlab_params(func):
    @click.option(
        '--gitlab-db-user',
        metavar='<str>',
        default='gitlab',
        show_default=True,
        help='GitLab database username',
    )
    @click.option(
        '--gitlab-db-password',
        metavar='<str>',
        help='GitLab database password',
    )
    @click.option(
        '--gitlab-db-name',
        metavar='<str>',
        default='gitlabhq_production',
        show_default=True,
        help='GitLab database name',
    )
    @click.option(
        '--gitlab-db-path',
        metavar='<path>',
        type=click.Path(),
        default='/var/opt/gitlab/postgresql/',
        show_default=True,
        help='GitLab database path',
    )
    @click.option(
        '--gitlab-db-uploads',
        metavar='<path>',
        type=click.Path(),
        default='/var/opt/gitlab/gitlab-rails/uploads',
        show_default=True,
        help='GitLab uploads storage directory path',
    )
    @click.option(
        '--gitlab-version',
        metavar='<str>',
        default='9.0.0',
        show_default=True,
        help='GitLab target version',
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

################################################################################
# main command group
################################################################################

@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    '--config',
    metavar='<path>',
    type=click.Path(exists=True, readable=True),
    help='Configuration file to be read for options (in toml format). '
         'Values in this file will be overridden by command line/env var values'
)
@click.option(
    '-v', '--verbose',
    count=True,
    help='Run in verbose mode'
)
@click.version_option('0.0.1')
@click.pass_context
def cli(ctx, config, verbose):
    """Toolbox for Trac to GitLab migrations."""
    # Read config file and update context_map
    if config:
        conf = toml.load(config)
        ctx.default_map.update(
            {k: conf for k in ['users', 'migrate', 'model', 'export']})
    # Convert verbosity to logging levels
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG
    else:  # < 1
        level = logging.ERROR
    logging.basicConfig(level=level)
    # Pass configuration to subcommands
    ctx.obj['verbose'] = verbose

################################################################################
# subcommands
################################################################################

@cli.command()
@trac_params
@click.pass_context
def users(ctx, trac_uri, ssl_verify):
    '''collect users from a Trac instance'''
    click.echo('Collecting Trac users from {}'.format(sanitize_url(trac_uri)))
    with click_spinner.spinner():
        source = trac.connect(trac_uri, encoding='UTF-8', use_datetime=True,
                                ssl_verify=ssl_verify)
        authors = trac.authors_get(source)
    click.echo('Trac users found: ')
    click.echo(pformat(authors, indent=2))


@cli.command()
@trac_params
@click.option(
    '--format',
    type=click.Choice(['json', 'python', 'pickle']),
    default='json',
    show_default=True,
    help='export format',
)
@click.pass_context
def export(ctx, trac_uri, ssl_verify, format):
    '''export a complete Trac instance'''
    click.echo('Crawling and exporting Trac instance from {}'.format(sanitize_url(trac_uri)))
    with click_spinner.spinner():
        source = trac.connect(trac_uri, encoding='UTF-8', use_datetime=True,
                                ssl_verify=ssl_verify)
        project = trac.project_get(source, collect_authors=True)
        click.echo(str(project))



@cli.command()
@trac_params
@gitlab_params
@click.confirmation_option(prompt='Are you sure you want to proceed with the migration?')
@click.pass_context
def migrate(ctx, trac_uri, ssl_verify, gitlab_db_user, gitlab_db_password,
              gitlab_db_name, gitlab_db_path, gitlab_db_uploads, gitlab_version):
    '''migrate a Trac instance'''
    pass


@cli.command()
@gitlab_params
@click.pass_context
def model(ctx, gitlab_db_user, gitlab_db_password, gitlab_db_name, gitlab_db_path,
            gitlab_db_uploads, gitlab_version):
    'generate the database model of a GitLab instance'
    pass

################################################################################
# setuptools entrypoint
################################################################################

def main():
    cli(obj={})
