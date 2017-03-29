# -*- coding: utf-8 -*-

import importlib


def get_model(gitlab_version):
    module_name = 'model' + gitlab_version.strip('.').strip()
    module_path = 'trac2gitlab.gitlab.model.' + module_name
    model = importlib.import_module(module_path)
    return model
