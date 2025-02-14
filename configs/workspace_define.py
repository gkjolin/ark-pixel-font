import os

project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

assets_dir = os.path.join(project_root_dir, 'assets')
unidata_dir = os.path.join(assets_dir, 'unidata')
design_dir = os.path.join(assets_dir, 'design')
templates_dir = os.path.join(assets_dir, 'templates')
images_dir = os.path.join(assets_dir, 'images')
www_static_dir = os.path.join(assets_dir, 'www-static')

outputs_dir = os.path.join(project_root_dir, 'outputs')

releases_dir = os.path.join(project_root_dir, 'releases')

docs_dir = os.path.join(project_root_dir, 'docs')

www_dir = os.path.join(project_root_dir, 'www')
