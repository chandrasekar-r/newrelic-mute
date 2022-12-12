import requests
import boto3
import json
from celery.utils.log import get_task_logger


LOGGER = get_task_logger(__name__)


def newrelic_session():
    """
    Create an aws client to fetch secrets from the AWS secret manager
    return: The New Relic account id, the New Relic API key
    """
    try:
        session = boto3.Session()  # credentials and config file for the AWS account should be in ~/.aws folder
        client = session.client(
            service_name='secretsmanager',
            region_name='us-east-1'
            )

        response = client.get_secret_value(
                    SecretId='newrelic_secrets' # New-relic Account ID and API_key are stored in AWS Secret Manager
                )

        database_secrets = json.loads(response['SecretString'])
        return database_secrets['ACCOUNT'], database_secrets['API_KEY']
    except Exception as ex:
        LOGGER.exception(ex)
        raise ex


class NewRelicRule:
    """
    Manages New-relic API to create/enable/disable/delete Mutation Rules.
    """
    def __init__(self, deployment):
        '''
        :param deployment: The deployment to create NewRelic Mute rules.
        '''
        try:
            self.deployment = deployment
            self.customer_name = deployment.customer_name
            self.account_id, self.api_key = newrelic_session()
            self.url = 'https://api.newrelic.com/graphql'
            self.headers = {'API-Key': self.api_key}
            self.variables = {'Account': self.account_id}
        except Exception as ex:
            LOGGER.exception(ex)
            pass


    def create_mute_rule(self):
        """
        Create Mutation Rule for Customers
        Mute Rule will be enabled by default when the rule is created.
        """
        create_mutation_rule = """
        mutation {
        alertsMutingRuleCreate(accountId: %(account_id)s, rule: {
            name: "%(customer_name)s - Mute Rule",
            description: "Mute Rule for customer %(customer_name)s",
            enabled: true,
            condition: {
            operator: OR,
            conditions: [
            {
                attribute: "tags.label.Customer",
                operator: EQUALS,
                values: ["%(customer_name)s"]
            },
            {
                attribute: "tags.appName",
                operator: CONTAINS,
                values: ["%(customer_name)s"]
            }
            ]
            }
        }) {
            id
        }
        }
        """ % {'account_id':self.account_id, 'customer_name':self.customer_name}
        try:
            request = requests.post(self.url, headers=self.headers, json={'query': create_mutation_rule, 'variables': self.variables})
            if 200 <= request.status_code <= 299:
                data = request.json()
                mute_id = data.get("data").get("alertsMutingRuleCreate").get("id")
                self.deployment.mutation_id = mute_id
                self.deployment.save()
            else:
                raise Exception("Query failed to run by returning code of {}".format(request.status_code))
        except Exception as ex:
            LOGGER.exception(ex)
            raise

    
    def toggle_mute_rule(self, mutation_id, is_enabled):
        """
        :param mutation_id:
        """
        disable_mutation_rule = """
            mutation {
            alertsMutingRuleUpdate(accountId: %s, id: %s, rule: {
                enabled: %s
            }) {
                name
                enabled
                id
            }
            }
            """ % (self.account_id, mutation_id, is_enabled)
        try:
            request = requests.post(self.url, headers=self.headers, json={'query': disable_mutation_rule, 'variables': self.variables})
            if 200 <= request.status_code <= 299:
                request.json()
            else:
                raise Exception("Query failed to run by returning code of {}".format(request.status_code))
        except Exception as ex:
            LOGGER.exception(ex)
            raise
