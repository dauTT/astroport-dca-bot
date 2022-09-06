import os
from bot.settings.default import *

# you need to set "DCA_BOT = 'prod'" as an environment variable
# in your OS (on which your website is hosted)

if os.environ['DCA_BOT'] == 'prod':
    from .prod import *
elif os.environ['DCA_BOT'] == 'test':
    from .test import *
elif os.environ['DCA_BOT'] == 'dev':
    from .dev import *
else:
    assert False,  "Please provide setting file link to the env variable DCA_BOT={}!".format(
        os.environ['DCA_BOT'])
