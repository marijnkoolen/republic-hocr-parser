from typing import Union, List, Dict
from elasticsearch import Elasticsearch
import json
import copy
from republic.config.republic_config import set_config_inventory_num
import republic.parser.republic_base_page_parser as base_parser
import republic.parser.republic_file_parser as file_parser
import republic.parser.republic_page_parser as page_parser


def create_es_scan_doc(scan_doc: dict) -> dict:
    doc = copy.deepcopy(scan_doc)
    if "lines" in doc:
        doc["lines"] = json.dumps(doc["lines"])
    return doc


def create_es_page_doc(page_doc: dict) -> dict:
    doc = copy.deepcopy(page_doc)
    for column_hocr in doc["columns"]:
        if "lines" in column_hocr:
            column_hocr["lines"] = json.dumps(column_hocr["lines"])
    return doc


def parse_es_scan_doc(scan_doc: dict) -> dict:
    if "lines" in scan_doc:
        scan_doc["lines"] = json.loads(scan_doc["lines"])
    return scan_doc


def parse_es_page_doc(page_doc: dict) -> dict:
    for column_hocr in page_doc["columns"]:
        if "lines" in column_hocr:
            if isinstance(column_hocr["lines"], str):
                column_hocr["lines"] = json.loads(column_hocr["lines"])
    return page_doc


def parse_hits_as_pages(hits: dict) -> List[dict]:
    return [parse_es_page_doc(hit["_source"]) for hit in hits]


def make_bool_query(match_fields, size: int = 10000) -> dict:
    return {
        "query": {
            "bool": {
                "must": match_fields
            }
        },
        "size": size
    }


def make_column_query(num_columns_min: int, num_columns_max: int, inventory_num: int) -> dict:
    match_fields = [
        {"match": {"inventory_num": inventory_num}},
        {
            "range": {
                "num_columns": {
                    "gte": num_columns_min,
                    "lte": num_columns_max
                }
            }
        }
    ]
    return make_bool_query(match_fields)


def retrieve_pages_by_number_of_columns(es: Elasticsearch, num_columns_min: int,
                                        num_columns_max: int, inventory_config: dict) -> list:
    query = make_column_query(num_columns_min, num_columns_max, inventory_config["inventory_num"])
    return retrieve_pages_with_query(es, query, inventory_config)


def make_page_type_query(page_type: str, year: Union[int, None] = None,
                         inventory_num: Union[int, None] = None,
                         size: int = 10000) -> dict:
    match_fields = [{"match": {"page_type": page_type}}]
    if inventory_num: match_fields += [{"match": {"inventory_num": inventory_num}}]
    if year: match_fields += [{"match": {"year": year}}]
    return make_bool_query(match_fields, size)


def retrieve_page_doc(es: Elasticsearch, page_id: str, config) -> Union[dict, None]:
    if not es.exists(index=config["page_index"], doc_type=config["page_doc_type"], id=page_id):
        return None
    response = es.get(index=config["page_index"], doc_type=config["page_doc_type"], id=page_id)
    if "_source" in response:
        page_doc = parse_es_page_doc(response["_source"])
        return page_doc
    else:
        return None


def retrieve_pages_with_query(es: Elasticsearch, query: dict, config: dict) -> list:
    response = es.search(index=config["page_index"], doc_type=config["page_doc_type"], body=query)
    if response['hits']['total'] == 0:
        return []
    return parse_hits_as_pages(response['hits']['hits'])


def retrieve_page_by_page_number(es: Elasticsearch, page_num: int, config: dict) -> dict:
    match_fields = [{"match": {"page_num": page_num}}]
    if "inventory_num" in config: match_fields += [{"match": {"inventory_num": config["inventory_num"]}}]
    elif "year" in config: match_fields += [{"match": {"year": config["year"]}}]
    query = make_bool_query(match_fields)
    pages = retrieve_pages_with_query(es, query, config)
    if len(pages) == 0:
        return None
    else:
        return pages[0]


def retrieve_pages_by_type(es: Elasticsearch, page_type: str, inventory_num: int, config: dict) -> List[dict]:
    query = make_page_type_query(page_type, inventory_num=inventory_num)
    return retrieve_pages_with_query(es, query, config)


def retrieve_title_pages(es: Elasticsearch, inventory_num: int, config: dict) -> list:
    return retrieve_pages_by_type(es, "title_page", inventory_num, config)


def retrieve_index_pages(es: Elasticsearch, inventory_num: int, config: dict) -> list:
    return retrieve_pages_by_type(es, "index_page", inventory_num, config)


def retrieve_resolution_pages(es: Elasticsearch, inventory_num: int, config: dict) -> list:
    return retrieve_pages_by_type(es, "resolution_page", inventory_num, config)


def retrieve_respect_pages(es: Elasticsearch, inventory_num: int, config: dict) -> list:
    return retrieve_pages_by_type(es, "respect_page", inventory_num, config)


def retrieve_paragraph_by_type_page_number(es: Elasticsearch, page_number: int, config: dict) -> list:
    match_fields = [
        {"match": {"metadata.type_page_num": page_number}},
        {"match": {"metadata.inventory_year": config["year"]}}
    ]
    query = make_bool_query(match_fields)
    response = es.search(index=config["paragraph_index"], doc_type=config["paragraph_doc_type"], body=query)
    if response["hits"]["total"] == 0:
        return []
    else:
        return [hit["_source"] for hit in response["hits"]["hits"]]


def delete_es_index(es: Elasticsearch, index: str):
    if es.indices.exists(index=index):
        print("exists, deleting")
        es.indices.delete(index=index)


def index_scan(es, scan_hocr, config):
    doc = create_es_scan_doc(scan_hocr)
    es.index(index=config["scan_index"], doc_type=config["scan_doc_type"], id=scan_hocr["scan_id"], body=doc)


def index_page(es, page_hocr, config):
    doc = create_es_page_doc(page_hocr)
    es.index(index=config["page_index"], doc_type=config["page_doc_type"], id=page_hocr["page_id"], body=doc)


def parse_inventory(es: Elasticsearch, inventory_num: int, base_config: dict, base_dir: str):
    inventory_config = set_config_inventory_num(base_config, inventory_num, base_dir)
    print(inventory_config)
    scan_files = file_parser.get_files(inventory_config["data_dir"])
    for scan_file in scan_files:
        scan_hocr = page_parser.get_scan_hocr(scan_file, inventory_config)
        if "double_page" in scan_hocr["scan_type"]:
            #print("double page scan:", scan_hocr["scan_num"], scan_hocr["scan_type"])
            pages_hocr = page_parser.parse_double_page_scan(scan_hocr, inventory_config)
            for page_hocr in pages_hocr:
                print(inventory_num, page_hocr["page_num"], page_hocr["page_type"])
                index_page(es, page_hocr, inventory_config)
        else:
            #print("NOT DOUBLE PAGE:", scan_hocr["scan_num"], scan_hocr["scan_type"])
            index_scan(es, scan_hocr, inventory_config)
            continue


def parse_pre_split_column_inventory(es: Elasticsearch, pages_info: dict, config: dict, delete_index: bool = False):
    numbering = 0
    if delete_index:
        delete_es_index(es, config["page_index"])
    for page_id in pages_info:
        numbering += 1
        if pages_info[page_id]["scan_num"] <= 0:
            continue
        if pages_info[page_id]["scan_num"] >= 700:
            continue
        page_doc = page_parser.make_page_doc(page_id, pages_info, config)
        page_doc["num_columns"] = len(page_doc["columns"])
        try:
            page_type = page_parser.get_page_type(page_doc, config, debug=False)
        except TypeError:
            print(json.dumps(page_doc, indent=2))
            raise
        page_doc["page_type"] = page_type
        page_doc["is_parseable"] = True if page_type != "bad_page" else False
        if base_parser.is_title_page(page_doc, config["title_page"]):
            numbering = 1 # reset numbering
            #page_doc["page_type"] += ["title_page"]
            page_doc["is_title_page"] = True
        else:
            page_doc["is_title_page"] = False
        page_doc["type_page_num"] = numbering
        page_doc["type_page_num_checked"] = False
        ##################################
        # DIRTY HACK FOR INVENTORY 3780! #
        if page_doc["page_num"] in [90, 565, 567]:
            if ["title_page"] not in page_doc["page_type"]:
                page_doc["page_type"] += ["title_page"]
            page_doc["is_title_page"] = True
        ##################################
        page_es_doc = create_es_page_doc(page_doc)
        print(config["inventory_num"], page_doc["page_num"], page_doc["page_type"])
        es.index(index=config["page_index"], doc_type=config["page_doc_type"], id=page_id, body=page_es_doc)
        #print(page_id, page_type, numbering)




