# -*- coding: utf-8 -*-
import os
import sys
import yaml
import click
import logging

from preview_generator_service.webserver import Webserver
from preview_generator_service.handler import PreviewGeneratorHandler
from preview_generator_service.consumer import PreviewGeneratorConsumer


class PreviewGeneratorSettings(object):
    def __init__(self, env, debug):
        self.env = os.environ.get('ENV', env)
        self.debug = debug
        if 'DEBUG' in os.environ:
            self.debug = os.environ['DEBUG'] == 'true'

        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.config = yaml.load(open(os.path.join(self.project_root, 'config.yml')).read())[self.env]

        if 'AMQP_URL' in os.environ:
            self.config['amqp']['url'] = os.environ['AMQP_URL']

        if 'AUTH_USERPW' in os.environ:
            self.config['webserver']['auth_userpw'] = os.environ['AUTH_USERPW']

        if 'USE_CACHE' in os.environ:
            self.config['app']['use_cache'] = os.environ['USE_CACHE'] == 'true'

        loglevel = logging.DEBUG if self.debug  else logging.ERROR
        logging.basicConfig(level=loglevel)


@click.group()
@click.option('--env', default='develop', help='environment, overwritten by ENV environment variable')
@click.option('--debug/--no-debug', default=True)
@click.pass_context
def cli(ctx, env, debug):
    """Preview Generator Service"""
    ctx.obj = PreviewGeneratorSettings(env, debug)


@cli.command()
@click.pass_context
def generate_preview(ctx):
    """Run Preview Generator Service - listen on message queue"""
    try:
        handler = PreviewGeneratorHandler(ctx.obj)
        consumer = PreviewGeneratorConsumer(ctx.obj, handler)
        consumer.run()
    except KeyboardInterrupt:
        consumer.stop()

@cli.command()
@click.pass_context
def webserver(ctx):
    """Run Preview Generator Service - webserver"""
    try:
        webserver = Webserver(ctx.obj)
        webserver.run()
    except KeyboardInterrupt:
        webserver.stop()

def main():
    cli(obj={})