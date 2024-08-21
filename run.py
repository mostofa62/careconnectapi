
from app import app
import os
from home import *
from insurrance import *
from caremanager import *
from agency import *
from agencyrate import *
from employee import *
from marketer import *
from caregiver import *
#import logging

#logging.basicConfig(filename='error.log',level=logging.DEBUG)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5002))
    app.run(debug=True, host='0.0.0.0', port=port)
    