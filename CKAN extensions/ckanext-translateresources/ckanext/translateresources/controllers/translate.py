import ckan.lib.base as base
import requests
import base64
import json
import urllib2
import time
from paste.fileapp import FileApp
from pylons import request, response
import logging


class TranslateController(base.BaseController):

    # Needed values into the methods of the code
    token = ''
    url_translate_file = 'https://iadaatpa.eu/api/translatefile'
    url_retrieve_file_trans = 'https://iadaatpa.eu/api/retrievefiletranslation'
    sleep_seconds = 30
    supplierId = ''

    def get_url_vals(self, url, pkg_url):
        """Obtains the target language and the extension of the file from the
        URL of the file.
        """
        lang = False
        extension = False
        filename = False
        url_array = url.split('/')
        pkg_url_array = pkg_url.split('/')
        if url_array:
            # The language obtained from the URL
            lang = url_array[3]
        if pkg_url_array:
            # The name of the file
            filename = pkg_url_array[len(pkg_url_array)-1]
            # The type of the file (extension)
            extension = filename.split('.')[1]
        return [lang, extension, filename]

    def generate_json(self, target_lang, extension, encodedFile, token):
        """Generates the JSON structure for the translate REST call."""
        new_json = {
            "token": str(token),
            "source": "es",
            "target": str(target_lang),
            "fileType": str(extension),
            "file": str(encodedFile),
            "supplierId": str(self.supplierId),
        }
        return new_json

    def translate_file(self, url, translate_json):
        """Sends a REST call to the translate file method, in order to start
        the translation of the current file.
        """
        data = translate_json
        data_json = json.dumps(data)
        headers = {'Content-type': 'application/json'}
        # Send the request with a POST call
        response = requests.post(url, data=data_json, headers=headers)
        # Obtain the response of the previous request
        response_content = json.loads(response.content)
        return response_content

    def obtain_translation(self, url, guid, token):
        """Sends a REST call to the retrieve file translation method, in order
        to obtain the base64 code of the new translated file.
        """
        new_json = {
            "token": str(token),
            "guid": str(guid)
        }
        data = new_json
        data_json = json.dumps(data)
        headers = {'Content-type': 'application/json'}
        success = False

        # While the file is not translated, send a request
        while not success:
            logging.info(
                'Checking if the resource is translated... ' + str(guid))
            response = requests.post(url, data=data_json, headers=headers)
            if response.status_code == 200:
                # The file is already translated
                response_content = json.loads(response.content)
                success = True
            elif response.status_code == 201:
                # Wait N seconds to try again
                logging.info('Sleeping and retrying...')
                time.sleep(self.sleep_seconds)
            else:
                logging.info('Unexpected response, avoiding the translation.')
                return False
        return response_content

    def generate_download_link(self, content, filename, extension):
        """Generate the header and the download link for the new translated
        file.
        This allows the user to download the new file directly without store
        the file into the database.
        """
        # Set the folder for the temporary file
        tmp_file_url = '/tmp/' + filename
        # Decode the content of the new translated file
        decoded_content = base64.b64decode(content)
        # Generate the new file in the tmp folder
        file = open(tmp_file_url, "wb")
        file.write(decoded_content)
        file.close()

        # Set the content of the header to return the download link
        headers = [
            ('Content-Disposition',
            'attachment; filename=\"' + filename + '\"'),
        ]
        if extension == 'csv':
            headers.append(('Content-Type', 'text/csv'))
        elif extension == 'json':
            headers.append(('Content-Type', 'application/json'))
        elif extension == 'xml':
            headers.append(('Content-Type', 'application/xml'))
        else:
            headers.append(('Content-Type', 'text/plain'))

        # Generate the response to download the new file into the web browser
        fapp = FileApp(tmp_file_url, headers=headers)
        return fapp(request.environ, self.start_response)

    def translate_resource(self, *args, **kw):
        """This method gets the resource from the webstore_url param and sends
        its content to be translated.
        After the translation, the new resource is offered to be downloaded.
        """
        route_args = kw['environ']['webob._parsed_query_vars'][0]
        url = route_args['url']
        pkg_url = route_args['pkg_url']
        # Obtain the needed vars, filtering the original URL
        url_vals = self.get_url_vals(url, pkg_url)
        if url_vals:
            target_lang = url_vals[0]
            extension = url_vals[1]
            filename = url_vals[2]
        encondedFile = False

        # TODO DELETEEEEEEE
        if '8080' in pkg_url:
            pkg_url = pkg_url.replace('8080', '5000')

        # Get the original resource
        req = requests.get(pkg_url)
        # Enconde the original resource in base64
        encodedFile = base64.b64encode(req.content)

        # Generate the JSON that will be sent to the translate file REST call
        translate_json = self.generate_json(
            target_lang, extension, encodedFile, self.token)

        # Send the encoded file to the iADAATPA platform and receive the guid
        translation_guid_json = self.translate_file(
            self.url_translate_file,
            translate_json
        )

        # Check if the file is already translated, asking with the guid
        translated_file_response = self.obtain_translation(
            self.url_retrieve_file_trans,
            translation_guid_json['data']['guid'],
            self.token
        )
        if translated_file_response:
            translated_file_base64 = translated_file_response['data']['file']
        else:
            return "The file couldn't be translated because of an error."

        # Generate the download link for the new translated file
        response = self.generate_download_link(
            translated_file_base64, filename, extension)

        logging.info('The translation of the file has finished.')
        return response
