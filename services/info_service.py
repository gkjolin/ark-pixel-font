import logging
import os

import minify_html
from PIL import Image, ImageFont, ImageDraw

import configs
from configs import font_define, workspace_define
from utils import unicode_util, gb2312_util, big5_util, shift_jis_util, ks_x_1001_util

logger = logging.getLogger('info-service')


def _get_unicode_char_count_infos(alphabet_map):
    positions = set()
    count_map = {}
    for size_mode in configs.size_modes:
        count_map[size_mode] = {}
        alphabet = alphabet_map[size_mode]
        for c in alphabet:
            code_point = ord(c)
            i, _ = unicode_util.index_block_by_code_point(configs.unicode_blocks, code_point)
            positions.add(i)
            count = count_map[size_mode].get(i, 0)
            count += 1
            count_map[size_mode][i] = count
    positions = list(positions)
    positions.sort()
    return [(configs.unicode_blocks[i], count_map['monospaced'].get(i, 0), count_map['proportional'].get(i, 0)) for i in positions]


def _get_gb2312_char_count_infos(alphabet_map):
    count_map = {}
    for size_mode in configs.size_modes:
        count_map[size_mode] = {}
        alphabet = alphabet_map[size_mode]
        for c in alphabet:
            block_name = gb2312_util.query_block(c)
            if block_name:
                block_count = count_map[size_mode].get(block_name, 0)
                block_count += 1
                count_map[size_mode][block_name] = block_count
                total_count = count_map[size_mode].get('total', 0)
                total_count += 1
                count_map[size_mode]['total'] = total_count
    return [
        ('一级汉字', count_map['monospaced'].get('level-1', 0), count_map['proportional'].get('level-1', 0), gb2312_util.alphabet_level_1_count),
        ('二级汉字', count_map['monospaced'].get('level-2', 0), count_map['proportional'].get('level-2', 0), gb2312_util.alphabet_level_2_count),
        ('其他字符', count_map['monospaced'].get('other', 0), count_map['proportional'].get('other', 0), gb2312_util.alphabet_other_count),
        ('总计', count_map['monospaced'].get('total', 0), count_map['proportional'].get('total', 0), gb2312_util.alphabet_count)
    ]


def _get_big5_char_count_infos(alphabet_map):
    count_map = {}
    for size_mode in configs.size_modes:
        count_map[size_mode] = {}
        alphabet = alphabet_map[size_mode]
        for c in alphabet:
            block_name = big5_util.query_block(c)
            if block_name:
                block_count = count_map[size_mode].get(block_name, 0)
                block_count += 1
                count_map[size_mode][block_name] = block_count
                total_count = count_map[size_mode].get('total', 0)
                total_count += 1
                count_map[size_mode]['total'] = total_count
    return [
        ('常用汉字', count_map['monospaced'].get('level-1', 0), count_map['proportional'].get('level-1', 0), big5_util.alphabet_level_1_count),
        ('次常用汉字', count_map['monospaced'].get('level-2', 0), count_map['proportional'].get('level-2', 0), big5_util.alphabet_level_2_count),
        ('标点符号、希腊字母、特殊符号，九个计量用汉字', count_map['monospaced'].get('other', 0), count_map['proportional'].get('other', 0), big5_util.alphabet_other_count),
        ('总计', count_map['monospaced'].get('total', 0), count_map['proportional'].get('total', 0), big5_util.alphabet_count)
    ]


def _get_shift_jis_char_count_infos(alphabet_map):
    count_map = {}
    for size_mode in configs.size_modes:
        count_map[size_mode] = {}
        alphabet = alphabet_map[size_mode]
        for c in alphabet:
            block_name = shift_jis_util.query_block(c)
            if block_name:
                block_count = count_map[size_mode].get(block_name, 0)
                block_count += 1
                count_map[size_mode][block_name] = block_count
                total_count = count_map[size_mode].get('total', 0)
                total_count += 1
                count_map[size_mode]['total'] = total_count
    return [
        ('单字节-ASCII字符', count_map['monospaced'].get('single-ascii', 0), count_map['proportional'].get('single-ascii', 0), shift_jis_util.alphabet_single_ascii_count),
        ('单字节-半角标点和片假名', count_map['monospaced'].get('single-other', 0), count_map['proportional'].get('single-other', 0), shift_jis_util.alphabet_single_other_count),
        ('双字节-假名和其他字符', count_map['monospaced'].get('double-basic', 0), count_map['proportional'].get('double-basic', 0), shift_jis_util.alphabet_double_basic_count),
        ('双字节-汉字', count_map['monospaced'].get('double-word', 0), count_map['proportional'].get('double-word', 0), shift_jis_util.alphabet_double_word_count),
        ('总计', count_map['monospaced'].get('total', 0), count_map['proportional'].get('total', 0), shift_jis_util.alphabet_count)
    ]


def _get_ks_x_1001_char_count_infos(alphabet_map):
    count_map = {}
    for size_mode in configs.size_modes:
        count_map[size_mode] = {}
        alphabet = alphabet_map[size_mode]
        for c in alphabet:
            block_name = ks_x_1001_util.query_block(c)
            if block_name:
                block_count = count_map[size_mode].get(block_name, 0)
                block_count += 1
                count_map[size_mode][block_name] = block_count
                total_count = count_map[size_mode].get('total', 0)
                total_count += 1
                count_map[size_mode]['total'] = total_count
    return [
        ('谚文音节', count_map['monospaced'].get('syllable', 0), count_map['proportional'].get('syllable', 0), ks_x_1001_util.alphabet_syllable_count),
        ('汉字', count_map['monospaced'].get('word', 0), count_map['proportional'].get('word', 0), ks_x_1001_util.alphabet_word_count),
        ('其他字符', count_map['monospaced'].get('other', 0), count_map['proportional'].get('other', 0), ks_x_1001_util.alphabet_other_count),
        ('总计', count_map['monospaced'].get('total', 0), count_map['proportional'].get('total', 0), ks_x_1001_util.alphabet_count)
    ]


def _write_unicode_char_count_infos_table(file, infos):
    file.write('| 区块范围 | 区块名称 | 区块含义 | 等宽体覆盖数 | 等宽体覆盖率 | 比例体覆盖数 | 比例体覆盖率 |\n')
    file.write('|---|---|---|---:|---:|---:|---:|\n')
    for unicode_block, monospaced_count, proportional_count in infos:
        code_point_range = f'0x{unicode_block.begin:04X}~0x{unicode_block.end:04X}'
        monospaced_progress = monospaced_count / unicode_block.char_count
        monospaced_finished_emoji = "🚩" if monospaced_count == unicode_block.char_count else "🚧"
        proportional_progress = proportional_count / unicode_block.char_count
        proportional_finished_emoji = "🚩" if proportional_count == unicode_block.char_count else "🚧"
        file.write(f'| {code_point_range} | {unicode_block.name} | {unicode_block.name_cn if unicode_block.name_cn else ""} | {monospaced_count} / {unicode_block.char_count} | {monospaced_progress:.2%} {monospaced_finished_emoji} | {proportional_count} / {unicode_block.char_count} | {proportional_progress:.2%} {proportional_finished_emoji} |\n')


def _write_locale_char_count_infos_table(file, infos):
    file.write('| 区块名称 | 等宽体覆盖数 | 等宽体覆盖率 | 比例体覆盖数 | 比例体覆盖率 |\n')
    file.write('|---|---:|---:|---:|---:|\n')
    for title, monospaced_count, proportional_count, total in infos:
        monospaced_progress = monospaced_count / total
        monospaced_finished_emoji = "🚩" if monospaced_count == total else "🚧"
        proportional_progress = proportional_count / total
        proportional_finished_emoji = "🚩" if proportional_count == total else "🚧"
        file.write(f'| {title} | {monospaced_count} / {total} | {monospaced_progress:.2%} {monospaced_finished_emoji} | {proportional_count} / {total} | {proportional_progress:.2%} {proportional_finished_emoji} |\n')


def make_info_file(font_config, alphabet_map):
    file_output_path = os.path.join(workspace_define.outputs_dir, font_config.get_ext_file_name('font-info', 'md'))
    with open(file_output_path, 'w', encoding='utf-8') as file:
        file.write(f'# {font_config.display_name}\n')
        file.write('\n')
        file.write('## 基本信息\n')
        file.write('\n')
        file.write('| 属性 | 值 |\n')
        file.write('|---|---|\n')
        file.write(f'| 字体名称 | {font_config.display_name} |\n')
        file.write(f'| 像素尺寸 | {font_config.px}px |\n')
        file.write(f'| 推荐行高 | {font_config.line_height_px}px |\n')
        file.write(f'| 版本号 | {font_define.version} |\n')
        file.write(f'| 等宽字符总数 | {len(alphabet_map["monospaced"])} |\n')
        file.write(f'| 比例字符总数 | {len(alphabet_map["proportional"])} |\n')
        file.write('\n')
        file.write('## Unicode 字符分布\n')
        file.write('\n')
        file.write(f'区块定义参考：[{unicode_util.blocks_doc_url}]({unicode_util.blocks_doc_url})\n')
        file.write('\n')
        _write_unicode_char_count_infos_table(file, _get_unicode_char_count_infos(alphabet_map))
        file.write('\n')
        file.write('## GB2312 字符分布\n')
        file.write('\n')
        file.write('简体中文参考字符集。统计范围不包含 ASCII，和 Unicode 有交集。\n')
        file.write('\n')
        _write_locale_char_count_infos_table(file, _get_gb2312_char_count_infos(alphabet_map))
        file.write('\n')
        file.write('## Big5 字符分布\n')
        file.write('\n')
        file.write('繁体中文参考字符集。统计范围不包含 ASCII，和 Unicode 有交集。\n')
        file.write('\n')
        _write_locale_char_count_infos_table(file, _get_big5_char_count_infos(alphabet_map))
        file.write('\n')
        file.write('## Shift-JIS 字符分布\n')
        file.write('\n')
        file.write('日语参考字符集。和 Unicode 有交集。\n')
        file.write('\n')
        _write_locale_char_count_infos_table(file, _get_shift_jis_char_count_infos(alphabet_map))
        file.write('\n')
        file.write('## KS X 1001 字符分布\n')
        file.write('\n')
        file.write('韩语参考字符集。统计范围不包含 ASCII，和 Unicode 有交集。\n')
        file.write('\n')
        _write_locale_char_count_infos_table(file, _get_ks_x_1001_char_count_infos(alphabet_map))
    logger.info(f'make {file_output_path}')


def make_preview_image_file(font_config):
    image_fonts = {}
    for size_mode in configs.size_modes:
        image_fonts[size_mode] = {}
        for locale_flavor in configs.locale_flavors:
            otf_file_path = os.path.join(workspace_define.outputs_dir, font_config.get_output_font_file_name(size_mode, locale_flavor, 'otf'))
            image_fonts[size_mode][locale_flavor] = ImageFont.truetype(otf_file_path, font_config.px)
    monospaced_offset = (font_config.line_height_px - font_config.px) / 2
    image = Image.new('RGBA', (font_config.line_height_px * 35, font_config.px * 2 + font_config.line_height_px * 11), (255, 255, 255))
    ImageDraw.Draw(image).text((font_config.px, font_config.px), '方舟像素字体 / Ark Pixel Font', fill=(0, 0, 0), font=image_fonts['monospaced']['zh_cn'])
    ImageDraw.Draw(image).text((font_config.px, font_config.px + font_config.line_height_px), '我们每天度过的称之为日常的生活，其实是一个个奇迹的连续也说不定。', fill=(0, 0, 0), font=image_fonts['proportional']['zh_cn'])
    ImageDraw.Draw(image).text((font_config.px, font_config.px + font_config.line_height_px * 2), '我們每天度過的稱之為日常的生活，其實是一個個奇跡的連續也說不定。', fill=(0, 0, 0), font=image_fonts['proportional']['zh_hk'])
    ImageDraw.Draw(image).text((font_config.px, font_config.px + font_config.line_height_px * 3), '日々、私たちが過ごしている日常は、実は奇跡の連続なのかもしれない。', fill=(0, 0, 0), font=image_fonts['proportional']['ja'])
    ImageDraw.Draw(image).text((font_config.px, font_config.px + font_config.line_height_px * 4), 'THE QUICK BROWN FOX JUMPS OVER A LAZY DOG.', fill=(0, 0, 0), font=image_fonts['proportional']['zh_cn'])
    ImageDraw.Draw(image).text((font_config.px, font_config.px + font_config.line_height_px * 5), 'the quick brown fox jumps over a lazy dog.', fill=(0, 0, 0), font=image_fonts['proportional']['zh_cn'])
    ImageDraw.Draw(image).text((font_config.px, font_config.px + font_config.line_height_px * 6 + monospaced_offset), 'THE QUICK BROWN FOX JUMPS OVER A LAZY DOG.', fill=(0, 0, 0), font=image_fonts['monospaced']['zh_cn'])
    ImageDraw.Draw(image).text((font_config.px, font_config.px + font_config.line_height_px * 7 + monospaced_offset), 'the quick brown fox jumps over a lazy dog.', fill=(0, 0, 0), font=image_fonts['monospaced']['zh_cn'])
    ImageDraw.Draw(image).text((font_config.px, font_config.px + font_config.line_height_px * 8), '0123456789', fill=(0, 0, 0), font=image_fonts['proportional']['zh_cn'])
    ImageDraw.Draw(image).text((font_config.px, font_config.px + font_config.line_height_px * 9 + monospaced_offset), '0123456789', fill=(0, 0, 0), font=image_fonts['monospaced']['zh_cn'])
    ImageDraw.Draw(image).text((font_config.px, font_config.px + font_config.line_height_px * 10), '★☆☺☹♠♡♢♣♤♥♦♧☀☼♩♪♫♬☂☁⚓✈⚔☯☎☏', fill=(0, 0, 0), font=image_fonts['monospaced']['zh_cn'])
    image = image.resize((image.width * 2, image.height * 2), Image.NEAREST)
    file_output_path = os.path.join(workspace_define.outputs_dir, font_config.get_ext_file_name('preview', 'png'))
    image.save(file_output_path)
    logger.info(f'make {file_output_path}')


def make_alphabet_txt_file(font_config, alphabet_map):
    for size_mode in configs.size_modes:
        alphabet = alphabet_map[size_mode]
        file_output_path = os.path.join(workspace_define.outputs_dir, font_config.get_ext_file_name(f'alphabet-{size_mode}', 'txt'))
        with open(file_output_path, 'w', encoding='utf-8') as file:
            file.write(''.join(alphabet))
        logger.info(f'make {file_output_path}')


def make_alphabet_html_file(font_config, alphabet_map):
    template = configs.template_env.get_template('alphabet.html')
    html = template.render(
        font_config=font_config,
        size_modes=configs.size_modes,
        locale_flavors=configs.locale_flavors,
        alphabet_map=alphabet_map
    )
    html = minify_html.minify(html, minify_css=True, minify_js=True)
    file_output_path = os.path.join(workspace_define.outputs_dir, font_config.get_ext_file_name('alphabet', 'html'))
    with open(file_output_path, 'w', encoding='utf-8') as file:
        file.write(html)
    logger.info(f'make {file_output_path}')


def make_demo_html_file(font_config):
    template = configs.template_env.get_template('demo.html')
    html = template.render(
        font_config=font_config,
        size_modes=configs.size_modes,
        locale_flavors=configs.locale_flavors
    )
    html = minify_html.minify(html, minify_css=True, minify_js=True)
    file_output_path = os.path.join(workspace_define.outputs_dir, font_config.get_ext_file_name('demo', 'html'))
    with open(file_output_path, 'w', encoding='utf-8') as file:
        file.write(html)
    logger.info(f'make {file_output_path}')
