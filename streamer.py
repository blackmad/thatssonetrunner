#!/usr/bin/python
from __future__ import unicode_literals

from twython import TwythonStreamer
import twitter
import secrets
from twython import Twython
import maker

class MyStreamer(TwythonStreamer):
  def __init__(self, *args, **kwargs):
    super(MyStreamer, self).__init__(*args, **kwargs)
    self.twythonApi = Twython(
      app_key = secrets.consumer_key,
      app_secret = secrets.consumer_secret,
      oauth_token = secrets.access_token_key,
      oauth_token_secret = secrets.access_token_secret
    )

  def on_success(self, data):
    status = twitter.Status.NewFromJsonDict(data)
    self.replyToStatus(status)

  def replyToStatusId(self, statusId):
    data = self.twythonApi.lookup_status(id=statusId)[0]
    status = twitter.Status.NewFromJsonDict(data)
    self.replyToStatus(status)

  def replyToStatus(self, status):
    print status
    print status.in_reply_to_status_id
    if status.in_reply_to_status_id:
      data = self.twythonApi.lookup_status(id=status.in_reply_to_status_id)[0]
      print 'switching to new status'
      status = twitter.Status.NewFromJsonDict(data)
    image = maker.fillIdentityFromStatus(status)
    path = '/tmp/%s.png' % status.id
    image.save(path)
    #self.twythonApi.update_status_with_media(media=path, status='Here is your ID')

    image_ids = self.twythonApi.upload_media(media=open(path))
    print image_ids
    self.twythonApi.update_status(
      status = '@' + status.screen_name,
      media_ids = image_ids['media_id'], 
      in_reply_to_status_id = status.id
    )

    print status

  def on_error(self, status_code, data):
    print status_code

stream = MyStreamer(secrets.consumer_key, secrets.consumer_secret, secrets.access_token_key, secrets.access_token_secret)
stream.statuses.filter(track='#thatssonetrunner')
