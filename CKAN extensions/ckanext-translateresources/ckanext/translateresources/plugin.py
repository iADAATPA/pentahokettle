import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from dateutil.relativedelta import relativedelta
from ckan.config.routing import SubMapper


class TranslateResourcesPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'translateresources')

    def before_map(self, map):
        ctlr = 'ckanext.translateresources.controllers.translate:TranslateController'
        map.connect('translate_resource', '/translate_resource',
                    controller=ctlr, action='translate_resource')
        return map
