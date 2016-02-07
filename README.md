# GedcomFingerprint
Print a census "fingerprint" for someone in your Gedcom export file

You know you've done this -- gone through the family of a person of interest and written down all of their ages, in order
to compare them to a census record.  Matching the family "Fingerprint".

This little script does that for you.

You can enter as much or as little of the names as you wish, and it will print the fingerprint for all matching people.

## Usage
```
usage: main.py gedfilename [-h] [-f FIRSTNAME] [-m MIDDLENAME] [-l LASTNAME] 

positional arguments:
  gedfilename           File and path to the GEDcom file

optional arguments:
  -h, --help            show this help message and exit
  -f FIRSTNAME, --firstname FIRSTNAME
                        First name of the person to fingerprint
  -m MIDDLENAME, --middlename MIDDLENAME
                        Middle name of the person to fingerprint
  -l LASTNAME, --lastname LASTNAME
                        Last name of the person to fingerprint
```

`python fingerprint.py ~/myGedComFile.ged -l Wise -f Edwin`

## Output

```
python main.py ~/crouch.ged -l Wise -f Carl

FINGERPRINT FOR CARL WILLIAM WISE
                                  1840  1850  1860  1870  1880  1890  1900  1910  1920  1930  1940  1950  1960  1970  1980  
Wilhelm Wiese               1835  5     15    25    35                                                                      
Matilda Seth                1845        5     15    25    35    45    55    65                                              
    Carl William Wise       1877                          3     13    23    33    43    53    63                            
    Lizzie Wise             1877                          3     13    23    33    43    53    63    73                      
    ... Robert Wise         1895                                      5     15    25    35    45    55    65                
    ... Edna O Thornberry   1906                                            4     14    24    34    44    54    64    74    
    
```

* The first line is the title for the fingerprint.
* The second line are the possible Federal census dates for this fingerprinted family group.
* The outdented people are the parents of the named target person
* Then comes the named target person and all of their spouses
* Finally, indented with elipses, are the children of the named target person
* The date column after the names are the birth dates of that person
* The body of the grid are the living ages of the various people, at the time of each federal census

For state census results, which occur on the five year mark, set the flag --state (-s)

