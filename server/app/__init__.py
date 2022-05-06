import logging
from os import getenv

from dotenv import load_dotenv
from flask import Flask
from flask_apscheduler import APScheduler
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy

load_dotenv(dotenv_path=getenv("ENV_FILE", ".env"), override=True)

# Configure main instances
app = Flask(__name__)
app.config.from_object("server.config." + (getenv("FLASK_ENVIRONMENT").capitalize()))
logging.getLogger().setLevel(app.config["LOG_LEVEL"])
db = SQLAlchemy(app)
ma = Marshmallow(app)
db.init_app(app)
CORS(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


@app.before_first_request
def create_table():
    db.create_all()


# Swagger configuration
api = Api(app, doc='/docs', title='Deemas', description='Proxy manager for Attack&Defence')
services_ns = api.namespace('services', description='Services')
scripts_ns = api.namespace('rules/scripts', description='Scripts')
conditions_ns = api.namespace('rules/conditions', description='Conditions')
proxy_ns = api.namespace('services/proxy', description='Proxy for services')
iptables_ns = api.namespace('services/iptables', description='Iptables rules for proxy and services')

# Create marshmallow schemes
from server.app.models import *
from server.app.schemas import *

# Service
service_schema = ServiceSchema()
services_schema = ServiceSchema(many=True, exclude=("condition_rules", "script_rules"))
# Script Rules
script_rules_schema = ScriptRuleSchema(many=True, exclude=("protocol",))
# Condition Rules
condition_rules_schema = ConditionRuleSchema(many=True, exclude=("protocol",))

# Create log dir if not exists
app.config["LOG_DIR"].mkdir(parents=True, exist_ok=True)

from server.app.swagger import *
from server.app.errorhandler import *
from server.app.views import *
from server.app.api.services import *
from server.app.api.proxy import *
from server.app.api.rules import *
from server.app.proxyhandler import update_state

if app.config["ENABLE_IPTABLES_MANAGEMENT"]:
    from server.app.api.iptables import *
