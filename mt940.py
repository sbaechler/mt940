import re
import sys

lookup = {
    '05': 'job number',
    '20': 'transaction reference number',
    '21': 'related reference',
    '23': 'account with',
    '24': 'conversion text',
    '25': 'account identification',
    '28C': 'sequence number',
    '32': 'instruct',
    '33': 'benefic',
    '60': 'reason',
    '60F': 'balance before',
    '61': 'amount',
    '62F': 'balance after',
    '64': 'available funds',
    '86': 'information',
}


def tag_name(tag):
    return lookup.get(tag, tag)


entries = []
bookings = []

titles = set()

with open(sys.argv[1], 'r') as f:
    text = f.read()
    entries = text.split('\n\n')  # Empty line

entry_re = re.compile('^:(\d+\w?):(.*)')

linebreak_re = re.compile('\r\n(?!:)')


# interesting stuff is in {4:.....}
book_pat = re.compile('\{4:(?P<booking>.*?)\}')

# seperate the fields in the booking :num:field
field_pat = re.compile(':(?P<num>\d\d.??):(?P<field>[^:]*)')

# seperate the values in the field 61
val61_pat = re.compile('^(?P<valuta>\d{6})(?P<date>\d{4})(?P<mark>\D\D?)'
                       '(?P<amount>\d+,\d{0,2})(?P<code>\D{4})(?P<cref>.*?)$')

# seperate the values in the field 86
value_pat = re.compile('^(?P<valuta>\d{6})(?P<date>\d{4})(?P<mark>\D\D?)'
                       '(?P<amount>\d+,\d{2})(?P<code>\D{4})(?P<cref>.*?)//'
                       '(?P<bref>.{16})(?P<add>.*)$')

balance_pat = re.compile('^C(?P<date>\d{6})(?P<currency>\w{3})(?P<amount>.*)$')


def get_balance(tag, entry):
    match = balance_pat.search(entry)
    if match:
        return {
            '{}:currency'.format(tag): match.group('currency'),
            '{}:amount'.format(tag): match.group('amount').replace(',', '.'),
        }

    return entry


def parse_61(tag, entry):
    match = val61_pat.search(entry)
    if match:
        return {
            '{}:valuta'.format(tag): match.group('valuta'),
            '{}:date'.format(tag): match.group('date'),
            '{}:mark'.format(tag): match.group('mark'),
            '{}:amount'.format(tag): match.group('amount').replace(',', '.'),
        }

    return entry


additional_processing = {
    '60F': get_balance,
    '61': parse_61,
    '62F': get_balance,
    '64': get_balance,
}


for entry in entries:
    sanitized_entry = re.sub(linebreak_re, ' ', entry)
    details = sanitized_entry.splitlines()
    booking = {}

    for row in details:
        matches = entry_re.search(row)
        if matches:
            tag = matches.group(1)
            content = matches.group(2)
            name = tag_name(tag)

            if tag in additional_processing:
                result = additional_processing[tag](name, content)
                if type(result) is dict:
                    for (t, v) in result.items():
                        titles.add(t)
                        booking[t] = v
                else:
                    titles.add(name)
                    booking[name] = result
            else:
                titles.add(name)
                booking[name] = content

    bookings.append(booking)


with open('export.csv', 'w') as f:
    headings = [t for t in titles]
    f.write('; '.join(headings) + '\n')
    for booking in bookings:
        entry = [booking.get(h, '') for h in headings]
        f.write('; '.join(entry) + '\n')
