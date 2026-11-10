#!/usr/bin/env python3

from array import array
import sys

import gi

gi.require_version('Gimp', '3.0')

gi.require_version('GimpUi', '3.0')
gi.require_version('Gegl', '0.4')
gi.require_version('Babl', '0.1')

from gi.repository import Gimp, GimpUi, Gegl, GObject, Babl, GLib

PROC_NAME   = 'plug-in-hl-alphatest'
AUTHOR      = 'Psycrow'
DATE        = '2020-2026'


def image_binarize_alpha(image, power):
    layers = image.get_layers()

    for layer in layers:
        if not layer.has_alpha():
            continue

        buffer = layer.get_buffer()
        rect = buffer.get_extent()

        babl_format = Babl.get_name(layer.get_format())

        pixel_bytes = buffer.get(rect, 1.0, babl_format, Gegl.AbyssPolicy.NONE)
        pixel_array = bytearray(pixel_bytes)

        step = layer.get_bpp()
        for i in range(step - 1, len(pixel_array), step):
            alpha = pixel_array[i]
            pixel_array[i] = 0 if alpha <= power else 255

        shadow_buffer = layer.get_shadow_buffer()
        shadow_buffer.set(rect, babl_format, bytes(pixel_array))
        shadow_buffer.flush()

        layer.merge_shadow(True)
        layer.update(rect.x, rect.y, rect.width, rect.height)


def image_convert_alphatest(image, power, dither_type, alpha_dither, quantize_after, force_pal):
    image.undo_group_start()

    # Gimp does not support indexed mode if the image contains layer groups, so delete them
    for layer in image.get_layers():
        if layer.is_group():
            layer.merge()

    if quantize_after and not alpha_dither:
        image_binarize_alpha(image, power)

    image.convert_indexed(
        dither_type,
        Gimp.ConvertPaletteType.GENERATE,
        255,
        alpha_dither,
        False,
        '')

    babl_format = Babl.format('RGBA u8')

    palette = image.get_palette()
    colormap, num_colors = palette.get_colormap(babl_format)

    if force_pal:
        colormap += (255 - num_colors) * b'\0\0\0\xff'
        num_colors = 255

    colormap += b'\0\0\xff\xff'

    palette.set_colormap(babl_format, colormap)

    last_index = num_colors
    layers = image.get_layers()
    layers_num = len(layers)

    Gimp.progress_init('Converting %d %s to alphatest' % (layers_num, 'layer' if layers_num == 1 else 'layers'))

    for l, layer in enumerate(layers):
        if layer.type() == Gimp.ImageType.INDEXED_IMAGE:
            continue

        buffer = layer.get_buffer()
        rect = buffer.get_extent()

        babl_format = Babl.get_name(layer.get_format())

        pixel_bytes = buffer.get(rect, 1.0, babl_format, Gegl.AbyssPolicy.NONE)
        pixel_array = bytearray(pixel_bytes)

        for i in range(0, len(pixel_array), 2):
            alpha = pixel_array[i+1]
            if alpha <= power:
                pixel_array[i] = last_index
            pixel_array[i+1] = 255

        buffer.set(rect, babl_format, bytes(pixel_array))
        buffer.flush()

        layer.update(rect.x, rect.y, rect.width, rect.height)
        Gimp.progress_update(l / float(layers_num))

    image.undo_group_end()


class HLAlphaTest(Gimp.PlugIn):
    def do_query_procedures(self):
        return [ PROC_NAME ]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name,
                                            Gimp.PDBProcType.PLUGIN,
                                            self.run, None)

        procedure.set_image_types("RGBA, GRAYA")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label("Half-Life Alphatest")
        procedure.add_menu_path('<Image>/Image/Half-Life/')

        procedure.set_documentation("Converts RGBA to Half-Life alphatest image",
                                    "Converts the image to color indexing mode, moving the alpha channel colors as the last index in the palette",
                                    name)
        procedure.set_attribution(AUTHOR, AUTHOR, DATE)

        procedure.add_uint_argument("power", "Alpha threshold value",
            "Alpha value above which a pixel is not transparent",
            0, 254, 127, GObject.ParamFlags.READWRITE)

        procedure.add_enum_argument("dither-type", "Dither type",
            "Dither type to use",
            Gimp.ConvertDitherType, Gimp.ConvertDitherType.NONE, GObject.ParamFlags.READWRITE)

        procedure.add_boolean_argument("alpha-dither", "Alpha dither",
            "Use alpha dither",
            False, GObject.ParamFlags.READWRITE)

        procedure.add_boolean_argument("quantize-after", "Quantize after mask",
            "Apply quantization after the alpha threshold mask has been enforced, rather than before. Ignored if alpha dither is enabled",
            True, GObject.ParamFlags.READWRITE)

        procedure.add_boolean_argument("force-pal", "Force 256 size palette",
            "Palette size will always be 256, regardless of the number of colors used",
            True, GObject.ParamFlags.READWRITE)

        return procedure

    def run(self, procedure, run_mode, image, drawables, config, run_data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(PROC_NAME)
            dialog = GimpUi.ProcedureDialog.new(procedure, config)
            dialog.fill(None)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL,
                                                       GLib.Error())

        power = config.get_property("power")
        dither_type = config.get_property("dither-type")
        alpha_dither = config.get_property("alpha-dither")
        quantize_after = config.get_property("quantize-after")
        force_pal = config.get_property("force-pal")

        image_convert_alphatest(image, power, dither_type, alpha_dither, quantize_after, force_pal)

        if run_mode == Gimp.RunMode.INTERACTIVE:
            dialog.destroy()

        Gimp.displays_flush()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)


if __name__ == '__main__':
    Gimp.main(HLAlphaTest.__gtype__, sys.argv)
