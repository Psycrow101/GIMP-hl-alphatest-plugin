#!/usr/bin/env python2

from gimpfu import *
from array import array


AUTHOR           = 'Psycrow'
COPYRIGHT        = AUTHOR
COPYRIGHT_YEAR   = '2020'

LOAD_PROC        = 'hl-alphatest'


def hl_alphatest(image, drawable, power, dither_type):
    pdb.gimp_context_push()
    pdb.gimp_image_undo_group_start(image)

    # Gimp does not support indexed mode if the image contains layer groups, so delete them
    for layer in image.layers:
        if pdb.gimp_item_is_group(layer):
            pdb.gimp_image_merge_layer_group(image, layer)
    pdb.gimp_image_convert_indexed(image, dither_type, MAKE_PALETTE, 255, 0, 0, '')

    num_bytes, colormap = pdb.gimp_image_get_colormap(image)
    pdb.gimp_image_set_colormap(image, num_bytes + 3, list(colormap) + [0, 0, 255])

    last_index = num_bytes // 3
    layers_num = len(image.layers)

    gimp.progress_init('Converting %d %s to alphatest' % (layers_num, 'layer' if layers_num == 1 else 'layers'))

    for l, layer in enumerate(image.layers):
        if layer.type == INDEXED_IMAGE:
            continue

        rgn = layer.get_pixel_rgn(0, 0, layer.width, layer.height)
        indices = array('B', rgn[:, :])
        for i in xrange(0, len(indices), 2):
            idx, alpha = indices[i:i+2]
            indices[i], indices[i+1] = (last_index, 0) if alpha <= power else (idx, 255)
        rgn[:, :] = indices.tostring()
        layer.flush()

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
        (PF_SLIDER, 'power', 'Maximum alpha value {0 - 255}', 0, (0, 255, 1)),
        (PF_OPTION, 'dither-type', 'The dither type to use', 0, (
            'None',
            'FS (normal)',
            'FS (reduced color bleeding)',
            'Positioned'
        )),
    ],
    [],
    hl_alphatest, menu='<Image>/Image/Half-Life/'
)

main()
