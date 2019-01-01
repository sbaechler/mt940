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

titles = ['valuta', 'date', 'mark', 'amount', 'value', 'text']

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
val_61 = re.compile('^:(?P<token>61):(?P<valuta>\d{6})(?P<date>\d{4})(?P<mark>\D\D?)'
                    '(?P<amount>\d+,\d{0,2})(?P<code>\D{4})(?P<cref>.*?)$', re.MULTILINE)

val_86 = re.compile('^:(?P<token>86):(?P<text>.*?)\n:\d', re.MULTILINE | re.S)

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
    match = val_61.search(entry)
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

booking_item_keys = {'61', '86'}


for entry in entries:
    booking_items = []
    booking_index = 0

    # A booking entry can have multiple items
    # I only care about tags 61 and 86.

    amount_matches = val_61.finditer(entry)
    info_matches = val_86.finditer(entry)

    for match in amount_matches:
        amount = match.group('amount').replace(',', '.')
        mark = match.group('mark')
        booking_items.append({
            'valuta': match.group('valuta'),
            'date': match.group('date'),
            'mark': mark,
            'amount': amount,
            'value': amount if mark == 'C' else '-' + amount
        })

    for i, match in enumerate(info_matches):
        booking_items[i].update({
            'text': match.group('text').replace('\n', ' ')
        })

    bookings += booking_items


with open('export.csv', 'w') as f:
    headings = [t for t in titles]
    f.write('; '.join(headings) + '\n')
    for booking in bookings:
        entry = [booking.get(h, '') for h in headings]
        f.write('; '.join(entry) + '\n')
