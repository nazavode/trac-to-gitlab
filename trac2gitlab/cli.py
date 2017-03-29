# -*- coding: utf-8 -*-

import click

CONTEXT_SETTINGS = {
    'max_content_width': 100,
    'auto_envvar_prefix': 'TRAC2GITLAB',
}

@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    '--trac-uri',
    metavar='<uri>',
    help='Trac instance uri.',
)
@click.option(
    '--gitlab-db-user',
    metavar='<str>',
    default='gitlab',
    show_default=True,
    help='GitLab database username.',
)
@click.option(
    '--gitlab-db-password',
    metavar='<str>',
    help='GitLab database password.',
)
@click.option(
    '--gitlab-db-name',
    metavar='<str>',
    default='gitlabhq_production',
    show_default=True,
    help='GitLab database name.',
)
@click.option(
    '--gitlab-db-path',
    metavar='<path>',
    type=click.Path(),
    default='/var/opt/gitlab/postgresql/',
    show_default=True,
    help='GitLab database path.',
)
@click.option(
    '--gitlab-db-uploads',
    metavar='<path>',
    type=click.Path(),
    default='/var/opt/gitlab/gitlab-rails/uploads',
    show_default=True,
    help='GitLab uploads storage directory path.',
)
@click.option(
    '--gitlab-version',
    metavar='<str>',
    default='9.0.0',
    show_default=True,
    help='GitLab target version.',
)
@click.option(
    '--config-file',
    metavar='<path>',
    type=click.Path(),
    help='Configuration file.'
)
@click.option(
    '--ssl-verify/--no-ssl-verify',
    default=True,
    help='Enable/disable SSL certificate verification.'
)
@click.option(
    '--verbose',
    is_flag=True,
    default=False,
    help='Run in verbose mode.'
)
@click.version_option('0.0.1')
@click.pass_context
def cli(ctx, **kwargs):
    """Toolbox for Trac to GitLab migrations."""
    ctx.obj.update(kwargs)
    
################################################################################
# commands
################################################################################

@cli.command(short_help='collect users from a Trac instance', context_settings=CONTEXT_SETTINGS)
@click.pass_context
def users(ctx):
    source = trac.connect(url, encoding='UTF-8', use_datetime=True, ssl_verify=True)
    authors = trac.authors_get(source, from_wiki=True, from_tickets=True)
    #
    click.echo(authors)

@cli.command(short_help='migrate a Trac instance', context_settings=CONTEXT_SETTINGS)
@click.pass_context
def migrate(ctx):
    print(ctx.obj)

@cli.command(short_help='generate the database model of a GitLab instance', context_settings=CONTEXT_SETTINGS)
@click.pass_context
def model(ctx):
    pass

################################################################################
# entry point
################################################################################

def main():
    cli(obj={})
