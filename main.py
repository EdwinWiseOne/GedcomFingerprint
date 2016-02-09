
import sys
import string
import math
from datetime import date
import argparse
from gedcom import Gedcom


# How wide do we print our dates?  4 characters for the year + 2 spaces = 6
DATE_WIDTH = 6

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
    death_year = entity.death_year()
    if death_year < 0:
        final_year = date.today().year
    else:
        final_year = death_year

    return {
        'id': id,
        'birth': entity.birth_year(),
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
    title = string.ljust('', id_length + DATE_WIDTH, ' ')

    # Once census date every ten years
    for date in range(earliest_census, latest_census+1, 10):
        title += string.ljust(str(date), DATE_WIDTH, ' ')

    # e.g:
    #                                       1810  1820  1830  1840  1850  1860  1870  1880  1890  1900  1910  1920
    return title

def _generate_fingerprint_entry(row, id_length, earliest_census, latest_census):
    '''Worker function to generate an entry in the fingerprint'''

    # Identifier, which is the indentation and full name of a person, padded with spaces to fill the slot
    entry = string.ljust(row['id'], id_length, ' ')

    birth = int(row['birth'])
    final = int(row['final'])
    if birth < 0:
        # We don't know when they were born, so we can't really generate a line for them
        entry += string.ljust('--', DATE_WIDTH, ' ')
    else:
        # The second column is the birth year, again padded with spaces to fill the slot
        entry += string.ljust(str(row['birth']), DATE_WIDTH, ' ')

        # For each ten year census date...
        for date in range(earliest_census, latest_census+1, 10):
            # ... determine their age at this year
            age = date - int(row['birth'])
            if age < 0:
                # ... if they weren't born yet, pad with spaces
                entry += string.ljust('', DATE_WIDTH, ' ')
            elif date <= final:
                # ... and if they weren't dead yet, generate a year entry
                entry += string.ljust(str(age), DATE_WIDTH, ' ')
            else:
                # ... but if they ARE dead, more spaces for the slot
                entry += string.ljust('', DATE_WIDTH, ' ')

    # e.g.:
    #     Jabez W Crouch              1813        7     17    27    37    47    57
    return entry


def fingerprint(gedcom, target, offset):
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
    target_row['id'] = target_row['id'].upper()
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
    modulo = 10-offset
    earliest_census = int(math.ceil(earliest_date / modulo) * modulo)
    latest_census = int(math.floor(latest_date / modulo) * modulo)

    # Collect the fingerprint strings generated for each row of entity data
    entries = []
    entries.append( generate_fingerprint(None, longest_id, earliest_census, latest_census))
    for row in rows:
        entries.append( generate_fingerprint(row, longest_id, earliest_census, latest_census))

    # Print the fingerprint chart itself
    print
    print string.upper("FINGERPRINT FOR {}".format(string.join(target.name(), ' ')))


    birth = target.birth()
    print "   Birth - " + birth[1] + " @ " + birth[0]

    residences = target.residences()
    for residence in residences:
        print "   Residence - " + residence[1] + " @ " + residence[0]

    marriages = gedcom.marriages(target)
    for marriage in marriages:
        print "   Marriage - " + marriage[1] + " @ " + marriage[0]

    death = target.death()
    print "   Death - " + death[1] + " @ " + death[0]

    print
    for entry in entries:
        print entry
    print



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("gedfilename", help="File and path to the GEDcom file")
    parser.add_argument("-s", "--state", action="store_true", help="Report on the five-year mark and not on the decade")
    parser.add_argument("-f", "--firstname", help="First name of the person to fingerprint")
    parser.add_argument("-m", "--middlename", help="Middle name of the person to fingerprint")
    parser.add_argument("-l", "--lastname", help="Last name of the person to fingerprint")

    args = parser.parse_args()

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
            fingerprint(gedcom, element, offset)
