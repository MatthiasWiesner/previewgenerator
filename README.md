# Preview Generator Service

_An implementaion of the schul-cloud preview generator service._

The preview generator service creates preview images from downloadable files by using the [previewgenerator](https://github.com/algoo/preview-generator) library.

## Usage
The preview generator service provides an http(s) endpoint to process incoming requests:
```
POST /filepreview
{
    "download_url": "http://example.com/static/powerpoint1.ppt",
    "signed_s3_url": "https://example.com/powerpoint1.png?options...",
    "callback_url": "http://example.com/callback/powerpoint1.ppt",
    "options": {
        "width": 200
    }
}
```
The payload has to be valid JSON, the URL parts are mandatory and the options are optional.
The options can be:
- `width`, `height`: integer (pixel)
- `page`: integer (default 1)

Upon this request, the preview generator service creates an internal _generate-preview-job_ and returns `HTTP/1.1 202 Accepted`

## Generate Preview Job

The generate-preview-job consists of the tasks:

1. Download the file
    The files type is detected by the `content-type` header field
2. Create the preview image
3. `PUT` request to the `signed_s3_url`
    More information to [presigned url](https://docs.aws.amazon.com/AmazonS3/latest/dev/ShareObjectPreSignedURL.html) you can find on AWS.
4. Reports the success/error to the `callback_url`:
    - The success report to the `callback_url` is a request:
        ```
        PUT <callback_url>
        {'previewUrl': 'https://example.com/powerpoint1.png'}
        ```
        The `previewUrl` is taken from the `signed_s3_url` path part.

    - The error report to the `callback_url` is a request:
        ```
        PUT <callback_url>
        status: 500 Internal Server Error
        {'error': '<errormessage>'}
        ```

## Authentification
The preview generator service is protected by BasicAuth authentification strategy.
For this, an `AUTH_USERPW` has to be provided as environment variables at startup (f.e. `export AUTH_USERPW=schulcloud:veryStrongPassword`).

## File types
The supported file-types are: [document-formats](https://github.com/algoo/preview-generator#supported-file-formats)
There are more supported file-types (f.e. `.doc`), not all types are listed.
Furthermore, the preview generator service supports Apple iWorks files. Tese files are `zip` files, which contains prerendered `preview.jpg` pictures.

## Requirements
Since the preview generator service uses a job queue, a rabbitmq-server is necessary. For this, at least the `AMQP_URL` has to be provided as environment variables at startup. F.e. `export AMQP_URL: amqp://username:password@rabbitmq/previewgenerator`

## Install
To get the preview generator service running in a Vagrant VM:
1. Create the folder `./secrets`
2. Copy `./resources/rabbitmq-definitions.template.json` to `./secrets/rabbitmq-definitions.json`. 
    Adjust the amqp `<user>` and the `<sha256-hash-of-users-password>`. To get the `<sha256-hash-of-users-password>` you can follow the (missleading) documentation from rabbitmq: https://www.rabbitmq.com/passwords.html#computing-password-hash.
    Or you can use my tool. Change to ./resources and run `python encrypt_rabbitmq_password.py --password="<your-rabbit-password>"` (only python2).
3. The `config.yml` is already part of the service, but the amqp and webserver credentials must be overwritten. You can do this in the `resources/*.service`files. Add to the service section:
    `Environment=AMQP_URL=amqp://user:password@localhost/previewgenerator` and
    `Environment=AUTH_USERPW=user:password`
4. Run `vagrant up`

## Docker
A docker image is created based on the `node:10.5.0-stretch` Debian-Stretch image.

So that the preview-generator-service, preview-generator-webserver and the rabbitmq-server can be run and connected, `docker-compose` can be used. For more details see `docker-compose.yml`. In production mode, however, this file must be adjusted accordingly. The necessary environment variables are `AUTH_USERPW` and the `AMQP_URL`.
