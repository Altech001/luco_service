from sqlalchemy.ext.automap import automap_base
from db_connect import engine

# automap base and reflect the database schema
Base = automap_base()
Base.prepare(engine, reflect=True)

# Map the tables to their respective classes
User = Base.classes.users
Transaction = Base.classes.transactions
SmsMessage = Base.classes.sms_messages
SmsTemplate = Base.classes.sms_templates
SmsDeliveryReport = Base.classes.sms_delivery_reports
APIKey = Base.classes.api_keys

