import re

regex = re.compile(r'(?:6553[0-5])|(?:655[0-2]\d)|(?:65[0-4]\d{2})|(?:6[0-4]\d{3})|(?:[0-5]\d{4})|(?:\d{1,4})(?:\-(?:(?:6553[0-5])|(?:655[0-2]\d)|(?:65[0-4]\d{2})|(?:6[0-4]\d{3})|(?:[0-5]\d{4})|(?:\d{1,4})))*')

text = "127.0.0.1"\
        "aoeuaoeuaooeuaoeuaoeuo172.168.0.123-172.168.1.123uaoeuaoeu"\
        "hello127.0.0.2uaeoeu"
found = regex.findall(text)
for line in found:
    print(line)
