# -*- coding: utf-8 -*-
import os
import json
import logging
import requests
import mimetypes
import magic
import tempfile
import shutil
import untangle
import zipfile
from copy import copy
from preview_generator.manager import PreviewManager


mimetypes.init()


class PreviewGeneratorHandler(object):
    def __init__(self, settings):
        self.config = settings.config

    def handle_error_message(self, payload, error_message):
        '''
        handles error messages
        '''
        logging.error('--- Start error message callback ---')
        logging.error('Error message was: {}'.format(error_message))
        callback_url = payload.get('callback_url', None)

        if not callback_url:
            logging.error('On sending error message: empty callback_url')
            return

        headers = {'status': '500 Internal Server Error'}
        result = {'error': str(error_message)}
        try:
            requests.put(callback_url, headers=headers, data=json.dumps(result))
        except Exception as e:
            logging.error('On sending error message: callback_url could not be called: {}, error message was: {}'.format(callback_url, e))

    def download_file(self, download_url):
        file_type = None
        downloaded_tmpfile = tempfile.NamedTemporaryFile(dir=self.config['app']['tmpdir'])

        res = requests.get(download_url, stream=True)
        if res.status_code >= 400:
            raise Exception('An error occurred while downloading the file: {0} {1}'.format(res.status_code, res.reason))

        if res.headers['content-type']:
            file_type = res.headers['content-type']

        with open(downloaded_tmpfile.name, 'wb') as f:
            for chunk in res.iter_content(chunk_size=1024): 
                if chunk:
                    f.write(chunk)

        # octed-stream type is too generic, check file type by magic
        if not file_type or file_type in ['binary/octet-stream', 'application/octet-stream']:
            file_type = magic.from_file(downloaded_tmpfile.name, mime=True)
        if not file_type:
            raise Exception('Filetype could not detemined')

        return downloaded_tmpfile, file_type

    def generate_preview(self, downloaded_tmpfile, file_type, options):
        manager = PreviewManager(self.config['app']['cache'], create_folder=True)

        generate_options = {'force': not self.config['app']['use_cache']}
        if 'width' in options:
            generate_options['width'] = options['width']
        if 'height' in options:
            generate_options['height'] = options['height']
        if 'page' in options:
            generate_options['page'] = options['page']

        logging.info(generate_options)

        return manager.get_jpeg_preview(downloaded_tmpfile.name, **generate_options)

    def upload_preview(self, signed_s3_url, preview_image_path):
        content_type = magic.from_file(preview_image_path, mime=True)

        try:
            with open(preview_image_path, 'rb') as fp:
                data = fp.read()
                res = requests.put(
                    signed_s3_url,
                    data=data,                         
                    headers={'content-type': content_type})

                if res.status_code > 200:
                    obj = untangle.parse(res.text)
                    raise Exception('Could not upload file: {0} ({1})'.format(obj.Error.Message.cdata, obj.Error.Code.cdata))
        finally:
            os.unlink(preview_image_path)

    def callback(self, callback_url, preview_image):
        requests.post(callback_url, 
            json=json.dumps({'preview_image': preview_image}), 
            headers={'content-type': 'application/json'})

    def parse_body(self, body):
        payload = json.loads(bytes(body).decode('utf-8'))
        assert 'download_url' in payload
        assert 'signed_s3_url' in payload
        assert 'callback_url' in payload
        return payload

    def handle_message(self, payload):
        '''
        handles generate preview image
        '''
        if not self.config['app']['use_cache'] and os.path.exists(self.config['app']['cache']):
            shutil.rmtree(self.config['app']['cache'])

        logging.info('------------- INCOMING MESSAGE -------------')
        logging.info(payload)

        download_url = payload['download_url']
        signed_s3_url = payload['signed_s3_url']
        callback_url = payload['callback_url']
        options = payload.get('options', {})

        download_file, file_type = self.download_file(download_url)

        if file_type == 'application/zip':
            # possibly an apple iWorks file
            zip = zipfile.ZipFile(download_file.name)
            if 'preview.jpg' in zip.namelist():
                download_file.close()
                download_file = tempfile.NamedTemporaryFile()
                with open(download_file.name, 'wb') as fp:
                    fp.write(zip.read('preview.jpg'))

        preview_image_path = self.generate_preview(download_file, file_type, options)

        self.upload_preview(signed_s3_url, preview_image_path)
        self.callback(callback_url, signed_s3_url.split('?')[0])
