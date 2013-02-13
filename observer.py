# coding=utf-8
__author__ = 'Qyon'
import allegro
import time
# Import smtplib for the actual sending function
import smtplib
# Import the email modules we'll need
from email.mime.text import MIMEText
import logging

logger = logging.getLogger(__name__)
print __name__

class Observer(object):
    def __init__(self, settings):
        self.settings = settings
        self.apiHelper = allegro.ApiHelper(self.settings)
        self.auctions = {}
        self.getAuctions()
        self.sleep_time_default = 60 * self.settings.CHECK_INTERVAL
        self.sleep_time_short = int(60 * self.settings.CHECK_INTERVAL / 10)
        self.sleep_time = self.sleep_time_default

    def getAuctions(self):
        self.old_auctions = self.auctions
        auctions = self.apiHelper.getAuctions()
        if auctions and len(auctions):
            self.auctions = auctions
            return True
        else:
            return False

    def getDelta(self):
        if not self.old_auctions:
            logger.debug('nie ma starych aukcji')
            return []
        #else:
        #    logger.debug('TEST: usuwamy 1 element z listy starych')
        #    del self.old_auctions[self.old_auctions.keys()[0]]

        delta = [self.auctions[i] for i in set(self.auctions.keys()) - set(self.old_auctions.keys())]
        return delta

    def watch(self):
        while True:
            delta = self.getDelta()
            if delta:
                self.handleDelta(delta)
            logger.info("Sleep for %d" % (self.sleep_time, ))
            time.sleep(self.sleep_time)
            if self.getAuctions():
                self.sleep_time = self.sleep_time_default
            else:
                self.sleep_time = self.sleep_time_short

    def handleDelta(self, delta):
        content = 'Nowe aukcje na allegro:<br><ul>'
        for i in delta:
            price = getattr(i, 's-it-price', None)
            if price is None or price <= 0.0:
                price =  getattr(i, 's-it-buy-now-price', 0.0)
            str_data = (
                getattr(i, 's-it-id'),
                getattr(i, 's-it-thumb-url'),
                getattr(i, 's-it-name'),
                price
                )
            content += '<li><a href="http://allegro.pl/show_item.php?item=%s"><img src="%s">%s (%2.2f PLN)</a></li>' % str_data

        content += '</ul>'
        msg = MIMEText(content, 'html', 'utf-8')
        msg['Subject'] = 'Na allegro jest %d nowych aukcji' % (len(delta),)
        msg['To'] = self.settings.EMAIL_TO

        try:
            s = smtplib.SMTP('localhost')
            s.sendmail(self.settings.EMAIL_FROM, [self.settings.EMAIL_TO], msg.as_string())
            logger.info('Wysyłam maila')
            s.quit()
        except:
            logger.exception('Błąd w czasie wysyłania maila')

