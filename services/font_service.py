import logging
import os.path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

import configs
from configs import font_define, workspace_define
from utils import glyph_util

logger = logging.getLogger('font-service')


def _get_glyph_name(code_point):
    if isinstance(code_point, int):
        return f'uni{code_point:04X}'
    else:
        return code_point


def _convert_point_to_open_type(point, origin_y):
    """
    转换左上角坐标系为 OpenType 坐标系
    """
    x, y = point
    y = origin_y - y
    return x, y


def _draw_glyph(design_file_path, origin_y_px, em_dot_size, is_ttf):
    logger.info(f'draw glyph by design file {design_file_path}')
    font_data, width, height = glyph_util.load_design_data_from_png(design_file_path)
    outlines = glyph_util.get_outlines_from_design_data(font_data, em_dot_size)
    if is_ttf:
        pen = TTGlyphPen(None)
    else:
        pen = T2CharStringPen(width * em_dot_size, None)
    if len(outlines) > 0:
        for outline_index, outline in enumerate(outlines):
            for point_index, point in enumerate(outline):
                point = _convert_point_to_open_type(point, origin_y_px * em_dot_size)
                if point_index == 0:
                    pen.moveTo(point)
                else:
                    pen.lineTo(point)
            if outline_index < len(outlines) - 1:
                pen.endPath()
            else:
                pen.closePath()
    else:
        pen.moveTo((0, 0))
        pen.closePath()
    advance_width = width * em_dot_size
    if is_ttf:
        return pen.glyph(), advance_width
    else:
        return pen.getCharString(), advance_width


def _draw_glyphs(glyph_info_pool, design_file_paths, origin_y_px, em_dot_size, is_ttf):
    glyph_info_map = {}
    for code_point, design_file_path in design_file_paths.items():
        if design_file_path in glyph_info_pool:
            glyph_info = glyph_info_pool[design_file_path]
        else:
            glyph_info = _draw_glyph(design_file_path, origin_y_px, em_dot_size, is_ttf)
            glyph_info_pool[design_file_path] = glyph_info
        glyph_name = _get_glyph_name(code_point)
        glyph_info_map[glyph_name] = glyph_info
    return glyph_info_map


def _create_font_builder(name_strings, units_per_em, ascent, descent, glyph_order, character_map, glyph_info_map, is_ttf):
    builder = FontBuilder(units_per_em, isTTF=is_ttf)
    builder.setupGlyphOrder(glyph_order)
    builder.setupCharacterMap(character_map)
    glyphs = {}
    advance_widths = {}
    for glyph_name in glyph_order:
        glyphs[glyph_name], advance_widths[glyph_name] = glyph_info_map[glyph_name]
    if is_ttf:
        builder.setupGlyf(glyphs)
        metrics = {glyph_name: (advance_width, glyphs[glyph_name].xMin) for glyph_name, advance_width in advance_widths.items()}
    else:
        builder.setupCFF(name_strings['psName'], {'FullName': name_strings['fullName']}, glyphs, {})
        metrics = {glyph_name: (advance_width, glyphs[glyph_name].calcBounds(None)[0]) for glyph_name, advance_width in advance_widths.items()}
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=ascent, descent=descent)
    builder.setupNameTable(name_strings)
    builder.setupOS2(sTypoAscender=ascent, usWinAscent=ascent, usWinDescent=-descent)
    builder.setupPost()
    return builder


def make_px_fonts(font_config, alphabet, design_file_paths_map):
    units_per_em, ascent, descent = font_config.get_metrics()
    glyph_order = ['.notdef']
    character_map = {}
    for c in alphabet:
        code_point = ord(c)
        glyph_name = _get_glyph_name(code_point)
        glyph_order.append(glyph_name)
        character_map[code_point] = glyph_name
    otf_glyph_info_pool = {}
    ttf_glyph_info_pool = {}
    for language_specific in configs.language_specifics:
        output_display_name = font_config.get_output_display_name(language_specific)
        output_unique_name = font_config.get_output_unique_name(language_specific)
        name_strings = {
            'copyright': font_define.copyright_string,
            'familyName': output_display_name,
            'styleName': font_define.style_name,
            'uniqueFontIdentifier': f'{output_unique_name}-{font_define.style_name};{font_define.version}',
            'fullName': output_display_name,
            'version': font_define.version,
            'psName': f'{output_unique_name}-{font_define.style_name}',
            'designer': font_define.designer,
            'description': font_define.description,
            'vendorURL': font_define.vendor_url,
            'designerURL': font_define.designer_url,
            'licenseDescription': font_define.license_description,
            'licenseInfoURL': font_define.license_info_url,
        }
        design_file_paths = design_file_paths_map[language_specific]

        otf_glyph_info_map = _draw_glyphs(otf_glyph_info_pool, design_file_paths, font_config.origin_y_px, font_config.em_dot_size, False)
        otf_builder = _create_font_builder(name_strings, units_per_em, ascent, descent, glyph_order, character_map, otf_glyph_info_map, False)
        otf_file_output_path = os.path.join(workspace_define.outputs_dir, font_config.get_output_font_file_name(language_specific, 'otf'))
        otf_builder.save(otf_file_output_path)
        logger.info(f'make {otf_file_output_path}')

        otf_builder.font.flavor = 'woff2'
        woff2_file_output_path = os.path.join(workspace_define.outputs_dir, font_config.get_output_font_file_name(language_specific, 'woff2'))
        otf_builder.save(woff2_file_output_path)
        logger.info(f'make {woff2_file_output_path}')

        ttf_glyph_info_map = _draw_glyphs(ttf_glyph_info_pool, design_file_paths, font_config.origin_y_px, font_config.em_dot_size, True)
        ttf_builder = _create_font_builder(name_strings, units_per_em, ascent, descent, glyph_order, character_map, ttf_glyph_info_map, True)
        ttf_file_output_path = os.path.join(workspace_define.outputs_dir, font_config.get_output_font_file_name(language_specific, 'ttf'))
        ttf_builder.save(ttf_file_output_path)
        logger.info(f'make {ttf_file_output_path}')
