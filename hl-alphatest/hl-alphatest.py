#!/usr/bin/env python2

from gimpfu import *
from array import array


AUTHOR           = 'Psycrow'
COPYRIGHT        = AUTHOR
COPYRIGHT_YEAR   = '2020'

LOAD_PROC        = 'hl-alphatest'


def prepare_layers(image, power):
    layers_num = len(image.layers)

    gimp.progress_init('Preparing %d %s' % (layers_num, 'layer' if layers_num == 1 else 'layers'))

    for l, layer in enumerate(image.layers):
        # Create a new layer to save the results (otherwise it will be impossible to undo the operation)
        new_layer = gimp.Layer(image, layer.name + "_hl_alphatest", layer.width, layer.height, layer.type, layer.opacity, layer.mode)
        image.add_layer(new_layer, l)
        pdb.gimp_edit_clear(new_layer)
        layer_name = layer.name

        rgn = layer.get_pixel_rgn(0, 0, layer.width, layer.height)
        colors = array('B', rgn[:, :])

        if layer.type == RGBA_IMAGE:
            for i in xrange(0, len(colors), 4):
                alpha = colors[i + 3]
                colors[i + 3] = 0 if alpha <= power else 255

        elif layer.type == GRAYA_IMAGE:
            for i in xrange(0, len(colors), 2):
                alpha = colors[i + 1]
                colors[i + 1] = 0 if alpha <= power else 255

        rgn = new_layer.get_pixel_rgn(0, 0, layer.width, layer.height)
        rgn[:, :] = colors.tostring()
        image.remove_layer(layer)
        new_layer.name = layer_name

        gimp.progress_update(l / float(layers_num))


def hl_alphatest(image, drawable, power, auto_power, dither_type, force_pal, alpha_dither):
    pdb.gimp_context_push()
    pdb.gimp_image_undo_group_start(image)

    # Gimp does not support indexed mode if the image contains layer groups, so delete them
    for layer in image.layers:
        if pdb.gimp_item_is_group(layer):
            pdb.gimp_image_merge_layer_group(image, layer)

    if not auto_power and not alpha_dither:
        prepare_layers(image, power)
    pdb.gimp_image_convert_indexed(image, dither_type, MAKE_PALETTE, 255, alpha_dither, 0, '')

    num_bytes, colormap = pdb.gimp_image_get_colormap(image)
    addition_colors = (255 - num_bytes // 3) * [0, 0, 0] if force_pal else []
    all_colors = list(colormap) + addition_colors + [0, 0, 255]
    pdb.gimp_image_set_colormap(image, len(all_colors), all_colors)

    last_index = len(all_colors) // 3 - 1
    layers_num = len(image.layers)

    gimp.progress_init('Converting %d %s to alphatest' % (layers_num, 'layer' if layers_num == 1 else 'layers'))

    for l, layer in enumerate(image.layers):
        if layer.type == INDEXED_IMAGE:
            continue

        rgn = layer.get_pixel_rgn(0, 0, layer.width, layer.height)
        indices = array('B', rgn[:, :])
        for i in xrange(0, len(indices), 2):
            idx, alpha = indices[i:i+2]
            indices[i] = last_index if alpha <= power else idx
            indices[i+1] = 255
        rgn[:, :] = indices.tostring()
        layer.flush()
        layer.update(0, 0, layer.width, layer.height)

        gimp.progress_update(l / float(layers_num))

    pdb.gimp_displays_flush()

    pdb.gimp_image_undo_group_end(image)
    pdb.gimp_context_pop()


register(
    LOAD_PROC,
    'Converts the image to color indexing mode, moving the alpha channel colors as the last index in the palette',
    '',
    AUTHOR,
    COPYRIGHT,
    COPYRIGHT_YEAR,
    'Alphatest',
    'RGBA, GRAYA',
    [
        (PF_IMAGE, 'image', 'Input image', None),
        (PF_DRAWABLE, 'drawable', 'Input drawable', None),
        (PF_SLIDER, 'power', 'Maximum alpha value {0 - 254}', 0, (0, 254, 1)),
        (PF_TOGGLE, 'auto-power', 'Auto maximum alpha value', False),
        (PF_OPTION, 'dither-type', 'The dither type to use', 0, (
            'None',
            'FS (normal)',
            'FS (reduced color bleeding)',
            'Positioned'
        )),
        (PF_TOGGLE, 'force-pal', 'Force 256 size palette', True),
        (PF_TOGGLE, 'alpha-dither', 'Use alpha dither', False),
    ],
    [],
    hl_alphatest, menu='<Image>/Image/Half-Life/'
)

main()
