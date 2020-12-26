# Example of importing simple "key = value" config file
# (example_settings.conf in this case). To run this example:
#
#    python3 -m imphook -i mod_conf example_conf.py

import example_settings as settings


print(settings.var1)
print(settings.var2)
