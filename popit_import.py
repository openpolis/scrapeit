# coding: utf-8
from pci import Popit
import tortilla



#
# This script reads popolo-compliant data from Openpolis's API
# and import them into a popit instance, using the /import api endpoint
#
# It's remarkable, because the popit instance is protected by http basic auth
# and writing permission is only granted when an api_key is provided
# providing both api key and user/password to the Popit constructor,
# it's possible to write behind the http protection
#

"""
                                           +---------------------+
                                           | ORG: Comune di Roma |
                                           +----------+----------+
                                                      |
                    +-------------------------------------------------------------------+
                    |                                 |                                 |
                    |                                 |                                 |
    +---------------+--------------+  +---------------+--------------+  +---------------+--------------+                  
    | ORG: Comune di Roma   2013   |  | ORG: Comune di Roma   2008   |  | ORG: Comune di Roma   2006   |
    +---+--------------------------+  +------------------------------+  +------------------------------+
        |
        |
        |
        |    +-----------------------------------+          +------------+               +----------+
        +----+ ORG: Consiglio Comunale Roma 2013 +---+------+ MEMBERSHIP +---------------+  PERSON  |
        |    +-----------------------------------+   |      +------------+               +----------+
        |                                            |
        |                                            |      +------------------+         +----------+
        |                                            +------+ MEMBERSHIP       +---------+  PERSON  |
        |                                                   | role: Presidente |         +----------+
        |                                                   +------------------+
        |
        |
        |    +-----------------------------------+          +-------------------+        +----------+
        +----+ ORG: Giunta Comunale Roma 2013    +---+------+ MEMBERSHIP        +--------+  PERSON  |
             +-----------------------------------+   |      | role: Sindaco     |        +----------+
                                                     |      +-------------------+
                                                     |
                                                     |      +-------------------+        +----------+
                                                     +------+ MEMBERSHIP        +--------+  PERSON  |
                                                            | role: Vicesindaco |        +----------+
                                                            +-------------------+

"""

popit = Popit(instance='pops3',
    host='popit.openpolis.it',
    user='es_admin',
    password='Vakka94',api_key='705640d779cfee8c25d03911793c939266a9a761',
    debug=False)
pops = tortilla.wrap('http://localhost:8003/pops/')

areas = pops.areas.get()

print(u"Fetching parties")
parties = pops.organizations.get(params={'classification': 'Partito o lista di elezione'})
for p in parties.results:
    p.pop('url')
print("Importing parties into popit instance @openpolis")
exp = {
    "organizations": parties.results,
}
popit.api.post('imports', data=exp)


for a in areas.results:
    print(u"Processing area {0}".format(a.name))

    a_mapit_url = [i.identifier for i in a.other_identifiers if i.scheme == 'http://mapit.openpolis.it'][0]

    print(u"  fetching persons")
    persons = pops.persons.get(params={'area_id': a.id, 'page_size': 500})
    for p in persons.results:
        p.pop('url')

    print(u"  fetching institutions")
    orgs = pops.organizations.get(params={'area_id': a.id})
    for o in orgs.results: 
        o['area_id'] = a_mapit_url
        o.pop('url')

    print(u"  fetching posts")
    posts = pops.posts.get(params={'area_id': a.id})
    for p in posts.results:
        p['area_id'] = a_mapit_url
        p.pop('url')

    print(u"  fetching memberships")
    memberships = pops.memberships.get(params={'area_id': a.id, 'page_size': 500})
    for m in memberships.results:
        m['area_id'] = a_mapit_url
        m.pop('url')

    print(u"Importing {0} into popit instance @openpolis".format(a.name))
    exp = {
        "persons": persons.results,
        "organizations": orgs.results,
        "posts": posts.results,
        "memberships": memberships.results
    }
    popit.api.post('imports', data=exp)

print("Finished")
