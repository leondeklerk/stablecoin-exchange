from bank.bank import Bank
import requests
from pathlib import Path

# Payment system based on the ABN Amro Tikkie API.
# See: https://developer.abnamro.com/api-products/tikkie/reference-documentation
class Tikkie(Bank):

    # Creates a new request in the API and returns the data needed information for the front-end
    def create_payment_request(self, amount, payment_id):
        "Returns payment destiation if successful"

        ans = self.create_request(amount=amount, description="EuroToken Exchange", referenceId=payment_id.replace("=", "_"))
        return {v:ans[k] for k, v in { 'url': 'url', 'paymentRequestToken': 'payment_id'}.items()}

    def initiate_payment(self, account, amount, payment_id):
        print(f"PAYOUT: {amount} to {account}")
        return None

    # Checks if a payment was actually done (payed status and number of payments larger than 0)
    def attempt_payment_done(self, paymentRequestToken):
        status = self.payment_request_status(paymentRequestToken)
        if status and status["numberOfPayments"] > 0:
            return paymentRequestToken
        else:
            return None

    # Retrieve the status based on the request id
    def payment_request_status(self, paymentRequestToken):
        url = self.get_url('paymentrequests') + f"/{paymentRequestToken}"
        x = requests.get(url, headers=self.get_headers())
        return x.json()

    # get a list of all open requests (Tikkies)
    def get_transactions(self):
        url = self.get_url('paymentrequests')
        data = {
                "pageNumber": 0,
                "pageSize": 50
                }
        x = requests.get(url, headers=self.get_headers(), params=data)
        return x.json()

    # Create a new Tikkie and return the request data
    def create_request(self, amount, description, referenceId, expiryDate="2999-12-31"):
        url = self.get_url('paymentrequests')
        data = {
                "amountInCents": amount, #empty is open req
                "description": description, #required, string <= 35 characters
                "expiryDate": expiryDate, #string Format yyyy-mm-dd, empty allowed, effect not tested
                "referenceId": referenceId #ID for the reference of the API consumer.
                }
        x = requests.post(url, headers=self.get_headers(), json=data)
        return x.json()

    # Returns the url and its related callback function
    def get_post_callback_routes(self):
        return {self.url : self.callback}

    # Get the URL of the local (non tikkie) API which is needed for callback
    def get_post_callback_url(self):
        result = self.hostname + self.url
        print(result)

    # Executed when a payed notification is received from the api, will finish the payment
    def callback(self, post_json):
        if post_json['notificationType'] == 'PAYMENT':
            status = self.payment_request_status( post_json['paymentRequestToken'] )
            payment_id = status['referenceId'].replace('_', '=')
            self.stablecoin.CREATE_finish_payment(payment_id)

    # Registers the listener for successfull payments, if not registered manual checks are needed.
    def register_payment_listener(self):
        url = self.get_url('paymentrequestssubscription')
        data = {
                "url": self.get_post_callback_url()
                }
        x = requests.post(url, headers=self.get_headers(), json=data)
        return x

    def __init__(self, api_key, sandbox_token, production_token, hostname,
            url="/api/exchange/e2t/tikkie_callback", production=False, testing=False):
        if production and not production_token:
            raise self.MissingKeyError("Missing production token")

        self.testing = testing

        self.production          = production
        self.production_key      = production_token
        self.abn_api_key         = api_key
        self.url                 = url
        self.hostname            = hostname

        if self.production:
            if not self.production_key:
                raise self.InvalidKeyError("Production key not defined")
        else:
            self.sandbox_key    = sandbox_token or self.generate_new_sandbox_key()
        if not self.testing:
            self.register_payment_listener()
        return super(Tikkie, self).__init__()

    # Apps requires a appToken, when in sandbox mode these can automatically be generated
    def generate_new_sandbox_key(self):
        url = self.get_url("sandboxapps")
        x = requests.post(url, headers={'API-Key': self.abn_api_key})
        if x.status_code != 201:
            print(x.text);
            raise self.InvalidKeyError("Invalid API key")
        else:
            key = x.json()["appToken"]
            return key

    # Get the headers, needed for API authentication
    def get_headers(self):
        if self.production:
            app_token=self.production_key
        else:
            app_token=self.sandbox_key
        return {'X-App-Token': app_token, "API-Key": self.abn_api_key}

    # Get the API URL
    def get_url(self, endpoint):
        if self.production:
            return "https://api.abnamro.com/v2/tikkie/"+endpoint
        else:
            return "https://api-sandbox.abnamro.com/v2/tikkie/"+endpoint

    def __str__(self):
        return "tikkie"

    class MissingKeyError(Exception):
        pass

    class InvalidKeyError(Exception):
        pass

