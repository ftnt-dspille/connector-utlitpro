"""
Steps related to making SOAP requests
"""
import requests
import xmltodict
import zeep
from connectors.core.connector import get_logger, ConnectorError

logger = get_logger("ultipro")


class Ultipro(object):
    """
    Soap connector. Configured by a WSDL file provided by the soap service. Does
    not currently support the sending of arbitrary xml.
    """

    def __init__(self, soap_config, *args, **kwargs):

        self.server_url = soap_config["server_url"].strip("/")
        self.username = soap_config["username"]
        self.password = soap_config["password"]
        self.clientApiKey = soap_config["clientAPIKey"]
        self.userApiKey = soap_config["userAPIKey"]
        self.verify_ssl = soap_config.get("verify_ssl", False)
        self.__authenticate()

    def __authenticate(self):
        login_header = {
            "UserName": self.username,
            "Password": self.password,
            "ClientAccessKey": self.clientApiKey,
            "UserAccessKey": self.userApiKey,
        }

        try:
            # Log in and get session token
            client = zeep.Client(f"{self.server_url}/services/LoginService")
            result = client.service.Authenticate(_soapheaders=login_header)
            self.ultiProToken = result["Token"]

            if not result["Token"]:
                raise ConnectorError(result)
        except Exception as Err:
            logger.error(Err)
            raise ConnectorError(Err)

    def __make_xml_request(self, method="POST", data={}, headers={}):
        try:
            response = requests.request(
                method,
                self.server_url,
                data=data,
                headers=headers,
                verify=self.verify_ssl,
            )
            if response.ok:
                response_dict = xmltodict.parse(response.text)
                return response_dict
                # status = response_dict.get("response").get("@status")
                # if status == "success":
                #     return response_dict.get("response").get("result")
                # else:
                #     raise ConnectorError(response.text)
            elif response.status_code == 401:
                logger.error("Unauthorized: Invalid credentials")
                raise ConnectorError("Unauthorized: Invalid credentials")
            else:
                raise ConnectorError(response.text)
        except requests.exceptions.SSLError as e:
            logger.exception("{}".format(e))
            raise ConnectorError("{}".format("SSL certificate validation failed"))
        except requests.exceptions.ConnectionError as e:
            logger.exception("{}".format(e))
            raise ConnectorError(
                "{}".format(
                    "The request timed out while trying to connect to the remote server"
                )
            )
        except Exception as e:
            logger.exception("{}".format(e))
            raise ConnectorError("{}".format(e))

    def __make_api_request(self, data, method="POST"):
        pass

    def _getPhoneInformationByEmployeeIdentifier(self, params):
        employeeId = params.get("employeeId")

        headers = {"Content-Type": "application/soap+xml"}
        body = f"""<s:Envelope xmlns:a="http://www.w3.org/2005/08/addressing" xmlns:s="http://www.w3.org/2003/05/soap-envelope">
                    <s:Header>
                        <a:Action s:mustUnderstand="1">http://www.ultipro.com/services/employeephoneinformation/IEmployeePhoneInformation/GetPhoneInformationByEmployeeIdentifier</a:Action>
                        <UltiProToken xmlns="http://www.ultimatesoftware.com/foundation/authentication/ultiprotoken">{self.ultiProToken}</UltiProToken>
                        <ClientAccessKey xmlns="http://www.ultimatesoftware.com/foundation/authentication/clientaccesskey">{self.clientApiKey}</ClientAccessKey>
                    </s:Header>
                    <s:Body>
                        <GetPhoneInformationByEmployeeIdentifier xmlns="http://www.ultipro.com/services/employeephoneinformation">
                        <employeeIdentifier xmlns:b="http://www.ultipro.com/contracts" xmlns:i="http://www.w3.org/2001/XMLSchema-instance" i:type="b:EmployeeNumberIdentifier">
                            <b:CompanyCode>{self.companyId}</b:CompanyCode>
                            <b:EmployeeNumber>{employeeId}</b:EmployeeNumber>
                        </employeeIdentifier>
                        </GetPhoneInformationByEmployeeIdentifier>
                    </s:Body>
                    </s:Envelope>"""
        try:
            result = self.__make_xml_request(method="POST", data=body, headers=headers)
            # response = requests.post(
            #     f"{self.server_url}/services/EmployeePhoneInformation",
            #     data=body,
            #     headers=headers,
            # )
            # if response.ok:
            #     response_dict = xmltodict.parse(response.text)
            if (
                result["s:Envelope"]["s:Body"][
                    "GetPhoneInformationByEmployeeIdentifierResponse"
                ]["GetPhoneInformationByEmployeeIdentifierResult"]["b:OperationResult"][
                    "b:Success"
                ]
                == "true"
            ):
                return result
            else:
                raise ConnectorError(result)
        except:
            logger.debug(f"Failed to Get Phone Information,BODY:{body}")
            raise ConnectorError("Failed to commit config changes")

        #     else:
        #         raise ConnectorError(response.text)
        # except requests.exceptions.SSLError as e:
        #     logger.exception("{}".format(e))
        #     raise ConnectorError("{}".format("SSL certificate validation failed"))
        # except requests.exceptions.ConnectionError as e:
        #     logger.exception("{}".format(e))
        #     raise ConnectorError(
        #         "{}".format(
        #             "The request timed out while trying to connect to the remote server"
        #         )
        #     )
        # except Exception as e:
        #     logger.exception("{}".format(e))
        #     raise ConnectorError("{}".format(e))

    def __findEmployeePhone(self, pageNumber, pageSize):
        # This function will perform a generic search to return all people in the company
        headers = {"Content-Type": "application/soap+xml"}
        body = f"""<s:Envelope xmlns:a="http://www.w3.org/2005/08/addressing" xmlns:s="http://www.w3.org/2003/05/soap-envelope">
        <s:Header>
            <a:Action s:mustUnderstand="1">http://www.ultipro.com/services/employeephoneinformation/IEmployeePhoneInformation/FindPhoneInformations</a:Action>
            <UltiProToken xmlns="http://www.ultimatesoftware.com/foundation/authentication/ultiprotoken">{self.ultiProToken}</UltiProToken>
            <ClientAccessKey xmlns="http://www.ultimatesoftware.com/foundation/authentication/clientaccesskey">{self.clientApiKey}</ClientAccessKey>
        </s:Header>
        <s:Body>
            <FindPhoneInformations xmlns="http://www.ultipro.com/services/employeephoneinformation">
            <query xmlns:b="http://www.ultipro.com/contracts" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
                <b:CompanyCode> = {self.companyId}</b:CompanyCode>
                <b:PageNumber> {pageNumber}</b:PageNumber>
                <b:PageSize> {pageSize}</b:PageSize>
            </query>
            </FindPhoneInformations>
        </s:Body>
        </s:Envelope>"""
        try:
            response = requests.post(
                "https://service5.ultipro.com/services/EmployeePhoneInformation",
                data=body,
                headers=headers,
            )
            if response.ok:
                response_dict = xmltodict.parse(response.text)
                return response_dict
            else:
                raise ConnectorError(response.text)
        except requests.exceptions.ConnectionError as e:
            logger.exception("{}".format(e))
            raise ConnectorError(
                "{}".format(
                    "The request timed out while trying to connect to the remote server"
                )
            )
        except Exception as e:
            logger.exception("{}".format(e))
            raise ConnectorError("{}".format(e))

    def _findEmployeePhone(self, params):
        # iterate through all pages and return employeeList
        pageNumber = params.get("pageNumber", "all")
        pageSize = params.get("pageSize")
        employeePhoneList = []
        if pageNumber != "all":
            response_dict = self.__findEmployeePhone(pageNumber, pageSize)
            return response_dict
        else:
            pageNumber = 1
            response_dict = self.__findEmployeePhone(pageNumber, pageSize)
            pageTotal = response_dict["s:Envelope"]["s:Body"][
                "FindPhoneInformationsResponse"
            ]["FindPhoneInformationsResult"]["b:OperationResult"]["b:PagingInfo"][
                "b:PageTotal"
            ]
            while pageNumber <= int(pageTotal):
                pageNumber += 1
                employeePhoneList += response_dict["s:Envelope"]["s:Body"][
                    "FindPhoneInformationsResponse"
                ]["FindPhoneInformationsResult"]["b:Results"][
                    "b:EmployeePhoneInformation"
                ]
                response_dict = self.__findEmployeePhone(pageNumber, pageSize)
            return employeePhoneList

    def __findEmployeePerson(self, pageNumber, pageSize):
        # This function will perform a generic search to return all people in the company
        headers = {"Content-Type": "application/soap+xml"}
        body = f"""<s:Envelope xmlns:a="http://www.w3.org/2005/08/addressing" xmlns:s="http://www.w3.org/2003/05/soap-envelope">
        <s:Header>
            <a:Action s:mustUnderstand="1">http://www.ultipro.com/services/employeeperson/IEmployeePerson/FindPeople</a:Action>
            <UltiProToken xmlns="http://www.ultimatesoftware.com/foundation/authentication/ultiprotoken">{self.ultiProToken}</UltiProToken>
            <ClientAccessKey xmlns="http://www.ultimatesoftware.com/foundation/authentication/clientaccesskey">{self.clientApiKey}</ClientAccessKey>
        </s:Header>
        <s:Body>
            <FindPeople xmlns="http://www.ultipro.com/services/employeeperson">
            <query xmlns:b="http://www.ultipro.com/contracts" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
                <b:CompanyCode> = {self.companyId}</b:CompanyCode>
                <b:PageNumber> {pageNumber}</b:PageNumber>
                <b:PageSize> {pageSize}</b:PageSize>
            </query>
            </FindPeople>
        </s:Body>
        </s:Envelope>"""
        try:
            response = requests.post(
                "https://service5.ultipro.com/services/EmployeePerson",
                data=body,
                headers=headers,
            )
            if response.ok:
                response_dict = xmltodict.parse(response.text)
                return response_dict
            else:
                raise ConnectorError(response.text)
        except requests.exceptions.ConnectionError as e:
            logger.exception("{}".format(e))
            raise ConnectorError(
                "{}".format(
                    "The request timed out while trying to connect to the remote server"
                )
            )
        except Exception as e:
            logger.exception("{}".format(e))
            raise ConnectorError("{}".format(e))

    def _getAllCompanyEmployees(self, params):
        # iterate through all pages and return employeeList
        pageNumber = params.get("pageNumber", "all")
        pageSize = params.get("pageSize")
        employeeList = []
        if pageNumber != "all":
            response_dict = self.__findEmployeePerson(pageNumber, pageSize)
            return response_dict
        else:
            pageNumber = 1
            response_dict = self.__findEmployeePerson(pageNumber, pageSize)
            while (
                response_dict["s:Envelope"]["s:Body"]["FindPeopleResponse"][
                    "FindPeopleResult"
                ]["b:OperationResult"]["b:PagingInfo"]["b:CurrentPage"]
                <= response_dict["s:Envelope"]["s:Body"]["FindPeopleResponse"][
                    "FindPeopleResult"
                ]["b:OperationResult"]["b:PagingInfo"]["b:PageTotal"]
            ):
                pageNumber += 1
                employeeList += response_dict["s:Envelope"]["s:Body"][
                    "FindPeopleResponse"
                ]["FindPeopleResult"]["b:Results"]["b:EmployeePerson"]
                response_dict = self.__findEmployeePerson(pageNumber, pageSize)
            return employeeList

    def _getPersonDetails(self, params):
        auth = (self.username, self.password)
        headers = {"US-Customer-Api-Key": self.clientApiKey}
        if params.get("companyId"):
            companyId = params.get("companyId")
        else:
            companyId = self.companyId
        parameters = {"companyId": companyId, "per_Page": 10000}
        print(parameters)
        try:
            response = requests.get(
                "https://service5.ultipro.com/personnel/v1/person-details",
                params=parameters,
                auth=auth,
                headers=headers,
                verify=self.verify_ssl,
            )
            if response.ok:
                return response.json()
            elif response.status_code == 401:
                logger.error("Unauthorized: Invalid credentials")
                raise ConnectorError("Unauthorized: Invalid credentials")
            else:
                raise ConnectorError(response.text)
        except requests.exceptions.SSLError as e:
            logger.exception("{}".format(e))
            raise ConnectorError("{}".format("SSL certificate validation failed"))
        except requests.exceptions.ConnectionError as e:
            logger.exception("{}".format(e))
            raise ConnectorError(
                "{}".format(
                    "The request timed out while trying to connect to the remote server"
                )
            )
        except Exception as e:
            logger.exception("{}".format(e))
            raise ConnectorError("{}".format(e))

    def _getEmploymentDetails(self, params):
        auth = (self.username, self.password)
        headers = {"US-Customer-Api-Key": self.clientApiKey}
        if params.get("companyId"):
            companyId = params.get("companyId")
        else:
            companyId = self.companyId
        parameters = {"companyId": companyId, "per_Page": 10000}
        try:
            response = requests.get(
                "https://service5.ultipro.com/personnel/v1/employment-details",
                params=parameters,
                auth=auth,
                headers=headers,
                verify=self.verify_ssl,
            )
            if response.ok:
                return response.json()
            elif response.status_code == 401:
                logger.error("Unauthorized: Invalid credentials")
                raise ConnectorError("Unauthorized: Invalid credentials")
            else:
                raise ConnectorError(response.text)
        except requests.exceptions.SSLError as e:
            logger.exception("{}".format(e))
            raise ConnectorError("{}".format("SSL certificate validation failed"))
        except requests.exceptions.ConnectionError as e:
            logger.exception("{}".format(e))
            raise ConnectorError(
                "{}".format(
                    "The request timed out while trying to connect to the remote server"
                )
            )
        except Exception as e:
            logger.exception("{}".format(e))
            raise ConnectorError("{}".format(e))


def getPhoneInformationByEmployeeIdentifier(config, params):
    ultipro = Ultipro(config)
    return ultipro._getPhoneInformationByEmployeeIdentifier(params)


def findEmployeePhone(config, params):
    ultipro = Ultipro(config)
    return ultipro._findEmployeePhone(params)


def getAllCompanyEmployees(config, params):
    ultipro = Ultipro(config)
    return ultipro._getAllCompanyEmployees(params)


def getPersonDetails(config, params):
    ultipro = Ultipro(config)
    return ultipro._getPersonDetails(params)


def getEmploymentDetails(config, params):
    ultipro = Ultipro(config)
    return ultipro._getEmploymentDetails(params)


def check_health(config, *args, **kwargs):
    try:
        Ultipro(config)
    except Exception as e:
        raise ConnectorError(str(e))


operations = {
    "getPhoneInformationByEmployeeIdentifier": getPhoneInformationByEmployeeIdentifier,
    "findEmployeePhone": findEmployeePhone,
    "getAllCompanyEmployees": getAllCompanyEmployees,
    "getPersonDetails": getPersonDetails,
    "getEmploymentDetails": getEmploymentDetails,
}
