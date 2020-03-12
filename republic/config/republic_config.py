import copy
import os
from republic.model.inventory_mapping import get_inventory_by_num


def set_config_inventory_num(default_config: dict, inventory_num: int, base_dir: str, ocr_type: str) -> dict:
    config = copy.deepcopy(default_config)
    assert(ocr_type == 'hocr' or ocr_type == 'pagexml')
    config['ocr_type'] = ocr_type
    config['base_dir'] = base_dir
    config['data_dir'] = os.path.join(config['base_dir'], f'{ocr_type}/{inventory_num}/')
    config['csv_dir'] = os.path.join(config['base_dir'], 'csv')
    config['page_index'] = f'republic_{ocr_type}_pages'
    config['scan_index'] = f'republic_{ocr_type}_scans'
    config['paragraph_index'] = f'republic_{ocr_type}_paragraphs'
    config['meeting_index'] = f'republic_{ocr_type}_meeting'
    config['meeting_doc_type'] = 'meeting'
    inv_map = get_inventory_by_num(inventory_num)
    config['year'] = inv_map['year']
    config['inventory_num'] = inventory_num
    return config


base_config = {
    'year': None,
    'inventory_num': None,
    'base_dir': None,
    'inventory_index': 'republic_inventory',
    'inventory_doc_type': 'inventory',
    'lemma_index': 'republic_lemma',
    'lemma_doc_type': 'lemma',
    'page_doc_type': 'page',
    'scan_doc_type': 'scan',
    'paragraph_doc_type': 'paragraph',
    # width numbers are pixel width
    'tiny_word_width': 15,
    'avg_char_width': 20,
    'remove_tiny_words': True,
    'remove_line_numbers': False,
    'normal_scan_width': 4840,
    'column_gap': {
        'gap_threshold': 50,
        'gap_pixel_freq_ratio': 0.75,
    },
    'word_conf_threshold': 10,
    'fulltext_char_threshold': 0.5,
    'filter_words': ['|', '{', '$', '}', '/', '\\', '[', ']', ';', ':', '(', ')', '!'],
    'index_page': {
        'left_jump_ratio_min': 0.5
    },
    'index_page_early_print': {
        'page_ref_line_threshold': 10,
        'left_jump_ratio_threshold': 0.5,
        'num_words_min': 200,
        'num_words_max': 600,
        'inventory_threshold': 3804,
    },
    'index_page_late_print': {
        'median_line_width_min': 250,
        'median_line_width_max': 400,
        'num_words_min': 200,
        'num_words_max': 500,
        'stdev_line_width_min': 100,
        'stdev_line_width_max': 400,
        'num_lines_min': 130,
        'num_lines_max': 230,
        'num_dates_threshold': 5,
        'num_page_refs_threshold': 15,
        'inventory_threshold': 3805,
        'left_jump_ratio_min': 0.5,
    },
    'resolution_page': {
        'left_jump_ratio_max': 0.3,
        'num_words_min': 700,
        'num_words_max': 1200,
    },
    'respect_page': {
        'column_min_threshold': 3,
        'column_max_threshold': 4,
        'capitalized_word_line_ratio': 0.3,
        'capital_freq_ratio': 0.5,
    },
    'title_page': {
        'min_char_width': 40,
        'min_word_height': 60,
        'min_word_num': 10,
        'num_top_half_words': 60,
        'num_top_half_chars': 150,
        'max_line_width_threshold': 1000,
        'large_word_lines_threshold': 2,
        'title_line_top_threshold': 1300,
        'max_word_num': 500
    }
}

column_config = {
    'avg_char_width': 20,
    'word_conf_threshold': 10,
}
