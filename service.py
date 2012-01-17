# -*- coding: utf-8 -*-

# Debug
Debug = True

import xbmc, xbmcaddon, os, datetime, time

__addon__ = xbmcaddon.Addon(id='service.inadyn')
__info__ = __addon__.getAddonInfo
__plugin__ = __info__('name')
__version__ = __info__('version')
__icon__ = __info__('icon')
__path__ = __info__('path')
__cachedir__ = __info__('profile')
__language__ = __addon__.getLocalizedString
__settings__ = __addon__.getSetting

STARTUP = True
now = datetime.datetime.now()

def LOG(description):
    xbmc.log("[SERVICE] '%s v%s': DEBUG: %s" % (__plugin__, __version__, description.encode('ascii', 'ignore')), xbmc.LOGNOTICE)

def notification(title, message):
    xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % \
                                     (title.encode('utf-8', 'ignore'), message.encode('utf-8', 'ignore'), 6000, __icon__))
# thanks to @amet
def waiter(seconds):
  LOG("Delaying %s secs" % seconds)
  for i in range(1, seconds):
    time.sleep(1)
    # kill inadyn before xbmc
    if xbmc.abortRequested == True:
      if Debug: LOG('inadyn stoping!')
      os.system('killall inadyn')
      sys.exit()

# Get settings
INADYN_START = __settings__('INADYN_START')
INADYN_SYSTEM = __settings__('INADYN_SYSTEM')
INADYN_UPDATE = int(__settings__('INADYN_UPDATE')) * 60000
INADYN_HOST = __settings__('INADYN_HOST')
INADYN_USER = __settings__('INADYN_USER')
INADYN_PWD = __settings__('INADYN_PWD')
INADYN_DBG = __settings__('INADYN_DBG')

# create inadyn options from settings value.
INADYN_ARG = '--dyndns_system %s ' % INADYN_SYSTEM
INADYN_ARG += '--update_period %d ' % INADYN_UPDATE
INADYN_ARG += '--alias %s ' % INADYN_HOST
INADYN_ARG += '--username %s ' % INADYN_USER
INADYN_ARG += '--password %s ' % INADYN_PWD
INADYN_ARG += '--log_file %sinadyn.log ' % xbmc.translatePath(__cachedir__)
INADYN_ARG += '--verbose %s ' % INADYN_DBG
INADYN_ARG += '--background '

while (not xbmc.abortRequested):
  if STARTUP:
    # make False for run service 1 time
    STARTUP = False
    # check settings is allowing for service start with xbmc 
    if INADYN_START == 'true':
      os.system('chmod +x %s/bin/inadyn' % __path__)
      #if check_running(['inadyn']):
      if Debug: LOG('inadyn starting!')
      # Start service
      if Debug: LOG('%s/bin/inadyn %s' % (__path__, INADYN_ARG))
      os.system('%s/bin/inadyn %s' % (__path__, INADYN_ARG))
      notification('inadyn service', 'Successfully started!')
  if datetime.datetime.now().minute >= ((now.minute / 5) * 5) + 5 or (datetime.datetime.now().hour > now.hour) or (datetime.datetime.now().hour == 1 and now.hour == 12) or (datetime.datetime.now().hour == 0 and now.hour == 23) :
    wait = 240
  else:
    wait = 3
  waiter(wait)