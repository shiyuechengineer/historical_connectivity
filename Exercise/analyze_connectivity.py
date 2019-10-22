READ_ME = '''
Run this script with the following arguments:
python[3] analyze_connectivity.py SERIAL_NUMBER START_TIME [END_TIME]
Both timestamps' format should be in ISO8601, UTC (don't specify time zone)
END_TIME is optional and if not included will use current time
SERIAL_NUMBER can be substituted by one of {MX, MS, MR, MV, ALL}

Examples:
python3 analyze_connectivity.py Q2AB-1234-CDEF 2019-10-24T12:34:56
python analyze_connectivity.py MR 2019-10-01 2019-11-01
'''


from datetime import datetime
# SOMETHING IS MISSING
import sys


# Analyze a single serial's connectivity, meat of the script
def analyze(data, serial, tallies, t0, t1):
    format = '%Y-%m-%d_%H-%M-%S'
    if serial not in data:
        print(f'Serial number {serial} not found in the data of file connectivity.json')
    else:
        # Format data into datetime objects
        states = [{'time': datetime.strptime(ts, format), 'state': state} for [ts, state] in data[serial]['states']]

        # Add another (dummy) sample with time=now to end of list, to simplify processing
        states.append({'time': datetime.utcnow(), 'state': states[-1]['state']})

        # Iterate through states
        for i in range(1, len(states)):
            start = max(t0, states[i-1]['time'])
            end = min(t1, states[i]['time'])
            tally = max(0, (end-start).total_seconds())     # ensure only positive tallies

            status = states[i-1]['state']
            tallies[status] += tally

            if states[i]['time'] > t1:
                break

        # Add in any "unknown" states before first sample or after last sample
        first = states[0]['time']
        last = states[-1]['time']
        t0_to_first = max(0, (first-t0).total_seconds())
        t1_to_first = max(0, (first-t1).total_seconds())
        last_to_t0 = max(0, (t0-last).total_seconds())
        last_to_t1 = max(0, (t1-last).total_seconds())
        tallies['unknown'] += (t0_to_first - t1_to_first) + (last_to_t1 - last_to_t0)


# For a list of serials, aggregate their connectivity tallies
def tally_up(data, serials, t0, t1):
    tallies = {
        'online': 0,
        'alerting': 0,
        'offline': 0,
        'unknown': 0,
    }
    for serial in serials:
        analyze(data, serial, tallies, t0, t1)
    return tallies


# Helper function to format display of time for readability
def display_time(seconds, granularity=2):
    if seconds == 0:
        return '0 seconds'
    else:
        seconds = round(seconds)

    intervals = (
        ('weeks', 604800),  # 60 * 60 * 24 * 7
        ('days', 86400),  # 60 * 60 * 24
        ('hours', 3600),  # 60 * 60
        ('minutes', 60),
        ('seconds', 1),
    )

    result = []
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append(f'{value} {name}')
    return ', '.join(result[:granularity])


# Print summary of connectivity analysis results
def display_results(serials, connectivity, t0, t1):
    total = sum(connectivity.values())
    online = connectivity['online']
    alerting = connectivity['alerting']
    offline = connectivity['offline']
    unknown = connectivity['unknown']

    if len(serials) == 1:
        devices = f'device {serials[0]}'
    else:
        devices = f'{len(serials)} devices'

    print(f'For {devices}, connectivity summary\n  from {t0:%Y-%m-%d %H:%M:%S} to {t1:%Y-%m-%d %H:%M:%S}')
    for (status, tally) in zip(('Online', 'Alerting', 'Offline', 'Unknown'), (online, alerting, offline, unknown)):
        if tally == 0:
            print(f'{status}: 0 seconds (0%)')
        else:
            print(f'{status}: {display_time(tally)} ({tally / total * 100:.2f}%)')


def main(analysis, start, end):
    # Convert input times to datetime objects
    try:
        t0 = datetime.fromisoformat(start)
        if type(end) == datetime:
            t1 = end
        else:
            t1 = datetime.fromisoformat(end)
    except ValueError:
        sys.exit(READ_ME)
    if t1 <= t0:
        sys.exit(READ_ME)

    # Determine which serial numbers to analyze
    file_name = 'connectivity.json'
    with open(file_name) as fp:
        # SOMETHING IS MISSING
        pass
    serials = []
    analysis = analysis.upper()
    if analysis == 'ALL':
        serials.extend(data.keys())
    elif analysis == 'MX':
        matches = [s for s in data if data[s]['model'][:2] in ('MX', 'Z1', 'Z3')]
        serials.extend(matches)
    elif analysis in ('MS', 'MR', 'MV'):
        matches = [s for s in data if data[s]['model'][:2] == analysis]
        serials.extend(matches)
    else:
        serials.extend([s for s in data if s == analysis])

    # Analyze connectivity
    if len(serials) == 0:
        sys.exit(f'Your input of {analysis} resulted in no serial numbers to analyze in {file_name}')
    else:
        connectivity = tally_up(data, serials, t0, t1)
        display_results(serials, connectivity, t0, t1)


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit(READ_ME)
    elif len(args) == 2:
        main(args[0], args[1], datetime.utcnow())
    else:
        main(args[0], args[1], args[2])
