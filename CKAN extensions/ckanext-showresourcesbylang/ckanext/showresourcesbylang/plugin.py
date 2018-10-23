import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from dateutil.relativedelta import relativedelta
from dateutil import parser
import datetime

NOT_SPANISH_LANGS = [
    'en', 'ca', 'fr', 'de', 'ru'
]

FILTER_DATASETS_FROM_DATE = datetime.datetime.now() - relativedelta(years=1)

class ShowResourcesByLangPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    # Declare that this plugin will implement ITemplateHelpers.
    plugins.implements(plugins.ITemplateHelpers)

    def update_config(self, config):
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'showresourcesbylang')

    def get_show_resource(*args, **kw):
        show = False
        if kw.get('name') and kw.get('url'):
            url = kw.get('url')
            name = kw.get('name')
            creation_date = parser.parse(kw.get('creation_date'))

            # If the resource has been created before the filter date, it is shown
            if creation_date < FILTER_DATASETS_FROM_DATE:
                show = True
            # Check if the resource has to be shown depending of the language
            else:
                url_array = url.split('/')
                if url_array:
                    # The language obtained from the URL
                    url_language = url_array[3]
                    # Check if the language (not Spanish) is the same than the URL one
                    if '-' in name:
                        filename_array = name.split('-')
                        if filename_array:
                            lang_with_ext = filename_array[len(filename_array) - 1]
                            if '.' in lang_with_ext:
                                # The language obtained from the file name
                                file_language = lang_with_ext.split('.')[0]
                                # Check if the languages coincide
                                if url_language == file_language:
                                    show = True
                                else:
                                    if url_language == 'es' and file_language not in NOT_SPANISH_LANGS:
                                        show = True
                        else:
                            if url_language == 'es':
                                show = True
                    else:
                        if url_language == 'es':
                            show = True
        return show

    def get_helpers(self):
        '''Register the get_show_resource() function above as a template
        helper function.

        '''
        # Template helper function names should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.
        return {
            'showresourcesbylang_get_show_resource': self.get_show_resource,
        }
