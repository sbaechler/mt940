import re
import sys

lookup = {'05': 'job number', '32': 'instruct', '33': 'benefic',
          '24': 'conversion text', '60': 'reason', '23': 'account with',
          '25': 'our expenses'}

text = open(sys.argv[1]).read().splitlines()
text = ''.join(text)

# interesting stuff is in {4:.....}
book_pat = re.compile('\{4:(?P<booking>.*?)\}')

# seperate the fields in the booking :num:field
field_pat = re.compile(':(?P<num>\d\d.??):(?P<field>[^:]*)')

# seperate the values in the field 61
val61_pat = re.compile('(?P<valuta>\d{6})(?P<date>\d{4})(?P<mark>\D\D?)'
                       '(?P<amount>\d+,\d{2})(?P<code>\D{4})(?P<cref>.*?)//'
                       '(?P<bref>.{16})(?P<add>.*)')

# seperate the values in the field 86
value_pat = re.compile('(?P<valuta>\d{6})(?P<date>\d{4})(?P<mark>\D\D?)'
                       '(?P<amount>\d+,\d{2})(?P<code>\D{4})(?P<cref>.*?)//'
                       '(?P<bref>.{16})(?P<add>.*)')

f = open('export.csv', 'w')
f.write('date, amount, payee, description, reference\n')

for match in re.finditer(book_pat, text):
    booking = match.group('booking')

    for match in re.finditer(field_pat, booking):
        num = match.group('num')
        field = match.group('field')

        if num == '61':
            match = re.match(val61_pat, field)
            match_dict = match.groupdict()
            print match_dict

        if num == '86':
            trig_dict = {}
            triggers = field.split('?')
            trig_dict['epc'] = triggers[0]
            for trigger in triggers[1:]:
                code = trigger[:2]
                code = lookup[code]
                value = trigger[2:]
                trig_dict[code] = value

            print trig_dict

            date = match_dict['valuta']
            amount = match_dict['amount']
            amount = amount.replace(',', '.')

            if match_dict['mark'] == 'D':
                sign = '-'
                benefic = trig_dict['benefic']
            else:
                sign = ''
                benefic = trig_dict['instruct']

            bref = match_dict['bref']

            if 'reason' in trig_dict.keys():
                reason = trig_dict['reason']
            else:
                reason = ''

            amount = '{0}{1}'.format(sign, amount)
            date = '{0}/{1}/{2}'.format(date[4:6], date[2:4], 2000 +
                                        int(date[:2]))

            f.write('{0}, {1}, {2}, {3}, {4}\n'.format(date, amount,
                                                       benefic, reason,
                                                       bref))

            print

f.close()
