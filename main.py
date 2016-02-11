import os
import sys
import glob
import string
import math
from datetime import date
import argparse
import re
from gedcom import Gedcom
from flask import Flask, request, jsonify, redirect, url_for

# How wide do we print our dates?  4 characters for the year + 2 spaces = 6
DATE_WIDTH = 6


app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['ALLOWED_EXTENSIONS'] = set(['ged'])

UPLOAD_PATH = "upload"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


@app.route("/")
def root():

    filepaths = glob.glob(os.path.join(basedir, "upload") + "/*.ged")

    ged_selector = ""
    for filepath in filepaths:
        filename = os.path.split(filepath)[1]
        listname = os.path.splitext(filename)[0]
        ged_selector += "<option value='{}'>{}</option>\n".format(filepath, listname)

    parameters = {'gedfiles': ged_selector}

    html = '''
<!DOCTYPE html>

<meta charset="utf-8">

<title>Fingerprint</title>
<head>
<link rel="stylesheet" href="/static/fingerprint.css">

</head>

<body>


<h1>GEDcom Fingerprint</h1>

<div class="box">
<h3>First, make sure your GED file is on the server:</h3>
<form action="/upload-target" method="post" enctype="multipart/form-data">
<table border="0">
    <tr>
        <td>1:</td>  <td><input style="height:2em"  type=file name=file><br/></td>
    </tr><tr>
        <td>2:</td>  <td><input style="display: inline-block; height:200px" type=submit value=Upload></td>
    </tr>
</table>
</form>
</div>

<br/>

<div class="box">
<h3>Then, select your GED file, specify one or more selection fields, and submit:</h3>
<form action="/fingerprint" method="post">
<table border="0">
<tr>
    <td>3:</td> <td>GED File:</td>
    <td><select name="gedFile">
        {gedfiles}
    <select></td>
</tr><tr>
    <td>4:</td> <td>First Name</td> <td><input type="text" name="firstName" /></td>
</tr><tr>
    <td/> <td>Middle Name</td> <td><input type="text" name="middleName" /></td>
</tr><tr>
    <td/> <td>Last Name</td> <td><input type="text" name="lastName" /></td>
</tr><tr>
    <td/> <td>5-year dates</td> <td><input type="checkbox" name="state" />State Census</td>
</tr><tr>
    <td>5:</td> <td></td> <td><input type="submit"/></td>
</tr>
</table>
</form>
</div>


</body>

'''.format(**parameters)

    return html

@app.route("/upload-target", methods=["POST"])
def upload():
    f = request.files['file']

    if f and allowed_file(f.filename):
        filename = f.filename
        updir = os.path.join(basedir, UPLOAD_PATH)
        filepath = os.path.join(updir, filename)
        f.save(filepath)

        return redirect('/')

    else:
        app.logger.info('ext name error')
        return jsonify(error='Error uploading file... back up and try again.')

@app.route("/fingerprint", methods=["POST"])
def web_fingerprint():
    form = request.form

    match_criteria = []

    given_names = []
    name = form.get('firstName')
    if name is not None:
        given_names.append(name)
    name = form.get('middleName')
    if name is not None:
        given_names.append(name)
    if given_names is not None:
        match_criteria.append("name={}".format(" ".join(given_names)))

    name = form.get('lastName')
    if name is not None:
        match_criteria.append("surname={}".format(name))

    # The matching criteria as defined in gedcom.py criteria_match() function
    criteria = ":".join(match_criteria)

    if form.get('state'):
        # State census dates fall on the fifth year of each decade, e.g. 1915, 1925, etc
        offset = 5
    else:
        # Federal census dates fall on the zero year of each decade, e.g. 1910, 1920, etc
        offset = 0

    # Parse the Gedcom file, using the lovely parser we snatched out of Github
    gedcom = Gedcom(form.get('gedFile'))

    html = '''
<!DOCTYPE html>

<meta charset="utf-8">

<title>Fingerprint</title>
<head>
<link rel="stylesheet" href="/static/fingerprint.css">
</head>

<body>


<h1>GEDcom Fingerprint</h1>

'''

    # Look at EVERYONE
    for element in gedcom.element_list():
        # Do they match?
        if element.criteria_match(criteria):
            # A match, fingerprint them
            data = fingerprint_data(gedcom, element, offset)
            html += table_fingerprint(data)

    html += '''
<h2>To get a different fingerprint, use the Back-arrow in your browser and re-submit a new name.</h2>

</body>
'''

    return html

def generate_entity_row(entity, level):
    '''Generate the information needed for a single row in the fingerprint.

    :param entity: the entity (person) to generate
    :param level: Where in the fingerprint this entity lies:
                    0, the parents
                    1, the target and spouses
                    2, the children

    :return: A dictionary of values that define an entity for the fingerprint
    '''

    # The row ID is the full name of the person
    id = string.join(entity.name(), ' ')

    # Indentation is baked into the ID for simplicity
    if level == 1:
        id = "    {}".format(id)
    elif level == 2:
        id = "    ... {}".format(id)

    # The final year is the year of their death, if known, otherwise, today's year
    birth_year = entity.birth_year()
    death_year = entity.death_year()
    if death_year < 0:
        final_year = date.today().year
        if final_year - birth_year > 100:
            final_year = birth_year + 100   # 100 years default age if none other given
    else:
        final_year = death_year

    return {
        'id': id,
        'birth': birth_year,
        'death': death_year,
        'final': final_year
    }

def generate_fingerprint(row, id_length, earliest_census, latest_census):
    '''Generate a line in the fingerprint, either the title line or details on a person

    :param row: details as returned by generate_entity_row()
    :param id_length: the number of characters to reserve for the identifier string
    :param earliest_census: the first date to fingerprint on
    :param latest_census: the last date to fingerprint on

    :return: A string suitable for printing in the fingerprint chart
    '''

    if row is None:
        return _generate_fingerprint_header(id_length, earliest_census, latest_census)
    else:
        return _generate_fingerprint_entry(row, id_length, earliest_census, latest_census)

def _generate_fingerprint_header(id_length, earliest_census, latest_census):
    '''Worker function to generate the string of dates for the fingerprint'''

    # Leading spaces to justify the census dates
    title = [string.ljust('', id_length, ' '), string.ljust('', DATE_WIDTH, ' ')]

    # Once census date every ten years
    for date in range(earliest_census, latest_census+1, 10):
        title.append(string.ljust(str(date), DATE_WIDTH, ' '))

    # e.g:
    #                                       1810  1820  1830  1840  1850  1860  1870  1880  1890  1900  1910  1920
    return title

def _generate_fingerprint_entry(row, id_length, earliest_census, latest_census):
    '''Worker function to generate an entry in the fingerprint'''

    is_target = row.get('target', False)

    # Identifier, which is the indentation and full name of a person, padded with spaces to fill the slot
    entry = row['id']
    if is_target:
        entry = entry.upper()
        separator = '.'
    else:
        separator = ' '
    entry = [string.ljust(entry, id_length, separator)]

    birth = int(row['birth'])
    final = int(row['final'])
    if birth < 0:
        # We don't know when they were born, so we can't really generate a line for them
        entry.append(string.ljust('--', DATE_WIDTH, separator))
    else:
        # The second column is the birth year, again padded with spaces to fill the slot
        entry.append(string.ljust(str(row['birth']), DATE_WIDTH, separator))

        # For each ten year census date...
        for date in range(earliest_census, latest_census+1, 10):
            # ... determine their age at this year
            age = date - int(row['birth'])
            if age < 0:
                # ... if they weren't born yet, pad with spaces
                entry.append(string.ljust('', DATE_WIDTH, separator))
            elif date <= final:
                # ... and if they weren't dead yet, generate a year entry
                entry.append(string.ljust(str(age), DATE_WIDTH, separator))
            else:
                # ... but if they ARE dead, more spaces for the slot
                entry.append(string.ljust('', DATE_WIDTH, separator))

    # e.g.:
    #     Jabez W Crouch              1813        7     17    27    37    47    57
    return entry

def year_only(date):
    p = re.compile('(\d{4})')
    match = p.search(date)
    if match is not None:
        return match.group(0)
    return ''

def fingerprint_data(gedcom, target, offset):
    ''' Print an entire fingerprint record for a given target person

    :param gedcom: the parsed Gedcom data
    :param target: the specific entity that is the person we are fingerprinting
    :param offset: year offset; 0 for federal census, 5 for state census dates
    :return: Prints a fingerprint chart for the target person and their family
    '''

    # The rows array collects dictionaries that define entities in the fingerprint
    # These get converted to strings by the generate_fingerprint() method, later
    rows = []

    # The first part of the fingerprint are the target's parents
    parents = gedcom.get_parents(target)
    for parent in parents:
        rows.append(generate_entity_row(parent, 0))

    # The next part are the target person themself...
    target_row = generate_entity_row(target, 1)
    target_row['target'] = True
    rows.append(target_row)

    # ... and the their family...
    families = gedcom.families(target)
    for family in families:
        # ...members of the target's family tagged as parents are spouses
        peers = gedcom.get_family_members(family, "PARENTS")
        for peer in peers:
            if (peer != target):
                rows.append(generate_entity_row(peer, 1))

        # ... children are tagged simply as children
        children = gedcom.get_family_members(family, "CHIL")
        for child in children:
            rows.append(generate_entity_row(child, 2))

    # In order to make a tidy chart, we need to know a few statistics about this fingerprint:
    #   The width of the widest identifier string
    #   The earliest birth date
    #   The latest final date
    longest_id = 0
    earliest_date = date.today().year + 1
    latest_date = 0
    for row in rows:
        id = row['id']
        longest_id = max(longest_id, len(id))
        birth = int(row['birth'])
        if birth > 0:
            earliest_date = min(earliest_date, birth)
        latest_date = max(latest_date, int(row['final']))
    # Modulo the longest identifier by 4, to give a decent 4-space tab effect
    longest_id = int(math.ceil((longest_id+1) / 4.0) * 4)

    # Snap the raw date range into the census grid
    modulo = 10
    earliest_census = int(math.floor(earliest_date / modulo) * modulo) - offset
    latest_census = int(math.ceil(float(latest_date) / modulo) * modulo) - offset

    # Residences!

    locations = []
    residences = target.residences()
    for residence in residences:
        locations.append(('Residence', year_only(residence[0]), residence[1]))

    marriages = gedcom.marriages(target)
    for marriage in marriages:
        locations.append(('Marriage', year_only(marriage[0]), marriage[1]))

    # TODO: Process the dates to do comparisons across different date formats

    locations.sort(key=lambda location:location[1])

    birth = target.birth()
    locations.insert(0, ('Birth', year_only(birth[0]), birth[1]))

    death = target.death()
    locations.append(('Death', year_only(death[0]), death[1]))

    return {
        'name': string.join(target.name(), ' '),
        'locations': locations,
        'fingerprint': rows,
        'longest_id': longest_id,
        'earliest_date': earliest_census,
        'latest_date': latest_census
    }

def print_fingerprint(fingerprint):
    # Print the fingerprint chart itself
    print string.upper("FINGERPRINT FOR {}".format(fingerprint.get('name')))
    print

    def generate_residence_string(entry):
        return "   " + entry[0] + " - " + entry[1] + " : " + entry[2]


    for location in fingerprint.get('locations'):
        print generate_residence_string(location)

    print

    longest_id = fingerprint.get('longest_id')
    earliest_date = fingerprint.get('earliest_date')
    latest_date = fingerprint.get('latest_date')
    print ''.join(generate_fingerprint(None, longest_id, earliest_date, latest_date))
    for row in fingerprint.get('fingerprint'):
        print ''.join(generate_fingerprint(row, longest_id, earliest_date, latest_date))

    print


def table_fingerprint(fingerprint):

    earliest_date = fingerprint.get('earliest_date')
    latest_date = fingerprint.get('latest_date')
    num_cols = 2 + (latest_date - (earliest_date+1)) / 10 + 2

    def generate_residence_string(entry):
        return "<tr><td>{}</td><td>{}</td><td colspan={}>{}</td></tr>".format(entry[0], entry[1], num_cols-2, entry[2])

    rows = []
    rows.append("<tr><th colspan={}>Fingerprint for {}</th></tr>".format(num_cols, fingerprint.get('name')))
    rows.append("<tr><th>Event</th><th>Year</th><th>Location</th><td colspan={}/></tr>".format(num_cols-3))

    for location in fingerprint.get('locations'):
        rows.append(generate_residence_string(location))
    rows.append("<tr><td colspan={} /></tr>".format(num_cols))



    rows.append("<tr><th>{}</th></tr>".format("</th><th>".join(generate_fingerprint(None, 0, earliest_date, latest_date))))
    for row in fingerprint.get('fingerprint'):
        rows.append("<tr><td>{}</td></tr>".format("</td><td>".join(generate_fingerprint(row, 0, earliest_date, latest_date))))

    html = '''
<div class="box">
<table>
{}
</table>
</div>
'''.format("\n".join(rows))

    return html

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("gedfilename", help="File and path to the GEDcom file")
    parser.add_argument("-w", "--web", action="store_true", help="Launch as web server (then ignores all other options)")
    parser.add_argument("-s", "--state", action="store_true", help="Report on the five-year mark and not on the decade")
    parser.add_argument("-f", "--firstname", help="First name of the person to fingerprint")
    parser.add_argument("-m", "--middlename", help="Middle name of the person to fingerprint")
    parser.add_argument("-l", "--lastname", help="Last name of the person to fingerprint")

    args = parser.parse_args()

    if args.web:
            app.run(port=5000)
    else:
        match_criteria = []

        given_names = []
        if args.firstname is not None:
            given_names.append(args.firstname)
        if args.middlename is not None:
            given_names.append(args.middlename)
        if given_names is not None:
            match_criteria.append("name={}".format(" ".join(given_names)))

        if args.lastname is not None:
            match_criteria.append("surname={}".format(args.lastname))

        # The matching criteria as defined in gedcom.py criteria_match() function
        criteria = ":".join(match_criteria)

        if args.state:
            # State census dates fall on the fifth year of each decade, e.g. 1915, 1925, etc
            offset = 5
        else:
            # Federal census dates fall on the zero year of each decade, e.g. 1910, 1920, etc
            offset = 0

        # Parse the Gedcom file, using the lovely parser we snatched out of Github
        gedcom = Gedcom(args.gedfilename)

        # Look at EVERYONE
        for element in gedcom.element_list():
            # Do they match?
            if element.criteria_match(criteria):
                # A match, fingerprint them
                data = fingerprint_data(gedcom, element, offset)
                print_fingerprint(data)
