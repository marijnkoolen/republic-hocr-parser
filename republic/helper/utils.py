from ..fuzzy.fuzzy_keyword_searcher import score_levenshtein_distance_ratio




def get_name_for_disambiguation(proposed, base_config, es=None, debug=False):
    """get a name candidate from the namenindex.
    It keeps count of a time frame and tries to select the most likely candidate.
    TODO make this more sophisticated
    and the time stuff syntax is apparently not good
    """
    year = int(base_config['year'])
    low_date_limit =  year - 85  # or do we have delegates that are over 85?
    high_date_limit = year - 20  # 20 is a very safe upper limit

    body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "fuzzy": {
                            "fullname": {
                                "value": proposed.lower()
                            }
                        }
                    },
                    {
                        "range": {
                            "by": {"gt": low_date_limit,
                                   "lt": high_date_limit
                                   },
                        }
                    },
                    {
                        "range": {
                            "dy": {"lt": year + 50,
                                   "gt": year
                                   },
                        }

                    }
                ],
                "should": [
                    {"match":
                         {"collection":
                              {"query": "raa",
                               "boost": 2.0
                               }
                          }
                     }
                ]
            }
        },
        "from": 0,
        "size": 1000,
        "sort": "_score"
    }

    results = es.search(index="namenindex", body=body)
    candidate = None
    if results['hits']['total'] > 0:
        names = [r['_source']['geslachtsnaam'] for r in results['hits']['hits']]
        people = [r['_source']['fullname'] for r in results['hits']['hits']]
        interjections = people = [r['_source']['intrapositie'] for r in results['hits']['hits']]
        candidate = [r for r in results['hits']['hits']]
    # think about this some more
    print('nr of candidates: {}'.format(results['hits']['total']))
    if debug == True:
        print(body)
    return candidate  # ([names, people])

def one_match(matchgrp):
    """returns one (hopefully the  best) match from a list of matches"""
    gr = {}
    for sr in matchgrp:
        if gr.get(sr[1]):
            gr[sr[1]].append(sr)
        else:
            gr[sr[1]] = [sr]
    for key in gr.keys():
        nw = min(gr[key], key=lambda x: x[2])
        gr[key] = nw
    return gr


# this is straight from the python docs
from itertools import tee


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def check_overlap(a, b, minlen=1):
    overlap = set(a) & set(b)
    if len(overlap) > minlen:
        result = True
    else:
        result = False
    return result

check_overlap(range(10, 20), range(12, 30), minlen=1)

def get_span_from_regex(r):
    m = r.group(0)
    s1 = r.string.find(m)
    s2 = s1 + len(m)
    return (s1, s2)

# merge lists from stackoverflow
# https://stackoverflow.com/questions/9110837/python-simple-list-merging-based-on-intersections

def merge(lsts):
    sets = [set(lst) for lst in lsts if lst]
    merged = True
    while merged:
        merged = False
        results = []
        while sets:
            common, rest = sets[0], sets[1:]
            sets = []
            for x in rest:
                if x.isdisjoint(common):
                    sets.append(x)
                else:
                    merged = True
                    common |= x
            results.append(common)
        sets = results
    return sets

def reverse_dict(d):
    """this returns a reverse mapping of a dictionary with key:[values] as single_value:key dictionary
    which is handy for storing variants in a database"""
    return {svalue: key for key, value in d.items() for svalue in value}


def levenst_vals(x, txt):
    scores= [score_levenshtein_distance_ratio(i.form,txt) for i in x if len(i.form)>1]
    if max(scores) > 0.8:
        return max(scores)
    else:
        return None

# def marker(text='', item=None, keywords=[], searcher=None, itemtype='', color='black'):
#     kw_searcher = searcher
#     kw_searcher.index_keywords(keywords)
#     for kw in keywords:
#         provs = kw_searcher.find_candidates_new(keyword=kw, text=text)
#     if len(provs) > 0:
#         profset = provs[0].get('match_offset') or 0
#     # mt.colormap[itemtype] = color
#     for res in provs:
#         ofset = res['match_offset']
#         span = (ofset, ofset + len(res['match_string']))
#         if span not in item.spans:
#             item.set_span(span, itemtype)


