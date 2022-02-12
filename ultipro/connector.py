from connectors.core.connector import Connector, get_logger, ConnectorError
from .operations import *

logger = get_logger("ultipro")


class UltiproConnector(Connector):
    def execute(self, config, operation, params, *args, **kwargs):
        try:
            operation = operations.get(operation)
            return operation(config, params)
        except Exception as e:
            logger.exception("An exception occurred in execute {}".format(e))
            raise ConnectorError(e)

    def check_health(self, config):
        try:
            check_health(config)
        except Exception as e:
            logger.exception("An exception occurred in check_health {}".format(e))
            raise ConnectorError(e)
