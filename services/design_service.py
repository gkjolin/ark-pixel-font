import logging
import os.path
import shutil
import unicodedata

import configs
from configs import workspace_define
from utils import fs_util, glyph_util, unicode_util

logger = logging.getLogger('design-service')


def _parse_design_file_name(design_file_name):
    """
    解析设计文件名称
    例如：'0030 zh_cn,ja.png'
    """
    params = design_file_name.replace('.png', '').split(' ')
    assert 1 <= len(params) <= 2, design_file_name
    uni_hex_name = params[0].lower() if params[0] == 'notdef' else params[0].upper()
    if len(params) >= 2:
        available_locale_flavors = params[1].lower().split(',')
        for locale_flavor in available_locale_flavors:
            assert locale_flavor in configs.locale_flavors, design_file_name
    else:
        available_locale_flavors = []
    return uni_hex_name, available_locale_flavors


def classify_design_files(font_config):
    """
    按照 Unicode 区块分类设计文件
    """
    for design_dir in configs.design_dirs:
        for size_mode in configs.size_modes:
            design_flavor_dir = os.path.join(design_dir, f'{font_config.px}', size_mode)
            if not os.path.isdir(design_flavor_dir):
                continue
            design_flavor_tmp_dir = os.path.join(design_dir, f'{font_config.px}', f'{size_mode}.tmp')
            os.rename(design_flavor_dir, design_flavor_tmp_dir)
            os.mkdir(design_flavor_dir)
            for design_file_parent_dir, _, design_file_names in os.walk(design_flavor_tmp_dir):
                for design_file_name in design_file_names:
                    if not design_file_name.endswith('.png'):
                        continue
                    design_file_from_path = os.path.join(design_file_parent_dir, design_file_name)
                    uni_hex_name, available_locale_flavors = _parse_design_file_name(design_file_name)
                    if uni_hex_name == 'notdef':
                        design_file_to_dir = design_flavor_dir
                    else:
                        code_point = int(uni_hex_name, 16)
                        _, unicode_block = unicode_util.index_block_by_code_point(configs.unicode_blocks, code_point)
                        block_dir_name = f'{unicode_block.begin:04X}-{unicode_block.end:04X} {unicode_block.name}'
                        design_file_to_dir = os.path.join(design_flavor_dir, block_dir_name)
                        if unicode_block.name == 'CJK Unified Ideographs':
                            design_file_to_dir = os.path.join(design_file_to_dir, f'{uni_hex_name[0:-2]}-')
                        fs_util.make_dirs_if_not_exists(design_file_to_dir)
                    design_file_name = f'{uni_hex_name}{" " if len(available_locale_flavors) > 0 else ""}{",".join(available_locale_flavors)}.png'
                    design_file_to_path = os.path.join(design_file_to_dir, design_file_name)
                    shutil.move(design_file_from_path, design_file_to_path)
                    logger.info(f'classify design file: {design_file_to_path}')
            shutil.rmtree(design_flavor_tmp_dir)


def verify_and_handle_design_files(font_config):
    """
    校验并格式化设计文件，并根据等宽数据生成比例数据
    """
    generated_design_proportional_dir = os.path.join(workspace_define.build_dir, 'generated_design', f'{font_config.px}', 'proportional')
    fs_util.cleanup_dir(generated_design_proportional_dir)
    for design_dir in configs.design_dirs:
        for size_mode in configs.size_modes:
            design_flavor_dir = os.path.join(design_dir, f'{font_config.px}', size_mode)
            if not os.path.isdir(design_flavor_dir):
                continue
            for design_file_parent_dir, _, design_file_names in os.walk(design_flavor_dir):
                for design_file_name in design_file_names:
                    if not design_file_name.endswith('.png'):
                        continue
                    design_file_path = os.path.join(design_file_parent_dir, design_file_name)
                    design_data, width, height = glyph_util.load_design_data_from_png(design_file_path)
                    uni_hex_name, _ = _parse_design_file_name(design_file_name)
                    if uni_hex_name == 'notdef':
                        code_point = -1
                        c = None
                    else:
                        code_point = int(uni_hex_name, 16)
                        c = chr(code_point)

                    # 校验宽度
                    if size_mode == 'monospaced':
                        east_asian_width_status = unicodedata.east_asian_width(c) if c else 'N'
                        if east_asian_width_status == 'H' or east_asian_width_status == 'Na':
                            assert width == font_config.px / 2, design_file_path
                        elif east_asian_width_status == 'F' or east_asian_width_status == 'W':
                            assert width == font_config.px, design_file_path
                        else:  # 'A' or 'N'
                            assert width == font_config.px / 2 or width == font_config.px, design_file_path

                    # 校验高度
                    if size_mode == 'monospaced':
                        assert height == font_config.px, design_file_path
                    else:
                        assert height == font_config.line_height_px, design_file_path

                    # 校验间距
                    if size_mode == 'monospaced' and 0x4E00 <= code_point <= 0x9FFF:
                        for alpha in design_data[0]:
                            assert alpha == 0, design_file_path
                        for i in range(0, len(design_data)):
                            assert design_data[i][-1] == 0, design_file_path

                    # 格式化设计文件
                    glyph_util.save_design_data_to_png(design_data, design_file_path)
                    logger.info(f'format design file: {design_file_path}')

                    # 生成对应比例数据
                    if size_mode == 'monospaced':
                        proportional_design_data = list(design_data)
                        for _ in range(font_config.proportional_origin_y_px - font_config.px):
                            proportional_design_data.insert(0, [0 for _ in range(width)])
                        for _ in range(font_config.proportional_design_px - font_config.proportional_origin_y_px):
                            proportional_design_data.append([0 for _ in range(width)])
                        proportional_design_file_path = os.path.join(generated_design_proportional_dir, design_file_name)
                        glyph_util.save_design_data_to_png(proportional_design_data, proportional_design_file_path)
                        logger.info(f'make proportional design file: {proportional_design_file_path}')


def collect_available_design(font_config):
    """
    收集可用字母表，生成设计文件映射表
    """
    alphabet_map = {}
    design_file_paths_map = {}
    for size_mode in configs.size_modes:
        design_file_paths_map[size_mode] = {}
        # 遍历文件并分组
        alphabet = set()
        common_design_file_paths = {}
        locale_design_file_paths_map = {}
        for locale_flavor in configs.locale_flavors:
            locale_design_file_paths_map[locale_flavor] = {}
        design_dirs = list(configs.design_dirs)
        if size_mode == 'proportional':
            design_dirs.insert(0, os.path.join(workspace_define.build_dir, 'generated_design'))
        for design_dir in design_dirs:
            design_flavor_dir = os.path.join(design_dir, f'{font_config.px}', size_mode)
            if not os.path.isdir(design_flavor_dir):
                continue
            for design_file_parent_dir, _, design_file_names in os.walk(design_flavor_dir):
                for design_file_name in design_file_names:
                    if not design_file_name.endswith('.png'):
                        continue
                    design_file_path = os.path.join(design_file_parent_dir, design_file_name)
                    uni_hex_name, available_locale_flavors = _parse_design_file_name(design_file_name)
                    if uni_hex_name == 'notdef':
                        common_design_file_paths['.notdef'] = design_file_path
                    else:
                        code_point = int(uni_hex_name, 16)
                        if len(available_locale_flavors) > 0:
                            for locale_flavor in configs.locale_flavors:
                                if locale_flavor in available_locale_flavors:
                                    locale_design_file_paths_map[locale_flavor][code_point] = design_file_path
                        else:
                            common_design_file_paths[code_point] = design_file_path
                            alphabet.add(chr(code_point))
        # 字母表排序
        alphabet = list(alphabet)
        alphabet.sort(key=lambda c: ord(c))
        alphabet_map[size_mode] = alphabet
        # 合并设计文件路径组
        for locale_flavor, locale_design_file_paths in locale_design_file_paths_map.items():
            design_file_paths = dict(common_design_file_paths)
            design_file_paths.update(locale_design_file_paths)
            design_file_paths_map[size_mode][locale_flavor] = design_file_paths
    return alphabet_map, design_file_paths_map
