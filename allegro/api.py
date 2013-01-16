# coding=utf-8
__author__ = 'Qyon'
from suds.client import Client
from suds import WebFault
import time

import logging

logger = logging.getLogger(__name__)

class InvalidSessionException(Exception):
    pass


class ApiHelper(object):
    """
    ...
    """

    def __init__(self, settings):
        logger.debug('Inicjalizacja')
        self.settings = settings
        self.client = self.getApiClient()
        self.session = self.getSession()
        self.get_auctions_retry_count = 0

    def getApiClient(self):
        """
        Pobiera klienta SOAPowego
        """
        logger.debug('getApiClient')
        client = Client('http://webapi.allegro.pl/uploader.php?wsdl')
        return client

    def getSysStatus(self):
        """
        Metoda pozwala na pobranie wartości jednego z wersjonowanych komponentów
        (drzewo kategorii oraz pola formularza sprzedaży) oraz umożliwia podgląd klucza wersji
        dla wskazanego krajów.
        """
        data_dict = {
            'sysvar': 3,
            'country-id': self.settings.ALLEGRO_COUNTRY,
            'webapi-key': self.settings.ALLEGRO_KEY
        }
        return self.client.service.doQuerySysStatus(**data_dict)

    def getSession(self):
        """
        Pobierz sesję dla usera z Allegro.
        """
        sys_info = self.getSysStatus()

        data_dict = {
            'user-login': self.settings.ALLEGRO_LOGIN,
            'user-password': self.settings.ALLEGRO_PASSWORD,
            'country-code': self.settings.ALLEGRO_COUNTRY,
            'webapi-key': self.settings.ALLEGRO_KEY,
            'local-version': sys_info['ver-key'] or self.settings.ALLEGRO_LOCALVERSION
        }
        logger.debug('getSession')
        return self.client.service.doLogin(**data_dict)

    def _get_auctions(self, doShowCatParams, offset):
        doShowCatParams['cat-items-offset'] = offset
        logger.info("Pobieram aukcje. Offset %d" % (doShowCatParams['cat-items-offset'], ))

        try:
            result = self.client.service.doShowCat(**doShowCatParams)
        except WebFault as e:
            if 'Sesja wygas' in e.message:
                raise InvalidSessionException
            logger.exception('API ERROR?')
            raise e

        return result

    def getAuctions(self):
        """

        """
        logger.info('getAuctions')
        doShowCatParams = {
            'session-handle': getattr(self.session, 'session-handle-part'),
            'cat-id': self.settings.CATEGORY_ID,
            'cat-items-limit': 100,
            'cat-items-offset': 0,
        }

        all_auctions = []
        result = {}
        first = True
        offset = 0
        while first or len(all_auctions) < getattr(result, 'cat-items-count', 0):
            first = False
            try:
                result = self._get_auctions(doShowCatParams, offset)
            except InvalidSessionException as e:
                if self.get_auctions_retry_count < 10:
                    logger.warning('Wygasła sesja. Próbuję odnowić')
                    self.session = self.getSession()
                    logger.debug('Sleep na 10 sekund, na wszelki wypadek...')
                    time.sleep(10)
                    self.get_auctions_retry_count += 1
                    first = True
                    continue
                else:
                    raise e

            offset += 1
            self.get_auctions_retry_count = 0
            items = getattr(result, 'cat-items-array')
            if not items or len(items) <= 0:
                print result
                logger.debug('Brak aukcji?')
                break
            all_auctions += items
        logger.info("Pobrano %d aukcji" % (len(all_auctions), ))

        return dict([(getattr(i, 's-it-id'), i) for i in all_auctions])



