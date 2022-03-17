# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.actions.base_action import AbstractFunctionAction
from mycodo.databases.models import Actions
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import get_measurement
from mycodo.utils.utils import random_alphanumeric

ACTION_INFORMATION = {
    'name_unique': 'mqtt_publish_input',
    'name': f"MQTT: {lazy_gettext('Publish')}: {lazy_gettext('Measurement')}",
    'library': None,
    'manufacturer': 'Mycodo',
    'application': ['inputs'],

    'url_manufacturer': None,
    'url_datasheet': None,
    'url_product_purchase': None,
    'url_additional': None,

    'message': 'Publish an Input measurement to an MQTT server.',

    'usage': '',

    'dependencies_module': [
        ('pip-pypi', 'paho', 'paho-mqtt==1.5.1')
    ],

    'custom_options': [
        {
            'id': 'measurement',
            'type': 'select_measurement_from_this_input',
            'name': lazy_gettext('Measurement'),
            'phrase': 'Select the measurement to send as the payload'
        },
        {
            'id': 'hostname',
            'type': 'text',
            'default_value': 'localhost',
            'required': True,
            'name': lazy_gettext('Hostname'),
            'phrase': 'The hostname of the MQTT server'
        },
        {
            'id': 'port',
            'type': 'integer',
            'default_value': 1883,
            'required': True,
            'name': lazy_gettext('Port'),
            'phrase': 'The port of the MQTT server'
        },
        {
            'id': 'topic',
            'type': 'text',
            'default_value': 'paho/test/single',
            'required': True,
            'name': 'Topic',
            'phrase': 'The topic to publish with'
        },
        {
            'id': 'keepalive',
            'type': 'integer',
            'default_value': 60,
            'required': True,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': lazy_gettext('Keep Alive'),
            'phrase': 'The keepalive timeout value for the client. Set to 0 to disable.'
        },
        {
            'id': 'clientid',
            'type': 'text',
            'default_value': f'client_{random_alphanumeric(8)}',
            'required': True,
            'name': 'Client ID',
            'phrase': 'Unique client ID for connecting to the MQTT server'
        },
        {
            'id': 'login',
            'type': 'bool',
            'default_value': False,
            'name': 'Use Login',
            'phrase': 'Send login credentials'
        },
        {
            'id': 'username',
            'type': 'text',
            'default_value': 'user',
            'required': False,
            'name': lazy_gettext('Username'),
            'phrase': 'Username for connecting to the server'
        },
        {
            'id': 'password',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': lazy_gettext('Password'),
            'phrase': 'Password for connecting to the server.'
        }
    ]
}


class ActionModule(AbstractFunctionAction):
    """Function Action: MQTT Publish."""
    def __init__(self, action_dev, testing=False):
        super().__init__(action_dev, testing=testing, name=__name__)

        self.publish = None

        self.measurement_device_id = None
        self.measurement_measurement_id = None

        self.hostname = None
        self.port = None
        self.topic = None
        self.keepalive = None
        self.clientid = None
        self.login = None
        self.username = None
        self.password = None

        action = db_retrieve_table_daemon(
            Actions, unique_id=self.unique_id)
        self.setup_custom_options(
            ACTION_INFORMATION['custom_options'], action)

        if not testing:
            self.setup_action()

    def setup_action(self):
        import paho.mqtt.publish as publish
        self.publish = publish
        self.action_setup = True

    def run_action(self, message, dict_vars):
        try:
            measurement_dict = dict_vars["value"]["topic"]
        except:
            measurement_dict = None

        if not measurement_dict:
            msg = f" Error: No measurements dictionary passed to Action."
            self.logger.error(msg)
            message += msg
            return

        device_measurement = get_measurement(
            self.measurement_measurement_id)
        if not device_measurement:
            msg = f" Error: A measurement needs to be selected as the payload."
            self.logger.error(msg)
            message += msg
            return

        self.logger.info(f"Measure: {measurement_dict}")

        channel = device_measurement.channel

        payload = None

        try:
            auth_dict = None
            if self.login:
                auth_dict = {
                    "username": self.username,
                    "password": self.password
                }
            self.publish.single(
                self.topic,
                payload,
                hostname=self.hostname,
                port=self.port,
                client_id=self.clientid,
                keepalive=self.keepalive,
                auth=auth_dict)
            message += f" MQTT Publish '{payload}'."
        except Exception as err:
            msg = f" Could not execute MQTT Publish: {err}"
            self.logger.error(msg)
            message += msg

        self.logger.debug(f"Message: {message}")

        return message

    def is_setup(self):
        return self.action_setup
