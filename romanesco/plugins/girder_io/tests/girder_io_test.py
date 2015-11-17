import json
import httmock
import os
import romanesco
import shutil
import unittest


class TestGirderIo(unittest.TestCase):

    def setUp(self):
        self.task = {
            'inputs': [{'name': 'input', 'type': 'string', 'format': 'text'}],
            'outputs': [{'name': 'out', 'type': 'string', 'format': 'text'}],
            'script': 'out = input',
            'mode': 'python'
        }

    def test_girder_io(self):
        file_uploaded = []
        upload_initialized = []

        @httmock.all_requests
        def girder_mock(url, request):
            api_root = '/girder/api/v1'
            self.assertEqual(request.headers['Girder-Token'], 'foo')
            self.assertEqual(url.scheme, 'http')
            self.assertTrue(url.path.startswith(api_root), url.path)
            self.assertEqual(url.netloc, 'localhost:8080')

            if url.path == api_root + '/item/item_id/files':
                return json.dumps([{
                    'name': 'test.txt',
                    '_id': 'file_id',
                    'size': 13
                }])
            elif url.path == api_root + '/item/new_item_id/files':
                return '[]'
            elif url.path == api_root + '/file/file_id/download':
                return 'file_contents'
            elif url.path == api_root + '/file' and request.method == 'POST':
                upload_initialized.append(1)
                return json.dumps({
                    '_id': 'upload_id'
                })
            elif (url.path == api_root + '/file/chunk' and
                  request.method == 'POST'):
                file_uploaded.append(1)
                return json.dumps({
                    '_id': 'new_file_id',
                    'name': 'test.txt'
                })
            else:
                raise Exception('Unexpected %s request to %s.' % (
                    request.method, url.path))

        inputs = {
            'input': {
                'mode': 'girder',
                'host': 'localhost',
                'scheme': 'http',
                'port': 8080,
                'api_root': '/girder/api/v1',
                'resource_type': 'item',
                'id': 'item_id',
                'type': 'string',
                'format': 'text',
                'name': 'test.txt',
                'token': 'foo'
            }
        }

        with httmock.HTTMock(girder_mock):
            outputs = romanesco.run(
                self.task, inputs=inputs, outputs=None, cleanup=False)
            path = outputs['out']['data']
            self.assertTrue(os.path.isfile(path), path + ' does not exist')
            with open(path) as f:
                self.assertEqual(f.read(), 'file_contents')
            shutil.rmtree(os.path.dirname(path))  # clean tmp dir

            # Now test pushing to girder
            del inputs['input']['data']
            outputs = {
                'out': {
                    'mode': 'girder',
                    'host': 'localhost',
                    'scheme': 'http',
                    'port': 8080,
                    'api_root': '/girder/api/v1',
                    'parent_type': 'folder',
                    'parent_id': 'some_folder_id',
                    'format': 'text',
                    'type': 'string',
                    'token': 'foo'
                }
            }

            romanesco.run(self.task, inputs=inputs, outputs=outputs)
            self.assertEqual(file_uploaded, [1])
            self.assertEqual(upload_initialized, [1])

    def test_memory_targets(self):
        upload_initialized = []
        chunk_sent = []

        @httmock.all_requests
        def girder_mock(url, request):
            api_root = '/girder/api/v1'
            self.assertEqual(request.headers['Girder-Token'], 'foo')
            self.assertEqual(url.scheme, 'http')
            self.assertTrue(url.path.startswith(api_root), url.path)
            self.assertEqual(url.netloc, 'localhost:8080')

            if url.path == api_root + '/item/item_id/files':
                return json.dumps([{
                    'name': 'test.txt',
                    '_id': 'file_id',
                    'size': 13
                }])
            elif url.path == api_root + '/item/new_item_id/files':
                return '[]'
            elif url.path == api_root + '/file/file_id/download':
                return 'file_contents'
            elif url.path == api_root + '/file' and request.method == 'POST':
                upload_initialized.append(1)
                return json.dumps({
                    '_id': 'upload_id'
                })
            elif (url.path == api_root + '/file/chunk' and
                  request.method == 'POST'):
                self.assertTrue('file_contents' in request.body)
                chunk_sent.append(1)
                return json.dumps({
                    '_id': 'new_file_id',
                    'name': 'test.txt'
                })
            else:
                raise Exception('Unexpected %s request to %s.' % (
                    request.method, url.path))

        inputs = {
            'input': {
                'mode': 'girder',
                'host': 'localhost',
                'scheme': 'http',
                'port': 8080,
                'api_root': '/girder/api/v1',
                'resource_type': 'item',
                'id': 'item_id',
                'type': 'string',
                'format': 'text',
                'name': 'test.txt',
                'token': 'foo'
            }
        }

        outputs = {
            'out': {
                'mode': 'girder',
                'host': 'localhost',
                'scheme': 'http',
                'port': 8080,
                'api_root': '/girder/api/v1',
                'parent_type': 'item',
                'parent_id': 'item_id',
                'format': 'text',
                'type': 'string',
                'token': 'foo',
                'name': 'hello_world.txt'
            }
        }

        task = {
            'inputs': [{
                'name': 'input',
                'type': 'string',
                'format': 'text',
                'target': 'memory'
            }],
            'outputs': [{
                'name': 'out',
                'type': 'string',
                'format': 'text',
                'target': 'memory'
            }],
            'script': 'out = input',
            'mode': 'python'
        }

        with httmock.HTTMock(girder_mock):
            outputs = romanesco.run(task, inputs=inputs, outputs=outputs)
            self.assertEqual(chunk_sent, [1])
            self.assertEqual(upload_initialized, [1])


if __name__ == '__main__':
    unittest.main()
