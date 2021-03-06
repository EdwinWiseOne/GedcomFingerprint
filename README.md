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
   Birth - Independence, Montgomery, Kansas, USA @ 3 July 1877
   Residence - Taney, Missouri @ 1917-1918
   Residence - Independence, Montgomery, Kansas, USA @ 1880
   Residence - Rural, Taney, Missouri @ 1935
   Residence - Amador, California, USA @ 1 Apr 1940
   Residence - Amador, California, USA @ 1942
   Residence - Cedar Creek, Taney, Missouri, USA @ 1900
   Residence - Cedar Creek, Taney, Missouri, USA @ 1910
   Residence - Oliver, Taney, Missouri, USA @ 1920
   Residence - Oliver, Taney, Missouri, USA @ 1930
   Marriage -  @ 1896
   Death - Long Beach, Los Angeles, California, USA @ 17 Feb 1948

                                  1830  1840  1850  1860  1870  1880  1890  1900  1910  1920  1930  1940  1950  1960  1970  1980  
Wilhelm Wiese               1835        5     15    25    35                                                                      
Matilda Seth                1845              5     15    25    35    45    55    65                                              
    CARL WILLIAM WISE       1877                                3     13    23    33    43    53    63                            
    Lizzie Wise             1877                                3     13    23    33    43    53    63    73                      
    ... Robert Wise         1895                                            5     15    25    35    45    55    65                
    ... Edna O Thornberry   1906                                                  4     14    24    34    44    54    64    74      
    
```

* The first line is the title for the fingerprint
* The block under the title are the various residences listed for the target person
* The second title lists the possible Federal census dates for this fingerprinted family group
* The outdented people are the parents of the named target person
* Then comes the named target person and all of their spouses
* Finally, indented with elipses, are the children of the named target person
* The date column after the names are the birth dates of that person
* The body of the grid are the living ages of the various people, at the time of each federal census

For state census results, which occur on the five year mark, set the flag --state (-s)

```
python main.py ~/crouch.ged -l Wise -f Carl -s

FINGERPRINT FOR CARL WILLIAM WISE
   Birth - Independence, Montgomery, Kansas, USA @ 3 July 1877
   Residence - Taney, Missouri @ 1917-1918
   Residence - Independence, Montgomery, Kansas, USA @ 1880
   Residence - Rural, Taney, Missouri @ 1935
   Residence - Amador, California, USA @ 1 Apr 1940
   Residence - Amador, California, USA @ 1942
   Residence - Cedar Creek, Taney, Missouri, USA @ 1900
   Residence - Cedar Creek, Taney, Missouri, USA @ 1910
   Residence - Oliver, Taney, Missouri, USA @ 1920
   Residence - Oliver, Taney, Missouri, USA @ 1930
   Marriage -  @ 1896
   Death - Long Beach, Los Angeles, California, USA @ 17 Feb 1948

                                  1835  1845  1855  1865  1875  1885  1895  1905  1915  1925  1935  1945  1955  1965  1975  1985  
Wilhelm Wiese               1835  0     10    20    30    40                                                                      
Matilda Seth                1845        0     10    20    30    40    50    60    70                                              
    CARL WILLIAM WISE       1877                                8     18    28    38    48    58    68                            
    Lizzie Wise             1877                                8     18    28    38    48    58    68    78                      
    ... Robert Wise         1895                                      0     10    20    30    40    50    60    70                
    ... Edna O Thornberry   1906                                                  9     19    29    39    49    59    69    79    ```

