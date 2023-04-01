from telegram.ext import ApplicationBuilder
import boto3
import os
import urllib.parse
from aws_lambda_powertools.utilities import parameters
import requests
import asyncio

DestinationBucketName = os.environ['DestinationBucketName']

s3 = boto3.client('s3')
ssm_provider = parameters.SSMProvider()

stage = os.environ['stage']
TelegramBotToken = ssm_provider.get("/telegramtasweerbot/telegram/"+stage+"/bot_token", decrypt=True)

application = ApplicationBuilder().token(TelegramBotToken).build()

async def image(image_filename):
    
    print ("Downloading blurred image ")
    s3.download_file(DestinationBucketName, image_filename, '/tmp/image-blur.jpg')
    
    data = image_filename[:-4].split('-')
    chat_id = '-' + data[1]
    chat_user_first_name = data[2]
    if (data[3] == "None"): # some users dont have a Last Name set in Telegram, so it displays as None. In which case, instead of showing None, just blank it out
        chat_user_last_name = ""
    else:
        chat_user_last_name = data[3]

    print ("reposting blurred image to chat_id: " + chat_id)
    await application.bot.send_photo(chat_id, open("/tmp/image-blur.jpg", 'rb'), 'Message from ' + chat_user_first_name + ' ' + chat_user_last_name)


def lambda_handler(event, context):
    return asyncio.get_event_loop().run_until_complete(main(event, context))

async def main(event, context):
    print("Start processing S3 Event")
    bucket = event['Records'][0]['s3']['bucket']['name']
    image_filename = urllib.parse.unquote_plus(urllib.parse.unquote(event['Records'][0]['s3']['object']['key']))  #S3 event contains document name in URL encoding, needs to be decoded - https://github.com/aws-samples/amazon-textract-enhancer/issues/2
    print ("Image: " + image_filename)
    image(image_filename)