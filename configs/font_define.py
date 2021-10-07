import time

display_name = 'Ark Pixel'
unique_name = 'Ark-Pixel'
output_name = 'ark-pixel'
style_name = 'Regular'
version_name = '0.0.0-dev'
version_time = time.strftime("%Y%m%d")
version = f'{version_name}-{version_time}'
copyright_string = "Copyright (c) 2021, TakWolf (https://ark-pixel-font.takwolf.com), with Reserved Font Name 'Ark Pixel'."
designer = 'TakWolf'
description = 'Ark pixel font.'
vendor_url = 'https://ark-pixel-font.takwolf.com'
designer_url = 'https://takwolf.com'
license_description = 'This Font Software is licensed under the SIL Open Font License, Version 1.1.'
license_info_url = 'https://scripts.sil.org/OFL'


class FontConfig:
    def __init__(self, px, monospaced_origin_y_px, proportional_design_px, proportional_origin_y_px, em_dot_size=100):
        # 字体信息
        self.display_name = f'{display_name} {px}px'
        self.unique_name = f'{unique_name}-{px}px'
        # 字体参数
        self.px = px
        self.monospaced_origin_y_px = monospaced_origin_y_px
        self.proportional_design_px = proportional_design_px
        self.proportional_origin_y_px = proportional_origin_y_px
        self.line_height_px = proportional_origin_y_px * 2 - px
        self.em_dot_size = em_dot_size

    def get_metrics(self, size_mode):
        units_per_em = self.px * self.em_dot_size
        if size_mode == 'monospaced':
            ascent = self.monospaced_origin_y_px * self.em_dot_size
            descent = (self.monospaced_origin_y_px - self.px) * self.em_dot_size
        else:
            ascent = self.proportional_origin_y_px * self.em_dot_size
            descent = (self.px - self.proportional_origin_y_px) * self.em_dot_size
        return units_per_em, ascent, descent

    def get_origin_y_px(self, size_mode):
        if size_mode == 'monospaced':
            return self.monospaced_origin_y_px
        else:
            return self.proportional_origin_y_px

    def get_output_display_name(self, size_mode, locale_flavor):
        return f'{display_name} {self.px}px {size_mode.capitalize()} {locale_flavor}'

    def get_output_unique_name(self, size_mode, locale_flavor):
        return f'{unique_name}-{self.px}px-{size_mode.capitalize()}-{locale_flavor}'

    def get_output_font_file_name(self, size_mode, locale_flavor, font_format):
        return f'{output_name}-{self.px}px-{size_mode}-{locale_flavor}.{font_format}'

    def get_ext_file_name(self, prefix, ext_name):
        return f'{prefix}-{self.px}px.{ext_name}'

    def get_release_zip_file_name(self, size_mode, font_format):
        return f'{output_name}-font-{self.px}px-{size_mode}-{font_format}-v{version}.zip'
