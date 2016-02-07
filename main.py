
import sys
import string
import math
from datetime import date
import argparse
from gedcom import Gedcom


date_width = 6



def generate_entity_row(entity, level):
    id = string.join(entity.name(), ' ')

    if level == 1:
        id = "    {}".format(id)
    elif level == 2:
        id = "    ... {}".format(id)

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

    if row is None:
        return generate_fingerprint_title(id_length, earliest_census, latest_census)
    else:
        return generate_fingerprint_entry(row, id_length, earliest_census, latest_census)

def generate_fingerprint_title(id_length, earliest_census, latest_census):

    title = string.ljust('', id_length + date_width, ' ')

    for date in range(earliest_census, latest_census+1, 10):
        title += string.ljust(str(date), date_width, ' ')

    return title

def generate_fingerprint_entry(row, id_length, earliest_census, latest_census):

    entry = string.ljust(row['id'], id_length, ' ')

    birth = int(row['birth'])
    final = int(row['final'])
    if birth < 0:
        entry += string.ljust('--', date_width, ' ')
    else:
        entry += string.ljust(str(row['birth']), date_width, ' ')

        for date in range(earliest_census, latest_census+1, 10):
            age = date - int(row['birth'])
            if age < 0:
                entry += string.ljust('', date_width, ' ')
            elif date <= final:
                entry += string.ljust(str(age), date_width, ' ')
            else:
                entry += string.ljust('', date_width, ' ')

    return entry


def fingerprint(gedcom, target, offset):

    rows = []

    parents = gedcom.get_parents(target)
    for parent in parents:
        rows.append(generate_entity_row(parent, 0))

    rows.append(generate_entity_row(target, 1))

    families = gedcom.families(target)
    for family in families:
        peers = gedcom.get_family_members(family, "PARENTS")
        children = gedcom.get_family_members(family, "CHIL")

        for peer in peers:
            if (peer != target):
                rows.append(generate_entity_row(peer, 1))

        for child in children:
            rows.append(generate_entity_row(child, 2))

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
    longest_id = int(math.ceil((longest_id+1) / 4.0) * 4)

    modulo = 10-offset
    earliest_census = int(math.ceil(earliest_date / modulo) * modulo)
    latest_census = int(math.floor(latest_date / modulo) * modulo)

    entries = []
    entries.append( generate_fingerprint(None, longest_id, earliest_census, latest_census))
    for row in rows:
        entries.append( generate_fingerprint(row, longest_id, earliest_census, latest_census))

    print
    print string.upper("FINGERPRINT FOR {}".format(string.join(target.name(), ' ')))

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

    if args.state:
        offset = 5
    else:
        offset = 0

    gedcom = Gedcom(args.gedfilename)


    criteria = ":".join(match_criteria)
    for element in gedcom.element_list():
        if element.criteria_match(criteria):
            fingerprint(gedcom, element, offset)
